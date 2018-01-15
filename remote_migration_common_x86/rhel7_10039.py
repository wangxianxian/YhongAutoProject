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

    test = CREATE_TEST(case_id='rhel7_10039', guest_name=GUEST_NAME, dst_ip=DST_HOST_IP, timeout=1800)
    id = test.get_id()
    src_host_session = HostSession(id)

    test.main_step_log('1. Boot guest with one system disk.')
    cmd_x86_src = cmd_x86
    src_host_session.boot_guest_v2(cmd=cmd_x86_src, vm_alias='src')

    src_remote_qmp = RemoteQMPMonitor_v2(id, SRC_HOST_IP, 3333)

    test.sub_step_log('Check guest disk')
    output = src_remote_qmp.qmp_cmd_output('{"execute":"query-block"}')
    if not re.findall(r'drive_image1', output):
        print 'No found system disk\n'
        src_remote_qmp.test_error('No found system disk')

    test.sub_step_log('Connecting to src serial')
    src_serial = RemoteSerialMonitor_v2(id, SRC_HOST_IP, 4444, logined=False)

    SRC_GUEST_IP = src_serial.ip

    print 'src guest ip :' ,SRC_GUEST_IP
    src_guest_session = GuestSession_v2(case_id=id, ip=SRC_GUEST_IP, passwd=GUEST_PASSWD)
    test.sub_step_log('Check dmesg info ')
    cmd = 'dmesg'
    output = src_guest_session.guest_cmd_output(cmd)
    if re.findall(r'Call Trace:', output):
        src_guest_session.test_error('Guest hit call trace')

    test.main_step_log('2. Hot add two disk(should also in shared storage).')
    test.sub_step_log('2.1 Create two image on src host')
    src_host_session.host_cmd_output('qemu-img create -f qcow2 /home/yhong/yhong-auto-project/data-disk0.qcow2 10G')
    src_host_session.host_cmd_output('qemu-img create -f qcow2 /home/yhong/yhong-auto-project/data-disk1.qcow2 20G')

    test.sub_step_log('2.2 Hot plug the above disks')
    src_remote_qmp.qmp_cmd_output('{"execute":"__com.redhat_drive_add", "arguments":'
                           '{"file":"/home/yhong/yhong-auto-project/data-disk0.qcow2",'
                           '"format":"qcow2","id":"drive-virtio-blk0"}}')
    src_remote_qmp.qmp_cmd_output('{"execute":"device_add","arguments":{"driver":"virtio-blk-pci","drive":"drive-virtio-blk0",'
                           '"id":"virtio-blk0","bus":"pci.0","addr":"10"}}')
    src_remote_qmp.qmp_cmd_output('{"execute":"__com.redhat_drive_add", "arguments":'
                           '{"file":"/home/yhong/yhong-auto-project/data-disk1.qcow2","format":"qcow2","id":"drive_r4"}}')
    src_remote_qmp.qmp_cmd_output('{"execute":"device_add","arguments":{"driver":"scsi-hd",'
                           '"drive":"drive_r4","id":"r4","bus":"virtio_scsi_pci0.0","channel":"0","scsi-id":"0","lun":"1"}}')

    test.sub_step_log('Check the hot plug disk on src guest')
    output = src_remote_qmp.qmp_cmd_output('{"execute":"query-block"}')
    if not re.findall(r'drive-virtio-blk0', output) or not re.findall(r'drive_r4', output):
        src_remote_qmp.test_error('Hot plug disk failed on src')

    test.main_step_log('3. Boot \'-incoming\' guest with disk added in step2 on des host. ')
    cmd_x86_dst = cmd_x86 + '-drive file=/home/yhong/yhong-auto-project/data-disk0.qcow2,format=qcow2,if=none,id=drive-virtio-blk0,werror=stop,rerror=stop ' \
                            '-device virtio-blk-pci,drive=drive-virtio-blk0,id=virtio-blk0,bus=pci.0,addr=10,bootindex=10  ' \
                            '-drive file=/home/yhong/yhong-auto-project/data-disk1.qcow2,if=none,id=drive_r4,format=qcow2,cache=none,aio=native,werror=stop,rerror=stop  ' \
                            '-device scsi-hd,drive=drive_r4,id=r4,bus=virtio_scsi_pci0.0,channel=0,scsi-id=0,lun=1 ' \
                            '-incoming tcp:0:4000 '
    src_host_session.boot_remote_guest(cmd=cmd_x86_dst,ip=DST_HOST_IP, vm_alias='dst')

    dst_remote_qmp = RemoteQMPMonitor_v2(id, DST_HOST_IP, 3333)

    test.main_step_log('4. Start live migration from src host')
    cmd = '{"execute":"migrate", "arguments": { "uri": "tcp:10.66.10.208:4000" }}'
    src_remote_qmp.qmp_cmd_output(cmd=cmd)

    test.sub_step_log('Check the status of migration')
    cmd = '{"execute":"query-migrate"}'
    while True:
        output = src_remote_qmp.qmp_cmd_output(cmd=cmd)
        if re.findall(r'"remaining": 0', output):
            break
        time.sleep(3)

    test.sub_step_log('Login dst guest')
    dst_serial = RemoteSerialMonitor_v2(case_id=id, ip=DST_HOST_IP, port=4444, logined=True)

    DST_GUEST_IP = dst_serial.ip

    print 'dst guest ip :', DST_GUEST_IP

    test.sub_step_log('Check disk on dst guest')
    output = src_remote_qmp.qmp_cmd_output('{"execute":"query-block"}')
    if not re.findall(r'drive-virtio-blk0', output) or not re.findall(r'drive_r4', output):
        src_remote_qmp.test_error('Hot plug disk failed on dst')

    dst_guest_session = GuestSession_v2(case_id=id, ip=DST_GUEST_IP, passwd=GUEST_PASSWD)
    test.sub_step_log('Check dmesg info on dst guest')
    cmd = 'dmesg'
    output = dst_guest_session.guest_cmd_output(cmd=cmd)
    if re.findall(r'Call Trace:', output):
        dst_guest_session.test_error('Guest hit call trace')

    src_host_session.test_pass()
    src_host_session.total_test_time(start_time=start_time)

if __name__ == '__main__':
    run_case()
