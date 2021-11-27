from extension import Extension, ExtensionParam
from file_index import FileIndex, FileIndexEntry
import hashlib

class Extension_df(Extension):
    READ_CHUNK_SIZE=16384
    UNIQUE_FILES_POLICIES=["drop", "ungroup", "group"]

    def __init__(self):
        self._unique_files_policy = "ungroup"

    def on_name_query(self):
        return "Duplicate Finder"

    def on_description_query(self):
        return "Creates groups consisting of files that have identical content. "\
                "Allows to quickly find duplicates"

    def on_params_query(self):
        return [
            ExtensionParam("unique",
                "How the unique files (ie. files that have no duplicates) should be presented in the index",
                values={
                    "drop": "Remove them from the index, so that only duplicates will be shown",
                    "ungroup": "Keep them in the index, but ungroup them (they will be placed in \"remaining files\" section)",
                    "group": "Keep them in the index grouped, even though they will be the only ones in the group"
                }, default="ungroup")
        ]

    def on_params_passed(self, params):
        assert("unique" in params)
        assert(params["unique"] in self.UNIQUE_FILES_POLICIES)
        self._unique_files_policy = params["unique"]


    def after_file_added(self, entry:FileIndexEntry):
        h = hashlib.sha224()
        with open(entry.current_name, "rb") as f:
            while True:
                data = f.read(self.READ_CHUNK_SIZE)
                if not data: break
                h.update(data)

        entry.assign_to_group(h.hexdigest())

    def on_index_complete(self, index: FileIndex):
        groups, ungrouped = index.get_files_by_groups()

        for group, entries_in_group in groups.items():
            if len(entries_in_group) == 1:
                if self._unique_files_policy == "ungroup":
                    entries_in_group[0].ungroup()
                if self._unique_files_policy == "drop":
                    index.remove(entries_in_group[0])
        index.purge()

