import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
import time
import re
from host_utils import HostSession
from guest_utils import GuestSession_v2
from monitor import RemoteSerialMonitor_v2, RemoteQMPMonitor_v2
from config import GUEST_PASSWD
import yhong_config
from vm import CREATE_TEST

def run_case(src_ip='0', dst_ip=None):
    HOST_IP = src_ip
    vnc_server_ip = '10.66.12.246'

    test = CREATE_TEST(case_id='rhel7_exam', guest_name='yhong-guest', timeout=600)
    id = test.get_id()

    host_session = HostSession(id)

    test.main_step_log('1. Start source vm')
    host_session.boot_guest_v3(yhong_config.CMD_X86_64, vm_alias='src')

    remote_qmp = RemoteQMPMonitor_v2(id, HOST_IP, yhong_config.QMP_PORT)
    remote_qmp.qmp_cmd_output('{"execute":"quit"}')

    test.main_step_log('2. Restart source vm')
    host_session.boot_guest_v3(yhong_config.CMD_X86_64)

    remote_qmp = RemoteQMPMonitor_v2(id, HOST_IP, yhong_config.QMP_PORT)

    test.sub_step_log('Connecting to src serial')
    serial = RemoteSerialMonitor_v2(id, HOST_IP, yhong_config.SERIAL_PORT)
    SRC_GUEST_IP = serial.vm_ip

    guest_session = GuestSession_v2(case_id=id, ip=SRC_GUEST_IP, passwd=GUEST_PASSWD)

    #guest_session.guest_cmd_output('uname -r', timeout=60)

    guest_session.guest_cmd_output('free -h', timeout=60)

    guest_session.guest_cmd_output('lsblk', timeout=60)

    guest_session.guest_cmd_output('reboot')

    test.sub_step_log('Check mem info ')
    cmd = 'free -h'
    guest_session.guest_cmd_output(cmd, timeout=60)

    guest_session.guest_cmd_output('poweroff')

    host_session.test_pass()

if __name__ == '__main__':
    run_case()