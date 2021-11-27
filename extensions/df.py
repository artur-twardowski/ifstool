from extension import Extension
from file_index import FileIndex, FileIndexEntry
import hashlib

class Extension_df(Extension):
    READ_CHUNK_SIZE=16384
    def on_name_query(self):
        return "Duplicate Finder"

    def on_description_query(self):
        return "Groups identical files together"

    def on_file_enter(self, entry:FileIndexEntry):
        h = hashlib.sha224()
        with open(entry.current_name, "rb") as f:
            while True:
                data = f.read(self.READ_CHUNK_SIZE)
                if not data: break

                h.update(data)

        entry.assign_to_group(h.hexdigest())



