import os, sys, subprocess
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print (__file__)
print (os.path.dirname(__file__))
print (os.path.dirname(os.path.dirname(__file__)))
print  BASE_DIR
print('Python %s on %s' % (sys.version, sys.platform))
sys.path.extend([BASE_DIR])
from utils import check_qemu_ver, create_images, exc_cmd_guest, subprocess_cmd, remote_scp
from loginfo import sub_step_log, main_step_log
import time
from monitor import Monitor
import re
import string
from config import CMD_PPC_COMMON, GUEST_PASSWD


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

    # print '--- Connecting to qmp ---'
    sub_step_log('Connecting to qmp')
    filename = '/var/tmp/qmp-cmd-monitor-yhong'
    qmp_monitor = Monitor(filename)
    cmd_capabilities = "{'execute': 'qmp_capabilities'}"
    qmp_monitor.send_cmd(cmd_capabilities)
    output = qmp_monitor.rec_data()
    print  output

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

    print  output
