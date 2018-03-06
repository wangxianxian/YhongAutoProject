import signal
import multiprocessing
import utils_modules
from usr_exceptions import Error


class CaseRunner():
    def __init__(self, params):
        self._params = params
        self._requirement_id = params.get_requirement_id()
        self._case_list = params.get('test_cases')
        self._case_dict = {}
        self._case_dict = utils_modules.setup_modules(self._requirement_id)

    def _run(self, case):
        try:
            getattr(self._case_dict[case], "run_case")(self._params)
        except Error:
            print 'Case %s test error.' % case

    def _sub_run(self, case_list):
        print 'Case list: ' ,case_list
        for case in case_list:
            sub_proc = multiprocessing.Process(target=self._run, args=(case,))
            sub_proc.start()
            sub_proc.name = case
            sub_proc.join()

    def main_run(self):
        main_proc = multiprocessing.Process(target=self._sub_run, args=(self._case_list,))
        main_proc.start()
        main_proc.name = 'main_run'
        #main_proc.daemon = True
