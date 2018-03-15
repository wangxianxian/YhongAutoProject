import os
import time
import pexpect
import subprocess
import socket
import usr_exceptions
import threading
import re
import Queue
import logging

BASE_FILE = os.path.dirname(os.path.abspath(__file__))

class Test():
    def __init__(self, case_id, params, timeout=3600):
        self.case_id = case_id
        self.pid_list = []
        self.start_time = time.time()
        self.params = params

    def log_echo_file(self, log_str, short_debug=True, serial_debug=False):
        prefix_file = self.case_id
        log_file_list = []
        if not prefix_file:
            prefix_file = 'Untitled'
        sub_log_dir = os.path.join(self.params.get('log_dir'), self.case_id + '_logs')
        #print sub_log_dir
        if not os.path.exists(sub_log_dir):
            os.mkdir(sub_log_dir)
        if short_debug == True and serial_debug == False:
            log_file = sub_log_dir + '/' + 'short_debug.log'
            log_file_list.append(log_file)
        if short_debug == True or serial_debug == True:
            log_file = sub_log_dir + '/' + 'long_debug.log'
            log_file_list.append(log_file)
        if serial_debug == True:
            log_file = sub_log_dir + '/' + 'serial_debug.log'
            log_file_list.append(log_file)
        for log_file in log_file_list:
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

    def test_print(self, info, short_debug=True, serial_debug=False):
        if self.params.get('verbose') == 'yes':
            print info
        self.log_echo_file(log_str=info, short_debug=short_debug, serial_debug=serial_debug)

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
        self.test_print(info=err_info)
        raise usr_exceptions.Error(err_info)
        #usr_exceptions.Error(err_info)

    def test_pass(self):
        pass_info = '%s \n' %('*' * 50)
        pass_info += 'Case %s --- Pass \n' % self.case_id.split(':')[0]
        self.test_print(info=pass_info)
        self.total_test_time(start_time=self.start_time)

    def test_timeout_daemon(self, passed, endtime):
        while time.time() < endtime:
            if passed == True:
                break
        if passed == False:
            err_info = 'Case Error: ' + 'RUN TIMEOUT'
            self.log_echo_file(log_str=err_info)
            #self.test_error(err_info)

class TestCmd(Test):
    def __init__(self, case_id, params):
        Test.__init__(self, case_id=case_id, params=params)

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

    def _reader(self, name, stream, outbuf, lock, vm_alias=None):
        """
        Thread runner for reading lines of from a subprocess into a buffer.

        :param name: The logical name of the stream (used for logging only).
        :param stream: The stream to read from. This will typically a pipe
                       connected to the output stream of a subprocess.
        :param outbuf: The list to append the read lines to.
        """
        lock.acquire()
        stop_find = False
        while True:
            s = stream.readline()
            if not s:
                break
            s = s.decode('utf-8').rstrip()
            outbuf.append(s)
            if re.findall(r'QEMU', s) or re.findall(r'qemu-kvm:', s)\
                    or re.findall(r'(qemu)', s):
                if stop_find == False:
                    lock.release()
                    if re.findall(r'Failed', s) \
                            or re.findall(r'Address already in use', s)\
                            or re.findall(r'not found', s):
                        err_info = 'Failed to boot guest : %s' %s
                        Test.test_error(self, err_info)
                    stop_find = True
            if vm_alias:
                Test.test_print(self, 'From %s->%s: %s' % (vm_alias, name, s))
            else:
                Test.test_print(self, '%s: %s' % (name, s))
        stream.close()
    # refer to /home/yhong/Github-Pycharm/staf-kvm-devel/workspace/lib/python2.7/site-packages/pip/_vendor/distlib/index.py
    def subprocess_cmd_v3(self, cmd, echo_cmd=True, vm_alias=None):
        pid = ''
        stdout = []
        self._lock = threading.Lock()
        if echo_cmd == True:
            Test.test_print(self, cmd)
        sub = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        t1 = threading.Thread(target=self._reader, args=('stdout', sub.stdout, stdout, self._lock, vm_alias))
        t1.daemon = True
        t1.name = 'stdout_thread'
        t1.start()
        while 1:
            if self._lock.acquire():
                break
            pass
        self._lock.release()
        return sub.returncode, stdout

    def local_ssh_cmd(self, cmd, timeout=1800):
        ssh = pexpect.spawn(cmd, timeout=timeout)
        try:
            ssh.sendline(cmd)
            output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
            ssh.close()
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

    def remote_ssh_cmd_v2(self, ip, passwd, cmd, timeout=300):
        output = ''
        ssh = pexpect.spawn('ssh root@%s %s' % (ip, cmd), timeout=timeout)
        try:
            i = ssh.expect(['password:', 'continue connecting (yes/no)?'])
            if i == 0:
                ssh.sendline(passwd)
                ssh.sendline(cmd)
                output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
                ssh.close()
                return output
            elif i == 1:
                ssh.sendline('yes\n')
                ssh.expect('password: ')
                ssh.sendline(passwd)
                ssh.sendline(cmd)
                output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
                ssh.close()
                return output
            else:
                ssh.sendline(cmd)
                output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
                ssh.close()
                return output

        except pexpect.EOF:
            err_info = 'End of File'
            Test.test_print(self, info=err_info)
            ssh.close()
            Test.test_error(self, err_info)
        except pexpect.TIMEOUT:
            err_info = 'Command : %s TIMEOUT ' % (cmd)
            #Test.test_print(self, info=err_info)
            ssh.close()
            Test.test_error(self, err_info)

    # Fix command timeout unexpectedly sometimes.
    def remote_ssh_cmd_v3(self, ip, passwd, cmd, timeout=300):
        pass

    def remote_scp_v2(self, cmd, passwd, timeout=1800):
        ssh = pexpect.spawn(cmd, timeout=timeout)
        try:
            i = ssh.expect(['password:', 'continue connecting (yes/no)?'], timeout=60)
            if i == 0:
                ssh.sendline(passwd)
                ssh.sendline(cmd)
                output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
                ssh.close()
                return output
            elif i == 1:
                ssh.sendline('yes\n')
                ssh.expect('password: ')
                ssh.sendline(passwd)
                ssh.sendline(cmd)
                output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
                ssh.close()
                return output
            else:
                ssh.sendline(cmd)
                output = self.remove_cmd_echo_blank_space(output=ssh.read(), cmd=cmd)
                ssh.close()
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
    def __init__(self, case_id, params):
        self.case_id = case_id
        #self.id = case_id + time.strftime(":%Y-%m-%d-%H:%M:%S")
        self.id = case_id
        self.params = params
        self.dst_ip = params.get('dst_host_ip')
        self.src_ip = params.get('src_host_ip')
        self.timeout = params.get('timeout')
        passed = False
        #endtime = time.time() + timeout
        endtime = time.time() + float(params.get('timeout'))
        thread = threading.Thread(target=Test.test_timeout_daemon, args=(self, passed, endtime,))
        thread.name = 'TimeoutThread'
        thread.daemon = True
        thread.start()
        Test.__init__(self, self.id, self.params)
        self.guest_name = params.get('vm_cmd_base')['name'][0]
        self.clear_env()

    def get_id(self):
        info = 'Start to run case : %s' % self.case_id
        Test.test_print(self, info)
        Test.test_print(self, '%s\n' % ('*' * 50))
        return self.id

    def check_guest_process(self):
        pid_list = []
        dst_pid_list = []
        output = ''

        if self.dst_ip:
            src_cmd_check = 'ssh root@%s ps -axu | grep %s | grep -v grep' % (self.dst_ip, self.guest_name)
            output, _ = TestCmd.subprocess_cmd_v2(self, echo_cmd=False, echo_output=False, cmd=src_cmd_check)
            if output:
                pid = re.split(r"\s+", output)[1]
                #pid_list.append(pid)
                info =  'Found a %s dst guest process : pid = %s' % (self.guest_name, pid)
                TestCmd.test_print(self, info)
                #for pid in pid_list:
                self.kill_dst_guest_process(pid)
            else:
                info = 'No found %s dst guest process' % self.guest_name
                TestCmd.test_print(self, info)
            time.sleep(3)

        src_cmd_check = 'ps -axu | grep %s | grep -v grep' % self.guest_name
        output, _ = TestCmd.subprocess_cmd_v2(self, echo_cmd=False, echo_output=False, cmd=src_cmd_check)
        if output:
            pid = re.split(r"\s+", output)[1]
            #pid_list.append(pid)
            info =  'Found a %s guest process : pid = %s' % (self.guest_name, pid)
            TestCmd.test_print(self, info)
            #for pid in pid_list:
            self.kill_guest_process(pid)
        else:
            info = 'No found %s guest process' % self.guest_name
            TestCmd.test_print(self, info)

        #return pid_list, dst_pid_list

    # need to merger to host_utils.py
    def host_cmd_output(self, cmd, echo_cmd=True, echo_output=True, timeout=600):
        output = ''
        if echo_cmd == True:
            TestCmd.test_print(self,cmd)
        output = TestCmd.local_ssh_cmd(self, cmd=cmd, timeout=timeout)
        # Here need to remove command echo and blank space again
        output = TestCmd.remove_cmd_echo_blank_space(self, output=output, cmd=cmd)
        if echo_output == True:
            TestCmd.test_print(self, output)
        return output

    # need to merger to host_utils.py !!!
    def host_cmd(self, cmd, echo_cmd=True):
        if echo_cmd == True:
            TestCmd.test_print(self,cmd)
        subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # need to merger to host_utils.py !!!
    def host_cmd_output_v2(self, cmd, echo_cmd=True, echo_output=True, timeout=600):
        output = ''
        stdout = []
        stderr = []
        endtime = time.time() + timeout
        if echo_cmd == True:
            TestCmd.test_print(self, cmd)
        sub = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while time.time() < endtime:
            output = sub.communicate()[0]
            if output:
                break
        if not output:
            err_info = 'CMD : %s TIMEOUT!!' % cmd
            TestCmd.test_error(self, err_info)
        # Here need to remove command echo and blank space again
        output = TestCmd.remove_cmd_echo_blank_space(self, output=output, cmd=cmd)
        if echo_output == True:
            TestCmd.test_print(self, output)
        return output

    def kill_guest_process(self, pid):
        cmd = 'kill -9 %s' % pid
        #self.host_cmd_output(cmd=cmd)
        self.host_cmd(cmd=cmd)

    def kill_dst_guest_process(self, pid):
            cmd = 'ssh root@%s kill -9 %s' %(self.dst_ip, pid)
            self.host_cmd(cmd=cmd)

    def clear_env(self):
        pid_list = []
        dst_pid_list = []
        Test.test_print(self, '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        Test.test_print(self, '======= Checking host kernel version: =======')
        #self.host_cmd_output('uname -r')
        self.host_cmd_output_v2('uname -r')
        if self.dst_ip:
            Test.test_print(self, '======= Checking host kernel version on dst host: =======')
            cmd = 'ssh root@%s uname -r' %(self.dst_ip)
            self.host_cmd_output_v2(cmd)

        Test.test_print(self, '======= Checking the version of qemu: =======')
        #self.host_cmd_output('/usr/libexec/qemu-kvm -version')
        self.host_cmd_output_v2('/usr/libexec/qemu-kvm -version')
        if self.dst_ip:
            Test.test_print(self, '======= Checking the version of qemu on dst host: =======')
            cmd = 'ssh root@%s /usr/libexec/qemu-kvm -version' %(self.dst_ip)
            self.host_cmd_output_v2(cmd)

        Test.test_print(self,'======= Checking guest process existed =======')
        self.check_guest_process()
        # if pid_list:
        #     for pid in pid_list:
        #        self.kill_guest_process(pid)
        #        #time.sleep(3)
        # if dst_pid_list:
        #     for pid in dst_pid_list:
        #        self.kill_dst_guest_process(pid)
        #        #time.sleep(3)
        Test.test_print(self, '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

    def main_step_log(self, log):
        log_tag = '='
        log_tag_rept = 7
        log_info = '%s Step %s %s' % (log_tag * log_tag_rept, log, log_tag * log_tag_rept)
        if self.params.get('verbose') == 'yes':
            print log_info
        Test.log_echo_file(self, log_str=log_info)

    def sub_step_log(self, str):
        log_tag = '-'
        log_tag_rept = 5
        log_info = '%s %s %s' % (log_tag * log_tag_rept, str, log_tag * log_tag_rept)
        Test.test_print(self, info=log_info)

if __name__ == '__main__':
    print os.path.abspath(__file__)
    print os.path.dirname(os.path.abspath(__file__))
    print os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pass