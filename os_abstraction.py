import os
import shutil
from configuration import Configuration
from sys import stdout

class IOSAbstraction:
    def ask_for_confirmation(self, prompt): pass
    def show_error(self, message): pass
    def show_info(self, message): pass
    
    def abspath(self, path): pass
    def isdir(self, path): pass
    def mkdir(self, path): pass
    def isfile(self, path): pass
    def split_path(self, path): pass
    def rename_move(self, old_path, new_path): pass
    def delete(self, path): pass
    def copy(self, old_path, new_path): pass
    def make_link(self, old_path, new_path): pass

class OSAbstraction(IOSAbstraction):
    def __init__(self, config:Configuration):
        self._conf = config

    def ask_for_confirmation(self, prompt):
        stdout.write("%s [y/N]: " % prompt)
        response = input()
        if len(response) > 0 and response[0] in ['y', 'Y']:
            return True
        else:
            return False

    def show_error(self, message):
        print("ERROR: %s" % message)

    def show_info(self, message):
        print("%s" % message)

    def abspath(self, path):
        return os.path.abspath(path)
    
    def isdir(self, path):
        return os.path.isdir(path)

    def mkdir(self, path):
        try:
            os.makedirs(path)
            return (True, "")
        except Exception as ex:
            return (False, str(ex))

    def isfile(self, path):
        return os.path.isfile(path)

    def split_path(self, path):
        return (os.path.dirname(path), os.path.basename(path))
    
    def rename_move(self, old_path, new_path):
        if self._conf.simulation_mode:
            print("mv %s %s" % (old_path, new_path))
            return (True, "")
        else:
            try:
                os.rename(old_path, new_path)
                return (True, "")
            except Exception as ex:
                return (False, str(ex))

    def delete(self, path):
        if self._conf.simulation_mode:
            print("rm %s" % path)
            return (True, "")
        else:
            try:
                os.remove(path)
                return (True, "")
            except Exception as ex:
                return (False, str(ex))


    def copy(self, old_path, new_path):
        if self._conf.simulation_mode:
            print("cp %s %s" % (old_path, new_path))
            return (True, "")
        else:
            try:
                shutil.copyfile(old_path, new_path)
                return (True, "")
            except Exception as ex:
                return (False, str(ex))

    def make_link(self, old_path, new_path):
        # FIXME  symlink's target must be relative to the path where the symlink
        # is stored (or absolute)
        if self._conf.simulation_mode:
            print("ln -s %s %s" % (old_path, new_path))
            return (True, "")
        else:
            try:
                os.symlink(old_path, new_path)
                return (True, "")
            except Exception as ex:
                return (False, str(ex))

def get_file_list_nonrecursive(directory:str, include_directories:bool):
    for name in os.listdir(directory):
        path = os.path.join(directory, name)
        if os.path.isdir(path) and not include_directories:
            continue
        yield path

def get_file_list_recursive(directory:str, include_directories:bool):
    for root, dirs, files in os.walk(directory):
        if include_directories:
            for name in dirs:
                yield os.path.join(root, name)
        for name in files:
            yield os.path.join(root, name)

