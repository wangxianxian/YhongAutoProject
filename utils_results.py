import os, time, sys

class Status:
    PASS = "\033[92mPASS\033[00m"
    ERROR = "\033[91mERROR\033[00m"
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNINGYELLOW = '\033[93m'
    FAILRED = '\033[91m'
    ENDC = '\033[5m'

bars = ['|', '/', '-', '\\', '|', '/', '-', '\\']
class Results():
    def __init__(self):
        self._bars = ['|', '/', '-', '\\', '|', '/', '-', '\\']

    def display_sum_results(self):
        pass

    def dispaly_process_bar(self, condition):
        sys.stdout.write(' ')
        sys.stdout.flush()
        while condition:
            for bar in self._bars:
                sys.stdout.write('\b')
                sys.stdout.write(bar)
                sys.stdout.flush()
                time.sleep(0.5)

class ProgressBar:
    def __init__(self,count = 0,total = 0,width = 50):
        self.count = count
        self.total = total
        self.width = width
    def move(self):
        self.count += 1
    def log(self,s):
        sys.stdout.write(' ' * (self.width + 9) + '\r')
        sys.stdout.flush()
        print s
        progress = self.width * self.count / self.total
        sys.stdout.write('{0:3}/{1:3}: '.format(self.count,self.total))
        sys.stdout.write('#' * progress + '-' * (self.width - progress) + '\r')
        if progress == self.width:
            sys.stdout.write('\n')
        sys.stdout.flush()


if __name__ == '__main__':
    ret = Results()
    ret.dispaly_process_bar()

    # bar = ProgressBar(total=10)
    # for i in range(10):
    #     bar.move()
    #     bar.log('We have arrived at: ' + str(i + 1))
    #     time.sleep(1)
