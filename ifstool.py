import getopt
import os
from sys import argv, stdout
import tempfile
import subprocess
from copy import deepcopy

class FileAction:
    RENAME_MOVE = 'r' # Rename or move the file
    DELETE = 'd'      # Delete the file
    COPY = 'c'        # Copy the file
    LINK = 'l'        # Create a symbolic link to the file
    IGNORE = 'i'      # Do not do anything with the file, but keep it in the index
    PICK= 'p'         # Return the file name (for picking mode)

    ALL_ACTIONS=[
            RENAME_MOVE,
            DELETE,
            COPY,
            LINK,
            IGNORE,
            PICK]

class Configuration:
    def __init__(self):
        self.default_action = FileAction.RENAME_MOVE
        self.use_absolute_paths = False
        self.include_directories = False
        self.prompt_on_actions = True
        self.simulation_mode = False
        self.multistage_mode = False
        self.create_directories = False

def index_uid():
    while True:
        index_uid.lastval += 1
        yield "%08d" % index_uid.lastval

index_uid.lastval = 0

class IOSAbstraction:
    def ask_for_confirmation(self, prompt): pass
    def show_error(self, message): pass
    def show_info(self, message): pass
    
    def abspath(self, path): pass
    def isdir(self, path): pass
    def mkdir(self, path): pass
    def split_path(self, path): pass
    def rename_move(self, old_path, new_path): pass
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
            return [True, ""]
        except Exception as ex:
            return (False, str(ex))

    def split_path(self, path):
        return (os.path.dirname(path), os.path.basename(path))
    
    def rename_move(self, old_path, new_path):
        if self._conf.simulation_mode:
            print("mv %s %s" % (old_path, new_path))
            return True
        else:
            try:
                os.rename(old_path, new_path)
                return (True, "")
            except Exception as ex:
                return (False, str(ex))

    def copy(self, old_path, new_path):
        print("cp %s %s" % (old_path, new_path))

    def make_link(self, old_path, new_path):
        print("ln %s %s" % (old_path, new_path))

class FileIndexEntry:
    def __init__(self, current_name, action):
        self.unique_id = next(index_uid())
        self.current_name = current_name
        self.target_names = [(current_name, action)]
        self.remarks = []

    def __str__(self):
        return "%s: %s -> %s" % (self.unique_id, self.current_name, self.target_names)

    def reset(self):
        self.target_names = []
        self.remarks = []

    def get_uid(self):
        return self.unique_id

    def generate_user_input(self):
        result = ""
        for remark in self.remarks:
            result += "# %s\n" % remark
        for name, action in self.target_names:
            result += "%s %c   %s\n" % (self.unique_id, action, name)

        return result

    def add_target_name(self, name, action):
        assert(action in FileAction.ALL_ACTIONS)
        self.target_names.append((name, action))

class FileIndex:
    def __init__(self, config:Configuration, os_abstraction:IOSAbstraction):
        self._files = {}
        self._config = config
        self._os = os_abstraction

    def get_all(self):
        return self._files

    def get_size(self):
        return len(self._files)

    def add(self, filenames:list, action:str=None):
        created_entries = []

        if action is None:
            action = self._config.default_action

        for filename in filenames:
            if self._config.use_absolute_paths:
                filename = self._os.abspath(filename)
            entry = FileIndexEntry(filename, action)
            self._files[entry.get_uid()] = entry
            created_entries.append(entry)

        return created_entries

    def purge(self):
        keys = [key for key in self._files.keys()]
        for key in keys:
            if len(self._files[key].target_names) == 0:
                del self._files[key]

    def generate_user_input(self):
        result = ""
        for entry_id, entry in self._files.items():
            result += entry.generate_user_input()
        return result

    def handle_user_input(self, user_input:list):
        for entry_id, entry in self._files.items():
            entry.reset()
        for line in user_input:
            # Skip empty lines and comment lines
            if len(line) > 0 and line[0] == '#': continue

            id, action, name = line.split(None, 2)
            if id in self._files:
                entry = self._files[id]
                entry.add_target_name(name, action)
            else:
                entry = self.add([name], action)[0]

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

def get_user_input(user_input_string):
    result = []

    tf = tempfile.NamedTemporaryFile("w+")
    tf.write(user_input_string)
    tf.flush()
    editor = subprocess.run(["vim", tf.name])
    tf.seek(0, 0)

    for line in tf:
        result.append(line.strip())

    return result

def do_action_rename(current_name:str, target_name:str, os:IOSAbstraction, conf:Configuration):
    current_dir, current_basename = os.split_path(current_name)
    target_dir, target_basename = os.split_path(target_name)
    remarks = []

    msg = ""
    if current_dir == target_dir:
        msg = "Rename \"%s\" to \"%s\" in \"%s\"?" % (current_basename, target_basename, current_dir)
    elif current_dir != target_dir and current_basename == target_basename:
        msg = "Move \"%s\" to \"%s\"?" % (current_name, target_dir)
    else:
        msg = "Move \"%s\" to \"%s\"?" % (current_name, target_name)

    if not conf.prompt_on_actions or os.ask_for_confirmation(msg):
        # If the target directory does not exist, create it when allowed
        if not os.isdir(target_dir) and conf.create_directories:
            if not conf.prompt_on_actions or os.ask_for_confirmation("Create directory \"%s\"" % target_dir):
                result, error_message = os.mkdir(target_dir)
                if not result:
                    msg = "Could not create directory \"%s\": %s" % (target_dir, error_message)
                    os.show_error(msg)
                    remarks.append(msg)
                    return (False, remarks)
                
        result, error_message = os.rename_move(current_name, target_name)
        if not result:
            msg = "Could not move %s: %s" % (current_name, error_message)
            os.show_error(msg)
            remarks.append(msg)
            return (False, remarks)

    return (True, remarks)

def execute_actions(file_index:FileIndex, os:IOSAbstraction, conf:Configuration):
    files = file_index.get_all()
    operations_done = 0

    for uid, file in files.items():
        new_target_names = []
        for target_name, action in file.target_names:

            if action == FileAction.RENAME_MOVE and file.current_name != target_name:
                result, remarks = do_action_rename(file.current_name, target_name, os, conf)
                if result:
                    operations_done += 1
                else:
                    file.remarks += remarks
                    new_target_names.append((target_name, action))

            elif action == FileAction.COPY and file.current_name != target_name:
                if not conf.prompt_on_actions or os.ask_for_confirmation("Copy %s to %s?" % (file.current_name, target_name)):
                    os.copy(file.current_name, target_name)
            
            elif action == FileAction.LINK and file.current_name != target_name:
                if not conf.prompt_on_actions or os.ask_for_confirmation("Create link to %s at %s?" % (file.current_name, target_name)):
                    os.make_link(file.current_name, target_name)

            elif action == FileAction.IGNORE:
                new_target_names.append((target_name, action))

        file.target_names = new_target_names

    file_index.purge()

    return (operations_done, file_index.get_size())

def parse_input_args(args:list, config:Configuration):
    dirs_recursive = []
    dirs_nonrecursive = []

    options, remainder = getopt.gnu_getopt(argv[1:], "n:Acdmsy", [
        "nonrecursive=",
        "absolute-paths",
        "create-directories",
        "include-dirs",
        "multistage",
        "simulate",
        "yes-to-all"])

    for option, value in options:
        print(option, value)
        if option in ['-n', '--nonrecursive']:
            dirs_nonrecursive.append(value)
        if option in ['-A', '--absolute-paths']:
            config.use_absolute_paths = True
        if option in ['-c', '--create-directories']:
            config.create_directories = True
        if option in ['-d', '--include-dirs']:
            config.include_directories = True
        if option in ['-m', '--multistage']:
            config.multistage_mode = True
        if option in ['-s', '--simulate']:
            config.simulation_mode = True
        if option in ['-y', '--yes-to-all']:
            config.prompt_on_actions = False

    for dir_name in remainder:
        dirs_recursive.append(dir_name)

    return (dirs_nonrecursive, dirs_recursive)


if __name__=="__main__":
    config = Configuration()
    os_abs = OSAbstraction(config)
    file_index = FileIndex(config, os_abs)

    dirs_nonrecursive, dirs_recursive = parse_input_args(argv[1:], config)

    for dir_name in dirs_nonrecursive:
        file_index.add(get_file_list_nonrecursive(dir_name, config.include_directories))

    for dir_name in dirs_recursive:
        file_index.add(get_file_list_recursive(dir_name, config.include_directories))

    while True:
        inp = file_index.generate_user_input()
        resp = get_user_input(inp)
        file_index.handle_user_input(resp)
        ops_done, remaining_entries = execute_actions(file_index, os_abs, config)
        if remaining_entries > 0:
            if config.multistage_mode:
                if ops_done > 0:
                    print("%d operations done, %d files not processed, launching the editor again" % (ops_done, remaining_entries))
                else:
                    if os_abs.ask_for_confirmation("No operations done, still %d files not processed. Continue?" % remaining_entries) == False:
                        break
            else:
                print("%d files not processed" % remaining_entries)
                print(file_index.generate_user_input())
                break
        else:
            break

