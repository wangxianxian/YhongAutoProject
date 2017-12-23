import os, sys, subprocess
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
from utils import create_images, exc_cmd_guest, subprocess_cmd, remote_scp,remove_monitor_cmd_echo,remote_ssh_cmd
from loginfo import sub_step_log, main_step_log
import time
from monitor import Monitor, QMPMonitor, RemoteQMPMonitor,RemoteSerialMonitor
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
        '-device virtio-serial-pci,id=virtio_serial_pci0,bus=pci.0,addr=03 ' \
        '-chardev socket,id=console0,path=/var/tmp/console-yhong,server,nowait ' \
        '-device virtserialport,chardev=console0,name=console0,id=console0,bus=virtio_serial_pci0.0 ' \
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
        '-chardev socket,id=console0,path=/var/tmp/console-yhong,server,nowait ' \
        '-device virtserialport,chardev=console0,name=console0,id=console0,bus=virtio_serial_pci0.0 ' \
        '-device nec-usb-xhci,id=usb1,bus=pci.0,addr=11 ' \
        '-device virtio-scsi-pci,id=virtio_scsi_pci0,bus=pci.0,addr=04 ' \
        '-drive id=drive_image1,if=none,cache=none,format=qcow2,snapshot=off,file=/home/yhong/yhong-auto-migration/rhel75-64-virtio-scsi.qcow2 ' \
        '-device scsi-hd,id=image1,drive=drive_image1,bus=virtio_scsi_pci0.0,channel=0,scsi-id=0,lun=0,bootindex=0 ' \
        '-netdev tap,vhost=on,id=idlkwV8e,script=/etc/qemu-ifup,downscript=/etc/qemu-ifdown ' \
        '-device virtio-net-pci,mac=9a:7b:7c:7d:7e:ff,id=idtlLxAk,vectors=4,netdev=idlkwV8e,bus=pci.0,addr=05 ' \
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

    time.sleep(5)

    sub_step_log('Check the status of src guest')
    src_remote_qmp = RemoteQMPMonitor('10.66.10.122', 3333)
    src_remote_qmp.qmp_initial()
    src_remote_qmp.qmp_cmd('"qmp_capabilities"')
    src_remote_qmp.qmp_cmd('"query-status"')

    sub_step_log('Connecting to console')
    src_serial = RemoteSerialMonitor('10.66.10.122', 4444)

    while True:
        output = src_serial.serial_output()
        print output
        if re.search(r"login:", output):
            break

    src_serial.serial_login()

    cmd = "ifconfig | grep -E 'inet ' | awk '{ print $2}'"
    output = src_serial.serial_cmd(cmd)
    """
    output = remove_monitor_cmd_echo(output, cmd)
    for ip in output.splitlines():
        if ip == '127.0.0.1':
            continue
        else:
             GUEST_IP = ip
    """
    main_step_log('Step 2. Boot a guest on det host')
    #remote_ssh_cmd('10.66.10.208', 'root','redhat', cmd_x86_dst)
    cmd = 'ssh root@10.66.10.208 %s' % cmd_x86_dst
    subprocess_cmd(cmd, enable_output=False)

    time.sleep(3)

    sub_step_log('Check the status of dst guest')
    dst_remote_qmp = RemoteQMPMonitor('10.66.10.208', 3333)
    dst_remote_qmp.qmp_initial()
    dst_remote_qmp.qmp_cmd('"qmp_capabilities"')
    dst_remote_qmp.qmp_cmd('"query-status"')

    main_step_log('Step 3. Migrate guest from src host to dst host')
    cmd = '"migrate", "arguments": { "uri": "tcp:10.66.10.208:4000" }'
    src_remote_qmp.qmp_cmd(cmd)

    sub_step_log('Check the status of migration')
    cmd = '"query-migrate"'
    while True:
        output = src_remote_qmp.qmp_cmd_result(cmd)
        if re.findall(r'"remaining": 0', output):
            break
        time.sleep(5)

    main_step_log('Step 4. Login dst guest and dmesg')
    dst_serial = RemoteSerialMonitor('10.66.10.208', 4444)
    dst_serial.serial_login()
    dst_serial.serial_cmd('dmesg')

    src_remote_qmp.close()
    dst_remote_qmp.close()
    dst_serial.close()
    src_serial.close()

    test_time = time.time() - start_time
    print 'Total of test time :', int(test_time/60), 'min'
