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

def run_case(src_ip='10.66.10.122', dst_ip='10.66.10.208'):
    start_time = time.time()
    SRC_HOST_IP = src_ip
    DST_HOST_IP = dst_ip
    #vnc_server_ip = '10.72.12.37'
    vnc_server_ip = '10.66.12.246'

    test = CREATE_TEST(case_id='rhel7_10022', guest_name=GUEST_NAME, dst_ip=DST_HOST_IP, timeout=1800)
    id = test.get_id()

    src_host_session = HostSession(id)

    test.main_step_log('1. Boot a guest.')
    cmd_x86_src = cmd_x86
    src_host_session.boot_guest_v2(cmd=cmd_x86_src, vm_alias='src')

    test.sub_step_log('Check the status of src guest')
    src_remote_qmp = RemoteQMPMonitor_v2(id, SRC_HOST_IP, 3333)

    test.sub_step_log('Connecting to src serial')
    src_serial = RemoteSerialMonitor_v2(id, SRC_HOST_IP, 4444)

    SRC_GUEST_IP = src_serial.ip

    print 'src guest ip :' ,SRC_GUEST_IP
    guest_session = GuestSession_v2(case_id=id, ip=SRC_GUEST_IP, passwd=GUEST_PASSWD)
    test.sub_step_log('Check dmesg info ')
    cmd = 'dmesg'
    output = guest_session.guest_cmd_output(cmd)
    if re.findall(r'Call Trace:', output):
        guest_session.test_error('Guest hit call trace')

    test.main_step_log('2. Save VM state into a compressed file in host')
    src_remote_qmp.qmp_cmd_output('{"execute":"stop"}')
    src_remote_qmp.qmp_cmd_output('{"execute":"query-status"}')
    src_remote_qmp.qmp_cmd_output('{"execute":"migrate_set_speed", "arguments": { "value": 104857600 }}')
    src_host_session.host_cmd_output(cmd='rm -rf /home/yhong/yhong-auto-project/STATEFILE.gz')
    src_remote_qmp.qmp_cmd_output('{"execute":"migrate","arguments":{"uri": "exec:gzip -c > /home/yhong/yhong-auto-project/STATEFILE.gz"}}')

    time.sleep(3)

    test.sub_step_log('Check the status of migration')
    cmd = '{"execute":"query-migrate"}'
    while True:
        output = src_remote_qmp.qmp_cmd_output(cmd)
        if re.findall(r'"remaining": 0', output):
            break
        time.sleep(2)

    time.sleep(2)
    src_remote_qmp.qmp_cmd_output('{"execute":"quit"}')

    time.sleep(2)

    test.main_step_log('3. Load the file in dest host(src host).')
    cmd_x86_dst = cmd_x86 + '-incoming \"exec: gzip -c -d /home/yhong/yhong-auto-project/STATEFILE.gz\" '
    src_host_session.boot_guest_v2(cmd=cmd_x86_dst, vm_alias='dst')

    test.sub_step_log('3.1 Login dst guest')
    dst_remote_qmp = RemoteQMPMonitor_v2(id, SRC_HOST_IP, 3333)
    while True:
        output = dst_remote_qmp.qmp_cmd_output('{"execute":"query-status"}')
        if re.findall(r'"paused"', output):
            break
        time.sleep(3)

    dst_remote_qmp.qmp_cmd_output('{"execute":"cont"}')
    dst_remote_qmp.qmp_cmd_output('{"execute":"query-status"}')

    dst_serial = RemoteSerialMonitor_v2(case_id=id, ip=SRC_HOST_IP, port=4444, logined=True)

    DST_GUEST_IP = dst_serial.ip

    print 'dst guest ip :', DST_GUEST_IP
    guest_session = GuestSession_v2(case_id=id, ip=DST_GUEST_IP, passwd=GUEST_PASSWD)

    test.main_step_log('4. Check if guest works well.')

    test.sub_step_log('4.1 Guest mouse and keyboard.')

    test.sub_step_log('4.2. Ping external host / copy file between guest and host')
    external_host_ip = '10.66.10.208'
    cmd_ping = 'ping %s -c 10' % external_host_ip
    output = guest_session.guest_cmd_output(cmd=cmd_ping)
    if re.findall(r'100% packet loss', output):
        guest_session.test_error('Ping failed')

    test.sub_step_log('4.3 dd a file inside guest.')
    cmd_dd = 'dd if=/dev/zero of=/tmp/dd.io bs=512b count=2000 oflag=direct'
    output = guest_session.guest_cmd_output(cmd=cmd_dd, timeout=60)
    if not output:
        guest_session.test_error('dd failed')

    test.sub_step_log('check dmesg info')
    cmd = 'dmesg'
    output = guest_session.guest_cmd_output(cmd=cmd)
    if re.findall(r'Call Trace:', output):
        guest_session.test_error('Guest hit call trace')

    test.sub_step_log('4.4. Reboot and then shutdown guest.')
    dst_serial.serial_cmd_output('reboot')

    dst_serial = RemoteSerialMonitor_v2(case_id=id, ip=SRC_HOST_IP, port=4444, logined=True)

    dst_serial.serial_cmd_output('shutdown -h now')

    src_host_session.test_pass()
    src_host_session.total_test_time(start_time=start_time)

if __name__ == '__main__':
    run_case()

