from configuration import Configuration
from os_abstraction import IOSAbstraction
from file_action import FileAction

def index_uid():
    while True:
        index_uid.lastval += 1
        yield "%08d" % index_uid.lastval

index_uid.lastval = 0

class FileIndexEntry:
    def __init__(self, current_name, action, index = None):
        self._index = index
        self._unique_id = next(index_uid())
        self.current_name = current_name
        self.target_names = [(current_name, action)]
        self.remarks = []
        self._group_id = None
        self.metadata = {}

    def __str__(self):
        return "%s: %s -> %s" % (self.unique_id, self.current_name, self.target_names)

    def reset(self):
        self.target_names = []
        self.remarks = []

    def get_uid(self):
        return self._unique_id

    def get_group_id(self):
        return self._group_id

    def generate_user_input(self):
        max_key_len = 0
        for key in self.metadata:
            if len(key) > max_key_len:
                max_key_len = len(key)

        result = ""
        for remark in self.remarks:
            result += "# %s\n" % remark
        for name, action in self.target_names:
            result += "%s %c   %s\n" % (self._unique_id, action, name)

        for key, value in self.metadata.items():
            if str(value).find('\n') != -1:
                result += "%-*s = <<END\n%s\n<<END\n" % (max_key_len, key, value)
            else:
                result += "%-*s = %s\n" % (max_key_len, key, value)

        return result

    def add_target_name(self, name, action):
        assert(action in FileAction.ALL_ACTIONS)
        self.target_names.append((name, action))

    def assign_to_group(self, group_id):
        self._index.register_group(group_id)
        self._group_id = group_id

class FileIndex:
    def __init__(self, config:Configuration, os_abstraction:IOSAbstraction):
        self._files = {}
        self._config = config
        self._os = os_abstraction
        self._groups = []

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
        if len(self._groups) > 0:

            for group in self._groups + [None]:
                if group is None:
                    result += "# remaining files\n"
                else:
                    result += "# group %s\n" % group

                for entry_id, entry in self._files.items():
                    if entry.get_group_id() == group:
                        result += entry.generate_user_input()
                result += "\n"

        else:
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

    def register_group(self, group_name):
        if group_name in self._groups:
            self._groups.append(group_name)

