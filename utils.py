import os,sys,time,subprocess
import pexpect
import subprocess
import socket

# Remove the echoed command
def remove_remote_command_echo(output, cmd):
    """
    count = 0
    for line in output.splitlines():
        print ('%d %s' % (count, line))
        count = count + 1
    """
    if output and output.splitlines()[1] == cmd:
        output = "".join(output.splitlines(True)[2:])
    return output

# Remove the echoed command
def remove_monitor_cmd_echo(output, cmd):
    """
    count = 0
    for line in output.splitlines():
        print ('%d %s' % (count, line))
        count = count + 1
    """
    if output and output.splitlines()[0] == cmd:
        output = "".join(output.splitlines(True)[1:-2])
    return output

def subprocess_cmd(cmd):
    print cmd
    sub = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = sub.communicate()
    if stderr:
        #print 'stderr : \n', stderr
        return stderr
    elif stdout:
        #print 'stdout : \n', stdout
        return stdout

def check_qemu_ver():
    cmd = 'rpm -qa | grep qemu'
    subprocess_cmd(cmd)

def create_images(image_file=None, size=None, format=None):
    cmd = 'qemu-img create -f %s %s %s' %(format, image_file, size)
    subprocess_cmd(cmd)

def remote_ssh_cmd(ip, passwd, cmd, timeout=600):
    output = ''
    ssh = pexpect.spawn('ssh root@%s "%s"' % (ip, cmd), timeout=timeout)
    try:
        i = ssh.expect(['password:', 'continue connecting (yes/no)?'], timeout=10)
        if i == 0 :
            ssh.sendline(passwd)
        elif i == 1:
            ssh.sendline('yes\n')
            ssh.expect('password: ')
            ssh.sendline(passwd)
        ssh.sendline(cmd)
        output = remove_remote_command_echo(ssh.read(), cmd)

    except pexpect.EOF:
        print "EOF"
        ssh.close()

    except pexpect.TIMEOUT:
        print "TIMEOUT"
        ssh.close()

    return output

def exc_cmd_guest(ip, passwd, cmd, timeout=600):
    rept_num = 90
    space_num = 1
    print ('<--%s--> \n Executing guest command: \n    %s' % (time.ctime(), cmd))
    output = remote_ssh_cmd(ip=ip, passwd=passwd, cmd=cmd, timeout=timeout)
    #print ('<--%s--> \n%sActual ouput: \n%s' % (time.ctime(),(' '*space_num), output))
    print ('%sActual ouput: \n%s' % ((' ' * space_num), output))
    #print('%s' %('*'*rept_num))
    return output

def remote_scp(dst_ip, passwd, src_file, dst_file, timeout=300):
    ssh = pexpect.spawn('scp %s %s:%s' % (src_file, dst_ip, dst_file), timeout=timeout)
    try:
        i = ssh.expect(['password:', 'continue connecting (yes/no)?'], timeout=timeout)
        if i == 0 :
            ssh.sendline(passwd)
        elif i == 1:
            ssh.sendline('yes\n')
            ssh.expect('password: ')
            ssh.sendline(passwd)
        output = ssh.read()
        print output

    except pexpect.EOF:
        print "EOF"
        ssh.close()

    except pexpect.TIMEOUT:
        print "TIMEOUT"
        ssh.close()

def check_if_alive_guest():
    pass

if __name__ =='__main__':
    output = remote_ssh_cmd('10.16.67.19', 'kvmautotest', 'uname -r')
    #print output
    exc_cmd_guest('10.16.67.19', 'kvmautotest', 'lsblk')
    #output = check_qemu_ver()
    #print  output
    #pass

