import os, sys, subprocess
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
from utils import create_images, exc_cmd_guest, subprocess_cmd, remote_scp,remove_monitor_cmd_echo
from loginfo import sub_step_log, main_step_log
import time
from monitor import MonitorFile, QMPMonitorFile
import re
import string
from config import CMD_PPC_COMMON, GUEST_PASSWD, GUEST_NAME
from guest_utils import Guest_Session
from host_utils import check_guest_thread, kill_guest_thread, check_host_kernel_ver, check_qemu_version, open_vnc_display

if __name__ == '__main__':
    GUEST_IP = ''
    HOST_IP ='10.16.67.19'
    VNC_HOST_IP ='10.72.12.32'
    VNC_HOST_PASSWD = 'hYX451029*()'
    VNC_PORT = '30'
    start_time = time.time()
    cmd_ppc = ''
    cmd_ppc_test = CMD_PPC_COMMON + \
        '-device virtio-scsi-pci,bus=pci.0,addr=0x06,id=scsi-pci-0 ' \
        '-device virtio-scsi-pci,bus=pci.0,addr=0x07,id=scsi-pci-1 ' \
        '-drive file=/root/test_home/yhong/image/rhel74-ppc64le-virtio-scsi.qcow2,snapshot=on,format=qcow2,' \
        'if=none,cache=none,media=disk,id=drive-0 ' \
        '-device scsi-hd,bus=scsi-pci-0.0,id=scsi-hd-0,drive=drive-0,channel=0,scsi-id=0,lun=0,bootindex=0 ' \
        '-drive file=/root/test_home/yhong/image/data-disk-20G.qcow2,snapshot=off,format=qcow2,' \
        'if=none,cache=none,media=disk,id=drive-1 ' \
        '-device scsi-hd,bus=scsi-pci-0.0,id=scsi-hd-1,drive=drive-1,channel=0,scsi-id=0,lun=1 ' \

    sub_step_log('Checking host kernel version:')
    check_host_kernel_ver()

    sub_step_log('Checking the version of qemu:')
    check_qemu_version()

    sub_step_log('Checking yhong guest thread')
    pid = check_guest_thread()
    if pid:
        kill_guest_thread(pid)

    time.sleep(3)

    main_step_log('Step 1. Create a data disk image')
    create_images('/root/test_home/yhong/image/data-disk-20G.qcow2', '20G', 'qcow2')

    main_step_log('Step 2. Boot a guest with data disk')
    sub_guest = subprocess_cmd(cmd_ppc_test, enable_output=False)

    sub_step_log('Check if guest boot up')
    check_guest_thread()

    sub_step_log('Connecting to VNC')
    open_vnc_display(HOST_IP, VNC_HOST_IP, VNC_HOST_PASSWD, VNC_PORT)

    sub_step_log('Connecting to serial')
    filename = '/var/tmp/serial-yhong'
    serial = MonitorFile(filename)
    while True:
        output = serial.rec_data()
        print output
        if re.search(r"login:", output):
            break

    sub_step_log('Connecting to qmp')
    filename = '/var/tmp/qmp-cmd-monitor-yhong'
    qmp_monitor = MonitorFile(filename)
    cmd_capabilities = "{'execute': 'qmp_capabilities'}"
    qmp_monitor.send_cmd(cmd_capabilities)
    output = qmp_monitor.rec_data()
    print  output

    cmd_root = 'root'
    serial.send_cmd(cmd_root)
    output = serial.rec_data()
    print  output

    cmd_passwd = GUEST_PASSWD
    serial.send_cmd(cmd_passwd)
    output = serial.rec_data()
    print  output

    cmd = "ifconfig | grep -E 'inet ' | awk '{ print $2}'"
    serial.send_cmd(cmd)
    output = serial.rec_data()

    print  output
