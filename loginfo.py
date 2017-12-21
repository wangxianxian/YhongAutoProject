
def main_step_log(str=None):
    log_tag = '='
    log_tag_rept = 5
    info = str
    print ('%s %s %s' %(log_tag*log_tag_rept, str, log_tag*log_tag_rept))
    pass

def sub_step_log(str=None):
    log_tag = '-'
    log_tag_rept = 3
    info = str
    print ('%s %s %s' %(log_tag*log_tag_rept, str, log_tag*log_tag_rept))
    pass


if __name__ == '__main__':
    main_step_log('This is a main step')
    sub_step_log('this is a sub step')
    pass