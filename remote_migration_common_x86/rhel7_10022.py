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
    #with threadlock:
    start_time = time.time()
    SRC_HOST_IP = src_ip
    DST_HOST_IP = dst_ip
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
        '-incoming \"exec: gzip -c -d /home/yhong/yhong-auto-project/STATEFILE.gz\" '

    #case_id = 'RHEL7-10022'
    #case_id += time.strftime(":%Y-%m-%d-%H:%M:%S")
    case_id = create_test_id('RHEL7-10022')
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

    step_log.main_step_log('1. Boot a guest.')
    src_host_session.boot_guest_v2(cmd_x86_src)

    step_log.sub_step_log('Check if guest boot up')
    src_host_session.check_guest_thread()

    time.sleep(5)
    src_host_session.vnc_daemon(ip='10.72.12.37', port=59999)

    step_log.sub_step_log('Check the status of src guest')
    src_remote_qmp = RemoteQMPMonitor_v2(case_id, SRC_HOST_IP, 3333)
    src_remote_qmp.qmp_initial()
    src_remote_qmp.qmp_cmd('"query-status"')

    step_log.sub_step_log('Connecting to src serial')
    src_serial = RemoteSerialMonitor_v2(case_id, SRC_HOST_IP, 4444)
    src_serial.serial_login(prompt_login=True)

    SRC_GUEST_IP = src_serial.serial_get_ip()

    print 'src guest ip :' ,SRC_GUEST_IP
    guest_session = GuestSession_v2(case_id=case_id, ip=SRC_GUEST_IP, passwd=GUEST_PASSWD)
    step_log.sub_step_log('Check dmesg info ')
    cmd = 'dmesg'
    output = guest_session.guest_cmd(cmd)
    if re.findall(r'Call Trace:', output):
        guest_session.test_error('Guest hit call trace')

    step_log.main_step_log('2. Save VM state into a compressed file in host')
    src_remote_qmp.qmp_cmd('"stop"')
    src_remote_qmp.qmp_cmd('"query-status"')
    src_remote_qmp.qmp_cmd('"migrate_set_speed", "arguments": { "value": 104857600 }')
    src_remote_qmp.qmp_cmd('"migrate","arguments":{"uri": "exec:gzip -c > /home/yhong/yhong-auto-project/STATEFILE.gz"}')

    time.sleep(3)

    step_log.sub_step_log('Check the status of migration')
    cmd = '"query-migrate"'
    while True:
        output = src_remote_qmp.qmp_cmd(cmd)
        if re.findall(r'"remaining": 0', output):
            break
        time.sleep(3)

    time.sleep(2)
    src_remote_qmp.qmp_cmd('"quit"')

    time.sleep(2)

    step_log.main_step_log('3. Load the file in dest host(src host).')
    src_host_session.boot_guest_v2(cmd_x86_dst)

    step_log.sub_step_log('Check if guest boot up')
    src_host_session.check_guest_thread()

    time.sleep(3)

    src_host_session.vnc_daemon(ip='10.72.12.37', port=59999)

    step_log.sub_step_log('3.1 Login dst guest')
    dst_remote_qmp = RemoteQMPMonitor_v2(case_id, SRC_HOST_IP, 3333)
    dst_remote_qmp.qmp_initial()
    while True:
        output = dst_remote_qmp.qmp_cmd('"query-status"')
        if re.findall(r'"paused"', output):
            break
        time.sleep(3)

    dst_remote_qmp.qmp_cmd('"cont"')
    dst_remote_qmp.qmp_cmd('"query-status"')

    dst_serial = RemoteSerialMonitor_v2(case_id, SRC_HOST_IP, 4444)
    dst_serial.serial_login()

    DST_GUEST_IP = dst_serial.serial_get_ip()

    print 'dst guest ip :', DST_GUEST_IP
    guest_session = GuestSession_v2(case_id=case_id, ip=DST_GUEST_IP, passwd=GUEST_PASSWD)

    step_log.main_step_log('4. Check if guest works well.')

    step_log.sub_step_log('4.1 Guest mouse and keyboard.')
    pass

    step_log.sub_step_log('4.2. Ping external host / copy file between guest and host')
    external_host_ip = '10.66.10.208'
    cmd_ping = 'ping %s -c 10' % external_host_ip
    output = guest_session.guest_cmd(cmd_ping)
    if re.findall(r'100% packet loss', output):
        guest_session.test_error('Ping failed')

    step_log.sub_step_log('4.3 dd a file inside guest.')
    cmd_dd = 'dd if=/dev/zero of=/tmp/dd.io bs=512b count=2000 oflag=direct'
    output = guest_session.guest_cmd(cmd_dd, timeout=60)
    if not output:
        guest_session.test_error('dd failed')

    step_log.sub_step_log('check dmesg info')
    cmd = 'dmesg'
    output = guest_session.guest_cmd(cmd)
    if re.findall(r'Call Trace:', output):
        guest_session.test_error('Guest hit call trace')

    step_log.sub_step_log('4.4. Reboot and then shutdown guest.')
    dst_serial.serial_cmd('reboot')

    dst_serial.serial_login(prompt_login=True)

    dst_serial.serial_cmd('shutdown -h now')

    src_host_session.test_pass()
    src_host_session.total_test_time(start_time=start_time)

if __name__ == '__main__':
    run_case()

