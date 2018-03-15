import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
import time
from host_utils import HostSession
from guest_utils import GuestSession_v2
from monitor import RemoteSerialMonitor_v2, RemoteQMPMonitor_v2
import re
from vm import CREATE_TEST

def run_case(params):
    SRC_HOST_IP = params.get('src_host_ip')
    DST_HOST_IP = SRC_HOST_IP

    qmp_port = int(params.get('vm_cmd_base')['qmp'][0].split(',')[0].split(':')[2])
    serail_port = int(params.get('vm_cmd_base')['serial'][0].split(',')[0].split(':')[2])

    test = CREATE_TEST(case_id='rhel7_10022', params=params)
    id = test.get_id()

    src_host_session = HostSession(id, params)

    test.main_step_log('1. Boot a guest.')
    src_qemu_cmd = params.create_qemu_cmd()
    src_host_session.boot_guest_v3(cmd=src_qemu_cmd, vm_alias='src')

    test.sub_step_log('Check the status of src guest')
    src_remote_qmp = RemoteQMPMonitor_v2(id, params, SRC_HOST_IP, qmp_port)

    test.sub_step_log('Connecting to src serial')
    src_serial = RemoteSerialMonitor_v2(case_id=id, params=params, ip=SRC_HOST_IP, port=serail_port)

    SRC_GUEST_IP = src_serial.serial_login()
    guest_session = GuestSession_v2(case_id=id, params=params, ip=SRC_GUEST_IP)
    test.sub_step_log('Check dmesg info ')
    cmd = 'dmesg'
    output = guest_session.guest_cmd_output(cmd)
    if re.findall(r'Call Trace:', output) or not output:
        guest_session.test_error('Guest hit call trace')

    test.main_step_log('2. Save VM state into a compressed file in host')
    src_remote_qmp.qmp_cmd_output('{"execute":"stop"}')
    src_remote_qmp.qmp_cmd_output('{"execute":"query-status"}')
    src_remote_qmp.qmp_cmd_output('{"execute":"migrate_set_speed", "arguments": { "value": 104857600 }}')

    src_host_session.host_cmd(cmd='rm -rf /home/yhong/yhong-auto-project/images/STATEFILE.gz')
    src_remote_qmp.qmp_cmd_output('{"execute":"migrate","arguments":{"uri": "exec:gzip -c > /home/yhong/yhong-auto-project/images/STATEFILE.gz"}}')

    time.sleep(3)

    test.sub_step_log('Check the status of migration')
    cmd = '{"execute":"query-migrate"}'
    while True:
        output = src_remote_qmp.qmp_cmd_output(cmd)
        if re.findall(r'"remaining": 0', output):
            break
        if re.findall(r'fail', output):
            test.test_error('Migrate failed!')
        time.sleep(2)

    time.sleep(2)
    src_remote_qmp.qmp_cmd_output('{"execute":"quit"}')

    time.sleep(2)

    test.main_step_log('3. Load the file in dest host(src host).')
    params.vm_base_cmd_add('incoming', '"exec: gzip -c -d /home/yhong/yhong-auto-project/images/STATEFILE.gz"')

    dst_qemu_cmd = params.create_qemu_cmd()
    src_host_session.boot_guest_v3(cmd=dst_qemu_cmd, vm_alias='dst')

    test.sub_step_log('3.1 Login dst guest')
    dst_remote_qmp = RemoteQMPMonitor_v2(id, params, DST_HOST_IP, qmp_port)
    while True:
        output = dst_remote_qmp.qmp_cmd_output('{"execute":"query-status"}')
        if re.findall(r'"paused"', output):
            break
        time.sleep(3)

    dst_remote_qmp.qmp_cmd_output('{"execute":"cont"}')
    dst_remote_qmp.qmp_cmd_output('{"execute":"query-status"}')

    time.sleep(10)
    dst_serial = RemoteSerialMonitor_v2(case_id=id, params=params, ip=SRC_HOST_IP, port=src_serial)

    guest_session = GuestSession_v2(case_id=id, params=params, ip=SRC_GUEST_IP)

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
    if re.findall(r'Call Trace:', output) or not output:
        guest_session.test_error('Guest hit call trace')

    test.sub_step_log('4.4. Reboot and then shutdown guest.')
    dst_serial.serial_cmd_output(cmd='reboot', recv_timeout=3)

    dst_serial.serial_login()

    dst_serial.serial_cmd_output(cmd='shutdown -h now', recv_timeout=3)
