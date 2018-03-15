import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
import time
from host_utils import HostSession
from monitor import RemoteSerialMonitor_v2, RemoteQMPMonitor_v2
from vm import CREATE_TEST

def run_case(params):
    SRC_HOST_IP = params.get('src_host_ip')
    DST_HOST_IP = params.get('dst_host_ip')
    src_qemu_cmd = params.create_qemu_cmd()
    qmp_port = int(params.get('vm_cmd_base')['qmp'][0].split(',')[0].split(':')[2])
    serail_port = int(params.get('vm_cmd_base')['serial'][0].split(',')[0].split(':')[2])

    test = CREATE_TEST(case_id='rhel7_10026', params=params)
    id = test.get_id()
    src_host_session = HostSession(id, params)

    test.main_step_log('1. start vm on the src host')
    src_host_session.boot_guest_v3(cmd=src_qemu_cmd, vm_alias='src')

    #test.test_error('Trigger a error!!')
    test.sub_step_log('Check the status of src guest')
    src_remote_qmp = RemoteQMPMonitor_v2(id, params, SRC_HOST_IP, qmp_port)

    test.sub_step_log('Connecting to src serial')
    src_serial = RemoteSerialMonitor_v2(case_id=id, params=params, ip=SRC_HOST_IP, port=serail_port)

    SRC_GUEST_IP = src_serial.serial_login()
    DST_GUEST_IP = SRC_GUEST_IP

    test.main_step_log('2.start listening mode on the dst host -incoming tcp:0:4000')
    params.vm_base_cmd_add('incoming', 'tcp:0:4000')
    dst_qemu_cmd = params.create_qemu_cmd()
    src_host_session.boot_remote_guest_v2(ip=DST_HOST_IP, cmd=dst_qemu_cmd, vm_alias='dst')

    test.sub_step_log('Check the status of src guest')
    dst_remote_qmp = RemoteQMPMonitor_v2(id, params, DST_HOST_IP, qmp_port)

    test.main_step_log('3. keep reboot vm with system_reset, let guest in bios stage, before kernel loading')

    test.main_step_log('4. implement migrate during vm reboot')
