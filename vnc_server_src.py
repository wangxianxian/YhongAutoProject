from socket import  *
import subprocess
import time

myHost = ''
myPort_src = 59999

cmd_src = 'vncviewer 10.66.10.122:30'
src = socket(AF_INET, SOCK_STREAM)
src.bind((myHost, myPort_src))
src.listen(5)

while True:
    connection_src, address_src = src.accept()
    print 'Server connected by', address_src
    echo_src = 'Connect successfully'

    while True:
        data_src = connection_src.recv(1024)
        time.sleep(3)
        if not data_src:
            break
            connection_src.send(b'Echo ==>' + echo_src)
        sub_src = subprocess.Popen(cmd_src, shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    connection_src.close()


