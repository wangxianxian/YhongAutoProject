QMP_PORT = 3333
SERIAL_PORT = 4444
DRIVE_FORMAT = 'virtio-scsi'
IMAGE_FORMAT = 'qcow2'
VNC_PORT = 30
CMD_X86_64 = \
'/usr/libexec/qemu-kvm ' \
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
'-drive id=drive_image1,if=none,cache=none,format=qcow2,snapshot=on,file=/home/yhong/yhong-auto-project/rhel75-64-virtio-scsi.qcow2 ' \
'-device scsi-hd,id=image1,drive=drive_image1,bus=virtio_scsi_pci0.0,channel=0,scsi-id=0,lun=0,bootindex=0 ' \
'-netdev tap,vhost=on,id=idlkwV8e,script=/etc/qemu-ifup,downscript=/etc/qemu-ifdown ' \
'-device virtio-net-pci,mac=9a:7b:7c:7d:7e:01,id=idtlLxAk,vectors=4,netdev=idlkwV8e,bus=pci.0,addr=05 ' \
'-m 2G ' \
'-smp 2 ' \
'-cpu SandyBridge ' \
'-device usb-tablet,id=usb-tablet1,bus=usb1.0,port=2 ' \
'-device usb-kbd,id=usb-kbd1,bus=usb1.0,port=3 ' \
'-device usb-mouse,id=usb-mouse1,bus=usb1.0,port=4 ' \
'-qmp tcp:0:3333,server,nowait ' \
'-serial tcp:0:4444,server,nowait ' \
'-vnc :30 ' \
'-rtc base=localtime,clock=vm,driftfix=slew ' \
'-boot order=cdn,once=c,menu=on,strict=off ' \
'-monitor stdio ' \
