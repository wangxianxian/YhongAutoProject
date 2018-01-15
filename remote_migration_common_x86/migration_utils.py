import time
import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([BASE_DIR])
import time
from monitor import RemoteSerialMonitor_v2, RemoteQMPMonitor_v2
import re

def do_migration(test, cmd, src_remote_qmp, dst_remote_qmp, migrate_port, src_ip=None,
                        dst_ip=None):
    if dst_ip:
        cmd = '{"execute":"migrate", "arguments": { "uri": "tcp:%s:%d" }}' % (dst_ip, migrate_port)
        src_remote_qmp.qmp_cmd_output(cmd=cmd)
    else:
        cmd = '{"execute":"migrate", "arguments": { "uri": "tcp:%s:%d" }}' % (src_ip, migrate_port)
        dst_remote_qmp.qmp_cmd_output(cmd=cmd)
    test.sub_step_log('Check the status of migration')
    cmd = '{"execute":"query-migrate"}'
    while 1:
        if dst_ip:
            output = src_remote_qmp.qmp_cmd_output(cmd=cmd)
        else:
            output = dst_remote_qmp.qmp_cmd_output(cmd=cmd)
        if re.findall(r'"remaining": 0', output):
            break
        if re.findall(r'"status": "failed"', output):
            if dst_ip:
                src_remote_qmp.test_error('migration failed')
            else:
                dst_remote_qmp.test_error('migration failed')
        time.sleep(2)

def do_migration_once():
    pass

def ping_pong_migration(test, cmd, id, src_host_session, src_remote_qmp, dst_remote_qmp, src_ip, src_port,
                        dst_ip, dst_port, migrate_port, even_times=2, stop_event=None):
    output = ''
    stop_migrate = False
    stop_migrate = stop_event
    if (even_times % 2) != 0:
        test.test_error('Please set the value of times to even')

    for i in range(1, even_times+1):
        if (even_times % 2) == 0 and stop_migrate == True:
            break
        src_output = src_remote_qmp.qmp_cmd_output(cmd='{"execute":"query-status"}', echo_cmd=False, echo_output=False)
        dst_output = dst_remote_qmp.qmp_cmd_output(cmd='{"execute":"query-status"}', echo_cmd=False, echo_output=False)

        if re.findall(r'"status": "running"', src_output) and re.findall(r'"status": "inmigrate"', dst_output):
            test.test_print('========>>>>>>>> %d : Do migration from src to dst ========>>>>>>>> \n' % i)
            test.sub_step_log('start dst with -incoming ')
            cmd_x86_dst = cmd + '-incoming tcp:0:%d ' % migrate_port
            src_host_session.boot_remote_guest(ip=dst_ip, cmd=cmd_x86_dst, vm_alias='dst')
            dst_remote_qmp = RemoteQMPMonitor_v2(id, dst_ip, dst_port)
            do_migration(test, cmd, src_remote_qmp, dst_remote_qmp, src_ip=None,
                        dst_ip=dst_ip, migrate_port=migrate_port)

        elif re.findall(r'"status": "running"', dst_output) and re.findall(r'"status": "postmigrate"', src_output):
            test.test_print('========>>>>>>>> %d : Do migration from dst to src ========>>>>>>>> \n' % i)
            src_remote_qmp.qmp_cmd_output(cmd='{"execute":"quit"}', echo_cmd=False, echo_output=False)
            test.sub_step_log('start src with -incoming ')
            cmd_x86_src = cmd + '-incoming tcp:0:%d ' % migrate_port
            src_host_session.boot_guest_v2(cmd=cmd_x86_src, vm_alias='src')
            src_remote_qmp = RemoteQMPMonitor_v2(id, src_ip, src_port)
            do_migration(test, cmd, src_remote_qmp, dst_remote_qmp, src_ip=src_ip,
                        dst_ip=None, migrate_port=migrate_port)

        elif re.findall(r'"status": "running"', src_output) and re.findall(r'"status": "postmigrate"', dst_output):
            test.test_print('========>>>>>>>> %d : Do migration from src to dst ========>>>>>>>> \n' % i)
            dst_remote_qmp.qmp_cmd_output(cmd='{"execute":"quit"}', echo_cmd=False, echo_output=False)
            test.sub_step_log('start dst with -incoming ')
            cmd_x86_dst = cmd + '-incoming tcp:0:%d ' % migrate_port
            src_host_session.boot_remote_guest(ip=dst_ip, cmd=cmd_x86_dst, vm_alias='dst')
            dst_remote_qmp = RemoteQMPMonitor_v2(id, dst_ip, dst_port)
            do_migration(test, cmd, src_remote_qmp, dst_remote_qmp, src_ip=None,
                        dst_ip=dst_ip, migrate_port=migrate_port)

    return src_remote_qmp, dst_remote_qmp