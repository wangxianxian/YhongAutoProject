import os
import time
import pexpect
import subprocess
import socket
import usr_exceptions
import threading
import re

class Test():
    def __init__(self, case_id, timeout=3600):
        self.case_id = case_id
        self.pid_list = []

    def log_echo_file(self, log_str):
        pre_path = os.getcwd()
        path = pre_path + '/run_log/'
        if not os.path.exists(path):
            os.mkdir(path)
        prefix_file = self.case_id
        if not prefix_file:
            prefix_file = 'Untitled'
        log_file = path + prefix_file
        if os.path.exists(log_file):
            run_log = open(log_file, "r")
            if run_log:
                for line in run_log.readlines():
                    self.check_err_info(line)

        if os.path.exists(log_file):
            try:
                run_log = open(log_file, "a")
                for line in log_str.splitlines():
                    timestamp = time.strftime("%Y-%m-%d-%H:%M:%S")
                    run_log.write("%s: %s\n" % (timestamp, line))
                    #self.check_err('TIMEOUT', line)
            except Exception, err:
                txt = "Fail to record log to %s.\n" % log_file
                txt += "Log content: %s\n" % log_str
                txt += "Exception error: %s" % err
                self.test_error(err_info=txt)
        else:
            try:
                run_log = open(log_file, "a")
                for line in log_str.splitlines():
                    timestamp = time.strftime("%Y-%m-%d-%H:%M:%S")
                    run_log.write("%s: %s\n" % (timestamp, line))
                    #self.check_err_infile('TIMEOUT', line)
            except Exception, err:
                txt = "Fail to record log to %s.\n" % log_file
                txt += "Log content: %s\n" % log_str
                txt += "Exception error: %s" % err
                self.test_error(err_info=txt)

    def check_err_info(self, content):
            if re.findall(r'Error', content):
                # Delete the timestamp of run timeout.e.g:2018-01-13-18
                if re.findall(r'\d+-\d+-\d+', content):
                    content_list = re.split(r':', content)
                    content = ':'.join(content_list[-2:])
                raise usr_exceptions.Error(content)

    def test_print(self, info):
        print info
        self.log_echo_file(log_str=info)

    def total_test_time(self, start_time):
        self._passed = True
        test_time = time.time() - start_time
        if format == 'sec':
            print 'Total of test time :', test_time, 'sec'
        elif format == 'min':
            print 'Total of test time :', int(test_time / 60), 'min'
        else:
            time_info =  'Total of test time : %s min %s sec' % (
            int(test_time / 60), int(test_time - int(test_time / 60) * 60))
            self.test_print(info=time_info)

    def open_vnc(self, ip, port, timeout=10):
        self.vnc_ip = ip
        self.vnc_port = port
        data = ''
        vnc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        vnc_socket.connect((self.vnc_ip, self.vnc_port))
        requet = 'Trying to connect vnc'
        end_time = time.time() + timeout
        while time.time() < end_time:
            vnc_socket.send(requet)
            data = vnc_socket.recv(1024)
            if data:
                break
        print 'Client recevied :', data
        vnc_socket.close()

    def vnc_daemon(self, ip, port, timeout=10):
        thread = threading.Thread(target=self.open_vnc, args=(ip, port, timeout))
        thread.name = 'vnc'
        thread.daemon = True
        thread.start()

    def test_error(self, err_info):
        err_info = 'Case Error: ' + err_info
        self.log_echo_file(log_str=err_info)
        raise usr_exceptions.Error(err_info)

    def test_pass(self):
        pass_info = '%s \n' %('*' * 50)
        pass_info += 'Case %s --- Pass \n' % self.case_id.split(':')[0]
        self.test_print(info=pass_info)

    def test_timeout_daemon(self, passed, endtime):
        while time.time() < endtime:
            if passed == True:
                break
        if passed == False:
            err_info = 'Case Error: ' + 'RUN TIMEOUT'
            self.log_echo_file(log_str=err_info)
            #self.test_error(err_info)

class TestCmd(Test):
    def __init__(self, case_id):
        Test.__init__(self, case_id=case_id)

    def subprocess_cmd_v2(self, cmd, echo_cmd=True, echo_output=True, enable_output=True):
        pid = ''
        if echo_cmd == True:
            Test.test_print(self, cmd)
        sub = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        fd = sub.stdout.fileno()
        pid = sub.pid
        if (enable_output == True):
            output = sub.communicate()[0]
            if echo_output == True:
                self.test_print(info=output)
            return output, fd
        elif (enable_output == False):
            return fd, pid

    def local_ssh_cmd(self, cmd, timeout=1800):
        ssh = pexpect.spawn(cmd, timeout=timeout)
        try:
            ssh.sendline(cmd)
            output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
            return output

        except pexpect.EOF:
            err_info = 'End of File'
            Test.test_print(self, info=err_info)
            ssh.close()
            Test.test_error(self, err_info)

        except pexpect.TIMEOUT:
            err_info = 'Command : %s TIMEOUT ' % (cmd)
            Test.test_print(self, info=err_info)
            ssh.close()
            Test.test_error(self, err_info)


    def remove_cmd_echo_blank_space(self, output, cmd):
        if output:
            lines = output.splitlines()
            count = 0
            for line in lines:
                #print '[%d]:%s;%d' %(count, line, len(line))
                if line == cmd or line == '\n' \
                        or len(line) == 1 \
                        or len(line) == 0:
                    #print 'count = %s' % count
                    count = count + 1
                    lines.remove(line)
                    continue
                count = count + 1
            output = "\n".join(lines)
        return output

    def remote_ssh_cmd_v2(self, ip, passwd, cmd, timeout=1800):
        output = ''
        ssh = pexpect.spawn('ssh root@%s %s' % (ip, cmd), timeout=timeout)
        try:
            i = ssh.expect(['password:', 'continue connecting (yes/no)?'], timeout=60)
            if i == 0:
                ssh.sendline(passwd)
                ssh.sendline(cmd)
                output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
                return output
            elif i == 1:
                ssh.sendline('yes\n')
                ssh.expect('password: ')
                ssh.sendline(passwd)
                ssh.sendline(cmd)
                output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
                return output
            else:
                ssh.sendline(cmd)
                output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
                return output

        except pexpect.EOF:
            err_info = 'End of File'
            Test.test_print(self, info=err_info)
            ssh.close()
            Test.test_error(self, err_info)

        except pexpect.TIMEOUT:
            err_info = 'Command : %s TIMEOUT ' % (cmd)
            Test.test_print(self, info=err_info)
            ssh.close()
            Test.test_error(self, err_info)

    def remote_scp_v2(self, cmd, passwd, timeout=1800):
        ssh = pexpect.spawn(cmd, timeout=timeout)
        try:
            i = ssh.expect(['password:', 'continue connecting (yes/no)?'], timeout=60)
            if i == 0:
                ssh.sendline(passwd)
                ssh.sendline(cmd)
                output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
                return output
            elif i == 1:
                ssh.sendline('yes\n')
                ssh.expect('password: ')
                ssh.sendline(passwd)
                ssh.sendline(cmd)
                output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
                return output
            else:
                ssh.sendline(cmd)
                output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
                return output

        except pexpect.EOF:
            err_info = 'End of File'
            Test.test_print(self, info=err_info)
            ssh.close()
            Test.test_error(self, err_info)

        except pexpect.TIMEOUT:
            err_info = 'Command : %s TIMEOUT ' % (cmd)
            Test.test_print(self, info=err_info)
            ssh.close()
            Test.test_error(self, err_info)


class CREATE_TEST(Test, TestCmd):
    def __init__(self, case_id, guest_name, dst_ip=None, timeout=1800):
        self.case_id = case_id
        self.id = case_id + time.strftime(":%Y-%m-%d-%H:%M:%S")
        passed = False
        endtime = time.time() + timeout
        thread = threading.Thread(target=Test.test_timeout_daemon, args=(self, passed, endtime,))
        thread.name = 'TimeoutThread'
        thread.daemon = True
        thread.start()
        Test.__init__(self, self.id)
        self.guest_name = guest_name
        self.clear_env(guest_name=guest_name, dst_ip=dst_ip)


    def get_id(self):
        info = 'Start to run case : %s' % self.case_id
        Test.test_print(self, info)
        Test.test_print(self, '%s\n' % ('*' * 50))
        return self.id

    def check_guest_process(self, guest_name, dst_ip):
        pid_list = []
        dst_pid_list = []
        output = ''
        cmd_check_list = []
        cmd_check_list.append('ps -axu | grep %s | grep -v grep' % guest_name)
        if dst_ip:
            cmd_check_list.append('ssh root@%s ps -axu | grep %s | grep -v grep' % (dst_ip, guest_name))
        for cmd_check in cmd_check_list:
            output, _ = TestCmd.subprocess_cmd_v2(self, echo_cmd=False, echo_output=False, cmd=cmd_check)
            if output and not re.findall(r'ssh root', cmd_check):
                pid = re.split(r"\s+", output)[1]
                pid_list.append(pid)
                info =  'Found a %s guest process : pid = %s' % (guest_name, pid_list)
                TestCmd.test_print(self, info)
            elif output and re.findall(r'ssh root', cmd_check):
                pid = re.split(r"\s+", output)[1]
                dst_pid_list.append(pid)
                info = 'Found a %s dst guest process : pid = %s' % (guest_name, dst_pid_list)
                TestCmd.test_print(self, info)
            elif not output and re.findall(r'ssh root', cmd_check):
                info = 'No found %s dst guest process' % guest_name
                TestCmd.test_print(self, info)
            elif not output and not re.findall(r'ssh root', cmd_check):
                info = 'No found %s guest process' % guest_name
                TestCmd.test_print(self, info)

        return pid_list, dst_pid_list

    def host_cmd_output(self, cmd, echo_cmd=True, echo_output=True, timeout=300):
        output = ''
        if echo_cmd == True:
            TestCmd.test_print(self,cmd)
        output = TestCmd.local_ssh_cmd(self, cmd=cmd, timeout=timeout)
        # Here need to remove command echo and blank space again
        output = TestCmd.remove_cmd_echo_blank_space(self, output=output, cmd=cmd)
        if echo_output == True:
            TestCmd.test_print(self, output)
        return output

    def kill_guest_process(self, pid, dst_ip=None):
        if dst_ip:
            cmd = 'ssh root@%s kill -9 %s' %(dst_ip, pid)
            self.host_cmd_output(cmd=cmd)
        else:
            cmd = 'kill -9 %s' % pid
            self.host_cmd_output(cmd=cmd)

    def clear_env(self, guest_name, dst_ip):
        pid_list = []
        dst_pid_list = []
        Test.test_print(self, '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        Test.test_print(self, '======= Checking host kernel version: =======')
        self.host_cmd_output('uname -r')

        Test.test_print(self, '======= Checking the version of qemu: =======')
        self.host_cmd_output('/usr/libexec/qemu-kvm -version')

        Test.test_print(self,'======= Checking guest process existed =======')
        pid_list, dst_pid_list = self.check_guest_process(guest_name, dst_ip)
        if pid_list:
            for pid in pid_list:
               self.kill_guest_process(pid)
               time.sleep(3)
        if dst_pid_list:
            for pid in dst_pid_list:
               self.kill_guest_process(pid, dst_ip)
               time.sleep(3)
        Test.test_print(self, '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

    def main_step_log(self, log):
        log_tag = '='
        log_tag_rept = 7
        log_info = '%s Step %s %s' % (log_tag * log_tag_rept, log, log_tag * log_tag_rept)
        print log_info
        Test.log_echo_file(self, log_str=log_info)

    def sub_step_log(self, str):
        log_tag = '-'
        log_tag_rept = 5
        log_info = '%s %s %s' % (log_tag * log_tag_rept, str, log_tag * log_tag_rept)
        Test.test_print(self, info=log_info)

