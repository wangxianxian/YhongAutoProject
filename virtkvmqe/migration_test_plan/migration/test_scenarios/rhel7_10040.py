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
    DST_HOST_IP = params.get('dst_host_ip')
    qmp_port = int(params.get('vm_cmd_base')['qmp'][0].split(',')[0].split(':')[2])
    serail_port = int(params.get('vm_cmd_base')['serial'][0].split(',')[0].split(':')[2])
    incoming_port = int(params.get('incoming_port'))

    test = CREATE_TEST(case_id='rhel7_10040', params=params)
    id = test.get_id()
    src_host_session = HostSession(id, params)

    test.main_step_log('1. Boot guest with a system disk, a block data disk and a scsi data disk.')
    test.sub_step_log('1.1 Create two images on src host')
    src_host_session.host_cmd_output_v2('qemu-img create -f qcow2 /home/yhong/yhong-auto-project/images/data-disk0.qcow2 2G')
    src_host_session.host_cmd_output_v2('qemu-img create -f qcow2 /home/yhong/yhong-auto-project/images/data-disk1.qcow2 2G')

    params.vm_base_cmd_add('drive', 'file=/home/yhong/yhong-auto-project/images/data-disk0.qcow2,format=qcow2,if=none,id=drive-virtio-blk0,werror=stop,rerror=stop')
    params.vm_base_cmd_add('device', 'virtio-blk-pci,drive=drive-virtio-blk0,id=virtio-blk0,bus=pci.0,addr=10,bootindex=10')
    params.vm_base_cmd_add('drive', 'file=/home/yhong/yhong-auto-project/images/data-disk1.qcow2,if=none,id=drive_r4,format=qcow2,cache=none,aio=native,werror=stop,rerror=stop')
    params.vm_base_cmd_add('device', 'scsi-hd,drive=drive_r4,id=r4,bus=virtio_scsi_pci0.0,channel=0,scsi-id=0,lun=1')

    src_qemu_cmd = params.create_qemu_cmd()
    src_host_session.boot_guest_v3(cmd=src_qemu_cmd, vm_alias='src')
    src_remote_qmp = RemoteQMPMonitor_v2(id, params, SRC_HOST_IP, qmp_port)

    test.sub_step_log('Check guest disk')
    output = src_remote_qmp.qmp_cmd_output('{"execute":"query-block"}', recv_timeout=10)
    if not re.findall(r'drive_image1', output):
        #print 'No found system disk\n'
        src_remote_qmp.test_error('No found system disk')

    test.sub_step_log('Connecting to src serial')
    src_serial = RemoteSerialMonitor_v2(id, params, SRC_HOST_IP, serail_port)

    SRC_GUEST_IP = src_serial.serial_login()

    #print 'src guest ip :' ,SRC_GUEST_IP
    src_guest_session = GuestSession_v2(case_id=id, params=params, ip=SRC_GUEST_IP)
    test.sub_step_log('Check dmesg info ')
    cmd = 'dmesg'
    output = src_guest_session.guest_cmd_output(cmd)
    if re.findall(r'Call Trace:', output):
        src_guest_session.test_error('Guest hit call trace')

    test.main_step_log('2. In HMP, hot remove the block data disk and scsi data disk.')
    src_remote_qmp.qmp_cmd_output('{"execute":"device_del","arguments":{"id":"virtio-blk0"}}', recv_timeout=10)
    src_remote_qmp.qmp_cmd_output('{"execute":"device_del","arguments":{"id":"r4"}}', recv_timeout=10)
    test.sub_step_log('Check guest disk again')
    time.sleep(3)
    output = src_remote_qmp.qmp_cmd_output('{"execute":"query-block"}', recv_timeout=10)
    if re.findall(r'virtio-blk0', output) or re.findall(r'r4', output):
        src_remote_qmp.test_error('Failed to hot remove two data disks.')

    test.main_step_log('3. Boot guest with \'-incoming\' on des host with only system disk.')

    params.vm_base_cmd_del('drive', 'file=/home/yhong/yhong-auto-project/images/data-disk0.qcow2,format=qcow2,if=none,id=drive-virtio-blk0,werror=stop,rerror=stop')
    params.vm_base_cmd_del('device', 'virtio-blk-pci,drive=drive-virtio-blk0,id=virtio-blk0,bus=pci.0,addr=10,bootindex=10')
    params.vm_base_cmd_del('drive', 'file=/home/yhong/yhong-auto-project/images/data-disk1.qcow2,if=none,id=drive_r4,format=qcow2,cache=none,aio=native,werror=stop,rerror=stop')
    params.vm_base_cmd_del('device', 'scsi-hd,drive=drive_r4,id=r4,bus=virtio_scsi_pci0.0,channel=0,scsi-id=0,lun=1')
    incoming_val = 'tcp:0:%d' %(incoming_port)
    params.vm_base_cmd_add('incoming', incoming_val)

    dst_qemu_cmd = params.create_qemu_cmd()
    src_host_session.boot_remote_guest_v2(cmd=dst_qemu_cmd, ip=DST_HOST_IP, vm_alias='dst')

    dst_remote_qmp = RemoteQMPMonitor_v2(id, params, DST_HOST_IP, qmp_port)
    output = dst_remote_qmp.qmp_cmd_output('{"execute":"query-block"}', recv_timeout=10)
    if re.findall('virtio-blk0', output) or re.findall('r4', output):
        dst_remote_qmp.test_error('Destination guest boot error')

    test.main_step_log('4. Start live migration from src host')
    cmd = '{"execute":"migrate", "arguments": {"uri": "tcp:%s:%d"}}' % (DST_HOST_IP, incoming_port)
    src_remote_qmp.qmp_cmd_output(cmd=cmd)

    test.sub_step_log('Check the status of migration')
    cmd = '{"execute":"query-migrate"}'
    while True:
        output = src_remote_qmp.qmp_cmd_output(cmd=cmd)
        if re.findall('"remaining": 0',output):
            break
        time.sleep(3)

    test.main_step_log('5. Check guest status. Reboot guest ,  guest has 1 system disk and keeps working well.')
    dst_serial = RemoteSerialMonitor_v2(id, params, DST_HOST_IP, serail_port)

    test.sub_step_log('5.1 Reboot dst guest')
    dst_serial.serial_cmd(cmd='reboot')
    DEST_GUEST_IP = dst_serial.serial_login()    

    test.sub_step_log('5.2 Check if guest only has 1 system disk')
    output = dst_remote_qmp.qmp_cmd_output('{"execute":"query-block"}', recv_timeout=10)
    if re.findall('drive-virtio-blk0', output) or re.findall('r4', output):
        dst_remote_qmp.test_error('Destination guest has other disk except 1 system disk')

    dst_guest_session = GuestSession_v2(case_id=id, params=params, ip=DEST_GUEST_IP)
    output = dst_guest_session.guest_cmd_output(cmd='fdisk -l', timeout=60)
    if re.findall(r'/dev/sda', output):
        dst_guest_session.test_print('The system disk is in disk')

    test.sub_step_log('5.3 Can access guest from external host')
    external_host_ip = DST_HOST_IP
    cmd_ping = 'ping %s -c 10' % external_host_ip
    output = dst_guest_session.guest_cmd_output(cmd=cmd_ping)
    if re.findall(r'100% packet loss', output):
        dst_guest_session.test_error('Ping failed')

