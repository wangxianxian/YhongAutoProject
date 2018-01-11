from vm import Test
import os
import re
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Conf(Test):
    def __init__(self, case_id):
        self.filename = case_id.split(':')[0] + '.cfg'
        #self.file = glob.glob(self.filename)
        Test.__init__(self, case_id=case_id)

    def get_file_cfg(self):
        for file in os.listdir(BASE_DIR):
            if re.findall(self.filename, file):
                print file
                return file
        err_info = 'No found %s' % self.filename
        Test.test_error(self, err_info)

    def get_params(self, params):
        file = self.get_file_cfg()
        content = open(file, "r")

        pass

if __name__ == '__main__':
    print '1 :', os.path.abspath(__file__)
    print '2 :', os.path.dirname(os.path.abspath(__file__))
    print '3 :', os.path.dirname(os.path.dirname(os.path.abspath(__file__)))