import migration_config as case
import threading
import rhel7_10022
import rhel7_10039
import os

if __name__ == '__main__':
    #testlock = threading.Lock()
    #print 'Start to run......'
    #thread = threading.Thread(target=rhel7_10022.run_case, args=('10.66.10.122', '10.66.10.208', testlock, 60))
    #thread.start()
    #thread = threading.Thread(target=rhel7_10039.run_case, args=('10.66.10.122', '10.66.10.208', testlock, 60))
    #thread.start()
    pid = os.fork()
    if pid == 0:
        rhel7_10022.run_case()
    pass