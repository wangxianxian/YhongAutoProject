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

def run_case(src_ip='10.66.10.122', dst_ip='10.66.10.208'):
    start_time = time.time()
    SRC_HOST_IP = src_ip
    DST_HOST_IP = dst_ip
    #vnc_server_ip = '10.72.12.37'
    vnc_server_ip = '10.66.12.246'

    cmd_x86_src = cmd_x86
    cmd_x86_dst = cmd_x86_src + '-incoming tcp:0:4000 '

    test = CREATE_TEST(case_id='rhel7_10026', guest_name=GUEST_NAME, dst_ip=DST_HOST_IP, timeout=3600)
    id = test.get_id()
    src_host_session = HostSession(id)

    test.main_step_log('1. start vm on the src host')
    src_host_session.boot_guest_v3(cmd=cmd_x86, vm_alias='src')

    test.sub_step_log('Check the status of src guest')
    src_remote_qmp = RemoteQMPMonitor_v2(id, SRC_HOST_IP, 3333)

    test.sub_step_log('Connecting to src serial')
    src_serial = RemoteSerialMonitor_v2(case_id=id, ip=SRC_HOST_IP, port=4444)

    SRC_GUEST_IP = src_serial.vm_ip
    DST_GUEST_IP = SRC_GUEST_IP

    test.main_step_log('2.start listening mode on the dst host -incoming tcp:0:4000')
    src_host_session.boot_remote_guest_v2(ip=DST_HOST_IP, cmd=cmd_x86_dst, vm_alias='dst')

    test.sub_step_log('Check the status of src guest')
    dst_remote_qmp = RemoteQMPMonitor_v2(id, DST_HOST_IP, 3333)

    test.main_step_log('3. keep reboot vm with system_reset, let guest in bios stage, before kernel loading')
    src_remote_qmp.qmp_cmd_output('{ "execute": "system_reset" }')

    test.main_step_log('4. implement migrate during vm reboot')

    src_host_session.test_pass()

if __name__ == '__main__':
    run_case()