import os
import time
import pexpect
import subprocess
import socket
import usr_exceptions
import threading

class Test():
    def __init__(self, case_id):
        self._case_id = case_id

    def log_echo_file(self, log_str):
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
                    run_log.write("%s: %s\n" % (timestamp, line))
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
            except Exception, err:
                txt = "Fail to record log to %s.\n" % log_file
                txt += "Log content: %s\n" % log_str
                txt += "Exception error: %s" % err
                self.test_error(err_info=txt)

    def test_print(self, info):
        print info
        self.log_echo_file(log_str=info)

    def total_test_time(self, start_time):
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
        pass_info += 'Case %s --- Pass \n' % self._case_id.split(':')[0]
        self.test_print(info=pass_info)

    def test_timeout(self):
        err_info = 'Case Error: ' + 'TIME OUT'
        self.log_echo_file(log_str=err_info)
        raise usr_exceptions.Error(err_info)

class TestCmd(Test):
    def __init__(self, case_id):
        Test.__init__(self, case_id=case_id)

    def subprocess_cmd_v2(self, cmd, enable_output=True):
        Test.test_print(self, cmd)
        sub = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        fd = sub.stdout.fileno()
        if (enable_output == True):
            output = sub.communicate()[0]
            self.test_print(info=output)
            return output, fd
        elif (enable_output == False):
            return fd

    def local_ssh_cmd(self, cmd, timeout=600):
        ssh = pexpect.spawn(cmd, timeout=timeout)
        try:
            ssh.sendline(cmd)
            #output = self.remove_local_command_echo_endline(ssh.read(), cmd)
            output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
            #Test.test_print(self, info=output)
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

    def remote_ssh_cmd_v2(self, ip, passwd, cmd, timeout=600):
        output = ''
        ssh = pexpect.spawn('ssh root@%s "%s"' % (ip, cmd), timeout=timeout)
        try:
            i = ssh.expect(['password:', 'continue connecting (yes/no)?', '\n'], timeout=10)
            if i == 0:
                ssh.sendline(passwd)
                ssh.sendline(cmd)
                output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
                #Test.test_print(self, info=output)
                return output
            elif i == 1:
                ssh.sendline('yes\n')
                ssh.expect('password: ')
                ssh.sendline(passwd)
                ssh.sendline(cmd)
                output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
                #Test.test_print(self, info=output)
                return output
            elif i == 2:
                ssh.sendline(cmd)
                output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
                #Test.test_print(self, info=output)
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

    def remote_scp_v2(self, cmd, passwd, timeout=300):
        #cmd = 'scp %s %s:%s' % (src_file, dst_ip, dst_file)
        ssh = pexpect.spawn(cmd, timeout=timeout)
        try:
            i = ssh.expect(['password:', 'continue connecting (yes/no)?', '\n'], timeout=10)
            if i == 0:
                ssh.sendline(passwd)
                ssh.sendline(cmd)
                output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
                #Test.test_print(self, info=output)
                return output
            elif i == 1:
                ssh.sendline('yes\n')
                ssh.expect('password: ')
                ssh.sendline(passwd)
                ssh.sendline(cmd)
                output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
                #Test.test_print(self, info=output)
                return output

            elif i == 2:
                ssh.sendline(cmd)
                output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
                #Test.test_print(self, info=output)
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

class CREATE_TEST_ID(Test):
    def __init__(self, case_id):
        self.case_id = case_id
        self.id = case_id + time.strftime(":%Y-%m-%d-%H:%M:%S")
        Test.__init__(self, self.id)

    def get_id(self):
        info = 'Start to run case : %s' % self.case_id
        Test.test_print(self, info)
        Test.test_print(self, '%s\n' % ('*' * 50))
        return self.id

