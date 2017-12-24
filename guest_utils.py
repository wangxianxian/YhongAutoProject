import utils
import re
import string


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
