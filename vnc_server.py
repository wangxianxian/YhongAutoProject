from socket import  *
import subprocess
import time

myHost = ''
myPort_src = 59999
myPort_dst = 58888

cmd_src = 'vncviewer 10.66.10.122:30'
src = socket(AF_INET, SOCK_STREAM)
src.bind((myHost, myPort_src))
src.listen(5)

cmd_dst = 'vncviewer 10.66.10.208:30'
dst = socket(AF_INET, SOCK_STREAM)
dst.bind((myHost, myPort_dst))
dst.listen(5)

while True:
    connection_src, address_src = src.accept()
    print 'Server connected by', address_src
    echo_src = 'Connect successfully'

    connection_dst, address_dst = dst.accept()
    print 'Server connected by', address_dst
    echo_dst = 'Connect successfully'

    while True:
        data_src = connection_src.recv(1024)
        data_dst = connection_dst.recv(1024)
        time.sleep(3)
        if not data_src and not data_dst:
            break
            connection_src.send(b'Echo ==>' + echo_src)
            connection_dst.send(b'Echo ==>' + echo_dst)
        sub_src = subprocess.Popen(cmd_src, shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        sub_dst = subprocess.Popen(cmd_dst, shell=True, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    connection_src.close()
    connection_dst.close()


