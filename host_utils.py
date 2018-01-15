import re
import os
import time
from vm import TestCmd, CREATE_TEST
import threading
import select
import subprocess
import utils

#========================Class Host_Session=====================================#
class HostSession(TestCmd, CREATE_TEST):
    def __init__(self, case_id):
        TestCmd.__init__(self, case_id=case_id)

    def host_cmd_output(self, cmd, echo_cmd=True, echo_output=True, timeout=300):
        output = ''
        if echo_cmd == True:
            TestCmd.test_print(self,cmd)
        output = self.local_ssh_cmd(cmd=cmd, timeout=timeout)
        # Here need to remove command echo and blank space again
        output = TestCmd.remove_cmd_echo_blank_space(self, output=output, cmd=cmd)
        if echo_output == True:
            TestCmd.test_print(self, output)
        return output

    def host_cmd_fd(self, cmd):
        sub = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        fd = sub.stdout.fileno()
        return fd

    def host_cmd(self, cmd):
        subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def host_cmd_scp(self, passwd, src_file, dst_file, src_ip=None, dst_ip=None, timeout=300):
        cmd = ''
        output = ''
        if dst_ip:
            cmd = 'scp %s %s:%s' % (src_file, dst_ip, dst_file)
        if src_ip:
            cmd = 'scp %s:%s %s' % (src_ip, src_file, dst_file)
        TestCmd.test_print(self, cmd)
        output = TestCmd.remote_scp_v2(self, cmd=cmd, passwd=passwd, timeout=timeout)
        # Here need to remove command echo and blank space again
        output = TestCmd.remove_cmd_echo_blank_space(self, output=output, cmd=cmd)
        if re.findall(r'No such file or directory', output):
            TestCmd.test_error(self, output)
        TestCmd.test_print(self, output)

    def check_guest_thread(self, guest_name):
        pid = ''
        name = '-name ' + guest_name
        #guest_name = guest_name
        cmd_check = 'ps -axu| grep %s | grep -v grep' % guest_name
        output, _ = TestCmd.subprocess_cmd_v2(self, cmd=cmd_check)
        for line in output.splitlines():
            if re.findall(name, line):
                pid = re.findall(r"\d+", line)[0]
                info =  'Found a %s guest thread : pid = %s' % (guest_name, pid)
                TestCmd.test_print(self, info)
                return pid
        info =  'No found %s guest thread' % guest_name
        TestCmd.test_print(self, info)
        return pid

    def kill_guest_thread(self, pid):
        cmd = 'kill -9 %s' % pid
        self.host_cmd_output(cmd=cmd)

    def open_vnc_display(self, host_ip, vnc_host_ip, dst_passwd, port):
        vnc_cmd = 'vncviewer %s:%s AutoSelect=0' % (host_ip, port)
        TestCmd.subprocess_cmd_v2(self, vnc_cmd)

    def boot_guest(self, cmd):
        sub_guest = TestCmd.subprocess_cmd_v2(self, cmd=cmd, enable_output=False)
        time.sleep(2)

    def create_images(self, image_file, size, format):
        cmd = 'qemu-img create -f %s %s %s' % (format, image_file, size)
        TestCmd.subprocess_cmd_v2(self, cmd=cmd)

    def check_qemu_fd_stdout(self, fd, vm_id=None):
        while select.select([fd], [], [])[0]:
            qemu_output = os.read(fd, 8192)
            if len(qemu_output) != 0:
                for line in qemu_output.splitlines():
                    if vm_id:
                        qemu_info = 'From %s: %s' % (vm_id, line)
                    else:
                        qemu_info = '%s' % line
                    TestCmd.test_print(self, qemu_info)
            if not os.fstat(fd):
                break

    def sub_step_log(self, str):
        log_tag = '-'
        log_tag_rept = 5
        log_info = '%s %s %s' %(log_tag*log_tag_rept, str, log_tag*log_tag_rept)
        TestCmd.test_print(self, info=log_info)

    def get_guest_pid(self, cmd, dst_ip=None):
        pid_list = []
        dst_pid = ''
        cmd_check_list = []
        guest_name = utils.get_guest_name(cmd=cmd)
        print '>>>>>Guest name :', guest_name
        if dst_ip:
            cmd_check = 'ssh root@%s ps -axu | grep %s | grep -v grep' % \
                        (dst_ip, guest_name)
            cmd_check_list.append(cmd_check)
        cmd_check = 'ps -axu| grep %s | grep -v grep' % guest_name
        cmd_check_list.append(cmd_check)
        for cmd_check in cmd_check_list:
            output, _ = TestCmd.subprocess_cmd_v2(self, echo_cmd=False, echo_output=False, cmd=cmd_check)
            output = TestCmd.remove_cmd_echo_blank_space(self, output=output, cmd=cmd)
            if output and not re.findall(r'ssh root', cmd_check):
                pid = re.split(r"\s+", output)[1]
                pid_list.append(pid)
                info =  'Guest PID : %s' % (pid_list[-1])
                TestCmd.test_print(self, info)
                return pid
            elif output and re.findall(r'ssh root', cmd_check):
                dst_pid = re.split(r"\s+", output)[1]
                info =  'DST Guest PID : %s' % (dst_pid)
                TestCmd.test_print(self, info)
                return dst_pid
            elif not output and re.findall(r'ssh root', cmd_check):
                err_info = 'DST Guest boot failed.'
                TestCmd.test_error(self, err_info)
            elif not output and not re.findall(r'ssh root', cmd_check):
                err_info = 'Guest boot failed.'
                TestCmd.test_error(self, err_info)

    def boot_guest_v2(self, cmd, vm_alias=None):
        cmd = cmd.rstrip(' ')
        fd, pid = TestCmd.subprocess_cmd_v2(self, cmd=cmd, enable_output=False)
        if fd:
            thread = threading.Thread(target=self.check_qemu_fd_stdout, args=(fd, vm_alias))
            thread.name = 'boot_guest_v2'
            thread.daemon = True
            thread.start()
        time.sleep(3)
        pid = self.get_guest_pid(cmd)

    def boot_remote_guest(self, ip, cmd, vm_alias=None):
        cmd = 'ssh root@%s %s' % (ip, cmd)
        fd, pid = TestCmd.subprocess_cmd_v2(self, cmd=cmd, enable_output=False)
        if fd:
            thread = threading.Thread(target=self.check_qemu_fd_stdout, args=(fd, vm_alias))
            thread.name = 'boot_remote_guest'
            thread.daemon = True
            thread.start()
        time.sleep(3)
        dst_pid = self.get_guest_pid(cmd, dst_ip=ip)

    def check_guest_alive(self, guest_pid):
        pass

    def backup_image(self, imagefile):
        pass

    def recover_image(self, imagebakfile):
        pass

if __name__ == '__main__':
    cmd = '/usr/libexec/qemu-kvm   -name yhong-guest     -sandbox off     -machine pc -nodefaults -vga std -device virtio-serial-pci,id=virtio_serial_pci0,bus=pci.0,addr=03 -chardev socket,id=console0,path=/var/tmp/serial-yhong,server,nowait -device virtserialport,chardev=console0,name=console0,id=console0,bus=virtio_serial_pci0.0 -device nec-usb-xhci,id=usb1,bus=pci.0,addr=11 -device virtio-scsi-pci,id=virtio_scsi_pci0,bus=pci.0,addr=04 -drive id=drive_image1,if=none,cache=none,format=qcow2,snapshot=off,werror=stop,rerror=stop,file=/home/yhong/yhong-auto-project/rhel75-64-virtio-scsi.qcow2 -device scsi-hd,id=image1,drive=drive_image1,bus=virtio_scsi_pci0.0,channel=0,scsi-id=0,lun=0,bootindex=0 -netdev tap,vhost=on,id=idlkwV8e,script=/etc/qemu-ifup,downscript=/etc/qemu-ifdown -device virtio-net-pci,mac=9a:7b:7c:7d:7e:7f,id=idtlLxAk,vectors=4,netdev=idlkwV8e,bus=pci.0,addr=05 -m 4G -smp 4 -cpu SandyBridge -device usb-tablet,id=usb-tablet1,bus=usb1.0,port=2 -device usb-kbd,id=usb-kbd1,bus=usb1.0,port=3 -device usb-mouse,id=usb-mouse1,bus=usb1.0,port=4 -qmp tcp:0:3333,server,nowait -serial tcp:0:4444,server,nowait -vnc :30 -rtc base=localtime,clock=vm,driftfix=slew -boot order=cdn,once=c,menu=off,strict=off -monitor stdio'
    lines = re.split(r'\s-', cmd)
    for line in lines:
        if re.findall(r'name', line):
            print line
            print 'found:', line.split(r' ')[1]
            #break
        print  '-',line
    pass