from utils import subprocess_cmd,remote_ssh_cmd
from config import GUEST_NAME
import re
import os

def check_guest_thread():
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

if __name__ == '__main__':
    print '', creat_isos_files()
    print '', creat_images_files()

    pass