import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
import time
from host_utils import HostSession
from guest_utils import GuestSession_v2
from monitor import RemoteSerialMonitor_v2, RemoteQMPMonitor_v2
import re
from vm import CREATE_TEST
from migration_utils import ping_pong_migration
import threading
import Queue

def scp_thread(session, queue, passwd, src_file, dst_file, src_ip=None, dst_ip=None, timeout=300):
    session.host_cmd_scp(passwd, src_file, dst_file, src_ip, dst_ip, timeout)

def run_case(params):
    SRC_HOST_IP = params.get('src_host_ip')
    DST_HOST_IP = params.get('dst_host_ip')
    qmp_port = int(params.get('vm_cmd_base')['qmp'][0].split(',')[0].split(':')[2])
    serail_port = int(params.get('vm_cmd_base')['serial'][0].split(',')[0].split(':')[2])
    guest_passwd = params.get('guest_passwd')
    guest_name = params.get('vm_cmd_base')['name'][0]
    queue = Queue.Queue()

    test = CREATE_TEST(case_id='rhel7_10059', guest_name=guest_name, dst_ip=DST_HOST_IP, timeout=3600)
    id = test.get_id()
    src_host_session = HostSession(id)

    test.main_step_log('1. Start source vm')
    params.vm_base_cmd_update('m', '4096', '2048')
    src_qemu_cmd = params.create_qemu_cmd()
    #src_host_session.boot_guest_v2(cmd_x86_src, vm_alias='src')
    src_host_session.boot_guest_v3(src_qemu_cmd, vm_alias='src')

    src_remote_qmp = RemoteQMPMonitor_v2(id, SRC_HOST_IP, qmp_port)

    test.sub_step_log('Connecting to src serial')
    src_serial = RemoteSerialMonitor_v2(id, SRC_HOST_IP, serail_port)
    SRC_GUEST_IP = src_serial.vm_ip
    DST_GUEST_IP = SRC_GUEST_IP

    src_guest_session = GuestSession_v2(case_id=id, ip=SRC_GUEST_IP, passwd=guest_passwd)
    test.sub_step_log('Check dmesg info ')
    cmd = 'dmesg'
    output = src_guest_session.guest_cmd_output(cmd)
    if re.findall(r'Call Trace:', output):
        src_guest_session.test_error('Guest hit call trace')

    test.main_step_log('2. Create a file in host')

    src_host_session.host_cmd(cmd='rm -rf /home/file_host')
    src_host_session.host_cmd(cmd='rm -rf /home/file_host2')

    cmd = 'dd if=/dev/urandom of=/home/file_host bs=1M count=5000 oflag=direct'

    src_host_session.host_cmd_output_v2(cmd, timeout=600)

    test.main_step_log('3. Start des vm in migration-listen mode: "-incoming tcp:0:****"')

    params.vm_base_cmd_update('m', '4096', '2048')
    params.vm_base_cmd_add('incoming', 'tcp:0:4000')
    dst_qemu_cmd = params.create_qemu_cmd()

    src_host_session.boot_remote_guest_v2(ip=DST_HOST_IP, cmd=dst_qemu_cmd, vm_alias='dst')

    dst_remote_qmp = RemoteQMPMonitor_v2(id, DST_HOST_IP, qmp_port)

    test.main_step_log('4. Transfer file from host to guest')

    src_guest_session.guest_cmd_output(cmd='rm -rf /home/file_guest')
    thread = threading.Thread(target=scp_thread,
                              args=(src_host_session, queue, guest_passwd,
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

    dst_guest_session = GuestSession_v2(case_id=id, ip=DST_GUEST_IP, passwd=guest_passwd)
    dst_guest_session.guest_cmd_output(cmd='dmesg')

    test.main_step_log('6. Ping-pong migrate until file transfer finished')
    src_remote_qmp, dst_remote_qmp = ping_pong_migration(params=params, test=test, cmd=src_qemu_cmd, id=id, src_host_session=src_host_session,
                        src_remote_qmp=src_remote_qmp, dst_remote_qmp=dst_remote_qmp,
                        src_ip=SRC_HOST_IP, src_port=qmp_port,
                        dst_ip=DST_HOST_IP, dst_port=qmp_port, migrate_port=4000, even_times=4, query_cmd='pgrep -x scp')

    test.sub_step_log('Login dst guest after ping-pong migration')

    dst_guest_session = GuestSession_v2(case_id=id, ip=DST_GUEST_IP, passwd=guest_passwd)
    dst_guest_session.guest_cmd_output(cmd='dmesg')

    file_src_host_md5 = src_host_session.host_cmd_output_v2(cmd='md5sum /home/file_host')
    file_guest_md5 = dst_guest_session.guest_cmd_output(cmd='md5sum /home/file_guest')

    if file_src_host_md5.split(' ')[0] != file_guest_md5.split(' ')[0]:
        test.test_error('Value of md5sum error!')

    test.main_step_log('7. Transfer file from guest to host')
    thread = threading.Thread(target=src_host_session.host_cmd_scp,
                              args=(guest_passwd, '/home/file_guest', '/home/file_host2',
                                    DST_GUEST_IP, None, 600))
    thread.name = 'scp_thread2'
    thread.daemon = True
    thread.start()

    test.main_step_log('8. Ping-Pong migration until file transfer finished.')
    src_remote_qmp, dst_remote_qmp = ping_pong_migration(params=params, test=test, cmd=src_qemu_cmd, id=id, src_host_session=src_host_session,
                        src_remote_qmp=src_remote_qmp, dst_remote_qmp=dst_remote_qmp,
                        src_ip=SRC_HOST_IP, src_port=qmp_port,
                        dst_ip=DST_HOST_IP, dst_port=qmp_port, migrate_port=4000, even_times=4, query_cmd='pgrep -x scp')

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

    dst_guest_session = GuestSession_v2(case_id=id, ip=DST_GUEST_IP, passwd=guest_passwd)
    dst_guest_session.guest_cmd_output(cmd='dmesg')

    src_host_session.test_pass()
