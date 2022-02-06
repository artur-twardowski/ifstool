from configuration import Configuration
from os_abstraction import IOSAbstraction
from file_action import FileAction

def index_uid():
    while True:
        index_uid.lastval += 1
        yield "%08d" % index_uid.lastval

index_uid.lastval = 0

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
