import utils

class Guest_Session:
    def __init__(self, ip, passwd):
        self.__ip = ip
        self.__passwd = passwd

    def guest_cmd(self, cmd, timeout=300):
        return utils.exc_cmd_guest(self.__ip, self.__passwd, cmd, timeout=timeout)

