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

    def host_cmd_scp(self, dst_ip, passwd, src_file, dst_file, timeout=300):
        cmd = 'scp %s %s:%s' % (src_file, dst_ip, dst_file)
        TestCmd.test_print(self, cmd)
        output = TestCmd.remote_scp_v2(self, cmd=cmd, passwd=passwd, timeout=timeout)
        # Here need to remove command echo and blank space again
        output = TestCmd.remove_cmd_echo_blank_space(self, output=output, cmd=cmd)
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
        #if os.fstat(fd):
        #while True:
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
        pid = ''
        dst_pid = ''
        name = 'yhong-guest'
        cmd_check_list = []
        if dst_ip:
            cmd_check = 'ssh root@%s ps -axu | grep "%s" | grep -v grep' % (dst_ip, name)
            cmd_check_list.append(cmd_check)
        cmd_check = 'ps -axu| grep "%s" | grep -v grep' % name
        cmd_check_list.append(cmd_check)
        for cmd_check in cmd_check_list:
            output, _ = TestCmd.subprocess_cmd_v2(self, echo_cmd=False, echo_output=False, cmd=cmd_check)
            output = TestCmd.remove_cmd_echo_blank_space(self, output=output, cmd=cmd)
            if output and not re.findall(r'ssh root', cmd_check):
                for line in output.splitlines():
                    if re.findall(name, line):
                        pid = re.split(r"\s+", line)[1]
                info =  'Guest PID : %s' % (pid)
                TestCmd.test_print(self, info)
                return pid
            elif output and re.findall(r'ssh root', cmd_check):
                for line in output.splitlines():
                    if re.findall(name, line):
                        dst_pid = re.split(r"\s+", line)[1]
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
        pid = self.get_guest_pid(cmd, dst_ip=ip)

if __name__ == '__main__':

    pass