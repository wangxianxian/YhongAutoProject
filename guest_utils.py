import utils
import re
import string
from vm import TestCmd
import time


class Guest_Session:
    def __init__(self, ip, passwd):
        self.__ip = ip
        self.__passwd = passwd

    def guest_cmd(self, cmd, timeout=300):
        return utils.exc_cmd_guest(self.__ip, self.__passwd, cmd, timeout=timeout)

    def guest_system_dev(self, enable_output=True):
        cmd = 'ls /dev/[svh]d*'
        output = self.guest_cmd(cmd)
        system_dev = re.findall('/dev/[svh]d\w+\d+', output)[0]
        system_dev = system_dev.rstrip(string.digits)
        if enable_output == True:
            print 'system device : ',system_dev
        return system_dev, output

#============================Class Guest_Session_v2=================================================#
class GuestSession_v2(TestCmd):
    def __init__(self, ip, passwd, case_id, timeout=None):
        self.__ip = ip
        self.__passwd = passwd
        TestCmd.__init__(self, case_id=case_id, timeout=timeout)

    def exc_cmd_guest(self, ip, passwd, cmd, timeout=600):
        rept_num = 90
        space_num = 1
        print ('<--%s--> \n Executing guest command: \n    %s' % (time.ctime(), cmd))
        output = TestCmd.remote_ssh_cmd(self, ip=ip, passwd=passwd, cmd=cmd, timeout=timeout)
        print ('%sActual ouput: \n%s' % ((' ' * space_num), output))
        TestCmd.log_echo_file(self, log_str=output)
        return output

    def guest_cmd(self, cmd, timeout=300):
        return self.exc_cmd_guest(self.__ip, self.__passwd, cmd, timeout=timeout)

    def guest_system_dev(self, enable_output=True):
        cmd = 'ls /dev/[svh]d*'
        output = self.guest_cmd(cmd)
        system_dev = re.findall('/dev/[svh]d\w+\d+', output)[0]
        system_dev = system_dev.rstrip(string.digits)
        if enable_output == True:
            print 'system device : ',system_dev
        return system_dev, output
