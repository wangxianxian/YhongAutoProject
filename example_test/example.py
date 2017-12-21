import os, sys, subprocess
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
from utils import check_qemu_ver, create_images, exc_cmd_guest, subprocess_cmd, remote_scp
from loginfo import sub_step_log, main_step_log
import time
from monitor import Monitor
import re
import string
from config import CMD_PPC_COMMON, GUEST_PASSWD
from guest import Guest_Session



GUEST_IP = '10.16.71.71'

if __name__ == '__main__':
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

    # print '--- Checking the version of qemu: ---'
    sub_step_log('Checking the version of qemu:')
    check_qemu_ver()

    # print '=== Step 1. Create a data disk image ==='
    main_step_log('Step 1. Create a data disk image')
    create_images('/root/test_home/yhong/image/data-disk-20G.qcow2', '20G', 'qcow2')

    # print '=== Step 2. Boot a guest with data disk ==='
    main_step_log('Step 2. Boot a guest with data disk')
    print cmd_ppc_test
    sub_guest = subprocess.Popen(cmd_ppc_test, shell=True, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # print '--- Check if guest boot up ---'
    sub_step_log('Check if guest boot up')
    cmd = 'ps -axu | grep guest-yhong'
    subprocess_cmd(cmd)

    # print '--- Connecting to console ---'
    sub_step_log('Connecting to console')
    filename = '/var/tmp/serial-yhong'
    console = Monitor(filename)
    while True:
        output = console.rec_data()
        print output
        """
        if not output:
            print 'Could not connect to console!'
            sub_guest.kill()
            break
        else:
            print output
        """
        if re.search(r"login:", output):
            break

    guest_session = Guest_Session(GUEST_IP, GUEST_PASSWD)
    guest_session.guest_cmd('ifconfig')
    guest_session.guest_cmd('lsblk')