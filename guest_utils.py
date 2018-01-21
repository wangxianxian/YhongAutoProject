import re
import string
from vm import TestCmd
import pexpect

#============================Class Guest_Session_v2=================================================#
class GuestSession_v2(TestCmd):
    def __init__(self, ip, passwd, case_id):
        self.__ip = ip
        self.__passwd = passwd
        TestCmd.__init__(self, case_id=case_id)

    def exc_cmd_guest(self, ip, passwd, cmd, timeout=300):
        output = TestCmd.remote_ssh_cmd_v2(self, ip=ip, passwd=passwd, cmd=cmd, timeout=timeout)
        return output

    def guest_cmd_output(self, cmd, echo_cmd=True, echo_output=True, timeout=300):
        if echo_cmd == True:
            TestCmd.test_print(self, cmd)
        output = self.exc_cmd_guest(self.__ip, self.__passwd, cmd=cmd, timeout=timeout)
        # Here need to remove command echo and blank space again
        output = TestCmd.remove_cmd_echo_blank_space(self, output=output, cmd=cmd)
        if echo_output == True:
            TestCmd.test_print(self, output)
        return output

    def guest_system_dev(self, enable_output=True):
        cmd = 'ls /dev/[svh]d*'
        output = self.guest_cmd_output(cmd)
        system_dev = re.findall('/dev/[svh]d\w+\d+', output)[0]
        system_dev = system_dev.rstrip(string.digits)
        if enable_output == True:
            info = 'system device : %s' %system_dev
            TestCmd.test_print(self, info=info)
        return system_dev, output
