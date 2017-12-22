import os, sys, subprocess
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
from utils import create_images, exc_cmd_guest, subprocess_cmd, remote_scp,remove_monitor_cmd_echo,remote_ssh_cmd
from loginfo import sub_step_log, main_step_log
import time
from monitor import Monitor, QMPMonitor
import re
import string
from config import CMD_PPC_COMMON, GUEST_PASSWD, GUEST_NAME
from guest_utils import Guest_Session
from host_utils import check_guest_thread, kill_guest_thread, check_host_kernel_ver, check_qemu_version

if __name__ == '__main__':
    start_time = time.time()
    cmd_x86_src = '/usr/libexec/qemu-kvm ' \
        '-name yhong-guest ' \
        '-sandbox off ' \
        '-machine pc ' \
        '-nodefaults ' \
        '-vga std ' \
        '-chardev socket,id=qmp_id_qmpmonitor1,path=/var/tmp/qmp-cmd-monitor-yhong,server,nowait ' \
        '-mon chardev=qmp_id_qmpmonitor1,mode=control ' \
        '-device virtio-serial-pci,id=virtio_serial_pci0,bus=pci.0,addr=03 ' \
        '-chardev socket,id=console0,path=/var/tmp/console-yhong,server,nowait ' \
        '-device virtserialport,chardev=console0,name=console0,id=console0,bus=virtio_serial_pci0.0 ' \
        '-chardev socket,id=serial0,path=/var/tmp/serial-yhong,server,nowait ' \
        '-device isa-serial,chardev=serial0,id=serial0 ' \
        '-device nec-usb-xhci,id=usb1,bus=pci.0,addr=11 ' \
        '-device virtio-scsi-pci,id=virtio_scsi_pci0,bus=pci.0,addr=04 ' \
        '-drive id=drive_image1,if=none,cache=none,format=qcow2,snapshot=off,file=/home/yhong/yhong-auto-migration/rhel75-64-virtio-scsi.qcow2 ' \
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
        '-chardev socket,id=qmp_id_qmpmonitor1,path=/var/tmp/qmp-cmd-monitor-yhong,server,nowait ' \
        '-mon chardev=qmp_id_qmpmonitor1,mode=control ' \
        '-device virtio-serial-pci,id=virtio_serial_pci0,bus=pci.0,addr=03 ' \
        '-chardev socket,id=console0,path=/var/tmp/console-yhong,server,nowait ' \
        '-device virtserialport,chardev=console0,name=console0,id=console0,bus=virtio_serial_pci0.0 ' \
        '-chardev socket,id=serial0,path=/var/tmp/serial-yhong,server,nowait ' \
        '-device isa-serial,chardev=serial0,id=serial0 ' \
        '-device nec-usb-xhci,id=usb1,bus=pci.0,addr=11 ' \
        '-device virtio-scsi-pci,id=virtio_scsi_pci0,bus=pci.0,addr=04 ' \
        '-drive id=drive_image1,if=none,cache=none,format=qcow2,snapshot=off,file=/home/yhong/yhong-auto-migration/rhel75-64-virtio-scsi.qcow2 ' \
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
        '-vnc :30 ' \
        '-rtc base=localtime,clock=vm,driftfix=slew ' \
        '-boot order=cdn,once=c,menu=off,strict=off ' \
        '-monitor stdio' \
        'incoming tcp:0:4000'

    sub_step_log('Checking host kernel version:')
    check_host_kernel_ver()

    sub_step_log('Checking the version of qemu:')
    check_qemu_version()

    sub_step_log('Checking yhong guest thread')
    pid = check_guest_thread()
    if pid:
        kill_guest_thread(pid)

    time.sleep(3)

    main_step_log('Step 1. Boot a guest on src host')
    sub_guest = subprocess_cmd(cmd_x86_src, enable_output=False)

    sub_step_log('Check if guest boot up')
    check_guest_thread()

    time.sleep(3)

    sub_step_log('Connecting to console')
    filename = '/var/tmp/serial-yhong'
    console = Monitor(filename)
    while True:
        output = console.rec_data()
        print output
        if re.search(r"login:", output):
            break

    cmd_root = 'root'
    console.send_cmd(cmd_root)
    output = console.rec_data()
    print  output

    cmd_passwd = GUEST_PASSWD
    console.send_cmd(cmd_passwd)
    output = console.rec_data()
    print  output

    cmd = "ifconfig | grep -E 'inet ' | awk '{ print $2}'"
    console.send_cmd(cmd)
    output = console.rec_data()
    output = remove_monitor_cmd_echo(output, cmd)
    for ip in output.splitlines():
        if ip == '127.0.0.1':
            continue
        else:
             GUEST_IP = ip

    sub_step_log('Connecting to qmp')
    filename = '/var/tmp/qmp-cmd-monitor-yhong'
    qmp_monitor = QMPMonitor(filename)
    qmp_monitor.qmp_initial()

    cmd = '"query-status"'
    qmp_monitor.qmp_cmd(cmd)

    main_step_log('Step 2. Boot a guest on det host')
    remote_ssh_cmd('10.66.10.208', 'root','redhat', cmd_x86_dst)
    

    pass