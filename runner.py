import multiprocessing
import utils_modules
from usr_exceptions import Error
import os
import time
from utils_results import ProgressBar, Results, Status

BASE_FILE = os.path.dirname(os.path.abspath(__file__))

class CaseRunner():
    def __init__(self, params):
        self._params = params
        self._requirement_id = params.get_requirement_id()
        self._case_list = params.get('test_cases')
        self._case_dict = {}
        self._case_dict = utils_modules.setup_modules(self._requirement_id)
        self._run_result = {}
        self._run_result['TOTAL'] = len(self._case_list)
        self._run_result['error_cases'] = []
        self._run_result['pass_cases'] = []
        self._run_result['total_time'] = 0
        self._bar = ProgressBar(total=len(self._case_list))

    def display_sum_results(self):
        self._run_result['ERROR'] = len(self._run_result['error_cases'])
        self._run_result['PASS'] = self._run_result['TOTAL'] - self._run_result['ERROR']

        print '%s' %('+' * 130)
        print 'RESULTS [%s]:' %(self._requirement_id)
        print '==>TOTAL : %s' %(self._run_result['TOTAL'])
        print '==>PASS : %s ' %(self._run_result['PASS'])
        if self._run_result['PASS'] != 0:
            cnt = 1
            for case in self._case_list:
                if case not in self._run_result['error_cases']:
                    self._run_result['pass_cases'].append(case)
            for pass_case in self._run_result['pass_cases']:
                print '   %d: %s' % (cnt, pass_case)
                cnt = cnt + 1
        print '==>ERROR : %s ' %(self._run_result['ERROR'])
        if self._run_result['ERROR'] != 0:
            cnt = 1
            for error_case in self._run_result['error_cases']:
                print '   %d: %s' % (cnt, error_case)
                cnt = cnt + 1
        print '==>RUN TIME : %s min %s sec ' % (int(self._run_time / 60), int(self._run_time - int(self._run_time / 60) * 60))
        print '==>TEST LOG : %s ' %(self._params.get('log_dir'))
        print '%s\n' % ('+' * 130)


    def _run(self, case, case_queue):
        try:
            getattr(self._case_dict[case], "run_case")(self._params)
        except KeyboardInterrupt:
            raise
        except:
            #self._run_result['error_cases'].append(case)
            case_queue.put(case)
            #pipe.close()

    #def _sub_run(self, case_list):
    def main_run(self):
        start_time = time.time()
        cont = 1
        #for case in case_list:
        case_queue = multiprocessing.Queue()
        if self._params.get('verbose') == 'no':
            print '====== Requirement : %s =====:' % (self._requirement_id)
        for case in self._case_list:
            out_pipe, in_pipe = multiprocessing.Pipe()
            if self._params.get('verbose') == 'no':
                print '--> Running case(%s/%s): %s ...' % (cont, self._run_result['TOTAL'], case)
            sub_proc = multiprocessing.Process(target=self._run, args=(case, case_queue))
            sub_proc.start()
            sub_proc.name = case
            sub_proc.join()

            if not case_queue.empty():
                self._run_result['error_cases'].append(case_queue.get())
            #self._run_result['error_cases'].append(out_pipe.recv())
            #out_pipe.close()
            if self._params.get('verbose') == 'no':
                if case in self._run_result['error_cases']:
                    print '----> Case %s done --- %s.' % (case, Status.ERROR)
                else:
                    print '----> Case %s done --- %s.' % (case, Status.PASS)
            cont = cont + 1

        end_time = time.time()
        self._run_time = end_time - start_time

        self.display_sum_results()

    # def main_run(self):
    #     main_proc = multiprocessing.Process(target=self._sub_run, args=(self._case_list,))
    #     main_proc.start()
    #     main_proc.name = 'main_run'

if __name__ == '__main__':
    pass
