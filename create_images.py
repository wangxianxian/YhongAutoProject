import subprocess

def check_qemu_ver():
    ver = subprocess.check_output('rpm -qa | grep qemu', shell=True)
    return ver

def create_images(image_file=None, size=None, format=None):
    cmd = ''
    cmd = 'qemu-img create -f %s %s %s' %(format, image_file, size)
    output = subprocess.check_output(cmd, shell=True)
    print output

if __name__ == '__main__':
    output = check_qemu_ver
    print output

    create_images('./disk-sys-20G.qcow2', '20G', 'qcow2')
