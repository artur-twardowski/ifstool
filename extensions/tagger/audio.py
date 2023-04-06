from extension import Extension, ExtensionParam
from file_index import FileIndex, FileIndexEntry
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen import id3
import re
import json
from os import path

#TODO: filetypes should be distinguished based on the header rather than on the name

class Extension_tagger_audio(Extension):

    def _read_json(self, filename):
        with open(filename, "r") as f:
            return json.load(f)

    def __init__(self):
        Extension.__init__(self)
        config_path = path.dirname(path.abspath(__file__))

        self.MAPPING_ID3 = self._read_json(path.join(config_path, "mapping_id3.json"))
        self.MAPPING_VORBIS = self._read_json(path.join(config_path, "mapping_vorbis.json"))

    def on_name_query(self):
        return "Metadata editor for audio files"

    def on_description_query(self):
        return ""

    def on_params_query(self):
        pass

    def before_file_added(self, filename):
        filename_lo = filename.lower()
        if filename_lo.endswith(".mp3"):
            return True
        if filename_lo.endswith(".flac"):
            return True

        return False

    def _tag_to_key(self, key, mapping):
        if key in mapping:
            return mapping[key]
        else:
            return key

    def _read_tags_mp3(self, filename):
        file = MP3(filename)
        result = {}

        for key, data in file.tags.items():
            if isinstance(data, id3.TextFrame):
                lines = [str(ln) for ln in data.text]
                displayable_key = self._tag_to_key(key, self.MAPPING_ID3)
                result[displayable_key] = '\n'.join(lines)

        return result

    def _read_tags_flac(self, filename):
        file = FLAC(filename)
        result = {}
        
        for key, data in file.tags.items():
            lines = [str(ln) for ln in data]
            displayable_key = self._tag_to_key(key, self.MAPPING_VORBIS)
            result[displayable_key] = '\n'.join(lines)

        return result

    def after_file_added(self, entry: FileIndexEntry):
        filename_lo = entry.current_name.lower()

        if filename_lo.endswith('.flac'):
            entry.metadata = self._read_tags_flac(entry.current_name)

        elif filename_lo.endswith('.mp3'):
            entry.metadata = self._read_tags_mp3(entry.current_name)

