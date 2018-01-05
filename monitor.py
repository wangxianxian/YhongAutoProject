import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
import socket
import select
import re
import time
from usr_exceptions import SocketConnectFailed
from vm import Test

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
            #Test.test_print(self, 'Fail to connect to monitor.')

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
            #Test.test_print(self, 'Verifying data on monitor socket')

    def send_cmd(self, cmd):
        try:
            self._socket.sendall(cmd + '\n')
            Test.log_echo_file(self, cmd)

        except socket.error:
            Test.test_error(self, 'Fail to send command to monitor.')
            #Test.test_print(self, 'Fail to send command to monitor.')

    def rec_data(self):
        s = ''
        data = ''
        while self.data_availabl():
            try:
                data = self._socket.recv(8192)
            except socket.error:
                Test.test_error(self, 'Fail to receive data from monitor.')
                #Test.test_print(self, 'Fail to receive data from monitor.')
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
    DATA_AVAILABLE_TIMEOUT = 3
    def __init__(self, case_id, ip, port):
        Test.__init__(self, case_id=case_id)
        self.address = (ip, port)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(self.CONNECT_TIMEOUT)
        try:
            self._socket.connect(self.address)
            Test.test_print(self, 'Connect to monitor successfully.')
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
            Test.test_print(self, 'Verifying data on monitor socket')

    def send_cmd(self, cmd):
        try:
            self._socket.sendall(cmd + '\n')

        except socket.error:
        #except Exception:
            Test.test_error(self, 'Fail to send command to monitor.')
            #Test.test_print(self, 'Fail to send command to monitor.')

    def rec_data(self):
        s = ''
        data = ''
        while self.data_availabl():
            try:
                data = self._socket.recv(1024)
            except socket.error:
                Test.test_error(self, 'Fail to receive data from monitor.')
                #Test.test_print(self, 'Fail to receive data from monitor.')
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
    def __init__(self, case_id, ip, port):
        RemoteMonitor_v2.__init__(self, case_id=case_id, ip=ip, port=port)

    def qmp_initial(self):
        cmd = '{"execute":"qmp_capabilities"}'
        RemoteMonitor_v2.test_print(self, cmd)
        RemoteMonitor_v2.send_cmd(self, cmd)

    def qmp_cmd_output(self, cmd):
        RemoteMonitor_v2.test_print(self, cmd)
        if re.search(r'quit', cmd):
            RemoteMonitor_v2.send_cmd(self, cmd)
        else:
            RemoteMonitor_v2.send_cmd(self, cmd)
            output = RemoteMonitor_v2.rec_data(self)
            RemoteMonitor_v2.test_print(self, output)
            return output

class RemoteSerialMonitor_v2(RemoteMonitor_v2):
    def __init__(self, case_id, ip, port):
        RemoteMonitor_v2.__init__(self, case_id=case_id, ip=ip, port=port)

    def serial_login(self, prompt_login=False, passwd='kvmautotest', timeout=300):
        end_time = time.time() + timeout
        if (prompt_login == True):
            while time.time() < end_time:
                output = RemoteMonitor_v2.rec_data(self)
                if re.findall(r'Call Trace:', output):
                    RemoteQMPMonitor_v2.test_error(self, 'Guest hit call trace')
                if re.search(r"login:", output):
                    RemoteMonitor_v2.test_print(self, output)
                    break

        cmd = 'root'
        RemoteMonitor_v2.send_cmd(self, cmd)
        output = RemoteMonitor_v2.rec_data(self)
        RemoteMonitor_v2.test_print(self, output)

        RemoteMonitor_v2.send_cmd(self, passwd)
        output = RemoteMonitor_v2.rec_data(self)
        RemoteMonitor_v2.test_print(self, output)
        if not output:
            RemoteMonitor_v2.test_error(self, 'LOGIN TIMEOUT!')
        print output

    def serial_cmd_output(self, cmd):
        RemoteMonitor_v2.test_print(self, cmd)
        RemoteMonitor_v2.send_cmd(self, cmd)
        output = RemoteMonitor_v2.rec_data(self)
        if cmd:
            #output = RemoteMonitor_v2.remove_remote_monitor_endline(self, output)
            output = RemoteMonitor_v2.remove_cmd_echo_blank_space(self, cmd=cmd, output=output)
        RemoteMonitor_v2.test_print(self, output)
        return output

    def serial_get_ip(self):
        ip = ''
        cmd = "ifconfig | grep -E 'inet ' | awk '{ print $2}'"
        output = self.serial_cmd_output(cmd)
        for ip in output.splitlines():
            if not ip:
                RemoteMonitor_v2.test_error(self, 'Could not get ip address!')
            if ip == '127.0.0.1':
                continue
            else:
                #info = 'Guest ip : ip %s' %ip
                #RemoteMonitor_v2.test_print(self, ip)
                return ip


if __name__ == '__main__':
    pass