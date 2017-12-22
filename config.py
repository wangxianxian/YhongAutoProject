import os

GUEST_PASSWD = 'kvmautotest'

GUEST_NAME = 'yhong-guest'
MACHINE_TYPE = 'pseries'
MEM_SIZE = '8G'

CMD_PPC_COMMON = \
    '/usr/libexec/qemu-kvm ' \
    '-name %s ' \
    '-machine %s ' \
    '-m %s ' \
    '-nodefaults ' \
    '-enable-kvm ' \
    '-smp 8,cores=4,threads=2,sockets=1 ' \
    '-boot order=cdn,once=d,menu=off,strict=off ' \
    '-device nec-usb-xhci,id=xhci0 ' \
    '-device usb-tablet,id=usb-tablet0 ' \
    '-device usb-kbd,id=usb-kbd0 ' \
    '-device VGA,id=vga0 ' \
    '-chardev socket,id=qmp_id_qmpmonitor,path=/var/tmp/qmp-cmd-monitor-yhong,server,nowait ' \
    '-chardev socket,id=serial_id_serial,path=/var/tmp/serial-yhong,server,nowait ' \
    '-device spapr-vty,reg=0x30000000,chardev=serial_id_serial ' \
    '-mon chardev=qmp_id_qmpmonitor,mode=control ' \
    '-netdev tap,id=hostnet0,script=/etc/qemu-ifup ' \
    '-device virtio-net-pci,netdev=hostnet0,id=virtio-net-pci0,mac=40:f2:e9:5d:9c:03 ' \
    '-qmp tcp:0:3000,server,nowait ' \
    '-monitor stdio -vnc :30 ' \
    % (GUEST_NAME, MACHINE_TYPE, MEM_SIZE)

if __name__ == '__main__':
    print CMD_PPC_COMMON
