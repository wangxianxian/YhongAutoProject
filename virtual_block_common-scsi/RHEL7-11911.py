"""
RHEL7-11911 - [virtual block] dd test one disk with different block size - rhel only
https://polarion.engineering.redhat.com/polarion/redirect/project/RedHatEnterpriseLinux7/workitem?id=RHEL7-11911

1. prepare a installed guest.

2. create a data disk.
    # qemu-img create -f qcow2/raw test1.img 10G

3. boot a guest attached data disk created by step 2.

4. in guest:
    # mkfs.ext4 /dev/[vs]db
    # mount /dev/[vs]db /mnt
    # dd if=/dev/zero of=/mnt/test1 bs=4k count=1000 oflag=direct

5. repeat step 4 using bs=8k / 16k / 32k/ 64k / 128k / 256k
    after step 4-5, guest works well and no crash, guest ping through
    [www.redhat.com](http://www.redhat.com) and there is no any error info in
    dmesg.

6. start multi dd progress in the same time.
    \- write 8 partition with bs= 4k/8k/16k/64k/128k/256k/4M/1G at the same
    time
    dd if=/dev/zero of=/dev/vdb1 bs=4M &
    dd if=/dev/zero of=/dev/vdb2 bs=1G &
    dd if=/dev/zero of=/dev/vdb3 bs=4k &
    dd if=/dev/zero of=/dev/vdb4 bs=8k &
    dd if=/dev/zero of=/dev/vdb5 bs=16k &
    dd if=/dev/zero of=/dev/vdb6 bs=64k &
    dd if=/dev/zero of=/dev/vdb7 bs=128k &
    dd if=/dev/zero of=/dev/vdb8 bs=256k &

    \- read 8 partition with bs= 4k/8k/16k/64k/128k/256k/4M/1G at the same time
    dd if=/dev/vdb1 of=/dev/null bs=4M &
    dd if=/dev/vdb2 of=/dev/null bs=1G &
    dd if=/dev/vdb3 of=/dev/null bs=4k &
    dd if=/dev/vdb4 of=/dev/null bs=8k &
    dd if=/dev/vdb5 of=/dev/null bs=16k &
    dd if=/dev/vdb6 of=/dev/null bs=64k &
    dd if=/dev/vdb7 of=/dev/null bs=128k &
    dd if=/dev/vdb8 of=/dev/null bs=256k &
    after step 6, guest works well and no crash, guest ping through
    [www.redhat.com](http://www.redhat.com) and there is no any error info in
    dmesg.

"""
import os, sys, subprocess
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
from utils import create_images, exc_cmd_guest, subprocess_cmd, remote_scp
from loginfo import sub_step_log, main_step_log
import time
from monitor import MonitorFile, QMPMonitorFile, SerialMonitorFile
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
    serial = SerialMonitorFile(filename)
    serial.serial_login(prompt_login=True)

    sub_step_log('Connecting to qmp')
    filename = '/var/tmp/qmp-cmd-monitor-yhong'
    qmp_monitor = QMPMonitorFile(filename)
    qmp_monitor.qmp_initial()
    cmd = '"query-status"'
    qmp_monitor.qmp_cmd(cmd)

    GUEST_IP = serial.serial_get_ip()
    guest_session = Guest_Session(GUEST_IP, GUEST_PASSWD)
    sub_step_log('Display disk info')
    cmd = 'lsblk'
    guest_session.guest_cmd(cmd)

    sub_step_log('Found out system device')
    cmd = 'ls /dev/[svh]d*'
    output = guest_session.guest_cmd(cmd)

    system_dev = re.findall('/dev/[svh]d\w+\d+', output)[0]
    system_dev = system_dev.rstrip(string.digits)
    print 'system device : ',system_dev

    main_step_log('Step 3. mkfs.ext4 /dev/[vs]db')
    for dev in re.split("\s+", output):
        if not dev:
            continue
        if not re.findall(system_dev, dev):
            cmd = 'yes | mkfs.ext4 %s' % dev
            dd_dev = dev
            guest_session.guest_cmd(cmd)
    main_step_log('Step 4. mount /dev/[vs]db /mnt')
    cmd = 'mount %s /mnt' % dd_dev
    guest_session.guest_cmd(cmd)

    main_step_log('Step 5. dd if=/dev/zero of=/mnt/test1 bs=4k count=1000 oflag=direct')
    cmd = 'dd if=/dev/zero of=/mnt/test1 bs=4k count=1000 oflag=direct'
    guest_session.guest_cmd(cmd)
    cmd = 'umount /mnt'
    guest_session.guest_cmd(cmd)
    cmd = 'yes | mkfs.ext4 %s' % dd_dev
    guest_session.guest_cmd(cmd)

    sub_step_log('check dmesg info')
    cmd = 'dmesg'
    guest_session.guest_cmd(cmd)

    main_step_log('Step 6. repeat step 5 using bs=8k / 16k / 32k/ 64k / 128k / 256k')
    bs_size = ['8k', '16k', '32k', '64k', '128k', '256k']
    timeout = 1800
    sub_step_log('check dmesg info')
    cmd = 'dmesg'
    guest_session.guest_cmd(cmd, timeout)
    if re.search(r"Opts: (null):", output):
        print 'found out null info'

    sub_step_log('Disconnect to serial')
    serial.close()

    sub_step_log('Quit guest')
    cmd = '"quit"'
    qmp_monitor.qmp_cmd(cmd)
    time.sleep(3)

    sub_step_log('Check if guest quit')
    check_guest_thread()

    sub_step_log('Reboot guest again')
    create_images('/root/test_home/yhong/image/data-disk-20G.qcow2', '20G', 'qcow2')
    sub_guest = subprocess_cmd(cmd_ppc_test, enable_output=False)

    sub_step_log('Check if guest boot')
    check_guest_thread()

    sub_step_log('Connecting to serial')
    filename = '/var/tmp/serial-yhong'
    serial = SerialMonitorFile(filename)
    serial.serial_login(prompt_login=True)

    main_step_log('Step 7. start multi dd progress in the same time')
    remote_scp(GUEST_IP, GUEST_PASSWD, '/root/test_home/yhong/YhongAutoProject/shell_scripts/auto_parted.sh', '/home/')
    cmd = 'sh /home/auto_parted.sh %s' % dd_dev
    guest_session.guest_cmd(cmd)

    bs_list = ['4k', '8k', '16k', '64k', '128k', '256k', '4M', '1G']
    count = 0
    cmd = 'ls %s*' % dd_dev
    output = guest_session.guest_cmd(cmd)
    for dev in re.split("\s+", output):
        if re.findall('/dev/[svh]d\w+\d+', dev):
            cmd = 'dd if=/dev/zero of=%s bs=%s count=300 oflag=direct & ' % (dev, bs_list[count])
            dd_dev = dev
            count = count + 1
            guest_session.guest_cmd(cmd)

    cmd = "pgrep -x dd"
    dd_thread_num = guest_session.guest_cmd(cmd)
    while dd_thread_num:
        time.sleep(5)
        dd_thread_num = guest_session.guest_cmd(cmd)

    main_step_log('Step 8. check dmesg info')
    cmd = 'dmesg'
    guest_session.guest_cmd(cmd)

    sub_step_log('Disconnect serial')
    serial.close()

    sub_step_log('Quit guest')
    cmd = '"quit"'
    qmp_monitor.qmp_cmd(cmd)

    test_time = time.time() - start_time
    print 'Total of test time :', int(test_time/60), 'min'