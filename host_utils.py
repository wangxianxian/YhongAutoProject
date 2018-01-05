from config import GUEST_NAME
import re
import os
import time
from vm import TestCmd
import threading
import select
import subprocess

#========================Class Host_Session=====================================#
class HostSession(TestCmd):
    def __init__(self, case_id):
        TestCmd.__init__(self, case_id)

    def host_cmd_output(self, cmd, timeout=300):
        output = ''
        TestCmd.test_print(self,cmd)
        output = self.local_ssh_cmd(cmd=cmd, timeout=timeout)
        # Here need to remove command echo and blank space again
        output = TestCmd.remove_cmd_echo_blank_space(self, output=output, cmd=cmd)
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

    def host_cmd_scp(self, dst_ip, passwd, src_file, dst_file, timeout=300):
        cmd = 'scp %s %s:%s' % (src_file, dst_ip, dst_file)
        TestCmd.test_print(self, cmd)
        output = TestCmd.remote_scp_v2(self, cmd=cmd, passwd=passwd, timeout=timeout)
        # Here need to remove command echo and blank space again
        output = TestCmd.remove_cmd_echo_blank_space(self, output=output, cmd=cmd)
        TestCmd.test_print(self, output)

    def check_guest_thread(self):
        pid = ''
        name = '-name ' + GUEST_NAME
        guest_name = GUEST_NAME
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

    def creat_images_files(self):
        src_file = os.getcwd()
        image_file = src_file + '/images/'
        try:
            os.mkdir(image_file)
            return image_file
        except OSError:
            print 'The directory already exists'
            return None

    def creat_isos_files(self):
        src_file = os.getcwd()
        isos_file = src_file + '/isos/'
        try:
            os.mkdir(isos_file)
            return isos_file
        except OSError:
            print 'The directory already exists'
            return None

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

    def boot_guest_v2(self, cmd, vm_alias=None):
        fd = TestCmd.subprocess_cmd_v2(self, cmd=cmd, enable_output=False)
        time.sleep(3)
        if fd:
            thread = threading.Thread(target=self.check_qemu_fd_stdout, args=(fd, vm_alias))
            thread.name = 'boot_guest_v2'
            thread.daemon = True
            thread.start()

    def boot_remote_guest(self, ip, cmd, vm_alias=None):
        cmd = 'ssh root@%s %s' % (ip, cmd)
        thread = threading.Thread(target=self.boot_guest_v2, args=(cmd, vm_alias))
        thread.name = 'boot_remote_guest'
        thread.daemon = True
        thread.start()
        time.sleep(3)

if __name__ == '__main__':

    pass