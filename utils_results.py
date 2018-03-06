import os, time, sys

bars = ['|', '/', '-', '\\', '|', '/', '-', '\\']
class Results():
    def __init__(self):
        pass

    def display_sum_results(self):
        pass

    def dispaly_process_bar(self):
        sys.stdout.write(' ')
        sys.stdout.flush()
        while 1:
            for bar in bars:
                sys.stdout.write('\b')
                sys.stdout.write(bar)
                sys.stdout.flush()
                time.sleep(0.5)

if __name__ == '__main__':
    ret = Results()
    ret.dispaly_process_bar()
