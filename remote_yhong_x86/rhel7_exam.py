import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
import time
from host_utils import HostSession
from guest_utils import GuestSession_v2
from monitor import RemoteSerialMonitor_v2, RemoteQMPMonitor_v2
from log_utils import StepLog
from config import GUEST_PASSWD
from yhong_config import cmd_x86
import re
from vm import CREATE_TEST

def run_case(src_ip='0', dst_ip=None, timeout=60):
    start_time = time.time()
    HOST_IP = src_ip
    vnc_server_ip = '10.66.12.246'

    test = CREATE_TEST('rhel7_exam', timeout=3600)
    id = test.get_id()

    host_session = HostSession(id)

    test.main_step_log('1. Start source vm')
    host_session.boot_guest_v2(cmd_x86)

    #host_session.vnc_daemon(ip=vnc_server_ip, port=59999, timeout=10)

    remote_qmp = RemoteQMPMonitor_v2(id, HOST_IP, 3333)

    test.sub_step_log('Connecting to src serial')
    serial = RemoteSerialMonitor_v2(id, HOST_IP, 4444)
    SRC_GUEST_IP = serial.ip

    guest_session = GuestSession_v2(case_id=id, ip=SRC_GUEST_IP, passwd=GUEST_PASSWD)
    test.sub_step_log('Check disk info ')
    cmd = 'lsblk'
    guest_session.guest_cmd_output(cmd, timeout=60)

    guest_session.guest_cmd_output('dd if=/dev/urandom of=/tmp/dd.test bs=512b count=10000 oflag=direct', timeout=300)

    guest_session.guest_cmd_output('reboot')

    serial.serial_login()

    guest_session = GuestSession_v2(case_id=id, ip=SRC_GUEST_IP, passwd=GUEST_PASSWD)
    test.sub_step_log('Check mem info ')
    cmd = 'free -h'
    guest_session.guest_cmd_output(cmd, timeout=60)

    test.sub_step_log('Quit guest')
    remote_qmp.qmp_cmd_output('{"execute":"quit"}')

    host_session.test_pass()
    host_session.total_test_time(start_time=start_time)

if __name__ == '__main__':
    run_case()