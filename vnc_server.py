from socket import  *
import subprocess
import time

myHost = ''
myPort = 59999

cmd = 'vncviewer 10.66.10.122:30'
socketobj = socket(AF_INET, SOCK_STREAM)
socketobj.bind((myHost, myPort))
socketobj.listen(5)

while True:
    connection, address = socketobj.accept()
    print 'Server connected by', address
    echo = 'Connect successfully'
    while True:
        data = connection.recv(1024)
        time.sleep(3)
        if not data:
            break
        connection.send(b'Echo ==>' + echo)
        sub = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    connection.close()


