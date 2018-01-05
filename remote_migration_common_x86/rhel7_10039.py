import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
import time
from host_utils import HostSession
from guest_utils import GuestSession_v2
from monitor import RemoteSerialMonitor_v2, RemoteQMPMonitor_v2
from log_utils import StepLog
from config import GUEST_PASSWD
import re
import threading
from utils import create_test_id

def run_case(src_ip='10.66.10.122', dst_ip='10.66.10.208', threadlock=None, timeout=60):
    start_time = time.time()
    SRC_HOST_IP = src_ip
    DST_HOST_IP = dst_ip
    #vnc_server_ip = '10.72.12.37'
    vnc_server_ip = '10.66.12.246'
    cmd_x86_src = '/usr/libexec/qemu-kvm ' \
        '-name yhong-guest ' \
        '-sandbox off ' \
        '-machine pc ' \
        '-nodefaults ' \
        '-vga std ' \
        '-device virtio-serial-pci,id=virtio_serial_pci0,bus=pci.0,addr=03 ' \
        '-chardev socket,id=console0,path=/var/tmp/serial-yhong,server,nowait ' \
        '-device virtserialport,chardev=console0,name=console0,id=console0,bus=virtio_serial_pci0.0 ' \
        '-device nec-usb-xhci,id=usb1,bus=pci.0,addr=11 ' \
        '-device virtio-scsi-pci,id=virtio_scsi_pci0,bus=pci.0,addr=04 ' \
        '-drive id=drive_image1,if=none,cache=none,format=qcow2,snapshot=off,file=/home/yhong/yhong-auto-project/rhel75-64-virtio-scsi.qcow2 ' \
        '-device scsi-hd,id=image1,drive=drive_image1,bus=virtio_scsi_pci0.0,channel=0,scsi-id=0,lun=0,bootindex=0 ' \
        '-netdev tap,vhost=on,id=idlkwV8e,script=/etc/qemu-ifup,downscript=/etc/qemu-ifdown ' \
        '-device virtio-net-pci,mac=9a:7b:7c:7d:7e:7f,id=idtlLxAk,vectors=4,netdev=idlkwV8e,bus=pci.0,addr=05 ' \
        '-m 4G ' \
        '-smp 4 ' \
        '-cpu SandyBridge ' \
        '-device usb-tablet,id=usb-tablet1,bus=usb1.0,port=2 ' \
        '-device usb-kbd,id=usb-kbd1,bus=usb1.0,port=3 ' \
        '-device usb-mouse,id=usb-mouse1,bus=usb1.0,port=4 ' \
        '-qmp tcp:0:3333,server,nowait ' \
        '-serial tcp:0:4444,server,nowait ' \
        '-vnc :30 ' \
        '-rtc base=localtime,clock=vm,driftfix=slew ' \
        '-boot order=cdn,once=c,menu=off,strict=off ' \
        '-monitor stdio'

    cmd_x86_dst = '/usr/libexec/qemu-kvm ' \
        '-name yhong-guest ' \
        '-sandbox off ' \
        '-machine pc ' \
        '-nodefaults ' \
        '-vga std ' \
        '-device virtio-serial-pci,id=virtio_serial_pci0,bus=pci.0,addr=03 ' \
        '-chardev socket,id=console0,path=/var/tmp/serial-yhong,server,nowait ' \
        '-device virtserialport,chardev=console0,name=console0,id=console0,bus=virtio_serial_pci0.0 ' \
        '-device nec-usb-xhci,id=usb1,bus=pci.0,addr=11 ' \
        '-device virtio-scsi-pci,id=virtio_scsi_pci0,bus=pci.0,addr=04 ' \
        '-drive id=drive_image1,if=none,cache=none,format=qcow2,snapshot=off,file=/home/yhong/yhong-auto-project/rhel75-64-virtio-scsi.qcow2 ' \
        '-device scsi-hd,id=image1,drive=drive_image1,bus=virtio_scsi_pci0.0,channel=0,scsi-id=0,lun=0,bootindex=0 ' \
        '-netdev tap,vhost=on,id=idlkwV8e,script=/etc/qemu-ifup,downscript=/etc/qemu-ifdown ' \
        '-device virtio-net-pci,mac=9a:7b:7c:7d:7e:7f,id=idtlLxAk,vectors=4,netdev=idlkwV8e,bus=pci.0,addr=05 ' \
        '-drive file=/home/yhong/yhong-auto-project/data-disk0.qcow2,format=qcow2,if=none,id=drive-virtio-blk0,werror=stop,rerror=stop ' \
        '-device virtio-blk-pci,drive=drive-virtio-blk0,id=virtio-blk0,bus=pci.0,addr=10,bootindex=10 ' \
        '-drive file=/home/yhong/yhong-auto-project/data-disk1.qcow2,if=none,id=drive_r4,format=qcow2,cache=none,aio=native,werror=stop,rerror=stop ' \
        '-device scsi-hd,drive=drive_r4,id=r4,bus=virtio_scsi_pci0.0,channel=0,scsi-id=0,lun=1 ' \
        '-m 4G ' \
        '-smp 4 ' \
        '-cpu SandyBridge ' \
        '-device usb-tablet,id=usb-tablet1,bus=usb1.0,port=2 ' \
        '-device usb-kbd,id=usb-kbd1,bus=usb1.0,port=3 ' \
        '-device usb-mouse,id=usb-mouse1,bus=usb1.0,port=4 ' \
        '-qmp tcp:0:3333,server,nowait ' \
        '-serial tcp:0:4444,server,nowait ' \
        '-vnc :30 ' \
        '-rtc base=localtime,clock=vm,driftfix=slew ' \
        '-boot order=cdn,once=c,menu=off,strict=off ' \
        '-incoming tcp:0:4000 ' \
        '-monitor stdio '

    #case_id = 'RHEL7-10039'
    #case_id += time.strftime(":%Y-%m-%d-%H:%M:%S")
    case_id = create_test_id('RHEL7-10039').get_id()
    step_log = StepLog(case_id)
    src_host_session = HostSession(case_id)
    step_log.sub_step_log('Checking host kernel version:')
    src_host_session.check_host_kernel_ver()

    step_log.sub_step_log('Checking the version of qemu:')
    src_host_session.check_qemu_version()

    step_log.sub_step_log('Checking yhong guest thread')
    pid = src_host_session.check_guest_thread()
    if pid:
        src_host_session.kill_guest_thread(pid)

    time.sleep(3)

    step_log.main_step_log('1. Boot guest with one system disk.')
    src_host_session.boot_guest_v2(cmd_x86_src)

    step_log.sub_step_log('Check if guest boot up')
    src_host_session.check_guest_thread()

    time.sleep(5)
    src_host_session.vnc_daemon(ip=vnc_server_ip, port=59999, timeout=10)

    step_log.sub_step_log('Check the status of src guest')
    src_remote_qmp = RemoteQMPMonitor_v2(case_id, SRC_HOST_IP, 3333)
    src_remote_qmp.qmp_initial()
    src_remote_qmp.qmp_cmd('"query-status"')

    step_log.sub_step_log('Check guest disk')
    output = src_remote_qmp.qmp_cmd('"query-block"')
    if not re.findall(r'drive_image1', output):
        print 'No found system disk\n'
        src_remote_qmp.test_error('No found system disk')

    step_log.sub_step_log('Connecting to src serial')
    src_serial = RemoteSerialMonitor_v2(case_id, SRC_HOST_IP, 4444)
    src_serial.serial_login(prompt_login=True)

    SRC_GUEST_IP = src_serial.serial_get_ip()

    print 'src guest ip :' ,SRC_GUEST_IP
    src_guest_session = GuestSession_v2(case_id=case_id, ip=SRC_GUEST_IP, passwd=GUEST_PASSWD)
    step_log.sub_step_log('Check dmesg info ')
    cmd = 'dmesg'
    output = src_guest_session.guest_cmd(cmd)
    if re.findall(r'Call Trace:', output):
        src_guest_session.test_error('Guest hit call trace')

    step_log.main_step_log('2. Hot add two disk(should also in shared storage).')
    step_log.sub_step_log('2.1 Create two image on src host')
    src_host_session.create_images('/home/yhong/yhong-auto-project/data-disk0.qcow2', '10G', 'qcow2')
    src_host_session.create_images('/home/yhong/yhong-auto-project/data-disk1.qcow2', '20G', 'qcow2')

    step_log.sub_step_log('2.2 Hot plug the above disks')
    src_remote_qmp.qmp_cmd('"__com.redhat_drive_add", "arguments":'
                           '{"file":"/home/yhong/yhong-auto-project/data-disk0.qcow2",'
                           '"format":"qcow2","id":"drive-virtio-blk0"}')
    src_remote_qmp.qmp_cmd('"device_add","arguments":{"driver":"virtio-blk-pci","drive":"drive-virtio-blk0",'
                           '"id":"virtio-blk0","bus":"pci.0","addr":"10"}')
    src_remote_qmp.qmp_cmd('"__com.redhat_drive_add", "arguments":'
                           '{"file":"/home/yhong/yhong-auto-project/data-disk1.qcow2","format":"qcow2","id":"drive_r4"}')
    src_remote_qmp.qmp_cmd('"device_add","arguments":{"driver":"scsi-hd",'
                           '"drive":"drive_r4","id":"r4","bus":"virtio_scsi_pci0.0","channel":"0","scsi-id":"0","lun":"1"}')

    step_log.sub_step_log('Check the hot plug disk on src guest')
    output = src_remote_qmp.qmp_cmd('"query-block"')
    if not re.findall(r'drive-virtio-blk0', output) or not re.findall(r'drive_r4', output):
        src_remote_qmp.test_error('Hot plug disk failed on src')

    step_log.main_step_log('3. Boot \'-incoming\' guest with disk added in step2 on des host. ')
    cmd = 'ssh root@10.66.10.208 %s' % cmd_x86_dst
    src_host_session.subprocess_cmd_v2(cmd, enable_output=False)

    time.sleep(3)
    src_host_session.vnc_daemon(ip=vnc_server_ip, port=58888, timeout=10)

    dst_remote_qmp = RemoteQMPMonitor_v2(case_id, DST_HOST_IP, 3333)
    dst_remote_qmp.qmp_initial()
    dst_remote_qmp.qmp_cmd('"query-status"')

    step_log.main_step_log('4. Start live migration from src host')
    cmd = '"migrate", "arguments": { "uri": "tcp:10.66.10.208:4000" }'
    src_remote_qmp.qmp_cmd(cmd)

    step_log.sub_step_log('Check the status of migration')
    cmd = '"query-migrate"'
    while True:
        output = src_remote_qmp.qmp_cmd(cmd)
        if re.findall(r'"remaining": 0', output):
            break
        time.sleep(5)

    step_log.sub_step_log('Login dst guest')
    dst_serial = RemoteSerialMonitor_v2(case_id, '10.66.10.208', 4444)
    dst_serial.serial_login()

    DST_GUEST_IP = dst_serial.serial_get_ip()

    print 'dst guest ip :', DST_GUEST_IP

    step_log.sub_step_log('Check disk on dst guest')
    output = src_remote_qmp.qmp_cmd('"query-block"')
    if not re.findall(r'drive-virtio-blk0', output) or not re.findall(r'drive_r4', output):
        src_remote_qmp.test_error('Hot plug disk failed on dst')

    dst_guest_session = GuestSession_v2(case_id=case_id, ip=DST_GUEST_IP, passwd=GUEST_PASSWD)
    step_log.sub_step_log('Check dmesg info on dst guest')
    cmd = 'dmesg'
    output = dst_guest_session.guest_cmd(cmd)
    if re.findall(r'Call Trace:', output):
        dst_guest_session.test_error('Guest hit call trace')

    step_log.sub_step_log('Quit src guest')
    src_remote_qmp.qmp_cmd('"quit"')
    step_log.sub_step_log('Quit dst guest')
    dst_remote_qmp.qmp_cmd('"quit"')
    src_remote_qmp.close()
    dst_remote_qmp.close()
    dst_serial.close()
    src_serial.close()

    src_host_session.test_pass()
    src_host_session.total_test_time(start_time=start_time)

if __name__ == '__main__':
    run_case()
