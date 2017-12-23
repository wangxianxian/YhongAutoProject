import os, sys, subprocess
from socket import *
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
from utils import create_images, exc_cmd_guest, subprocess_cmd, remote_scp, remove_monitor_cmd_echo, remote_ssh_cmd
from loginfo import sub_step_log, main_step_log
import time
from monitor import Monitor, QMPMonitor, RemoteQMPMonitor,RemoteMonitor
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
                  '-qmp tcp:0:3333,server,nowait' \
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
                  '-qmp tcp:0:3333,server,nowait' \
                  '-vnc :30 ' \
                  '-rtc base=localtime,clock=vm,driftfix=slew ' \
                  '-boot order=cdn,once=c,menu=off,strict=off ' \
                  '-monitor stdio' \
                  'incoming tcp:0:4000'

    sub_step_log('Open vnc dispaly')
    subprocess_cmd('vncviewer 10.66.10.208:30')

    main_step_log('Step 1. Boot a guest on dst host')
    #remote_ssh_cmd('10.66.10.208', 'root', 'redhat', cmd_x86_dst)
    main_step_log('Step 2. Connecting dst host qmp')
    remote_qmp = RemoteQMPMonitor('10.66.10.208', 3333)
    remote_qmp.qmp_initial()
    remote_qmp.qmp_cmd('"qmp_capabilities"')
    remote_qmp.qmp_cmd('"query-status"')
    remote_qmp.close()
    print '*************************************************************************'
    serail = RemoteMonitor('10.66.10.208', 4444)
    serail.send_cmd('root')
    output = serail.rec_data()
    print output

    serail.send_cmd('kvmautotest')
    output = serail.rec_data()
    print output

    serail.send_cmd('dmesg')
    output = serail.rec_data()
    print output

    print '===================================================================='
    serverHost = '10.66.10.208'
    serverPort = 3333

    socketobj = socket(AF_INET, SOCK_STREAM)
    #socketobj.connect((serverHost, serverPort))
    socketobj.connect(('10.66.10.208', 3333))
    socketobj.send('{"execute": "qmp_capabilities"}')
    data = socketobj.recv(1024)
    print 'Client recevied :', data
    data = socketobj.recv(1024)
    print 'Client recevied :', data

    socketobj.send('{"execute": "query-status"}')
    data = socketobj.recv(1024)
    print 'Client recevied :', data

    socketobj.close()

    pass