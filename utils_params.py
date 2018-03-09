import os, sys
BASE_FILE = os.path.dirname(os.path.abspath(__file__))
import re
import yaml
from usr_exceptions import Error
import log_utils

def find_yaml_file(yaml_id):
    file_path = ''
    search_name = yaml_id + '.yaml'
    for (thisdir, subshere, fileshere) in os.walk(BASE_FILE):
        #print 'Searching current file:', thisdir
        for fname in fileshere:
            path = os.path.join(thisdir, fname)
            #print '==>', path
            last_file = re.split(r'/', path)[-1]
            if search_name == last_file:
                print 'Found corresponding yaml file: \n', path
                file_path = path
                return file_path

    if not file_path:
        err_info =  'No found corresponding yaml file :', search_name
        raise Error(err_info)
        #return  file_path

def combine_yaml(requirement_id, case_id):

    pass

def vm_base_cmd_add(base_params, option, value):
    for key, val in base_params.items():
        if re.findall(r'vm_cmd', key):
            #print val
            cmd_dict = val
            for opt, val_list in cmd_dict.items():
                if opt == option:
                    val_list.append(value)

    return base_params

def vm_base_cmd_update(base_params, option, old_value, new_value):
    for key, val in base_params.items():
        if re.findall(r'vm_cmd', key):
            #print val
            cmd_dict = val
            if cmd_dict.has_key(option):
                for opt, val_list in cmd_dict.items():
                    if opt == option:
                        try:
                            index = val_list.index(old_value)
                            cmd_dict[opt][index] = new_value
                        except ValueError:
                            #print 'Error: No such value: %s' % old_value
                            err_info = 'Error: No such value: %s' % old_value
                            raise Error(err_info)
            else:
                #print 'Error: No such option: %s' % option
                err_info = 'Error: No such option: %s' % option
                raise Error(err_info)
    return base_params

def vm_base_cmd_del(base_params, option):
    for key, val in base_params.items():
        if re.findall(r'vm_cmd', key):
            #print val
            cmd_dict = val
            if cmd_dict.has_key(option):
                for opt, val_list in cmd_dict.items():
                    if opt == option:
                        del cmd_dict[opt]
            else:
                #print 'Error: No such option: %s' % option
                err_info = 'Error: No such option: %s' % option
                raise Error(err_info)
    return base_params

def build_dict_from_yaml(yaml_id):
    params_dict = {}
    file = find_yaml_file(yaml_id)
    with open(file) as f:
        params_dict = yaml.load(f)
    #for k, v in params_dict.items():
        #print k, v
    return params_dict

def create_qemu_cmd(params):
    cmd_line = ''
    cmd_line_script = ''
    cmd_line += '/usr/libexec/qemu-kvm '
    cmd_line_script += cmd_line + ' \\' + '\n'
    cmd_dict = {}
    for key, val in params.items():
        if re.findall(r'vm_cmd', key):
            #print val
            cmd_dict = val
            for opt, val in cmd_dict.items():
                for v in val:
                    cmd_line += '-' + opt + ' '
                    cmd_line += str(v) + ' '
                    cmd_line_script +=  '-' + opt + ' '
                    cmd_line_script += str(v) + ' \\' + '\n'

    cmd_line = cmd_line.replace('None', '')
    cmd_line_script = cmd_line_script.replace('None', '')
    print '===>qemu command line: \n', cmd_line
    print '===>qemu command script line: \n', cmd_line_script

class Params():
    def __init__(self, yaml_id):
        self._yaml_id = yaml_id
        self._params = {}
        self.build_dict_from_yaml()

    def get_requirement_id(self):
        return self._yaml_id

    def get(self, key, default=None):
        val = self._params.get(key)
        if not val:
            self._params[key] = default
            val = self._params.get(key)
        return val

    def find_yaml_file(self):
        file_path = ''
        search_name = self._yaml_id + '.yaml'
        for (thisdir, subshere, fileshere) in os.walk(BASE_FILE):
            for fname in fileshere:
                path = os.path.join(thisdir, fname)
                last_file = re.split(r'/', path)[-1]
                if search_name == last_file:
                    #print 'Found corresponding yaml file: \n', path
                    file_path = path
                    return file_path

        if not file_path:
            print 'No found corresponding yaml file :', search_name
            return file_path

    def build_dict_from_yaml(self):
        params_dict = {}
        file = self.find_yaml_file()
        with open(file) as f:
            params_dict = yaml.load(f)
        # for k, v in params_dict.items():
        # print k, v
        self._params = params_dict

    def vm_base_cmd_add(self, option, value):
        val_list = []
        if self._params['vm_cmd_base'].has_key(option) == False:
            val_list.append(value)
            self._params['vm_cmd_base'][option] = val_list
        else:
            for opt, val_list in self._params['vm_cmd_base'].items():
                if opt == option:
                    val_list.append(value)

    def vm_base_cmd_update(self, option, old_value, new_value):
        if self._params['vm_cmd_base'].has_key(option) == True:
            for opt, val_list in self._params['vm_cmd_base'].items():
                if opt == option:
                    try:
                        index = val_list.index(old_value)
                        self._params['vm_cmd_base'][opt][index] = new_value
                    except ValueError:
                        #print 'Error: No such value: %s' % old_value
                        err_info = 'Error: No such value: %s' % old_value
                        raise Error(err_info)
        else:
            #print 'Error: No such option: %s' % option
            err_info = 'Error: No such option: %s' % option
            raise Error(err_info)

    def vm_base_cmd_del(self, option):
        if self._params['vm_cmd_base'].has_key(option) == True:
            for opt, val_list in self._params['vm_cmd_base'].items():
                if opt == option:
                    del self._params['vm_cmd_base'][opt]
        else:
            #print 'Error: No such option: %s' % option
            err_info = 'Error: No such option: %s' % option
            raise Error(err_info)

    def create_qemu_cmd(self):
        cmd_line = ''
        cmd_line_script = ''
        cmd_line += '/usr/libexec/qemu-kvm '
        cmd_line_script += cmd_line + ' \\' + '\n'

        for opt, val in self._params['vm_cmd_base'].items():
            for v in val:
                cmd_line += '-' + opt + ' '
                cmd_line += str(v) + ' '
                cmd_line_script += '-' + opt + ' '
                cmd_line_script += str(v) + ' \\' + '\n'

        cmd_line = cmd_line.replace('None', '')
        cmd_line_script = cmd_line_script.replace('None', '')
        #print '===>qemu command line: \n', cmd_line
        #print '===>qemu command script line: \n', cmd_line_script

        return cmd_line


