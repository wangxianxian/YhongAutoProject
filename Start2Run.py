from multiprocessing import Process, Lock
import os, sys
import utils
import time
import imp
from tqdm import tqdm
from progressbar import AnimatedMarker, Bar, BouncingBar, Counter, ETA, \
    FileTransferSpeed, FormatLabel, Percentage, \
    ProgressBar, ReverseBar, RotatingMarker, SimpleProgress, Timer


import sys
import re
import yaml
import utils_params
import utils_modules
import runner
import log_utils

BASE_FILE = os.path.dirname(os.path.abspath(__file__))

def find_cfg(cfg_name):
    cfg_file = ''
    cfg_name = cfg_name + '.cfg'
    for (thisdir, subshere, fileshere) in os.walk(BASE_FILE):
        for fname in fileshere:
            if fname.endswith('.cfg'):
                path = os.path.join(thisdir, fname)
                #print path.split('/')[-1]
                if cfg_name == path.split('/')[-1]:
                    print 'Found corresponding file :\n %s' %path
                    cfg_file = path
                    return cfg_file
    if not cfg_file:
        print 'No found corresponding %s file!' %cfg_name

if __name__ == "__main__":
    test_modules = {}
    requirement_id = ''
    case_list = []
    if len(sys.argv) < 2:
        print "Usage of %s:" % sys.argv[0]
        print " For run test loop please add $requirement_id"
        print " For run test case please add $requirement_id $case_id_1 $case_id_2 $case_id_3 ..."
        sys.exit(1)

    # if len(sys.argv) == 2:
    #     requirement_id = sys.argv[1]
    if len(sys.argv) >= 2:
        requirement_id = sys.argv[1]
        for case in sys.argv[2:]:
            case_list.append(case)

    params = utils_params.Params(requirement_id, case_list)

    log_dir = log_utils.create_log_file(requirement_id)

    params.get('log_dir', log_dir)

    runner = runner.CaseRunner(params)

    runner.main_run()



