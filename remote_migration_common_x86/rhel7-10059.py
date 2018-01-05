import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
import time
from host_utils import HostSession
from guest_utils import GuestSession_v2
from monitor import RemoteSerialMonitor_v2, RemoteQMPMonitor_v2
from log_utils import StepLog
from config import GUEST_PASSWD
import re
from vm import CREATE_TEST_ID

def run_case(src_ip='10.66.10.122', dst_ip='10.66.10.208', timeout=60):
    start_time = time.time()
    SRC_HOST_IP = src_ip
    DST_HOST_IP = dst_ip
    #vnc_server_ip = '10.72.12.37'
    vnc_server_ip = '10.66.12.246'
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
        '-drive id=drive_image1,if=none,cache=none,format=qcow2,snapshot=off,file=/home/yhong/yhong-auto-project/rhel75-64-virtio-scsi.qcow2 ' \
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
        '-drive id=drive_image1,if=none,cache=none,format=qcow2,snapshot=off,file=/home/yhong/yhong-auto-project/rhel75-64-virtio-scsi.qcow2 ' \
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
        '-incoming tcp:0:4000 ' \
        '-monitor stdio '

    id = CREATE_TEST_ID('RHEL7-10059').get_id()
    step_log = StepLog(id)
    src_host_session = HostSession(id)

    step_log.sub_step_log('Checking host kernel version:')
    src_host_session.host_cmd_output('uname -r')

    step_log.sub_step_log('Checking the version of qemu:')
    src_host_session.host_cmd_output('/usr/libexec/qemu-kvm -version')

    step_log.sub_step_log('Checking yhong guest thread')
    pid = src_host_session.check_guest_thread()
    if pid:
        src_host_session.kill_guest_thread(pid)

    time.sleep(3)

    step_log.main_step_log('1. Start source vm')
    src_host_session.boot_guest_v2(cmd_x86_src, vm_alias='src')

    step_log.sub_step_log('Check if guest boot up')
    src_host_session.check_guest_thread()

    time.sleep(5)
    src_host_session.vnc_daemon(ip=vnc_server_ip, port=59999, timeout=10)

    step_log.sub_step_log('Check the status of src guest')
    src_remote_qmp = RemoteQMPMonitor_v2(id, SRC_HOST_IP, 3333)
    src_remote_qmp.qmp_initial()
    src_remote_qmp.qmp_cmd_output('{"execute":"query-status"}')

    step_log.sub_step_log('Connecting to src serial')
    src_serial = RemoteSerialMonitor_v2(id, SRC_HOST_IP, 4444)
    src_serial.serial_login(prompt_login=True)

    SRC_GUEST_IP = src_serial.serial_get_ip()

    src_guest_session = GuestSession_v2(case_id=id, ip=SRC_GUEST_IP, passwd=GUEST_PASSWD)
    step_log.sub_step_log('Check dmesg info ')
    cmd = 'dmesg'
    output = src_guest_session.guest_cmd_output(cmd)
    if re.findall(r'Call Trace:', output):
        src_guest_session.test_error('Guest hit call trace')

    step_log.main_step_log('2. Create a file in host')
    cmd = 'dd if=/dev/urandom of=/tmp/file_host bs=1M count=100 oflag=direct'
    src_host_session.host_cmd_output(cmd, timeout=300)

    step_log.sub_step_log('Check md5sum on src host')
    file_src_host_md5 = src_host_session.host_cmd_output('md5sum /tmp/file_host')

    step_log.main_step_log('3. Start des vm in migration-listen mode: "-incoming tcp:0:****"')
    src_host_session.boot_remote_guest(ip='10.66.10.208', cmd=cmd_x86_dst, vm_alias='dst')

    dst_remote_qmp = RemoteQMPMonitor_v2(id, DST_HOST_IP, 3333)
    dst_remote_qmp.qmp_initial()
    dst_remote_qmp.qmp_cmd_output('{"execute":"query-status"}')

    src_host_session.vnc_daemon(ip=vnc_server_ip, port=58888, timeout=10)

    step_log.main_step_log('4. Start migration')
    cmd = '{"execute":"migrate", "arguments": { "uri": "tcp:10.66.10.208:4000" }}'
    src_remote_qmp.qmp_cmd_output(cmd)

    step_log.sub_step_log('Check the status of migration')
    cmd = '{"execute":"query-migrate"}'
    while True:
        output = src_remote_qmp.qmp_cmd_output(cmd)
        if re.findall(r'"remaining": 0', output):
            break
        if re.findall(r'"status": "failed"', output):
            src_remote_qmp.test_error('migration failed')
        time.sleep(5)

    step_log.sub_step_log('Login dst guest')
    dst_serial = RemoteSerialMonitor_v2(id, '10.66.10.208', 4444)
    dst_serial.serial_login()

    DST_GUEST_IP = dst_serial.serial_get_ip()

    dst_guest_session = GuestSession_v2(case_id=id, ip=DST_GUEST_IP, passwd=GUEST_PASSWD)

    step_log.main_step_log('5. Transfer file from host to guest')
    src_host_session.host_cmd_scp(dst_ip=SRC_GUEST_IP, passwd=GUEST_PASSWD,
                                src_file='/tmp/file_host', dst_file='/tmp/file_guest', timeout=300)
    step_log.sub_step_log('Check md5sum on dst guest')
    file_dst_guest_md5 = dst_guest_session.guest_cmd_output('md5sum /tmp/file_guest')

    if file_dst_guest_md5.split(' ')[0] != file_src_host_md5.split(' ')[0]:
        step_log.sub_step_log('Quit src guest')
        src_remote_qmp.qmp_cmd_output('{"execute":"quit"}')
        step_log.sub_step_log('Quit dst guest')
        dst_remote_qmp.qmp_cmd_output('{"execute":"quit"}')
        src_host_session.test_error('md5sum value error!!')

    step_log.main_step_log('6. Ping-pong migrate until file transfer finished')

    step_log.main_step_log('7. Transfer file from guest to host')

    step_log.main_step_log('9. Check md5sum after file transfer')


    step_log.sub_step_log('Quit src guest')
    src_remote_qmp.qmp_cmd_output('{"execute":"quit"}')
    step_log.sub_step_log('Quit dst guest')
    dst_remote_qmp.qmp_cmd_output('{"execute":"quit"}')

    src_host_session.test_pass()
    src_host_session.total_test_time(start_time=start_time)

if __name__ == '__main__':
    run_case()