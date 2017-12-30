import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
import socket
import select
import sys
import re
import time
from utils import remove_monitor_cmd_echo_endline, remove_remote_monitor_endline
from usr_exceptions import Timeout, NoGetIP, SocketConnectFailed
from vm import Test

class MonitorFile:
    CONNECT_TIMEOUT = 60
    DATA_AVAILABLE_TIMEOUT = 3
    def __init__(self, filename):
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        #self._socket.settimeout(self.CONNECT_TIMEOUT)
        try:
            self._socket.connect(filename)
            print 'Connect to monitor successfully'
        except socket.error:
            print 'Fail to connect to monitor : ', filename

    def __del__(self):
        self._socket.close()

    def close(self):
        self._socket.close()

    def _data_availabl(self, timeout=DATA_AVAILABLE_TIMEOUT):
        timeout = max(0, timeout)
        try:
            return bool(select.select([self._socket], [], [], timeout)[0])
        except socket.error:
            print 'Verifying data on monitor socket'

    def send_cmd(self, cmd):
        try:
            self._socket.sendall(cmd + '\n')

        except socket.error:
            print 'Fail to send command to monitor.'

    def rec_data(self):
        s = ''
        data = ''
        while self._data_availabl():
        #while True:
            try:
                data = self._socket.recv(8192)
                #data = remove_monitor_cmd_echo(output)
            except socket.error:
                print 'Fail to receive data from monitor.'
                return None

            if not data:
                break
            #print 'Monitor data timestamp :', time.ctime()
            s += data
        return s

class SerialMonitorFile(MonitorFile):
    def __init__(self, filename):
        MonitorFile.__init__(self, filename)

    def serial_login(self, prompt_login=False, passwd='kvmautotest', timeout=60):
        if (prompt_login == True):
            while True:
                output = MonitorFile.rec_data(self)
                #print type(output)
                print output
                if re.search(r"login:", output):
                    break
        cmd = 'root'
        MonitorFile.send_cmd(self, cmd)
        output = MonitorFile.rec_data(self)
        print output
        MonitorFile.send_cmd(self, passwd)
        output = MonitorFile.rec_data(self)
        print output

    def serial_cmd(self, cmd):
        print cmd
        MonitorFile.send_cmd(self, cmd)
        #output = MonitorFile.rec_data(self)
        #print output

    def serial_output(self, cmd=None):
        output = MonitorFile.rec_data(self)
        if cmd:
            output = remove_monitor_cmd_echo_endline(output, cmd)
        return output

    def serial_get_ip(self):
        ip = ''
        cmd = "ifconfig | grep -E 'inet ' | awk '{ print $2}'"
        self.serial_cmd(cmd)
        output = self.serial_output(cmd)
        for ip in output.splitlines():
            print 'ip :', ip
            if ip == '127.0.0.1':
                continue
            else:
                return ip

class QMPMonitorFile(MonitorFile):
    def __init__(self, filename):
        MonitorFile.__init__(self, filename)

    def qmp_initial(self):
        cmd = '{"execute":"qmp_capabilities"}'
        MonitorFile.send_cmd(self, cmd)

    def qmp_cmd(self, cmd):
        cmd ='{"execute": %s}' % cmd
        print cmd
        if re.search(r'quit', cmd):
            MonitorFile.send_cmd(self, cmd)
        else:
            MonitorFile.send_cmd(self, cmd)
            output = MonitorFile.rec_data(self)
            print output
            return output

class RemoteMonitor():
    CONNECT_TIMEOUT = 60
    DATA_AVAILABLE_TIMEOUT = 3
    def __init__(self, ip, port,timeout=10):
        #end_time = time.time() + timeout
        self.address = (ip, port)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(self.CONNECT_TIMEOUT)
        try:
            self._socket.connect(self.address)
            print 'Connect to monitor successfully'
        except socket.error:
            print 'Fail to connect to monitor'
            raise SocketConnectFailed('Fail to connect to monitor')

    def __del__(self):
        self._socket.close()

    def close(self):
        self._socket.close()

    def _data_availabl(self, timeout=DATA_AVAILABLE_TIMEOUT):
        timeout = max(0, timeout)
        try:
            return bool(select.select([self._socket], [], [], timeout)[0])
        except socket.error:
            print 'Verifying data on monitor socket'

    def send_cmd(self, cmd):
        try:
            self._socket.sendall(cmd + '\n')

        except socket.error:
            print 'Fail to send command to monitor.'

    def rec_data(self):
        s = ''
        data = ''
        while self._data_availabl():
            try:
                data = self._socket.recv(1024)
            except socket.error:
                print 'Fail to receive data from monitor.'
                return None

            if not data:
                break
            s += data
        #print 'Monitor data timestamp :' ,time.ctime()
        return s

class RemoteQMPMonitor(RemoteMonitor):
    def __init__(self, ip, port):
        RemoteMonitor.__init__(self, ip, port)

    def qmp_initial(self):
        cmd = '{"execute":"qmp_capabilities"}'
        RemoteMonitor.send_cmd(self, cmd)

    def qmp_cmd(self, cmd):
        cmd ='{"execute": %s}' % cmd
        print cmd
        if re.search(r'quit', cmd):
            RemoteMonitor.send_cmd(self, cmd)
        else:
            RemoteMonitor.send_cmd(self, cmd)
            output = RemoteMonitor.rec_data(self)
            print output
            return output

class RemoteSerialMonitor(RemoteMonitor):
    def __init__(self, ip, port):
        RemoteMonitor.__init__(self, ip, port)

    def serial_login(self, prompt_login=False, passwd='kvmautotest', timeout=300):
        end_time = time.time() + timeout
        if (prompt_login == True):
            while time.time() < end_time:
                output = RemoteMonitor.rec_data(self)
                if re.search(r"login:", output):
                    print output
                    break

        cmd = 'root'
        RemoteMonitor.send_cmd(self, cmd)
        output = RemoteMonitor.rec_data(self)
        print output
        RemoteMonitor.send_cmd(self, passwd)
        output = RemoteMonitor.rec_data(self)
        if not output:
            raise Timeout('Login time out...')
        print output

    def serial_cmd(self, cmd):
        print cmd
        RemoteMonitor.send_cmd(self, cmd)
        #output = RemoteMonitor.rec_data(self)
        #print output

    def serial_output(self, cmd=None):
        output = RemoteMonitor.rec_data(self)
        if cmd:
            output = remove_remote_monitor_endline(output)
        return output

    def serial_get_ip(self):
        ip = ''
        cmd = "ifconfig | grep -E 'inet ' | awk '{ print $2}'"
        self.serial_cmd(cmd)
        output = self.serial_output(cmd)
        for ip in output.splitlines():
            if not ip:
                raise NoGetIP('Could not get ip adress!')
            print 'ip :', ip
            if ip == '127.0.0.1':
                continue
            else:
                return ip


#===========================================Class v2====================================================#
class MonitorFile_v2(Test):
    CONNECT_TIMEOUT = 60
    DATA_AVAILABLE_TIMEOUT = 1
    def __init__(self, case_id, filename, timeout=None):
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        #self._socket.settimeout(self.CONNECT_TIMEOUT)
        Test.__init__(self, case_id=case_id,timeout=timeout)
        try:
            self._socket.connect(filename)
            Test.log_echo_file(self, 'Connect to monitor successfully')
            print 'Connect to monitor successfully'
        except socket.error:
            Test.log_echo_file(self, 'Fail to connect to monitor')
            print 'Fail to connect to monitor : ', filename

    def __del__(self):
        self._socket.close()

    def close(self):
        self._socket.close()

    def _data_availabl(self, timeout=DATA_AVAILABLE_TIMEOUT):
        timeout = max(0, timeout)
        try:
            return bool(select.select([self._socket], [], [], timeout)[0])
        except socket.error:
            Test.log_echo_file(self, 'Verifying data on monitor socket')
            print 'Verifying data on monitor socket'

    def send_cmd(self, cmd):
        try:
            self._socket.sendall(cmd + '\n')

        except socket.error:
            Test.log_echo_file(self, 'Fail to send command to monitor.')
            print 'Fail to send command to monitor.'

    def rec_data(self):
        s = ''
        data = ''
        while self._data_availabl():
        #while True:
            try:
                data = self._socket.recv(8192)
                #data = remove_monitor_cmd_echo(output)
            except socket.error:
                Test.log_echo_file(self, 'Fail to receive data from monitor.')
                print 'Fail to receive data from monitor.'
                return None

            if not data:
                break
            #print 'Monitor data timestamp :', time.ctime()
            s += data
        return s

class SerialMonitorFile_v2(MonitorFile_v2):
    def __init__(self, case_id, filename, timeout=None):
       MonitorFile_v2.__init__(self, case_id=case_id, filename=filename, timeout=timeout)

    def serial_login(self, prompt_login=False, passwd='kvmautotest', timeout=60):
        if (prompt_login == True):
            while True:
                output = MonitorFile_v2.rec_data(self)
                #print type(output)
                MonitorFile_v2.log_echo_file(self, log_str=output)
                print output
                if re.search(r"login:", output):
                    break
        cmd = 'root'
        MonitorFile_v2.send_cmd(self, cmd)
        output = MonitorFile_v2.rec_data(self)
        MonitorFile_v2.log_echo_file(self, log_str=output)
        print output
        MonitorFile_v2.send_cmd(self, passwd)
        output = MonitorFile_v2.rec_data(self)
        MonitorFile_v2.log_echo_file(self, log_str=output)
        print output

    def serial_cmd(self, cmd):
        print cmd
        MonitorFile_v2.send_cmd(self, cmd)
        #output = MonitorFile.rec_data(self)
        #print output

    def serial_output(self, cmd=None):
        output = MonitorFile_v2.rec_data(self)
        if cmd:
            output = remove_monitor_cmd_echo_endline(output, cmd)
        MonitorFile_v2.log_echo_file(self, log_str=output)
        return output

    def serial_get_ip(self):
        ip = ''
        cmd = "ifconfig | grep -E 'inet ' | awk '{ print $2}'"
        self.serial_cmd(cmd)
        output = self.serial_output(cmd)
        for ip in output.splitlines():
            print 'ip :', ip
            if ip == '127.0.0.1':
                continue
            else:
                MonitorFile_v2.log_echo_file(self, log_str=output)
                return ip

class QMPMonitorFile_v2(MonitorFile_v2):
    def __init__(self, case_id, filename, timeout=None):
        MonitorFile_v2.__init__(self, case_id=case_id, filename=filename, timeout=timeout)

    def qmp_initial(self):
        cmd = '{"execute":"qmp_capabilities"}'
        MonitorFile_v2.send_cmd(self, cmd)

    def qmp_cmd(self, cmd):
        cmd ='{"execute": %s}' % cmd
        print cmd
        if re.search(r'quit', cmd):
            MonitorFile_v2.send_cmd(self, cmd)
        else:
            MonitorFile_v2.send_cmd(self, cmd)
            output = MonitorFile_v2.rec_data(self)
            MonitorFile_v2.log_echo_file(self, log_str=output)
            print output
            return output

class RemoteMonitor_v2(Test):
    CONNECT_TIMEOUT = 60
    DATA_AVAILABLE_TIMEOUT = 3
    def __init__(self, case_id, ip, port, timeout=10):
        Test.__init__(self, case_id=case_id, timeout=timeout)
        #end_time = time.time() + timeout
        self.address = (ip, port)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(self.CONNECT_TIMEOUT)
        try:
            self._socket.connect(self.address)
            Test.log_echo_file(self, 'Connect to monitor successfully')
            print 'Connect to monitor successfully'
        except socket.error:
            Test.log_echo_file(self, 'Fail to connect to monitor')
            print 'Fail to connect to monitor'
            raise SocketConnectFailed('Fail to connect to monitor')

    def __del__(self):
        self._socket.close()

    def close(self):
        self._socket.close()

    def _data_availabl(self, timeout=DATA_AVAILABLE_TIMEOUT):
        timeout = max(0, timeout)
        try:
            return bool(select.select([self._socket], [], [], timeout)[0])
        except socket.error:
            Test.log_echo_file(self, 'Verifying data on monitor socket')
            print 'Verifying data on monitor socket'

    def send_cmd(self, cmd):
        try:
            self._socket.sendall(cmd + '\n')

        except socket.error:
            Test.log_echo_file(self, 'Fail to send command to monitor.')
            print 'Fail to send command to monitor.'

    def rec_data(self):
        s = ''
        data = ''
        while self._data_availabl():
            try:
                data = self._socket.recv(1024)
            except socket.error:
                Test.log_echo_file(self, 'Fail to receive data from monitor.')
                print 'Fail to receive data from monitor.'
                return None

            if not data:
                break
            s += data
        #print 'Monitor data timestamp :' ,time.ctime()
        return s

class RemoteQMPMonitor_v2(RemoteMonitor_v2):
    def __init__(self, case_id, ip, port, timeout=None):
        RemoteMonitor_v2.__init__(self, case_id=case_id, ip=ip, port=port, timeout=timeout)

    def qmp_initial(self):
        cmd = '{"execute":"qmp_capabilities"}'
        RemoteMonitor_v2.send_cmd(self, cmd)

    def qmp_cmd(self, cmd):
        cmd ='{"execute": %s}' % cmd
        print cmd
        Test.log_echo_file(self, log_str=cmd)
        if re.search(r'quit', cmd):
            RemoteMonitor_v2.send_cmd(self, cmd)
        else:
            RemoteMonitor_v2.send_cmd(self, cmd)
            output = RemoteMonitor_v2.rec_data(self)
            RemoteMonitor_v2.log_echo_file(self, output)
            print output
            return output

class RemoteSerialMonitor_v2(RemoteMonitor_v2):
    def __init__(self, case_id, ip, port, timeout=None):
        RemoteMonitor_v2.__init__(self, case_id=case_id, ip=ip, port=port, timeout=timeout)

    def serial_login(self, prompt_login=False, passwd='kvmautotest', timeout=300):
        end_time = time.time() + timeout
        if (prompt_login == True):
            while time.time() < end_time:
                output = RemoteMonitor_v2.rec_data(self)
                if re.findall(r'Call Trace:', output):
                    raise RemoteQMPMonitor_v2.test_error(self, 'Guest hit call trace')
                if re.search(r"login:", output):
                    print output
                    RemoteMonitor_v2.log_echo_file(self, output)
                    break

        cmd = 'root'
        RemoteMonitor_v2.send_cmd(self, cmd)
        output = RemoteMonitor_v2.rec_data(self)
        RemoteMonitor_v2.log_echo_file(self, output)
        print output
        RemoteMonitor_v2.send_cmd(self, passwd)
        output = RemoteMonitor_v2.rec_data(self)
        RemoteMonitor_v2.log_echo_file(self, output)
        if not output:
            raise Timeout('Login time out...')
        print output

    def serial_cmd(self, cmd):
        print cmd
        RemoteMonitor_v2.send_cmd(self, cmd)
        #output = RemoteMonitor.rec_data(self)
        #print output

    def serial_output(self, cmd=None):
        output = RemoteMonitor_v2.rec_data(self)
        if cmd:
            output = remove_remote_monitor_endline(output)
        RemoteMonitor_v2.log_echo_file(self, output)
        return output

    def serial_get_ip(self):
        ip = ''
        cmd = "ifconfig | grep -E 'inet ' | awk '{ print $2}'"
        self.serial_cmd(cmd)
        output = self.serial_output(cmd)
        for ip in output.splitlines():
            if not ip:
                raise NoGetIP('Could not get ip adress!')
            print 'ip :', ip
            if ip == '127.0.0.1':
                continue
            else:
                RemoteMonitor_v2.log_echo_file(self, ip)
                return ip


if __name__ == '__main__':
    filename = sys.argv[1]
    monitor = MonitorFile(filename)

    cmd_qmp = '{"execute":"qmp_capabilities"}'
    monitor.send_cmd(cmd_qmp)
    output = monitor.rec_data()
    print  output

    cmd_qmp = '{"execute":"query-status"}'
    monitor.send_cmd(cmd_qmp)
    output = monitor.rec_data()
    print  output

    monitor.close()