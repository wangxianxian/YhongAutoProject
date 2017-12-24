import os, sys, subprocess
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
from utils import create_images, exc_cmd_guest, subprocess_cmd, remote_scp,remote_ssh_cmd, total_test_time
from loginfo import sub_step_log, main_step_log
import time
from monitor import MonitorFile, QMPMonitorFile, RemoteQMPMonitor,RemoteSerialMonitor
import re
import string
from config import CMD_PPC_COMMON, GUEST_PASSWD, GUEST_NAME
from guest_utils import Guest_Session
from host_utils import check_guest_thread, kill_guest_thread, check_host_kernel_ver, check_qemu_version

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
        '-device virtio-serial-pci,id=virtio_serial_pci0,bus=pci.0,addr=03 ' \
        '-chardev socket,id=console0,path=/var/tmp/serial-yhong,server,nowait ' \
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
        '-chardev socket,id=console0,path=/var/tmp/serial-yhong,server,nowait ' \
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
        '-monitor stdio ' \
        '-incoming tcp:0:4000 ' \
        '-drive file=/home/yhong/yhong-auto-migration/disk-data0-20G.qcow2,format=qcow2,if=none,cache=none,id=drive_data0 ' \
        '-device virtio-blk-pci,drive=drive_data0,id=virtio-blk-1,addr=0x09 '

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

    sub_step_log('Connecting to src serial')
    src_serial = RemoteSerialMonitor('10.66.10.122', 4444)
    src_serial.serial_login(prompt_login=True)

    cmd = "ifconfig | grep -E 'inet ' | awk '{ print $2}'"
    src_serial.serial_cmd(cmd)
    SRC_GUEST_IP = src_serial.serial_get_ip()

    print 'src guest ip :' ,SRC_GUEST_IP
    guest_session = Guest_Session(SRC_GUEST_IP, GUEST_PASSWD)
    sub_step_log('Display disk info on src host')
    cmd = 'lsblk'
    guest_session.guest_cmd(cmd)

    main_step_log('Step 2. Hotplug a virtio-blk device')
    sub_step_log('Create a virtio block disk')
    create_images('/home/yhong/yhong-auto-migration/disk-data0-20G.qcow2', '10G', 'qcow2')

    src_remote_qmp.qmp_cmd('"__com.redhat_drive_add", "arguments":'
                           '{"file":"/home/yhong/yhong-auto-migration/disk-data0-20G.qcow2",'
                           '"format":"qcow2","id":"drive_data0"}')
    src_remote_qmp.qmp_cmd('"device_add","arguments":'
                           '{"driver":"virtio-blk-pci","drive":"drive_data0","id":"virtio-blk-1","addr":"0x09"}')
    time.sleep(3)
    sub_step_log('Display disk info on src host after hot plugging')
    cmd = 'lsblk'
    guest_session.guest_cmd(cmd)

    main_step_log('Step 3. Boot a guest on dst host')
    cmd = 'ssh root@10.66.10.208 %s' % cmd_x86_dst
    subprocess_cmd(cmd, enable_output=False)

    time.sleep(3)

    sub_step_log('Check the status of dst guest')
    dst_remote_qmp = RemoteQMPMonitor('10.66.10.208', 3333)
    dst_remote_qmp.qmp_initial()
    dst_remote_qmp.qmp_cmd('"qmp_capabilities"')
    dst_remote_qmp.qmp_cmd('"query-status"')

    main_step_log('Step 4. Migrate guest from src host to dst host')
    cmd = '"migrate", "arguments": { "uri": "tcp:10.66.10.208:4000" }'
    src_remote_qmp.qmp_cmd(cmd)

    sub_step_log('Check the status of migration')
    cmd = '"query-migrate"'
    while True:
        output = src_remote_qmp.qmp_cmd_result(cmd)
        if re.findall(r'"remaining": 0', output):
            break
        time.sleep(5)


    main_step_log('Step 5. Login dst guest')
    dst_serial = RemoteSerialMonitor('10.66.10.208', 4444)
    dst_serial.serial_login()

    DST_GUEST_IP = dst_serial.serial_get_ip()

    print 'dst guest ip :', DST_GUEST_IP
    guest_session = Guest_Session(DST_GUEST_IP, GUEST_PASSWD)
    sub_step_log('Display disk info on dst host')
    cmd = 'lsblk'
    guest_session.guest_cmd(cmd)

    main_step_log('Step 6. reboot dst guest and login dmesg')
    dst_serial.serial_cmd('reboot')
    dst_serial.serial_login(prompt_login=True)
    dst_serial.serial_cmd('dmesg')
    print dst_serial.serial_output('dmesg')

    sub_step_log('Display disk info on dst host after rebooting')
    cmd = 'lsblk'
    guest_session.guest_cmd(cmd)

    src_remote_qmp.close()
    dst_remote_qmp.close()
    dst_serial.close()
    src_serial.close()

    total_test_time(start_time)
