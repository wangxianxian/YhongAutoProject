import migration_config as case
import threading
import rhel7_10022
import rhel7_10039
import os

if __name__ == '__main__':
    testlock = threading.Lock()
    print 'Start to run......'
    rhel7_10022.run_case()
    rhel7_10039.run_case()
    pass
