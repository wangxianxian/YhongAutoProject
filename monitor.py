import socket
import select
import sys
import re
import time
from utils import remove_monitor_cmd_echo_endline, remove_remote_monitor_endline

class MonitorFile:
    CONNECT_TIMEOUT = 60
    DATA_AVAILABLE_TIMEOUT = 3
    def __init__(self, filename):
        self.__socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        #self.__socket.settimeout(self.CONNECT_TIMEOUT)

        try:
            self.__socket.connect(filename)
        except socket.error:
            print 'Fail to connect to monitor : ', filename

    def __del__(self):
        self.__socket.close()

    def close(self):
        self.__socket.close()

    def _data_availabl(self, timeout=DATA_AVAILABLE_TIMEOUT):
        timeout = max(0, timeout)
        try:
            return bool(select.select([self.__socket], [], [], timeout)[0])
        except socket.error:
            print 'Verifying data on monitor socket'

    def send_cmd(self, cmd):
        try:
            self.__socket.sendall(cmd + '\n')

        except socket.error:
            print 'Fail to send command to monitor.'

    def rec_data(self):
        s = ''
        data = ''
        while self._data_availabl():
        #while True:
            try:
                data = self.__socket.recv(8192)
                #data = remove_monitor_cmd_echo(output)
            except socket.error:
                print 'Fail to receive data from monitor.'
                return None

            if not data:
                break
            s += data
        return s

class SerialMonitorFile(MonitorFile):
    def __init__(self, filename):
        MonitorFile.__init__(self, filename)

    def serial_login(self, prompt_login=False, passwd='kvmautotest'):
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
        MonitorFile.send_cmd(self, cmd)
        output = MonitorFile.rec_data(self)
        print output
        return output

class RemoteMonitor():
    CONNECT_TIMEOUT = 60
    DATA_AVAILABLE_TIMEOUT = 3
    def __init__(self, ip, port):
        self.address = (ip, port)
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.__socket.connect(self.address)
        except socket.error:
            print 'Fail to connect to monitor '

    def __del__(self):
        self.__socket.close()

    def close(self):
        self.__socket.close()

    def _data_availabl(self, timeout=DATA_AVAILABLE_TIMEOUT):
        timeout = max(0, timeout)
        try:
            return bool(select.select([self.__socket], [], [], timeout)[0])
        except socket.error:
            print 'Verifying data on monitor socket'

    def send_cmd(self, cmd):
        try:
            self.__socket.sendall(cmd + '\n')

        except socket.error:
            print 'Fail to send command to monitor.'

    def rec_data(self):
        s = ''
        data = ''
        while self._data_availabl():
            # while True:
            try:
                data = self.__socket.recv(8192)
                # data = remove_monitor_cmd_echo(output)
            except socket.error:
                print 'Fail to receive data from monitor.'
                return None

            if not data:
                break
            s += data
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
        RemoteMonitor.send_cmd(self, cmd)
        output = RemoteMonitor.rec_data(self)
        print output

    def qmp_cmd_result(self, cmd):
        cmd ='{"execute": %s}' % cmd
        print cmd
        RemoteMonitor.send_cmd(self, cmd)
        output = RemoteMonitor.rec_data(self)
        print output
        return output

class RemoteSerialMonitor(RemoteMonitor):
    def __init__(self, ip, port):
        RemoteMonitor.__init__(self, ip, port)

    def serial_login(self, prompt_login=False, passwd='kvmautotest'):
        if (prompt_login == True):
            while True:
                output = RemoteMonitor.rec_data(self)
                #print type(output)
                print output
                if re.search(r"login:", output):
                    break
        cmd = 'root'
        RemoteMonitor.send_cmd(self, cmd)
        output = RemoteMonitor.rec_data(self)
        print output
        RemoteMonitor.send_cmd(self, passwd)
        output = RemoteMonitor.rec_data(self)
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