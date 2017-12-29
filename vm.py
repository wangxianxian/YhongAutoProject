import os
import time
import pexpect
import subprocess


class VM():
    def __init__(self, case_id=None, timeout=None):
        self._case_id = case_id


class Test(VM):
    def __init__(self, case_id=None, timeout=None):
        #self._case_id = case_id
        VM.__init__(self, case_id=case_id, timeout=timeout)

    def log_echo_file(self, log_str=None):
        pre_path = os.getcwd()
        path = pre_path + '/run_log/'
        if not os.path.exists(path):
            os.mkdir(path)
        prefix_file = self._case_id
        if not prefix_file:
            prefix_file = 'Untitled'
        log_file = path + prefix_file
        if os.path.exists(log_file):
            try:
                run_log = open(log_file, "a")
                for line in log_str.splitlines():
                    timestamp = time.strftime("%Y-%m-%d-%H:%M:%S")
                    run_log.write(
                        "%s: %s\n" % (timestamp, line))
            except Exception, err:
                txt = "Fail to record log to %s.\n" % log_file
                txt += "Log content: %s\n" % log_str
                txt += "Exception error: %s" % err
        else:
            try:
                run_log = open(log_file, "a")
                for line in log_str.splitlines():
                    timestamp = time.strftime("%Y-%m-%d-%H:%M:%S")
                    run_log.write(
                        "%s: %s\n" % (timestamp, line))
            except Exception, err:
                txt = "Fail to record log to %s.\n" % log_file
                txt += "Log content: %s\n" % log_str
                txt += "Exception error: %s" % err

    def total_test_time(self, start_time, timeout=None):
        test_time = time.time() - start_time
        if format == 'sec':
            print 'Total of test time :', test_time, 'sec'
        elif format == 'min':
            print 'Total of test time :', int(test_time / 60), 'min'
        else:
            print 'Total of test time : %s min %s sec' % (
            int(test_time / 60), int(test_time - int(test_time / 60) * 60))

class TestCmd(Test):
    def __init__(self, case_id=None, timeout=None):
        Test.__init__(self, case_id=case_id, timeout=timeout)

    def subprocess_cmd_v2(self, cmd, enable_output=True):
        print cmd
        sub = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        fd = sub.stdout.fileno()
        if (enable_output == True):
            output = sub.communicate()[0]
            print output
            Test.log_echo_file(self, log_str=output)
            return output, fd
        elif (enable_output == False):
            return fd

    def _remove_remote_command_echo(self, output=None, cmd=None):
        if output and output.splitlines()[1] == cmd:
            output = "".join(output.splitlines(True)[2:])
        return output

    def remote_ssh_cmd(self, ip=None, passwd=None, cmd=None, timeout=600):
        output = ''
        ssh = pexpect.spawn('ssh root@%s "%s"' % (ip, cmd), timeout=timeout)
        try:
            i = ssh.expect(['password:', 'continue connecting (yes/no)?'], timeout=10)
            if i == 0:
                ssh.sendline(passwd)
            elif i == 1:
                ssh.sendline('yes\n')
                ssh.expect('password: ')
                ssh.sendline(passwd)
            ssh.sendline(cmd)
            output = self._remove_remote_command_echo(ssh.read(), cmd)
            Test.log_echo_file(self, log_str=output)

        except pexpect.EOF:
            print "EOF"
            ssh.close()

        except pexpect.TIMEOUT:
            print "TIMEOUT"
            ssh.close()
        return output

    def remote_scp(self, dst_ip=None, passwd=None, src_file=None, dst_file=None, timeout=300):
        ssh = pexpect.spawn('scp %s %s:%s' % (src_file, dst_ip, dst_file), timeout=timeout)
        try:
            i = ssh.expect(['password:', 'continue connecting (yes/no)?'], timeout=timeout)
            if i == 0:
                ssh.sendline(passwd)
            elif i == 1:
                ssh.sendline('yes\n')
                ssh.expect('password: ')
                ssh.sendline(passwd)
            output = ssh.read()
            Test.log_echo_file(self, log_str=output)
            print output

        except pexpect.EOF:
            print "EOF"
            ssh.close()

        except pexpect.TIMEOUT:
            print "TIMEOUT"
            ssh.close()

def example():
    pass
