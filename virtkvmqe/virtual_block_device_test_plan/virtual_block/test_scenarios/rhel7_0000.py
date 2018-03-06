"""
Trial Case
"""

from host_utils import HostSession
from guest_utils import GuestSession_v2
from monitor import RemoteSerialMonitor_v2, RemoteQMPMonitor_v2

from vm import CREATE_TEST

def run_case(params):
    HOST_IP = '0'
    params.vm_base_cmd_update('device', 'virtio-scsi-pci,id=virtio_scsi_pci0,bus=pci.0,addr=0x4',
                              'virtio-scsi-pci,id=virtio_scsi_pci0,bus=pci.0,addr=0x2')
    qemu_cmd = params.create_qemu_cmd()
    qmp_port = int(params.get('vm_cmd_base')['qmp'][0].split(',')[0].split(':')[2])
    serail_port = int(params.get('vm_cmd_base')['serial'][0].split(',')[0].split(':')[2])
    guest_passwd = params.get('guest_passwd')
    guest_name = params.get('vm_cmd_base')['name'][0]

    test = CREATE_TEST(case_id='rhel7_0000', guest_name=guest_name, timeout=600)
    id = test.get_id()

    host_session = HostSession(id)

    test.main_step_log('1. Start source vm')
    host_session.boot_guest_v3(qemu_cmd, vm_alias='src')

    remote_qmp = RemoteQMPMonitor_v2(id, HOST_IP, qmp_port)
    remote_qmp.qmp_cmd_output('{"execute":"quit"}')

    test.main_step_log('2. Restart source vm')
    host_session.boot_guest_v3(qemu_cmd)

    remote_qmp = RemoteQMPMonitor_v2(id, HOST_IP, qmp_port)

    test.sub_step_log('Connecting to src serial')
    serial = RemoteSerialMonitor_v2(id, HOST_IP, serail_port)
    SRC_GUEST_IP = serial.vm_ip

    guest_session = GuestSession_v2(case_id=id, ip=SRC_GUEST_IP, passwd=guest_passwd)

    guest_session.guest_cmd_output('free -h', timeout=60)

    guest_session.guest_cmd_output('lsblk', timeout=60)

    host_session.test_pass()
