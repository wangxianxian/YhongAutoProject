import socket
import select
import sys
import time
from utils import remove_monitor_cmd_echo

class Monitor:
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

class ConsoleMonitor(Monitor):
    pass

class QMPMonitor(Monitor):
    def __init__(self, filename):
        Monitor.__init__(self, filename)

    def qmp_initial(self):
        cmd = '{"execute":"qmp_capabilities"}'
        Monitor.send_cmd(self, cmd)

    def qmp_cmd(self, cmd):
        cmd ='{"execute": %s}' % cmd
        print cmd
        Monitor.send_cmd(self, cmd)
        output = Monitor.rec_data(self)
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

class RemoteSerialMonitor(RemoteMonitor):
    def __init__(self, ip, port):
        RemoteMonitor.__init__(self, ip, port)

    def serial_login(self):
        cmd = 'root'
        RemoteMonitor.send_cmd(self, cmd)
        cmd = 'kvmautotest'
        RemoteMonitor.send_cmd(self, cmd)


    def serial_cmd(self, cmd):
        print cmd
        RemoteMonitor.send_cmd(self, cmd)
        output = RemoteMonitor.rec_data(self)
        print output

    def serial_output(self):
        output = RemoteMonitor.rec_data(self)
        return output

if __name__ == '__main__':
    filename = sys.argv[1]
    monitor = Monitor(filename)

    cmd_qmp = '{"execute":"qmp_capabilities"}'
    monitor.send_cmd(cmd_qmp)
    output = monitor.rec_data()
    print  output

    cmd_qmp = '{"execute":"query-status"}'
    monitor.send_cmd(cmd_qmp)
    output = monitor.rec_data()
    print  output

    monitor.close()