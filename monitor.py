import socket
import select
import sys

class Monitor:
    CONNECT_TIMEOUT = 60
    DATA_AVAILABLE_TIMEOUT = 0
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

    def _data_availabl(self):
        timeout = self.DATA_AVAILABLE_TIMEOUT
        try:
            return bool(select.select([self.__socket], [], [], timeout)[0])
        except socket.error:
            print 'Verifying data on monitor socket'

    def rec_data(self):
        s = ''
        data = ''
        while self._data_availabl():
        #while True:
            try:
                data = self.__socket.recv(4096)
            except socket.error:
                print 'Fail to receive data from monitor.'

            if not data:
                break
            s += data
        return s

    def send_cmd(self, cmd):
        try:
            self.__socket.sendall(cmd + '\n')

        except socket.error:
            print 'Fail to send command to monitor.'

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