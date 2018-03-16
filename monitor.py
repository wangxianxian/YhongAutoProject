import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
import socket
import select
import re
import time
from usr_exceptions import SocketConnectFailed
from vm import Test
import Queue

#===========================================Class v2====================================================#
class MonitorFile_v2(Test):
    CONNECT_TIMEOUT = 60
    DATA_AVAILABLE_TIMEOUT = 1
    def __init__(self, case_id, filename):
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        #self._socket.settimeout(self.CONNECT_TIMEOUT)
        Test.__init__(self, case_id=case_id)
        try:
            self._socket.connect(filename)
            Test.test_print(self, 'Connect to monitor successfully')
        except socket.error:
            Test.test_error(self, 'Fail to connect to monitor.')

    def __del__(self):
        self._socket.close()

    def close(self):
        self._socket.close()

    def data_availabl(self, timeout=DATA_AVAILABLE_TIMEOUT):
        timeout = max(0, timeout)
        try:
            return bool(select.select([self._socket], [], [], timeout)[0])
        except socket.error:
            Test.test_error(self, 'Verifying data on monitor socket')

    def send_cmd(self, cmd):
        try:
            self._socket.sendall(cmd + '\n')
            Test.log_echo_file(self, cmd)

        except socket.error:
            Test.test_error(self, 'Fail to send command to monitor.')

    def rec_data(self):
        s = ''
        data = ''
        while self.data_availabl():
            try:
                data = self._socket.recv(8192)
            except socket.error:
                Test.test_error(self, 'Fail to receive data from monitor.')
                return None

            if not data:
                break
            s += data
        return s

    def remove_cmd_echo_blank_space(self, output, cmd):
        if output:
            lines = output.splitlines()
            for line in lines:
                if line == cmd or line == ' ':
                    lines.remove(line)
                    continue
            output = "\n".join(lines)
        return output

class SerialMonitorFile_v2(MonitorFile_v2):
    def __init__(self, case_id, filename):
       MonitorFile_v2.__init__(self, case_id=case_id, filename=filename)

    def serial_login(self, prompt_login=False, passwd='kvmautotest'):
        if (prompt_login == True):
            while True:
                output = MonitorFile_v2.rec_data(self)
                MonitorFile_v2.test_print(self, info=output)
                if re.search(r"login:", output):
                    break
        cmd = 'root'
        MonitorFile_v2.send_cmd(self, cmd)
        output = MonitorFile_v2.rec_data(self)
        MonitorFile_v2.test_print(self, info=output)
        MonitorFile_v2.send_cmd(self, passwd)
        output = MonitorFile_v2.rec_data(self)
        MonitorFile_v2.test_print(self, info=output)


    def serial_cmd_output(self, cmd):
        MonitorFile_v2.test_print(self,info=cmd)
        MonitorFile_v2.send_cmd(self, cmd)
        output = MonitorFile_v2.rec_data(self)
        if cmd:
            output = MonitorFile_v2.remove_cmd_echo_blank_space(self, cmd=cmd, output=output)
        MonitorFile_v2.test_print(self, info=output)
        return output

    def serial_get_ip(self):
        ip = ''
        cmd = "ifconfig | grep -E 'inet ' | awk '{ print $2}'"
        output = self.serial_cmd_output(cmd)
        for ip in output.splitlines():
            print 'ip :', ip
            if ip == '127.0.0.1':
                continue
            else:
                #MonitorFile_v2.log_echo_file(self, log_str=output)
                return ip

class QMPMonitorFile_v2(MonitorFile_v2):
    def __init__(self, case_id, filename):
        MonitorFile_v2.__init__(self, case_id=case_id, filename=filename)

    def qmp_initial(self):
        cmd = '{"execute":"qmp_capabilities"}'
        MonitorFile_v2.send_cmd(self, cmd)

    def qmp_cmd_output(self, cmd):
        MonitorFile_v2.test_print(self, info=cmd)
        if re.search(r'quit', cmd):
            MonitorFile_v2.send_cmd(self, cmd)
        else:
            MonitorFile_v2.send_cmd(self, cmd)
            output = MonitorFile_v2.rec_data(self)
            MonitorFile_v2.test_print(self, info=output)
            return output

class RemoteMonitor_v2(Test):
    CONNECT_TIMEOUT = 60
    DATA_AVAILABLE_TIMEOUT = 0
    def __init__(self, case_id, params, ip, port):
        Test.__init__(self, case_id=case_id, params=params)
        self._ip = ip
        self._qmp_port = int(params.get('vm_cmd_base')['qmp'][0].split(',')[0].split(':')[2])
        self._serail_port = int(params.get('vm_cmd_base')['serial'][0].split(',')[0].split(':')[2])
        self._guest_passwd = params.get('guest_passwd')
        self._port = port
        self.address = (ip, port)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(self.CONNECT_TIMEOUT)
        try:
            self._socket.connect(self.address)
            Test.test_print(self, 'Connect to monitor(%s:%s) successfully.' %(ip, port))
        except socket.error:
            Test.test_error(self, 'Fail to connect to monitor(%s:%s).' %(ip, port))

    def quit_vm_qmp(self):
        cmd = '{"execute":"qmp_capabilities"}'
        self.test_print(cmd)
        self.send_cmd(cmd)
        output = self.rec_data()
        self.test_print(output)

        cmd = '{"execute":"query-status"}'
        self.test_print(cmd)
        self.send_cmd(cmd)
        output = self.rec_data()
        self.test_print(output)
        if re.findall(r'paused', output):
            cmd = '{"execute":"cont"}'
            self.test_print(cmd)
            self.send_cmd(cmd)
            output = self.rec_data()
            self.test_print(output)
        if re.findall(r'inmigrate', output) \
                or re.findall(r'postmigrate', output):
            cmd = '{"execute":"quit"}'
            self.test_print(cmd)
            self.send_cmd(cmd)
            output = self.rec_data()
            self.test_print(output)

    def check_vm_alive_serial(self):
        #try:
        Test.test_print(self, '=====>Checking vm alive')
        self.send_cmd('\n')
        output = self.rec_data()
        info = '--->', output
        Test.test_print(self, info)
        if not output:
            return False
        else:
            return True
        # except:
        #     return False

    def shut_down_vm_serial(self, timeout=60):
        end_time = time.time() + timeout
        flag_timeout = True
        output = ''
        #if self.check_vm_alive_serial():
            # self.send_cmd('\n')
            # if re.findall(r'login:', self.rec_data()):
            #     cmd = 'root'
            #     self.send_cmd(cmd)
            #     output = self.rec_data(recv_timeout=3)
            #     self.test_print(output)
            #
            #     self.send_cmd(self._guest_passwd)
            #     output = self.rec_data(recv_timeout=3)
            #     self.test_print(output)
        Test.test_print(self, 'Shutting down vm by serial (%s:%s).' %(self._ip, self._serail_port))
        cmd = 'shutdown -h now'
        self.send_cmd(cmd)
        while time.time() < end_time:
            output = self.rec_data()
            self.test_print(info=output, serial_debug=True)
            if re.findall(r'Power down', output):
                if re.findall(r'Call Trace:', output):
                    self.test_error('Guest hit call trace')
                flag_timeout = False
                time.sleep(3)
                break

        if not output:
            self.test_print('Serial is hung...')
            flag_timeout = False

        if flag_timeout:
            self.test_error('Power down system timeout (%s:%s).' %(self._ip, self._serail_port))

    def __del__(self):
        # if self._port == self._qmp_port:
        #     self.quit_vm_qmp()
        #     Test.test_print(self, 'Close the qmp monitor(%s:%s).' % (self._ip, self._port))
        if self._port == self._serail_port:
            info = '%s Shutting down vm %s' % (('*' * 20), ('*' * 20))
            Test.test_print(self, info)
            self.shut_down_vm_serial()
            Test.test_print(self, 'Close the serial monitor(%s:%s).' % (self._ip, self._port))
        self._socket.close()

    def close(self):
        # if self._port == self._qmp_port:
        #     self.quit_vm_qmp()
        #     Test.test_print(self, 'Close the qmp monitor(%s:%s).' % (self._ip, self._port))
        if self._port == self._serail_port:
            info = '[close(self)]%s Shutting down vm %s' % (('*' * 20), ('*' * 20))
            Test.test_print(self, info)
            self.shut_down_vm_serial()
            Test.test_print(self, 'Close the serial monitor(%s:%s).' % (self._ip, self._port))
        self._socket.close()

    def data_availabl(self, timeout=DATA_AVAILABLE_TIMEOUT):
        timeout = max(0, timeout)
        try:
            return bool(select.select([self._socket], [], [], timeout)[0])
        except socket.error:
            Test.test_error(self, 'Verifying data on monitor(%s:%s) socket.' % (self._ip, self._port))

    def send_cmd(self, cmd):
        try:
            self._socket.sendall(cmd + '\n')
        except socket.error:
            Test.test_error(self, 'Fail to send command to monitor(%s:%s).'%(self._ip, self._port))

    def rec_data(self, recv_timeout=DATA_AVAILABLE_TIMEOUT, max_recv_data=1024):
        s = ''
        data = ''
        max_recv_data = max_recv_data
        while self.data_availabl(timeout=recv_timeout):
            try:
                data = self._socket.recv(max_recv_data)
            except socket.error:
                Test.test_error(self, 'Fail to receive data from monitor(%s:%s).'%(self._ip, self._port))
                return s

            if not data:
                break
            s += data
        return s

    def remove_cmd_echo_blank_space(self, output, cmd):
        if output:
            lines = output.splitlines()
            for line in lines:
                if line == cmd or line == ' ':
                    lines.remove(line)
                    continue
            output = "\n".join(lines)
        return output

class RemoteQMPMonitor_v2(RemoteMonitor_v2):
    def __init__(self, case_id, params, ip, port):
        self._ip = ip
        self._port = port
        self._address = (self._ip, self._port)
        RemoteMonitor_v2.__init__(self, case_id=case_id, params=params, ip=ip, port=port)
        self.qmp_initial()

    def qmp_initial(self):
        cmd = '{"execute":"qmp_capabilities"}'
        RemoteMonitor_v2.test_print(self, cmd)
        RemoteMonitor_v2.send_cmd(self, cmd)
        output = RemoteMonitor_v2.rec_data(self, recv_timeout=3)
        RemoteMonitor_v2.test_print(self, output)

        cmd = '{"execute":"query-status"}'
        RemoteMonitor_v2.test_print(self, cmd)
        RemoteMonitor_v2.send_cmd(self, cmd)
        output = RemoteMonitor_v2.rec_data(self, recv_timeout=3)
        RemoteMonitor_v2.test_print(self, output)

    def qmp_cmd_output(self, cmd, echo_cmd=True, echo_output=True, recv_timeout=0, timeout=1800):
        output =''
        if echo_cmd == True:
            RemoteMonitor_v2.test_print(self, cmd)
        if re.search(r'quit', cmd):
            RemoteMonitor_v2.send_cmd(self, cmd)
        else:
            RemoteMonitor_v2.send_cmd(self, cmd)
            endtime = time.time() + timeout
            while time.time() < endtime:
                output = RemoteMonitor_v2.rec_data(self, recv_timeout=recv_timeout)
                if output:
                    break
            if not output:
                err_info = '%s TIMEOUT' % cmd
                RemoteMonitor_v2.test_error(self, err_info)
            if echo_output == True:
                RemoteMonitor_v2.test_print(self, output)
            return output

class RemoteSerialMonitor_v2(RemoteMonitor_v2):
    def __init__(self, case_id, params, ip, port):
        self._ip = ip
        self._port = port
        self._parmas = params
        self._guest_passwd = params.get('guest_passwd')
        #self._logined_queue = Queue.Queue()
        #self._logined_queue.put('no')
        RemoteMonitor_v2.__init__(self, case_id=case_id, ip=ip, port=port, params=params)
        #if logined == False:
        #self.vm_ip = self.serial_login()
        # else:
        #     self.vm_ip = self.serial_get_ip()

    def serial_login(self, timeout=300):
        output = ''

        end_time = time.time() + timeout
        while time.time() < end_time:
            output = RemoteMonitor_v2.rec_data(self, recv_timeout=3)
            RemoteMonitor_v2.test_print(self, info=output, serial_debug=True)
            if re.findall(r'Call Trace:', output):
                RemoteQMPMonitor_v2.test_error(self, 'Guest hit call trace')
            if re.search(r"login:", output):
                break
        if not output and not re.search(r"login:", output):
            RemoteMonitor_v2.test_error(self, 'LOGIN TIMEOUT!')

        cmd = 'root'
        RemoteMonitor_v2.send_cmd(self, cmd)
        output = RemoteMonitor_v2.rec_data(self, recv_timeout=3)
        RemoteMonitor_v2.test_print(self, info=output, serial_debug=True)

        RemoteMonitor_v2.send_cmd(self, self._guest_passwd)
        RemoteMonitor_v2.test_print(self, info=self._guest_passwd, serial_debug=True)
        output = RemoteMonitor_v2.rec_data(self, recv_timeout=3)
        RemoteMonitor_v2.test_print(self, info=output, serial_debug=True)

        ip = self.serial_get_ip()
        return ip

    def serial_output(self, max_recv_data=1024):
        output = RemoteMonitor_v2.rec_data(self, max_recv_data=max_recv_data)
        return output

    def serial_cmd(self, cmd):
        RemoteMonitor_v2.test_print(self, info=cmd, serial_debug=True)
        RemoteMonitor_v2.send_cmd(self, cmd)

    def serial_cmd_output(self, cmd, recv_timeout=0, timeout=300):
        output = ''
        RemoteMonitor_v2.test_print(self, info=cmd, serial_debug=True)
        RemoteMonitor_v2.send_cmd(self, cmd)
        endtime = time.time() + timeout
        while time.time() < endtime:
            output = RemoteMonitor_v2.rec_data(self, recv_timeout=recv_timeout)
            if output:
                break
        if not output:
            err_info = '%s TIMEOUT' % cmd
            RemoteMonitor_v2.test_error(self, err_info)
        output = RemoteMonitor_v2.remove_cmd_echo_blank_space(self, cmd=cmd, output=output)
        RemoteMonitor_v2.test_print(self, info=cmd, serial_debug=True)
        return output

    def serial_get_ip(self):
        ip = ''
        output = ''
        cmd = "ifconfig | grep -E 'inet ' | awk '{ print $2}'"
        output = self.serial_cmd_output(cmd, recv_timeout=3)
        self.test_print(info=output, serial_debug=True)
        for ip in output.splitlines():
            if ip == '127.0.0.1':
                continue
            else:
                if not ip:
                    RemoteMonitor_v2.test_error(self, 'Could not get ip address!')
                return ip


if __name__ == '__main__':
    pass