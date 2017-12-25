import os, sys, subprocess
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
from utils import create_images, exc_cmd_guest, \
    subprocess_cmd, remote_scp,remote_ssh_cmd, total_test_time, subprocess_cmd_v2, check_qemu_fd_stdout
from loginfo import sub_step_log, main_step_log
import time
from monitor import MonitorFile, QMPMonitorFile, RemoteQMPMonitor,RemoteSerialMonitor, SerialMonitorFile
import re
import string
from config import CMD_PPC_COMMON, GUEST_PASSWD, GUEST_NAME
from guest_utils import Guest_Session
from host_utils import check_guest_thread, kill_guest_thread, \
    check_host_kernel_ver, check_qemu_version,boot_guest,kill_guest_thread_v2,boot_guest_v2

if __name__ == '__main__':
    start_time = time.time()
    SRC_GUEST_IP = ''
    DST_GUEST_IP = ''
    cmd_x86_src = '/usr/libexec/qemu-kvm ' \
        '-name yhong-guest ' \
        '-sandbox off ' \
        '-machine pc ' \
        '-nodefaults ' \
        '-vga std ' \
        '-device nec-usb-xhci,id=usb1,bus=pci.0,addr=11 ' \
        '-device virtio-scsi-pci,id=virtio_scsi_pci0,bus=pci.0,addr=04 ' \
        '-drive id=drive_image1,if=none,cache=none,format=qcow2,snapshot=off,file=/home/yhong/yhong-auto-project/rhel75-64-virtio-scsi-2.qcow2 ' \
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
        '-monitor stdio '

    sub_step_log('Checking host kernel version:')
    check_host_kernel_ver()

    sub_step_log('Checking the version of qemu:')
    check_qemu_version()

    sub_step_log('Checking yhong guest thread')
    """
    pid = check_guest_thread()
    if pid:
        kill_guest_thread(pid)
    """
    kill_guest_thread_v2()

    main_step_log('Step 1. Boot a guest on src host')
    #boot_guest(cmd_x86_src)
    #fd = subprocess_cmd_v2(cmd_x86_src, enable_output=False)
    #check_qemu_fd_stdout(fd)
    boot_guest_v2(cmd_x86_src)

    sub_step_log('Check if guest boot up')
    check_guest_thread()

    sub_step_log('Connecting to src serial')
    src_serial = RemoteSerialMonitor('10.66.10.122', 4444)

    src_serial.serial_login(prompt_login=True, timeout=10)
    SRC_GUEST_IP = src_serial.serial_get_ip()

    src_serial.serial_cmd('df -h')
    print src_serial.serial_output('df -h')

    src_serial.serial_cmd('free -h')
    print src_serial.serial_output('free -h')

    sub_step_log('Check the status of src guest')
    src_remote_qmp = RemoteQMPMonitor('10.66.10.122', 3333)
    src_remote_qmp.qmp_initial()
    src_remote_qmp.qmp_cmd('"qmp_capabilities"')
    src_remote_qmp.qmp_cmd('"query-status"')

    print 'src guest ip :' ,SRC_GUEST_IP
    guest_session = Guest_Session(SRC_GUEST_IP, GUEST_PASSWD)
    sub_step_log('Display pci info')
    cmd = 'lspci'
    guest_session.guest_cmd(cmd)

    guest_session.guest_cmd('dmesg')

    src_remote_qmp.qmp_cmd('"quit"')

    src_serial.close()

    total_test_time(start_time)
