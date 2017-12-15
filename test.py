import subprocess

if __name__ == '__main__':
    output = ''
    #sub = subprocess.Popen('/usr/libexec/qemu-kvm -name yhong-guest -monitor stdio',
     #                      shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    sub = subprocess.Popen('ls',
                           shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = sub.communicate('/home/yhong')[0]

    print output