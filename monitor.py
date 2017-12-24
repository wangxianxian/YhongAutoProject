import socket
import select
import sys
import re
import time
from utils import remove_monitor_cmd_echo_endline, remove_remote_monitor_endline
from usr_exceptions import Timeout, NoGetIP, SocketConnectFailed

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
    """
    def qmp_cmd_result(self, cmd):
        cmd ='{"execute": %s}' % cmd
        print cmd
        RemoteMonitor.send_cmd(self, cmd)
        output = RemoteMonitor.rec_data(self)
        print output
        return output
    """
class RemoteMonitor():
    CONNECT_TIMEOUT = 60
    DATA_AVAILABLE_TIMEOUT = 3
    def __init__(self, ip, port,timeout=10):
        end_time = time.time() + timeout
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
    """
    def qmp_cmd_result(self, cmd):
        cmd ='{"execute": %s}' % cmd
        print cmd
        RemoteMonitor.send_cmd(self, cmd)
        output = RemoteMonitor.rec_data(self)
        print output
        return output
    """

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