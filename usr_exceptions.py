import exceptions

class Timeout(Exception):
    def __init__(self, str):
        self.error_info = str
    def __str__(self):
        return self.error_info

class NoGetIP(Exception):
    def __init__(self, str):
        self.error_info = str
    def __str__(self):
        return self.error_info

class SocketConnectFailed(Exception):
    def __init__(self, str):
        self.error_info = str
    def __str__(self):
        return self.error_info

class GuestBootFailed(Exception):
    def __init__(self, str):
        self.error_info = str
    def __str__(self):
        return self.error_info


if __name__ == '__main__':
    try:
        raise Timeout('it timeout')
    except Timeout as t:
        print 'show :', t.error_info

    raise Timeout('aa')