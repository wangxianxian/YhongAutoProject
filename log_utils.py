import os, sys, time
from vm import Test

#=================================================#
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