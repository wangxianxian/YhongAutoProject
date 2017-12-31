from socket import  *
import subprocess
import time

myHost = ''
myPort_dst = 58888

cmd_dst = 'vncviewer 10.66.10.208:30'
dst = socket(AF_INET, SOCK_STREAM)
dst.bind((myHost, myPort_dst))
dst.listen(5)

while True:
    connection_dst, address_dst = dst.accept()
    print 'Server connected by', address_dst
    echo_dst = 'Connect successfully'

    while True:
        data_dst = connection_dst.recv(1024)
        time.sleep(3)
        if not data_dst:
            break
            connection_dst.send(b'Echo ==>' + echo_dst)
        sub_dst = subprocess.Popen(cmd_dst, shell=True, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    connection_dst.close()


