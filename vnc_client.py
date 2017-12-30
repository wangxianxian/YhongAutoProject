import  sys
from socket import *
import time
#serverHost = '10.66.13.195'
serverHost = '10.72.12.37'
serverPort = 59999

socketobj = socket(AF_INET, SOCK_STREAM)
socketobj.connect((serverHost, serverPort))
requet = 'Trying to connect vnc'
timeout = 1
end_time = time.time() + timeout
while time.time() < end_time:
    socketobj.send(requet)
    data = socketobj.recv(1024)
    print 'Client recevied :', data
socketobj.close()