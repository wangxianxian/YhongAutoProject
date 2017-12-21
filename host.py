from utils import subprocess_cmd
from config import GUEST_NAME
import re

def check_guest_thread(cmd=None):
    guest_name = GUEST_NAME
    cmd_check = 'ps -axu| grep %s' % guest_name
    output = subprocess_cmd('cmd_check')
    for line in output.splitlines():
        if re.search(cmd, line):
            return True



if __name__ == '__main__':
    check_guest_thread