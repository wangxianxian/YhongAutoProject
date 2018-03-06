import re
import os
import sys
import time
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_guest_name(cmd):
    cmd_split_lines = re.split(r'\s-', cmd)
    for line in cmd_split_lines:
        if re.findall(r'name', line):
            return line.split(' ')[1]

def creat_images_files():
    src_file = os.path.dirname(os.path.abspath(__file__))
    image_file = src_file + '/images/'
    try:
        os.mkdir(image_file)
        return image_file
    except OSError:
        print 'The directory already exists'
        return None

def creat_isos_files():
    src_file = os.path.dirname(os.path.abspath(__file__))
    isos_file = src_file + '/isos/'
    try:
        os.mkdir(isos_file)
        return isos_file
    except OSError:
        print 'The directory already exists'
        return None

def check_core_dump():
    pass

def progress_wait(case_id='rhel7_00000', inteval_time=0.7):
    progress_status = ['-', '\\', '|', '/', '-', '\\', '|', '/']
    sys.stdout.write('%s Running case %s  ' % (time.ctime(), case_id))
    sys.stdout.flush()
    while True:
        for status in progress_status:
            sys.stdout.write('\b%s' % status)
            time.sleep(inteval_time)
            sys.stdout.flush()

if __name__ == '__main__':
    print os.path.abspath(__file__)
    print os.path.dirname(os.path.abspath(__file__))
    print os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    creat_images_files()
    creat_isos_files()
    progress_wait()

