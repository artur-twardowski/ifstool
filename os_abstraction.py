import os
import shutil
from configuration import Configuration
from sys import stdout
from console_output import print_error, print_warning, print_debug
from console_output import print_message, print_status, print_prompt


class IOSAbstraction:
    def ask_for_confirmation(self, prompt): pass
    def show_error(self, message): pass
    def show_warning(self, message): pass
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
    def __init__(self, config: Configuration):
        self._conf = config

    def ask_for_confirmation(self, prompt):
        print_prompt(prompt, ["&yes", "&no"], "n")
        response = input()
        if len(response) > 0 and response[0] in ['y', 'Y']:
            return True
        else:
            return False

    def show_error(self, message):
        print_error("ERROR: %s" % message)

    def show_warning(self, message):
        print_warning("WARNING: %s" % message)

    def show_info(self, message):
        print_message("%s" % message)

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
        print_debug("mv %s %s" % (old_path, new_path))
        if self._conf.simulation_mode:
            return (True, "")
        else:
            try:
                os.rename(old_path, new_path)
                return (True, "")
            except Exception as ex:
                return (False, str(ex))

    def delete(self, path):
        print_debug("rm %s" % path)
        if self._conf.simulation_mode:
            return (True, "")
        else:
            try:
                os.remove(path)
                return (True, "")
            except Exception as ex:
                return (False, str(ex))

    def copy(self, old_path, new_path):
        print_debug("cp %s %s" % (old_path, new_path))
        if self._conf.simulation_mode:
            return (True, "")
        else:
            try:
                shutil.copyfile(old_path, new_path)
                return (True, "")
            except Exception as ex:
                return (False, str(ex))

    def make_link(self, old_path, new_path):
        dest_path = os.path.relpath(old_path, os.path.dirname(new_path))
        print_debug("ln -s %s %s" % (dest_path, new_path))
        if self._conf.simulation_mode:
            return (True, "")
        else:
            try:
                os.symlink(dest_path, new_path)
                return (True, "")
            except Exception as ex:
                return (False, str(ex))


def get_file_list_nonrecursive(directory: str, include_directories: bool):
    for name in os.listdir(directory):
        path = os.path.join(directory, name)
        if os.path.isdir(path) and not include_directories:
            continue
        yield path


def get_file_list_recursive(directory: str, include_directories: bool):
    print_status("Entering %s" % directory)
    stdout.flush()
    for name in os.listdir(directory):
        path = os.path.join(directory, name)
        if os.path.isdir(path):
            if include_directories:
                yield path
            yield from get_file_list_recursive(path, include_directories)
        else:
            yield path


