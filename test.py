import os,sys,time,subprocess
import pexpect
import subprocess
import socket
import select
import re
import usr_exceptions

class Test():
    def __init__(self, case_id=None, timeout=None):
        self._case_id = case_id

    def _log_echo_file(self, case_id=None, log_str=None):
        pre_path = os.getcwd()
        path = pre_path + '/run_log/'
        if not os.path.exists(path):
            os.mkdir(path)
        prefix_file = case_id
        log_file = path + prefix_file
        try:
            run_log = open(log_file, "a")
            for line in log_str.splitlines():
                timestamp = time.strftime("%Y-%m-%d-%H:%M:%S")
                run_log.write(
                    "%s: %s\n" % (timestamp, line))
        except Exception, err:
            txt = "Fail to record log to %s.\n" % log_file
            txt += "Log content: %s\n" % log_str
            txt += "Exception error: %s" % err

    def subprocess_cmd_v2(self, cmd, enable_output=True):
        print cmd
        sub = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        fd = sub.stdout.fileno()
        if (enable_output == True):
            output = sub.communicate()[0]
            print output
            self._log_echo_file(self._case_id, output)
            return output, fd
        elif (enable_output == False):
            return fd

    pass