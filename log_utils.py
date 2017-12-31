import os, sys, time
from vm import Test

def main_step_log(str=None):
    log_tag = '='
    log_tag_rept = 5
    print ('%s %s %s' %(log_tag*log_tag_rept, str, log_tag*log_tag_rept))
    log = '%s %s %s' %(log_tag*log_tag_rept, str, log_tag*log_tag_rept)
    log_echo_file(log_str=log)

def sub_step_log(str=None):
    log_tag = '-'
    log_tag_rept = 3
    info = str
    print ('%s %s %s' %(log_tag*log_tag_rept, str, log_tag*log_tag_rept))

def log_echo_file(case_id=None,log_str=None):
    pre_path = os.getcwd()
    path = pre_path + '/run_log/'
    if not os.path.exists(path):
        os.mkdir(path)
    prefix_file = case_id
    if not prefix_file:
        prefix_file = 'Untitled'
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

#=================================================#
class StepLog(Test):
    def __init__(self, case_id=None, tiemout=None):
        Test.__init__(self, case_id=case_id, timeout=tiemout)

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
        #print log_info
        #Test.log_echo_file(self, log_str=log_info)

if __name__ == '__main__':
    main_step_log('This is a main step')
    sub_step_log('this is a sub step')
    """
    log_echo_file('RHEL7-1111', 'Scanning USB ')
    log_echo_file('RHEL7-1111', '  XHCI: Initializing ')
    log_echo_file('RHEL7-1111', '    USB Keyboard  ')
    log_echo_file('RHEL7-1111', 'No console specified using screen & keyboard ')
    log_echo_file('RHEL7-1111', '      ')
    log_echo_file('RHEL7-1111', ' ')
    log_echo_file('RHEL7-1111', ' ')
    log_echo_file('RHEL7-1111', '  Welcome to Open Firmware ')
    log_echo_file('RHEL7-1111', ' ')
    log_echo_file('RHEL7-1111', '  Copyright (c) 2004, 2017 IBM Corporation All rights reserved. ')
    log_echo_file('RHEL7-1111', '  This program and the accompanying materials are made available ')
    log_echo_file('RHEL7-1111', '  under the terms of the BSD License available at ')
    log_echo_file('RHEL7-1111', '  http://www.opensource.org/licenses/bsd-license.php ')
    log_echo_file('RHEL7-1111', ' ')
    log_echo_file('RHEL7-1111', ' ')
    log_echo_file('RHEL7-1111',
                  'Trying to load:  from: /pci@800000020000000/scsi@6/disk@100000000000000 ...   Successfully loaded ')
    log_echo_file('RHEL7-1111', 'CF000012 ')
    log_echo_file('RHEL7-1111', 'CF000015ch ')
    log_echo_file('RHEL7-1111', 'Linux ppc64 ')
    log_echo_file('RHEL7-1111', '#1 SMP Tue Dec 2 ')
    log_echo_file('RHEL7-1111', 'Red Hat Enterprise Linux Server 7.5 Beta (Maipo) ')
    log_echo_file('RHEL7-1111', 'Kernel 3.10.0-825.el7.ppc64 on an ppc64 ')
    log_echo_file('RHEL7-1111', 'dhcp46-201 login:  ')
    """

    log_echo_file('Scanning USB ')
    log_echo_file('  XHCI: Initializing ')
    log_echo_file('    USB Keyboard  ')
    log_echo_file('No console specified using screen & keyboard ')
    log_echo_file('      ')
    log_echo_file(' ')
    log_echo_file(' ')
    log_echo_file('  Welcome to Open Firmware ')
    log_echo_file(' ')
    log_echo_file('  Copyright (c) 2004, 2017 IBM Corporation All rights reserved. ')
    log_echo_file('  This program and the accompanying materials are made available ')
    log_echo_file('  under the terms of the BSD License available at ')
    log_echo_file('  http://www.opensource.org/licenses/bsd-license.php ')
    log_echo_file(' ')
    log_echo_file(' ')
    log_echo_file('CF000012 ')
    log_echo_file('CF000015ch ')
    log_echo_file('Linux ppc64 ')
    log_echo_file('#1 SMP Tue Dec 2 ')
    log_echo_file('Red Hat Enterprise Linux Server 7.5 Beta (Maipo) ')
    log_echo_file('Kernel 3.10.0-825.el7.ppc64 on an ppc64 ')
    log_echo_file('dhcp46-201 login:  ')


    pass