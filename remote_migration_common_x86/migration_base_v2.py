import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
import time
from host_utils import HostSession
from guest_utils import GuestSession_v2
from monitor import RemoteSerialMonitor_v2, RemoteQMPMonitor_v2
from log_utils import StepLog
from config import GUEST_PASSWD
from utils import subprocess_cmd_v2
import re

def run_case(timeout=60):
    start_time = time.time()
    SRC_GUEST_IP = ''
    DST_GUEST_IP = ''
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
        '-monitor stdio ' \
        '-incoming tcp:0:4000 '
    case_id = 'RHEL7-0000:'
    case_id += time.strftime("%Y-%m-%d-%H:%M:%S")
    step_log = StepLog(case_id)
    host_session = HostSession(case_id)
    step_log.sub_step_log('Checking host kernel version:')
    host_session.check_host_kernel_ver()

    step_log.sub_step_log('Checking the version of qemu:')
    host_session.check_qemu_version()

    step_log.sub_step_log('Checking yhong guest thread')
    pid = host_session.check_guest_thread()
    if pid:
        host_session.kill_guest_thread(pid)

    time.sleep(3)

    step_log.main_step_log('Step 1. Boot a guest on src host')
    #sub_guest = subprocess_cmd(cmd_x86_src, enable_output=False)
    host_session.boot_guest_v2(cmd_x86_src)

    step_log.sub_step_log('Check if guest boot up')
    host_session.check_guest_thread()

    time.sleep(5)

    step_log.sub_step_log('Check the status of src guest')
    src_remote_qmp = RemoteQMPMonitor_v2(case_id,'10.66.10.122', 3333)
    src_remote_qmp.qmp_initial()
    src_remote_qmp.qmp_cmd('"query-status"')

    step_log.sub_step_log('Connecting to src serial')
    src_serial = RemoteSerialMonitor_v2(case_id, '10.66.10.122', 4444)
    src_serial.serial_login(prompt_login=True)

    cmd = "ifconfig | grep -E 'inet ' | awk '{ print $2}'"
    SRC_GUEST_IP = src_serial.serial_get_ip()

    print 'src guest ip :' ,SRC_GUEST_IP
    guest_session = GuestSession_v2(case_id, SRC_GUEST_IP, GUEST_PASSWD)
    step_log.sub_step_log('Display pci info')
    cmd = 'lspci'
    guest_session.guest_cmd(cmd)

    step_log.main_step_log('Step 2. Boot a guest on dst host')
    cmd = 'ssh root@10.66.10.208 %s' % cmd_x86_dst
    subprocess_cmd_v2(cmd, enable_output=False)

    time.sleep(3)

    step_log.sub_step_log('Check the status of dst guest')
    dst_remote_qmp = RemoteQMPMonitor_v2(case_id, '10.66.10.208', 3333)
    dst_remote_qmp.qmp_initial()
    dst_remote_qmp.qmp_cmd('"qmp_capabilities"')
    dst_remote_qmp.qmp_cmd('"query-status"')

    step_log.main_step_log('Step 3. Migrate guest from src host to dst host')
    cmd = '"migrate", "arguments": { "uri": "tcp:10.66.10.208:4000" }'
    src_remote_qmp.qmp_cmd(cmd)

    step_log.sub_step_log('Check the status of migration')
    cmd = '"query-migrate"'
    while True:
        #output = src_remote_qmp.qmp_cmd_result(cmd)
        output = src_remote_qmp.qmp_cmd(cmd)
        if re.findall(r'"remaining": 0', output):
            break
        time.sleep(5)

    step_log.main_step_log('Step 4. Login dst guest')
    dst_serial = RemoteSerialMonitor_v2(case_id, '10.66.10.208', 4444)
    dst_serial.serial_login()

    DST_GUEST_IP = dst_serial.serial_get_ip()

    print 'dst guest ip :', DST_GUEST_IP
    guest_session = GuestSession_v2(case_id, DST_GUEST_IP, GUEST_PASSWD)
    step_log.sub_step_log('Display pci info')
    cmd = 'lspci'
    guest_session.guest_cmd(cmd)

    step_log.main_step_log('Step 5. reboot dst guest and login dmesg')
    dst_serial.serial_cmd('reboot')
    dst_serial.serial_login(prompt_login=True)
    dst_serial.serial_cmd('dmesg')
    print dst_serial.serial_output('dmesg')

    src_remote_qmp.qmp_cmd('"quit"')
    dst_remote_qmp.qmp_cmd('"quit"')
    dst_remote_qmp.close()
    dst_serial.close()
    src_serial.close()

    step_log.total_test_time(start_time)

if __name__ == '__main__':
    run_case()