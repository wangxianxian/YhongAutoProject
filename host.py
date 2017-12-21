from utils import subprocess_cmd
from config import GUEST_NAME
import re


def check_guest_thread(cmd=None):
    name = '-name ' + GUEST_NAME
    pid =''
    guest_name = GUEST_NAME
    cmd_check = 'ps -axu| grep %s' % guest_name
    output = subprocess_cmd(cmd_check)
    for line in output.splitlines():
        if re.findall(name, line):
            pid = re.findall(r"\d+", line)[0]
            return pid
    return pid

def kill_guest_thread(pid=None):
    cmd = 'kill -9 %s' % pid
    subprocess_cmd(cmd)

if __name__ == '__main__':
    pass