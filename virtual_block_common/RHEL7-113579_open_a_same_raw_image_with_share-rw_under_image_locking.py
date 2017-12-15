import os, sys, logging, subprocess
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print (__file__)
print (os.path.dirname(__file__))
print (os.path.dirname(os.path.dirname(__file__)))
print  BASE_DIR
print('Python %s on %s' % (sys.version, sys.platform))
sys.path.extend([BASE_DIR])
from utils import check_qemu_ver,create_images
import time
from monitor import Monitor

if __name__ == '__main__':
    cmd_ppc = ''
    cmd_ppc = '/usr/libexec/qemu-kvm -name guest-yhong-autopro ' \
          '-machine pseries ' \
          '-m 8G ' \
          '-nodefaults ' \
          '-smp 8,cores=4,threads=2,sockets=1 ' \
          '-boot order=cdn,once=d,menu=off,strict=off ' \
          '-device nec-usb-xhci,id=xhci0 ' \
          '-device usb-tablet,id=usb-tablet0 ' \
          '-device usb-kbd,id=usb-kbd0 ' \
          '-device VGA,id=vga0 ' \
          '-chardev socket,id=qmp_id_qmpmonitor,path=/var/tmp/qmp-cmd-monitor-yhong,server,nowait ' \
          '-mon chardev=qmp_id_qmpmonitor,mode=control ' \
          '-enable-kvm -device virtio-scsi-pci,bus=pci.0,addr=0x06,id=scsi-pci-0 ' \
          '-device virtio-scsi-pci,bus=pci.0,addr=0x07,id=scsi-pci-1 ' \
          '-drive file=/root/test_home/yhong/iso/RHEL-7.4-20170711.0-Server-ppc64le-dvd1.iso,format=raw,if=none,id=cd-0 ' \
          '-device scsi-cd,bus=scsi-pci-1.0,id=scsi-cd-0,drive=cd-0,channel=0,scsi-id=0,lun=0,bootindex=1 ' \
          '-drive file=/root/test_home/yhong/image/rhel74-ppc64le-virtio-scsi.qcow2,snapshot=on,format=qcow2,if=none,cache=none,media=disk,id=drive-0 ' \
          '-device scsi-hd,bus=scsi-pci-0.0,id=scsi-hd-0,drive=drive-0,channel=0,scsi-id=0,lun=0,bootindex=0 ' \
          '-netdev tap,id=hostnet0,script=/etc/qemu-ifup -device virtio-net-pci,netdev=hostnet0,id=virtio-net-pci0,mac=40:f2:e9:5d:9c:03 ' \
          '-qmp tcp:0:3000,server,nowait ' \
          '-chardev socket,id=serial_id_serial,path=/var/tmp/serial-yhong,server,nowait ' \
          '-device spapr-vty,reg=0x30000000,chardev=serial_id_serial ' \
          '-monitor stdio -vnc :30'

    print '***Checking the version of qemu:***'
    output = check_qemu_ver()
    print output


    print '***Create a sys image:***'
    cmd_create_images = 'qemu-img create -f qcow2 /root/test_home/yhong/image/disk-sys-20G.qcow2 20G'
    print cmd_create_images
    sub = subprocess.Popen(cmd_create_images, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ouput_stdout, ouput_stderr = sub.communicate()
    print ouput_stdout
    #print ouput_stderr


    print '***Boot a guest with data disk***'
    print cmd_ppc
    sub_guest = subprocess.Popen(cmd_ppc, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    #time.sleep(5)
    #sub_guest.kill()
    print '***Waiting for boot up***'
    time.sleep(5)

    print '***Connecting qmp monitor***'
    filename = '/var/tmp/qmp-cmd-monitor-yhong'
    qmp_monitor = Monitor(filename)
    output = qmp_monitor.rec_data()
    print  output
    cmd_qmp = '{"execute":"qmp_capabilities"}'
    print cmd_qmp
    qmp_monitor.send_cmd(cmd_qmp)
    output = qmp_monitor.rec_data()
    print  output
    cmd_qmp = '{"execute":"query-status"}'
    print cmd_qmp
    qmp_monitor.send_cmd(cmd_qmp)
    output = qmp_monitor.rec_data()
    print  output

    time.sleep(60)

    print '***Connecting to console***'
    filename = '/var/tmp/serial-yhong'
    qmp_monitor = Monitor(filename)
    output = qmp_monitor.rec_data()
    print  output

    cmd_root = 'root'
    print cmd_root
    qmp_monitor.send_cmd(cmd_root)
    output = qmp_monitor.rec_data()
    print  output
    time.sleep(3)

    cmd_passwd = 'kvmautotest'
    print cmd_passwd
    qmp_monitor.send_cmd(cmd_passwd)
    output = qmp_monitor.rec_data()
    print  output
    time.sleep(3)

    cmd = 'dmesg'
    print cmd
    qmp_monitor.send_cmd(cmd)
    output = qmp_monitor.rec_data()
    print  output
    time.sleep(3)

    cmd = 'dd if=/dev/zero of=/home/dd-file bs=1M count=1000 oflag=direct status=progress'
    print cmd
    qmp_monitor.send_cmd(cmd)
    output = qmp_monitor.rec_data()
    print  output
    time.sleep(3)

    print '***Disconnect to Monitor.***'
    qmp_monitor.close()
    print '***Kill guest.***'
    sub_guest.kill()


