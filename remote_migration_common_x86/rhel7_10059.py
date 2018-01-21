import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
import time
from host_utils import HostSession
from guest_utils import GuestSession_v2
from monitor import RemoteSerialMonitor_v2, RemoteQMPMonitor_v2
from config import GUEST_PASSWD
from migration_config import cmd_x86, GUEST_NAME
import re
from vm import CREATE_TEST
import threading
import Queue
from migration_utils import ping_pong_migration

def scp_thread(session, queue, passwd, src_file, dst_file, src_ip=None, dst_ip=None, timeout=300):
    session.host_cmd_scp(passwd, src_file, dst_file, src_ip, dst_ip, timeout)

def run_case(src_ip='10.66.10.122', dst_ip='10.66.10.208'):
    SRC_HOST_IP = src_ip
    DST_HOST_IP = dst_ip
    #vnc_server_ip = '10.72.12.37'
    vnc_server_ip = '10.66.12.246'
    queue = Queue.Queue()

    cmd_x86_src = cmd_x86
    cmd_x86_dst = cmd_x86_src + '-incoming tcp:0:4000 '

    test = CREATE_TEST(case_id='rhel7_10059', guest_name=GUEST_NAME, dst_ip=DST_HOST_IP, timeout=3600)
    id = test.get_id()
    src_host_session = HostSession(id)

    test.main_step_log('1. Start source vm')
    #src_host_session.boot_guest_v2(cmd_x86_src, vm_alias='src')
    src_host_session.boot_guest_v3(cmd_x86_src, vm_alias='src')

    src_remote_qmp = RemoteQMPMonitor_v2(id, SRC_HOST_IP, 3333)

    test.sub_step_log('Connecting to src serial')
    src_serial = RemoteSerialMonitor_v2(id, SRC_HOST_IP, 4444)
    SRC_GUEST_IP = src_serial.vm_ip
    DST_GUEST_IP = SRC_GUEST_IP

    src_guest_session = GuestSession_v2(case_id=id, ip=SRC_GUEST_IP, passwd=GUEST_PASSWD)
    test.sub_step_log('Check dmesg info ')
    cmd = 'dmesg'
    output = src_guest_session.guest_cmd_output(cmd)
    if re.findall(r'Call Trace:', output):
        src_guest_session.test_error('Guest hit call trace')

    test.main_step_log('2. Create a file in host')
    #src_host_session.host_cmd_output(cmd='rm -rf /home/file_host', timeout=300)
    #src_host_session.host_cmd_output(cmd='rm -rf /home/file_host2', timeout=300)
    src_host_session.host_cmd(cmd='rm -rf /home/file_host')
    src_host_session.host_cmd(cmd='rm -rf /home/file_host2')

    cmd = 'dd if=/dev/urandom of=/home/file_host bs=1M count=5000 oflag=direct'
    #src_host_session.host_cmd_output(cmd, timeout=300)
    src_host_session.host_cmd_output_v2(cmd, timeout=600)

    test.main_step_log('3. Start des vm in migration-listen mode: "-incoming tcp:0:****"')
    #src_host_session.boot_remote_guest(ip='10.66.10.208', cmd=cmd_x86_dst, vm_alias='dst')
    src_host_session.boot_remote_guest_v2(ip='10.66.10.208', cmd=cmd_x86_dst, vm_alias='dst')

    dst_remote_qmp = RemoteQMPMonitor_v2(id, DST_HOST_IP, 3333)
    #src_host_session.vnc_daemon(ip=vnc_server_ip, port=58888, timeout=10)

    test.main_step_log('4. Transfer file from host to guest')

    src_guest_session.guest_cmd_output(cmd='rm -rf /home/file_guest')
    thread = threading.Thread(target=scp_thread,
                              args=(src_host_session, queue, GUEST_PASSWD,
                                    '/home/file_host', '/home/file_guest',
                                    None, SRC_GUEST_IP, 600))

    thread.name = 'scp_thread'
    thread.daemon = True
    thread.start()

    test.main_step_log('5. Start migration')
    cmd = '{"execute":"migrate", "arguments": { "uri": "tcp:10.66.10.208:4000" }}'
    src_remote_qmp.qmp_cmd_output(cmd=cmd)

    test.sub_step_log('Check the status of migration')
    cmd = '{"execute":"query-migrate"}'
    while True:
        output = src_remote_qmp.qmp_cmd_output(cmd=cmd)
        if re.findall(r'"remaining": 0', output):
            break
        if re.findall(r'"status": "failed"', output):
            src_remote_qmp.test_error('migration failed')
        time.sleep(3)

    test.sub_step_log('Login dst guest')

    dst_guest_session = GuestSession_v2(case_id=id, ip=DST_GUEST_IP, passwd=GUEST_PASSWD)
    dst_guest_session.guest_cmd_output(cmd='dmesg')

    test.main_step_log('6. Ping-pong migrate until file transfer finished')
    src_remote_qmp, dst_remote_qmp = ping_pong_migration(test=test, cmd=cmd_x86, id=id, src_host_session=src_host_session,
                        src_remote_qmp=src_remote_qmp, dst_remote_qmp=dst_remote_qmp,
                        src_ip=SRC_HOST_IP, src_port=3333,
                        dst_ip=DST_HOST_IP, dst_port=3333, migrate_port=4000, even_times=4, query_cmd='pgrep -x scp')

    test.sub_step_log('Login dst guest after ping-pong migration')

    dst_guest_session = GuestSession_v2(case_id=id, ip=DST_GUEST_IP, passwd=GUEST_PASSWD)
    dst_guest_session.guest_cmd_output(cmd='dmesg')

    #file_src_host_md5 = src_host_session.host_cmd_output(cmd='md5sum /home/file_host')
    file_src_host_md5 = src_host_session.host_cmd_output_v2(cmd='md5sum /home/file_host')
    file_guest_md5 = dst_guest_session.guest_cmd_output(cmd='md5sum /home/file_guest')

    if file_src_host_md5.split(' ')[0] != file_guest_md5.split(' ')[0]:
        test.test_error('Value of md5sum error!')

    test.main_step_log('7. Transfer file from guest to host')
    thread = threading.Thread(target=src_host_session.host_cmd_scp,
                              args=(GUEST_PASSWD, '/home/file_guest', '/home/file_host2',
                                    DST_GUEST_IP, None, 600))
    thread.name = 'scp_thread2'
    thread.daemon = True
    thread.start()

    test.main_step_log('8. Ping-Pong migration until file transfer finished.')
    src_remote_qmp, dst_remote_qmp = ping_pong_migration(test=test, cmd=cmd_x86, id=id, src_host_session=src_host_session,
                        src_remote_qmp=src_remote_qmp, dst_remote_qmp=dst_remote_qmp,
                        src_ip=SRC_HOST_IP, src_port=3333,
                        dst_ip=DST_HOST_IP, dst_port=3333, migrate_port=4000, even_times=4, query_cmd='pgrep -x scp')

    test.main_step_log('9. Check md5sum after file transfer')

    #file_src_host_md5 = src_host_session.host_cmd_output(cmd='md5sum /home/file_host')
    file_src_host_md5 = src_host_session.host_cmd_output_v2(cmd='md5sum /home/file_host')
    #file_guest_md5 = dst_guest_session.guest_cmd_output(cmd='md5sum /home/file_guest')
    file_src_host2_md5 = src_host_session.host_cmd_output_v2(cmd='md5sum /home/file_host2')

    if file_src_host_md5.split(' ')[0] != file_src_host2_md5.split(' ')[0] \
            and file_src_host_md5.split(' ')[0] != file_guest_md5.split(' ')[0] \
            and file_src_host2_md5.split(' ')[0] != file_guest_md5.split(' ')[0] :
        test.test_error('Value of md5sum error!')

    test.sub_step_log('Login dst guest after ping-pong migration')

    dst_guest_session = GuestSession_v2(case_id=id, ip=DST_GUEST_IP, passwd=GUEST_PASSWD)
    dst_guest_session.guest_cmd_output(cmd='dmesg')

    src_host_session.test_pass()

if __name__ == '__main__':
    run_case()