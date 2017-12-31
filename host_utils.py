from utils import subprocess_cmd,remote_ssh_cmd, subprocess_cmd_v2, check_qemu_fd_stdout
from config import GUEST_NAME
import re
import os
import time
from vm import TestCmd
import threading
import usr_exceptions
import select

def check_guest_thread():
    pid = ''
    name = '-name ' + GUEST_NAME
    guest_name = GUEST_NAME
    cmd_check = 'ps -axu| grep %s | grep -v grep' % guest_name
    output, _ = subprocess_cmd(cmd_check)
    for line in output.splitlines():
        if re.findall(name, line):
            pid = re.findall(r"\d+", line)[0]
            print 'Found a yhong guest thread : pid =', pid
            return pid
    print 'No found yhong guest thread'

def check_qemu_version():
    cmd_check = '/usr/libexec/qemu-kvm -version'
    subprocess_cmd(cmd_check)

def kill_guest_thread(pid=None, timeout=5):
    cmd = 'kill -9 %s' % pid
    subprocess_cmd(cmd)

def kill_guest_thread_v2(timeout=5):
    pid = ''
    while check_guest_thread():
        pid = check_guest_thread()
        cmd = 'kill -9 %s' % pid
        subprocess_cmd(cmd)

def creat_images_files():
    src_file = os.getcwd()
    image_file = src_file + '/images/'
    try :
        os.mkdir(image_file)
        return image_file
    except OSError:
        print 'The directory already exists'
        return None

def creat_isos_files():
    src_file = os.getcwd()
    isos_file = src_file + '/isos/'
    try :
        os.mkdir(isos_file)
        return isos_file
    except OSError:
        print 'The directory already exists'
        return None

def check_host_kernel_ver():
    cmd = 'uname -r'
    subprocess_cmd(cmd)

def open_vnc_display(host_ip, vnc_host_ip, dst_passwd, port):
    vnc_cmd = 'vncviewer %s:%s AutoSelect=0' % (host_ip, port)
    remote_ssh_cmd(vnc_host_ip, dst_passwd, vnc_cmd)

def boot_guest(cmd, timeout=60):
    sub_guest = subprocess_cmd(cmd, enable_output=False)
    time.sleep(2)

def boot_guest_v2(cmd, timeout=60):
    fd = subprocess_cmd_v2(cmd, enable_output=False)
    check_qemu_fd_stdout(fd)

def install_qemu(qemu_ver=None):
    pass

def pre_install_tools():
    pass


#========================Class Host_Session=====================================#
class HostSession(TestCmd):
    def __init__(self, case_id=None, timeout=None):
        TestCmd.__init__(self, case_id, timeout=timeout)

    def check_guest_thread(self):
        pid = ''
        name = '-name ' + GUEST_NAME
        guest_name = GUEST_NAME
        cmd_check = 'ps -axu| grep %s | grep -v grep' % guest_name
        output, _ = TestCmd.subprocess_cmd_v2(self, cmd=cmd_check)
        for line in output.splitlines():
            if re.findall(name, line):
                pid = re.findall(r"\d+", line)[0]
                info =  'Found a yhong guest thread : pid = %s' % pid
                TestCmd.test_print(self, info)
                return pid
        info =  'No found yhong guest thread'
        TestCmd.test_print(self, info)

    def check_qemu_version(self):
        cmd_check = '/usr/libexec/qemu-kvm -version'
        #TestCmd.log_echo_file(self, cmd_check)
        TestCmd.subprocess_cmd_v2(self, cmd_check)

    def kill_guest_thread(self, pid=None, timeout=5):
        cmd = 'kill -9 %s' % pid
        TestCmd.subprocess_cmd_v2(self, cmd)

    def kill_guest_thread_v2(self, timeout=5):
        pid = ''
        while self.check_guest_thread():
            pid = self.check_guest_thread()
            cmd = 'kill -9 %s' % pid
            TestCmd.subprocess_cmd_v2(self, cmd)

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

    def check_host_kernel_ver(self):
        cmd = 'uname -r'
        #TestCmd.log_echo_file(self, cmd)
        TestCmd.subprocess_cmd_v2(self, cmd)

    def open_vnc_display(self, host_ip, vnc_host_ip, dst_passwd, port):
        vnc_cmd = 'vncviewer %s:%s AutoSelect=0' % (host_ip, port)
        TestCmd.subprocess_cmd_v2(self, vnc_cmd)

    def boot_guest(self, cmd, timeout=60):
        sub_guest = TestCmd.subprocess_cmd_v2(self, cmd=cmd, enable_output=False)
        time.sleep(2)

    def create_images(self, image_file=None, size=None, format=None):
        cmd = 'qemu-img create -f %s %s %s' % (format, image_file, size)
        #TestCmd.log_echo_file(self, log_str=cmd)
        TestCmd.subprocess_cmd_v2(self, cmd=cmd)

    def check_qemu_fd_stdout(self, fd):
        #while select.select([fd], [], [])[0]:
        while True:
            print '===>From class HostSession : Checking the qemu output...\n '
            print '===>From class HostSession : threads num : %s \n' % (threading.active_count())
            print('===>From class HostSession : Current thread name : %s \n' % (threading.current_thread().name))
            print('===>From class HostSession : All threads : %s \n' % (threading.enumerate()))
            time.sleep(1)
            if not fd:
                break
            else:
                tmp = os.read(fd, 8192)
                if re.search(r'qemu-kvm:', tmp):
                    print tmp
                    info = 'Guest boot failed!! \n%s' % tmp
                    raise TestCmd.test_error(self, info)

    def boot_guest_v2(self, cmd, timeout=60):
        fd = TestCmd.subprocess_cmd_v2(self, cmd=cmd, enable_output=False)
        if fd:
            thread = threading.Thread(target=self.check_qemu_fd_stdout, args=(fd,))
            #thread.name =
            thread.daemon = True
            thread.start()

    def install_qemu(self, qemu_ver=None):
        pass

    def pre_install_tools(self):
        pass



if __name__ == '__main__':
    print '', creat_isos_files()
    print '', creat_images_files()

    pass