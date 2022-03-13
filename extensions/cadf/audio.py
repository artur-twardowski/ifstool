from extension import Extension, ExtensionParam
from file_index import FileIndex, FileIndexEntry
import hashlib
import io


class Extension_cadf_audio(Extension):
    READ_CHUNK_SIZE = 16384
    UNIQUE_FILES_POLICIES = ["drop", "ungroup", "group"]

    def __init__(self):
        self._unique_files_policy = "ungroup"

    def on_name_query(self):
        return "Content-Aware Duplicate Finder for audio files"

    def on_description_query(self):
        return "Creates groups consisting of audio files that have identical sound data, "\
                "regardless of the differences in the tags. Allows to quickly find" \
                "audio files which have the same content, but may be tagged differently."

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

    def before_file_added(self, filename):
        filename_lo = filename.lower()
        if filename_lo.endswith(".mp3"):
            return True

        return False

    def _get_audio_region_mp3(self, filename):
        offset = 0
        length = 0
        with open(filename, "rb") as f:
            f.seek(0, io.SEEK_END)
            length = f.tell()
            f.seek(0, io.SEEK_SET)
            # Check if ID3v2 region is present, and skip it to reach audio data
            # ID3 header consists of 10 bytes: mmmvvxllll
            # where:
            #   * mmm = "ID3"
            #   * vv - version
            #   * x - flags
            #   * llll - length
            id3_magic = f.read(3)
            if id3_magic == b'ID3':
                id3_header = f.read(7)
                offset += 10
                id3_region_length = 0
                for byte in range(3, 7):
                    # synch-safe format - only 7 bits are used
                    id3_region_length = (id3_region_length << 7) | id3_header[byte]
                offset += id3_region_length

                length -= offset

            # Check if ID3 (v1) region is present
            f.seek(-128, io.SEEK_END)
            id3_magic = f.read(3)
            if id3_magic == b'TAG':
                length -= 128

        return offset, length


    
    def after_file_added(self, entry):
        if entry.current_name.lower().endswith("mp3"):
            offset, length = self._get_audio_region_mp3(entry.current_name)

        h = hashlib.sha224()
        with open(entry.current_name, "rb") as f:
            f.seek(offset, io.SEEK_SET)
            yet_to_read = length
            while yet_to_read > 0:
                read_size = self.READ_CHUNK_SIZE
                if read_size > yet_to_read:
                    read_size = yet_to_read

                data = f.read(read_size)
                h.update(data)

                yet_to_read -= read_size

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

