import getopt
from sys import argv
from os import getenv
import tempfile
import subprocess

from file_index import FileIndex
from file_action import FileAction
from configuration import Configuration
from os_abstraction import *
from extension import Extension, ExtensionParam
from extensions.df import Extension_df
from extensions.cadf.audio import Extension_cadf_audio


def get_user_input(user_input_string):
    result = []

    editor = getenv("EDITOR", "vi")
    tf = tempfile.NamedTemporaryFile("w+")
    tf.write(user_input_string)
    tf.flush()
    editor = subprocess.run([editor, tf.name])
    tf.seek(0, 0)

    for line in tf:
        result.append(line.strip())

    return result


def do_action_copy_move_common(current_name: str, target_name: str, action: str, os: IOSAbstraction, conf: Configuration):
    """
    Common code covering rename/move, copy and link actions, involving
    the following sequence of operations:
      - checking if the destination file will be overwritten
      - asking the user for confirmation of the operation
      - creation of the target directory (if does not exist yet and can
        be created)
      - executing the action
      - evaluating the results of operations at each stage
    """
    current_dir, current_basename = os.split_path(current_name)
    target_dir, target_basename = os.split_path(target_name)
    remarks = []
    overwriting = False

    # Check if target file exists.d 
    if os.isfile(target_name):
        if conf.allow_overwriting:
            overwriting = True
        else:
            msg = "Target file \"%s\" already exists.\nUse -o or --allow-overwriting option to force the overwrite." % target_name
            os.show_error(msg)
            remarks.append(msg)
            return (False, remarks)

    msg = ""
    if current_dir == target_dir:
        if action == FileAction.RENAME_MOVE:
            msg = "Rename \"%s\" to \"%s\" in \"%s\"?" % (current_basename, target_basename, current_dir)
        elif action == FileAction.COPY:
            msg = "Make a copy of \"%s\" as \"%s\" in \"%s\"?" % (current_basename, target_basename, current_dir)
        elif action == FileAction.LINK:
            msg = "Create a link to \"%s\" as \"%s\" in \"%s\"?" % (current_basename, target_basename, current_dir)

    elif current_dir != target_dir and current_basename == target_basename:
        if action == FileAction.RENAME_MOVE:
            msg = "Move \"%s\" to \"%s\"?" % (current_name, target_dir)
        elif action == FileAction.COPY:
            msg = "Make a copy of \"%s\" in \"%s\"?" % (current_name, target_dir)
        elif action == FileAction.LINK:
            msg = "Create a link to \"%s\" in \"%s\"?" % (current_name, target_dir)
    else:
        if action == FileAction.RENAME_MOVE:
            msg = "Move \"%s\" to \"%s\"?" % (current_name, target_name)
        elif action == FileAction.COPY:
            msg = "Make a copy of \"%s\" in \"%s\"?" % (current_name, target_name)
        elif action == FileAction.LINK:
            msg = "Create a link to \"%s\" in \"%s\"?" % (current_name, target_name)

    if overwriting:
        msg += " Destination file will be overwritten!"

    if not conf.prompt_on_actions or os.ask_for_confirmation(msg):
        # If the target directory does not exist, create it when allowed
        if not os.isdir(target_dir) and conf.create_directories:
            if not conf.prompt_on_actions or os.ask_for_confirmation("Target directory \"%s\" does not exist. Create it?" % target_dir):
                result, error_message = os.mkdir(target_dir)
                if not result:
                    msg = "Could not create directory \"%s\": %s" % (target_dir, error_message)
                    os.show_error(msg)
                    remarks.append(msg)
                    return (False, remarks)
        
        if action == FileAction.RENAME_MOVE:
            result, error_message = os.rename_move(current_name, target_name)
        elif action == FileAction.COPY:
            result, error_message = os.copy(current_name, target_name)
        elif action == FileAction.LINK:
            result, error_message = os.make_link(current_name, target_name)

        if not result:
            msg = "Could not create the target file %s: %s" % (current_name, error_message)
            os.show_error(msg)
            remarks.append(msg)
            return (False, remarks)

    return (True, remarks)


def do_action_delete(current_name: str, os: IOSAbstraction, conf: Configuration):
    msg = "Delete \"%s\"?" % current_name
    remarks = []

    if not conf.prompt_on_actions or os.ask_for_confirmation(msg):
        result, error_message = os.delete(current_name)
        if not result:
            msg = "Could not delete \"%s\": %s" % (current_name, error_message)
            os.show_error(msg)
            remarks.append(msg)
            return (False, remarks)

    return (True, remarks)


def execute_actions(file_index: FileIndex, os: IOSAbstraction, conf: Configuration):
    files = file_index.get_all()
    operations_done = 0

    for uid, file in files.items():
        new_target_names = []
        for target_name, action in file.target_names:

            if action in [FileAction.RENAME_MOVE, FileAction.COPY, FileAction.LINK] \
                    and file.current_name != target_name:

                result, remarks = do_action_copy_move_common(file.current_name, target_name, action, os, conf)
                if result:
                    operations_done += 1
                else:
                    file.remarks += remarks
                    new_target_names.append((target_name, action))

            elif action == FileAction.DELETE:
                result, remarks = do_action_delete(file.current_name, os, conf)
                if result:
                    operations_done += 1
                else:
                    file.remarks += remarks
                    new_target_names.append((target_name, action))

            elif action == FileAction.IGNORE:
                new_target_names.append((target_name, action))

        file.target_names = new_target_names

    file_index.purge()

    return (operations_done, file_index.get_size())


def get_extensions():
    extensions = {
            "df": Extension_df,
            "cadf.audio": Extension_cadf_audio
            }
    return extensions


def display_help():
    str_extensions = ""
    for ext_name, ext_class in get_extensions().items():
        ext = ext_class()
        assert(isinstance(ext, Extension))
        str_extensions += " "*30 + "  - %s: %s\n" % (ext_name, ext.on_name_query())

    print("""IFSTool - Interactive FileSystem Tool v0.1
A tool that allows to manage large number of files in the directory tree
using a text editor, in a way similar to interactive rebase feature of Git SCM.
USAGE: ifstool [options] directory1 [[-n] directory2 [[-n] directory_n]]\n
Options available:
  -n, --nonrecursive=dirname  Do not enter subdirectories of the directory specified
  -A, --absolute-paths        Use absolute paths in the input.
  -D, --default-action=actn   Select default action for each file:
                              r - rename/move    d - delete
                              c - copy           l - link
                              i - ignore
  -c, --create-directories    Create new directories, if needed.
  -m, --multistage            Enable multi-stage mode; keep reopening the editor as long
                              as there are files that have not been processed.
  -o, --allow-overwriting     Allow overwriting existing files.
  -s, --simulate              Simulation mode - show the actions that would be done, but without
                              triggering any actual actions in the filesystem.
  -x, --extension=name:[args] Use an extension. Available extensions are:
%s
                              Use --extension=<name>:help for details on the extension
  -y, --yes-to-all            Do not ask for confirmation at actions, assume \"yes\" response
                              for all questions
""" % str_extensions)
    exit(1)


def show_extension_info(ext: Extension):
    print("Extension %s" % ext.on_name_query())
    print(ext.on_description_query())

    params = ext.on_params_query()
    if len(params) > 0:
        print("Parameters:")
        for param in params:
            assert(isinstance(param, ExtensionParam))
            print("  %-14s %s" % (param.name, param.description))
            if param.enum_values is not None:
                print(" "*17 + "Possible values:")
                for value, description in param.enum_values.items():
                    print(" "*17 + "  %-14s %s" % (value, description))
            if param.default_value is not None:
                print(" "*17 + "Default value: %s" % param.default_value)

def validate_and_fill(params_dict: dict, extension_interface: list):
    for ext_param in extension_interface:
        assert(isinstance(ext_param, ExtensionParam))
        if ext_param.name not in params_dict and ext_param.default_value is not None:
            params_dict[ext_param.name] = ext_param.default_value

        if ext_param.enum_values is not None:
            if params_dict[ext_param.name] not in ext_param.enum_values:
                valid_items = ""
                for val in ext_param.enum_values:
                    valid_items += val+ ", "
                valid_items = valid_items[:-2]
                print("Invalid value of %s: %s. Valid values are: %s" % (
                    ext_param.name,
                    params_dict[ext_param.name],
                    valid_items))
    return params_dict


def use_extension(config: Configuration, os: IOSAbstraction, ext_str: str):
    exts = get_extensions()

    if ext_str.find(':') != -1:
        ext_name, ext_param_str = ext_str.split(':', 1)
    else:
        ext_name = ext_str
        ext_param_str = None

    if ext_name in exts:
        extension_obj = exts[ext_name]()
        if ext_param_str == "help":
            show_extension_info(extension_obj)
            exit(1)
        elif ext_param_str is not None:
            params = ext_param_str.split(' ')
            params_dict = {}
            for param in params:
                if '=' in param:
                    key, value = param.split('=', 1)
                else:
                    key = param
                    value = None
                params_dict[key] = value

            params_dict = validate_and_fill(params_dict, extension_obj.on_params_query())
            print(params_dict)
            extension_obj.on_params_passed(params_dict)
        config.extensions_chain.append(extension_obj)
    else:
        os.show_error("No such extension: %s" % ext_name)
        exit(1)


def parse_input_args(args:list, config:Configuration, os_abs: IOSAbstraction):
    dirs_recursive = []
    dirs_nonrecursive = []

    options, remainder = getopt.gnu_getopt(argv[1:], "n:AD:cmosx:y", [
        "nonrecursive=",
        "default-action=",
        "absolute-paths",
        "create-directories",
        "multistage",
        "allow-overwriting",
        "simulate",
        "extension=",
        "yes-to-all",
        "help"])

    for option, value in options:
        if option in ['-n', '--nonrecursive']:
            dirs_nonrecursive.append(value)
        if option in ['-A', '--absolute-paths']:
            config.use_absolute_paths = True
        if option in ['-D', '--default-action']:
            if value in FileAction.ALL_ACTIONS:
                config.default_action = value
            else:
                os_abs.show_error("Incorrect action: %s" % value)
                exit(1)
        if option in ['-c', '--create-directories']:
            config.create_directories = True
        if option in ['-d', '--include-dirs']:
            config.include_directories = True
        if option in ['-m', '--multistage']:
            config.multistage_mode = True
        if option in ['-o', '--allow-overwriting']:
            config.allow_overwriting = True
        if option in ['-s', '--simulate']:
            config.simulation_mode = True
        if option in ['-x', '--extension']:
            use_extension(config, os_abs, value)
        if option in ['-y', '--yes-to-all']:
            config.prompt_on_actions = False
        if option in ['--help']:
            display_help()

    for dir_name in remainder:
        dirs_recursive.append(dir_name)

    return (dirs_nonrecursive, dirs_recursive)

def run():
    config = Configuration()
    os_abs = OSAbstraction(config)
    file_index = FileIndex(config, os_abs)

    dirs_nonrecursive, dirs_recursive = parse_input_args(argv[1:], config, os_abs)

    for dir_name in dirs_nonrecursive:
        file_index.add(get_file_list_nonrecursive(dir_name, config.include_directories))

    for dir_name in dirs_recursive:
        file_index.add(get_file_list_recursive(dir_name, config.include_directories))

    while True:
        for extension in config.extensions_chain:
            extension.on_index_complete(file_index)
        inp = file_index.generate_user_input()
        resp = get_user_input(inp)
        file_index.handle_user_input(resp)
        ops_done, remaining_entries = execute_actions(file_index, os_abs, config)
        if remaining_entries > 0:
            if config.multistage_mode:
                if ops_done > 0:
                    os_abs.show_info("%d operations done, %d files not processed, launching the editor again" % (ops_done, remaining_entries))
                else:
                    if os_abs.ask_for_confirmation("No operations done, still %d files not processed. Continue?" % remaining_entries) == False:
                        break
            else:
                os_abs.show_info("%d files not processed" % remaining_entries)
                os_abs.show_info(file_index.generate_user_input())
                break
        else:
            break

if __name__=="__main__":
    run()

