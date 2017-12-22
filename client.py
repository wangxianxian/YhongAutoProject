import utils

class Guest_Session:
    def __init__(self, ip, passwd):
        self.__ip = ip
        self.__passwd = passwd

    def guest_cmd(self, cmd):
        return utils.exc_cmd_guest(self.__ip, self.__passwd, cmd)

    def __del__(self):
        pass