import multiprocessing
import utils_modules
from usr_exceptions import Error
import os
import sys
import time
from utils_results import ProgressBar, Results, Status
import traceback

BASE_FILE = os.path.dirname(os.path.abspath(__file__))
bars = ['|', '/', '-', '\\', '|', '/', '-', '\\']

class CaseRunner():
    def __init__(self, params):
        self._result = Results()
        self._bars = ['|', '/', '-', '\\', '|', '/', '-', '\\']
        self._params = params
        self._requirement_id = params.get_requirement_id()
        self._requirement_name = params.get('test_requirement')['name'][0]
        self._case_list = []
        self._case_dict = {}
        self._case_dict = utils_modules.setup_modules(self._requirement_id)
        self._run_result = {}
        self._run_result['error_cases'] = []
        self._run_result['pass_cases'] = []
        self._run_result['total_time'] = 0
        self._bar = ProgressBar(total=len(self._case_list))
        self.get_case_list()
        self._run_result['TOTAL'] = len(self._case_list)

    def dispaly_process_bar(self, processor):
        sys.stdout.write(' ')
        sys.stdout.flush()
        while processor.is_alive():
            for bar in self._bars:
                sys.stdout.write('\b')
                sys.stdout.write(bar)
                sys.stdout.flush()
                time.sleep(0.5)

    def get_case_list(self):
        for k, v in self._params.get('test_cases').items():
            self._case_list.append(k)
        #print self._case_list

    def display_sum_results(self):
        self._run_result['ERROR'] = len(self._run_result['error_cases'])
        self._run_result['PASS'] = self._run_result['TOTAL'] - self._run_result['ERROR']

        print '\033[93m%s\033[00m' %('*' * 94)
        print 'RESULTS [%s]:' %(self._requirement_id.upper().replace('_', '-'))
        print '==>TOTAL : %s' %(self._run_result['TOTAL'])
        print '==>PASS : %s ' %(self._run_result['PASS'])
        if self._run_result['PASS'] != 0:
            cnt = 1
            for case in self._case_list:
                if case not in self._run_result['error_cases']:
                    self._run_result['pass_cases'].append(case)
            for pass_case in self._run_result['pass_cases']:
                print '   %d: %s-%s' % (cnt, pass_case.upper().replace('_', '-'),
                                        self._params.get('test_cases')[pass_case]['name'][0])
                cnt = cnt + 1
        print '==>ERROR : %s ' %(self._run_result['ERROR'])
        if self._run_result['ERROR'] != 0:
            cnt = 1
            for error_case in self._run_result['error_cases']:
                print '   %d: \033[91m%s\033[00m-%s' % (cnt, error_case.upper().replace('_', '-'),
                                        self._params.get('test_cases')[error_case]['name'][0])
                cnt = cnt + 1
        print '==>RUN TIME : %s min %s sec ' % (int(self._run_time / 60), int(self._run_time - int(self._run_time / 60) * 60))
        print '==>TEST LOG : %s ' %(self._params.get('log_dir'))
        print '\033[93m%s\033[00m' % ('*' * 94)

    def _run(self, case, case_queue):
        log_file_list = []
        try:
            getattr(self._case_dict[case], "run_case")(self._params)
        except KeyboardInterrupt:
            raise
        except Exception as info:
            test_log_dir = os.path.join(self._params.get('log_dir'), case + '_logs')
            log_file = test_log_dir + '/' + 'long_debug.log'
            log_file_list.append(log_file)
            log_file = test_log_dir + '/' + 'short_debug.log'
            log_file_list.append(log_file)
            for log_file in log_file_list:
                if os.path.exists(log_file):
                    traceback.print_exc(file=open(log_file, "a"))
            case_queue.put(case)

    def _clean_vm(self):
        pass

    #def _sub_run(self, case_list):
    def main_run(self):
        start_time = time.time()
        cont = 1
        #for case in case_list:
        case_queue = multiprocessing.Queue()
        if self._params.get('verbose') == 'no':
            print '\033[94m%s Test Requirement: %s(%s) %s\033[00m' % \
                  (('=' * 25), self._requirement_id.upper().replace('_', '-'), self._requirement_name, ('=' * 25),)
        for case in self._case_list:
            self._sub_start_time = time.time()
            if self._params.get('verbose') == 'no':
                info = '--> Running case(%s/%s): %s-%s ' % (cont, self._run_result['TOTAL'], case.upper().replace('_', '-'),
                                                           self._params.get('test_cases')[case]['name'][0])
                sys.stdout.write(info)
                sys.stdout.flush()
            sub_proc = multiprocessing.Process(target=self._run, args=(case, case_queue))
            sub_proc.start()
            sub_proc.name = case
            if self._params.get('verbose') == 'no':
                self.dispaly_process_bar(sub_proc)
            sub_proc.join()

            self._sub_end_time = time.time()
            self._sub_run_time = self._sub_end_time - self._sub_start_time
            if not case_queue.empty():
                self._run_result['error_cases'].append(case_queue.get())
            if self._params.get('verbose') == 'no':
                sys.stdout.write('\b')
                if case in self._run_result['error_cases']:
                    info = '(%s min %s sec)--- %s.\n' % (int(self._sub_run_time / 60),
                                                         int(self._sub_run_time - int(self._sub_run_time / 60) * 60),
                                             Status.ERROR)
                else:
                    info = '(%s min %s sec)--- %s.\n' % (int(self._sub_run_time / 60),
                                                         int(self._sub_run_time - int(self._sub_run_time / 60) * 60),
                                             Status.PASS)
                sys.stdout.write(info)
                sys.stdout.flush()
            cont = cont + 1

        end_time = time.time()
        self._run_time = end_time - start_time

        self.display_sum_results()

if __name__ == '__main__':
    pass
