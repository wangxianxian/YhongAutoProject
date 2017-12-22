from utils import subprocess_cmd
from config import GUEST_NAME
import re
import os

def check_guest_thread():
    name = '-name ' + GUEST_NAME
    pid =''
    guest_name = GUEST_NAME
    cmd_check = 'ps -axu| grep %s' % guest_name
    output = subprocess_cmd(cmd_check, output=False)
    for line in output.splitlines():
        if re.findall(name, line):
            pid = re.findall(r"\d+", line)[0]
            print 'Found a yhong guest thread : ', line
            return pid
    print 'No found yhong guest thread'
    return pid

def check_qemu_version():
    pass

def kill_guest_thread(pid=None):
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

if __name__ == '__main__':
    print '', creat_isos_files()
    print '', creat_images_files()

    pass