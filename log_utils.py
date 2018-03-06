import os, sys, time
from vm import Test

BASE_FILE = os.path.dirname(os.path.abspath(__file__))

#=================================================#
def create_log_file(requirement_id):
    logs_base_path = os.path.join(BASE_FILE, 'test_logs')
    #print logs_base_path
    if not os.path.exists(logs_base_path):
        os.mkdir(logs_base_path)

    timestamp = time.strftime("%Y-%m-%d-%H:%M:%S")
    log_file = requirement_id + '-' + timestamp
    log_path = os.path.join(logs_base_path, log_file)
    #print log_path
    os.mkdir(log_path)
    return log_path


class StepLog(Test):
    def __init__(self, case_id=None):
        Test.__init__(self, case_id=case_id)

    def main_step_log(self, log):
        log_tag = '='
        log_tag_rept = 7
        log_info = '%s Step %s %s' %(log_tag*log_tag_rept, log, log_tag*log_tag_rept)
        print log_info
        Test.log_echo_file(self, log_str=log_info)

    def sub_step_log(self, str):
        log_tag = '-'
        log_tag_rept = 5
        log_info = '%s %s %s' %(log_tag*log_tag_rept, str, log_tag*log_tag_rept)
        Test.test_print(self, info=log_info)

if __name__ == '__main__':
    pass