import os,time
import pexpect
import subprocess
import select
import re
import usr_exceptions

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
def remove_monitor_cmd_echo_endline(output, cmd):
    """
    count = 0
    for line in output.splitlines():
        print ('%d %s' % (count, line))
        count = count + 1
    """
    if output and output.splitlines()[0] == cmd:
        output = "".join(output.splitlines(True)[1:-2])
    return output

def remove_remote_monitor_endline(output):
    """
    count = 0
    for line in output.splitlines():
        print ('%d %s' % (count, line))
        count = count + 1
    """
    output = "".join(output.splitlines(True)[0:-1])
    return output

def subprocess_cmd(cmd, enable_output=True):
    print cmd
    sub = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if (enable_output == True):
        output = sub.communicate()[0]
        print output
        return output, sub
    elif (enable_output == False):
        return sub

def check_qemu_fd_stdout(fd=None, timeout=3):
    while select.select([fd], [], [], timeout)[0]:
        tmp = os.read(fd, 819200)
        if re.search(r'qemu-kvm:', tmp):
            print tmp
            info = 'Guest boot failed!! \n%s' %tmp
            raise usr_exceptions.GuestBootFailed(info)
        else:
            return True

def subprocess_cmd_v2(cmd, enable_output=True):
    print cmd
    sub = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    fd = sub.stdout.fileno()
    if (enable_output == True):
        output = sub.communicate()[0]
        print output
        return output, fd
    elif (enable_output == False):
        return fd

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

def total_test_time(start_time, format=None):
    test_time = time.time() - start_time
    if format == 'sec':
        print 'Total of test time :', test_time, 'sec'
    elif format == 'min':
        print 'Total of test time :', int(test_time / 60), 'min'
    else:
        print 'Total of test time : %s min %s sec' %(int(test_time / 60), int(test_time - int(test_time / 60) * 60 ))
    pass


if __name__ =='__main__':
    output = remote_ssh_cmd('10.16.67.19', 'kvmautotest', 'uname -r')
    #print output
    exc_cmd_guest('10.16.67.19', 'kvmautotest', 'lsblk')
    #output = check_qemu_ver()
    #print  output
    #pass

