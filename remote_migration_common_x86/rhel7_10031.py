import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
import time
from host_utils import HostSession
from guest_utils import GuestSession_v2
from monitor import RemoteSerialMonitor_v2, RemoteQMPMonitor_v2
from config import GUEST_PASSWD
from migration_config import cmd_x86, GUEST_NAME
import re
from vm import CREATE_TEST
import threading

def run_case(src_ip='10.66.10.122', dst_ip='10.66.10.208'):
    SRC_HOST_IP = src_ip
    DST_HOST_IP = dst_ip
    #vnc_server_ip = '10.72.12.37'
    vnc_server_ip = '10.66.65.161'

    test = CREATE_TEST(case_id='rhel7_10031', guest_name=GUEST_NAME, dst_ip=DST_HOST_IP, timeout=1800)
    id = test.get_id()
    src_host_session = HostSession(id)

    test.sub_step_log('Create a data disk')
    #output = src_host_session.host_cmd_output('qemu-img create -f qcow2 /home/yhong/yhong-auto-project/data-disk0.qcow2 10G')
    output = src_host_session.host_cmd_output_v2('qemu-img create -f qcow2 /home/yhong/yhong-auto-project/data-disk0.qcow2 10G')
    if re.findall(r'Failed', output):
        src_host_session.test_error('Create image failed!')

    cmd_x86_src = cmd_x86 + \
    '-object iothread,id=iothread0 ' \
    '-device virtio-scsi-pci,id=virtio_scsi_pci1,bus=pci.0,addr=a,iothread=iothread0 ' \
    '-drive id=drive_data0,if=none,cache=none,format=qcow2,snapshot=on,file=/home/yhong/yhong-auto-project/data-disk0.qcow2 ' \
    '-device scsi-hd,id=data0,drive=drive_data0,bus=virtio_scsi_pci1.0,channel=0,scsi-id=0,lun=0 '

    test.main_step_log('1. Boot the guest on source host with data-plane and \"werror=stop,rerror=stop\"')
    #src_host_session.boot_guest_v2(cmd=cmd_x86_src, vm_alias='src')
    src_host_session.boot_guest_v3(cmd=cmd_x86_src, vm_alias='src')

    src_remote_qmp = RemoteQMPMonitor_v2(id, SRC_HOST_IP, 3333)

    test.sub_step_log('Connecting to src serial')
    src_serial = RemoteSerialMonitor_v2(id, SRC_HOST_IP, 4444)
    SRC_GUEST_IP = src_serial.vm_ip
    DST_GUEST_IP = SRC_GUEST_IP

    src_guest_session = GuestSession_v2(case_id=id, ip=SRC_GUEST_IP, passwd=GUEST_PASSWD)
    test.sub_step_log('Check dmesg info ')
    cmd = 'dmesg'
    output = src_guest_session.guest_cmd_output(cmd)
    if re.findall(r'Call Trace:', output):
        src_guest_session.test_error('Guest hit call trace')

    test.main_step_log('2. Boot the guest on destination host with \'werror=stop,rerror=stop\'')

    cmd_x86_dst = cmd_x86_src + '-incoming tcp:0:4000 '
    #src_host_session.boot_remote_guest(ip='10.66.10.208', cmd=cmd_x86_dst, vm_alias='dst')
    src_host_session.boot_remote_guest_v2(ip='10.66.10.208', cmd=cmd_x86_dst, vm_alias='dst')

    dst_remote_qmp = RemoteQMPMonitor_v2(id, DST_HOST_IP, 3333)

    test.main_step_log('3. Log in to the guest and launch processe that access the disk which is using data-plane')
    sys_dev, output = src_guest_session.guest_system_dev()
    fio_dev = ''
    for dev in re.split("\s+", output):
        if not dev:
            continue
        if not re.findall(sys_dev, dev):
            fio_dev = dev
            print 'data disk : ', fio_dev
            break

    test.sub_step_log('run fio with data disk')
    output = src_guest_session.guest_cmd_output('fio -v')
    if re.findall(r'command not found', output):
        src_guest_session.guest_cmd_output('cd /home; git clone git://git.kernel.dk/fio.git')
        src_guest_session.guest_cmd_output('cd /home/fio; ./configure; make; make install')
        output = src_guest_session.guest_cmd_output('fio -v')
        if re.findall(r'command not found', output) or not output:
            src_guest_session.test_error('Install fio failed')

    cmd = 'fio --filename=%s --direct=1 --rw=randrw --bs=512 --runtime=600 --name=test --iodepth=1 --ioengine=libaio' % fio_dev
    thread = threading.Thread(target=src_guest_session.guest_cmd_output, args=(cmd, True, True, 1200,))
    thread.name = 'fio'
    thread.daemon = True
    thread.start()

    time.sleep(1)
    src_guest_session.guest_cmd_output('pgrep -x fio')

    test.main_step_log('4. Migrate to the destination')
    cmd = '{"execute":"migrate", "arguments": { "uri": "tcp:10.66.10.208:4000" }}'
    src_remote_qmp.qmp_cmd_output(cmd)

    test.sub_step_log('Check the status of migration')
    cmd = '{"execute":"query-migrate"}'
    while True:
        output = src_remote_qmp.qmp_cmd_output(cmd)
        if re.findall(r'"remaining": 0', output):
            break
        if re.findall(r'"status": "failed"', output):
            src_remote_qmp.test_error('migration failed')
        time.sleep(5)

    test.sub_step_log('Login dst guest')

    dst_guest_session = GuestSession_v2(case_id=id, ip=DST_GUEST_IP, passwd=GUEST_PASSWD)
    dst_guest_session.guest_cmd_output('dmesg')
    if re.findall(r'Call Trace:', output):
        src_guest_session.test_error('Guest hit call trace')

    test.sub_step_log('checking fio process')
    output = dst_guest_session.guest_cmd_output('pgrep -x fio')
    while output :
        output = dst_guest_session.guest_cmd_output('pgrep -x fio')
        time.sleep(3)

    dst_guest_session.guest_cmd_output('dmesg')
    if re.findall(r'Call Trace:', output):
        src_guest_session.test_error('Guest hit call trace')

    src_host_session.test_pass()

if __name__ == '__main__':
    run_case()