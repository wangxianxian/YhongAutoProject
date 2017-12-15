import os,sys,time,subprocess
import pexpect
import subprocess

def check_qemu_ver():
    ver = subprocess.check_output('rpm -qa | grep qemu', shell=True)
    return ver

def create_images(image_file=None, size=None, format=None):
    cmd = ''
    cmd = 'qemu-img create -f %s %s %s' %(format, image_file, size)
    output = subprocess.check_output(cmd, shell=True)
    print output

def remote_ssh_cmd(ip, passwd, cmd):
    output = ''

    ssh = pexpect.spawn('ssh root@%s "%s"' % (ip, cmd))
    try:
        i = ssh.expect(['password:', 'continue connecting (yes/no)?'], timeout=60)
        if i == 0 :
            ssh.sendline(passwd)
        elif i == 1:
            ssh.sendline('yes\n')
            ssh.expect('password: ')
            ssh.sendline(passwd)
        ssh.sendline(cmd)
        output = ssh.read()
        print output

    except pexpect.EOF:
        print "EOF"
        ssh.close()

    except pexpect.TIMEOUT:
        print "TIMEOUT"
        ssh.close()

    return output

if __name__ =='__main__':
    pass

