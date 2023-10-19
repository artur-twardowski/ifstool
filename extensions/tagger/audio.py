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

    TEXT_ONLY = 1
    TEXT_DESC = 2
    URL = 3

    ID3_IMPL_INTERNAL = {
        "COMM": (id3.COMM, TEXT_ONLY, "Comment"),
        "GRP1": (id3.GRP1, TEXT_ONLY, "iTunes Grouping"),
        "MVIN": (id3.MVIN, TEXT_ONLY, "iTunes Movement Number"),
        "MVNM": (id3.MVNM, TEXT_ONLY, "iTunes Movement Name"),
        "TALB": (id3.TALB, TEXT_ONLY, "Album name"),
        "TBPM": (id3.TBPM, TEXT_ONLY, "Beats per minute"),
        "TCAT": (id3.TCAT, TEXT_ONLY, "iTunes Podcast Category"),
        "TCMP": (id3.TCMP, TEXT_ONLY, "iTunes Compilation Flag"),
        "TCOM": (id3.TCOM, TEXT_ONLY, "Composer"),
        "TCON": (id3.TCON, TEXT_ONLY, "Genre"),
        "TCOP": (id3.TCOP, TEXT_ONLY, "Copyright"),
        "TDAT": (id3.TDAT, TEXT_ONLY, "Date of recording"),
        "TDEN": (id3.TDEN, TEXT_ONLY, "Encoding time"),
        "TDES": (id3.TDES, TEXT_ONLY, "iTunes Podcast Description"),
        "TDLY": (id3.TDLY, TEXT_ONLY, "Audio Delay"),
        "TDOR": (id3.TDOR, TEXT_ONLY, "Original Release Time"),
        "TDRC": (id3.TDRC, TEXT_ONLY, "Recording Time"),
        "TDRL": (id3.TDRL, TEXT_ONLY, "Release Time"),
        "TDTG": (id3.TDTG, TEXT_ONLY, "Tagging Time"),
        "TENC": (id3.TENC, TEXT_ONLY, "Encoder"),
        "TEXT": (id3.TEXT, TEXT_ONLY, "Lyricist"),
        "TFLT": (id3.TFLT, TEXT_ONLY, "File Type"),
        "TGID": (id3.TGID, TEXT_ONLY, "iTunes Podcast Identifier"),
        "TIME": (id3.TIME, TEXT_ONLY, "Time of recording"),
        "TIPL": (id3.TIPL, TEXT_ONLY, "Involved People List"),
        "TIT1": (id3.TIT1, TEXT_ONLY, "Content Group Description"),
        "TIT2": (id3.TIT2, TEXT_ONLY, "Title"),
        "TIT3": (id3.TIT3, TEXT_ONLY, "Subtitle"),
        "TKEY": (id3.TKEY, TEXT_ONLY, "Starting key"),
        "TKWD": (id3.TKWD, TEXT_ONLY, "iTunes Podcast Keywords"),
        "TLAN": (id3.TLAN, TEXT_ONLY, "Languages"),
        "TLEN": (id3.TLEN, TEXT_ONLY, "Audio Length"),
        "TMCL": (id3.TMCL, TEXT_ONLY, "Musicians Credit List"),
        "TMOO": (id3.TMOO, TEXT_ONLY, "Mood"),
        "TOAL": (id3.TOAL, TEXT_ONLY, "Original Album"),
        "TOFN": (id3.TOFN, TEXT_ONLY, "Original Filename"),
        "TOLY": (id3.TOLY, TEXT_ONLY, "Original Lyricist"),
        "TOPE": (id3.TOPE, TEXT_ONLY, "Original performer"),
        "TORY": (id3.TORY, TEXT_ONLY, "Original Release Year"),
        "TOWN": (id3.TOWN, TEXT_ONLY, "Owner/Licensee"),
        "TPE1": (id3.TPE1, TEXT_ONLY, "Artist"),
        "TPE2": (id3.TPE2, TEXT_ONLY, "Band/Orchestra/Featuring"),
        "TPE3": (id3.TPE3, TEXT_ONLY, "Conductor"),
        "TPE4": (id3.TPE4, TEXT_ONLY, "Remixer/Modifier"),
        "TPOS": (id3.TPOS, TEXT_ONLY, "Part of set"),
        "TPRO": (id3.TPRO, TEXT_ONLY, "Produced"),
        "TPUB": (id3.TPUB, TEXT_ONLY, "Publisher"),
        "TRCK": (id3.TRCK, TEXT_ONLY, "Track number"),
        "TRDA": (id3.TRDA, TEXT_ONLY, "Recording Dates"),
        "TRSN": (id3.TRSN, TEXT_ONLY, "Internet Radio Station Name"),
        "TRSO": (id3.TRSO, TEXT_ONLY, "Internet Radio Station Owner"),
        "TSIZ": (id3.TSIZ, TEXT_ONLY, "Size of audio data"),
        "TSSE": (id3.TSSE, TEXT_ONLY, "Encoder settings"),
        "TSST": (id3.TSST, TEXT_ONLY, "Set Subtitle"),
        "TYER": (id3.TYER, TEXT_ONLY, "Year Of Recording"),
        "TXXX": (id3.TXXX, TEXT_DESC, "Comment")
    }

    def _read_json(self, filename):
        with open(filename, "r") as f:
            return json.load(f)

    def __init__(self):
        Extension.__init__(self)
        config_path = path.dirname(path.abspath(__file__))

        self.MAPPING_ID3 = {}
        for key, descriptor in self.ID3_IMPL_INTERNAL.items():
            _, _, name = descriptor
            self.MAPPING_ID3[key] = name

        # To be modified, to use only user tags
        user_tags = self._read_json(path.join(config_path, "mapping_id3.json"))
        for key, value in user_tags.items():
            self.MAPPING_ID3[key] = value

        self.MAPPING_VORBIS = self._read_json(path.join(config_path, "mapping_vorbis.json"))

    def on_name_query(self):
        return "Metadata editor for audio files"

    def on_description_query(self):
        return ""

    def on_params_query(self):
        pass

    def _get_format(self, filename):
        filename_lo = filename.lower()

        if filename_lo.endswith(".mp3"):
            return "mp3"
        if filename_lo.endswith(".flac"):
            return "flac"

        return None


    def before_file_added(self, filename):
        if self._get_format(filename) is not None:
            return True
        else:
            return False

    def _tag_to_key(self, key, mapping):
        if key in mapping:
            return mapping[key]
        else:
            return key

    def _key_to_tag(self, key, mapping):
        for file_tag, input_key in mapping.items():
            if input_key == key:
                return file_tag

    def _read_tags_mp3(self, filename):
        file = MP3(filename)
        result = {}

        for key, data in file.tags.items():
            if isinstance(data, id3.TextFrame):
                lines = [str(ln) for ln in data.text]
                displayable_key = self._tag_to_key(key, self.MAPPING_ID3)
                result[displayable_key] = '\n'.join(lines)

        return result

    def _write_tags_mp3(self, filename, tags):
        file = MP3(filename)

        for tag_to_write, value in tags.items():

            if tag_to_write not in file.tags:
                if value != "":
                    TagType, constructor_format, _ = self.ID3_IMPL_INTERNAL[tag_to_write]
                    if constructor_format == self.TEXT_ONLY:
                        file.tags.add(TagType(encoding=id3.Encoding.UTF8, text=value))
                    elif constructor_format == self.TEXT_DESC:
                        if tag_to_write[4] == ':':
                            descr = tag_to_write[5:]
                            file.tags.add(TagType(encoding=id3.Encoding.UTF8, desc=descr, text=value))
                    elif constructor_format == self.URL:
                        file.tags.add(TagType(encoding=id3.Encoding.UTF8, url=value))
            else:
                file.tags[tag_to_write].text = value

        file.save()

    def _read_tags_flac(self, filename):
        file = FLAC(filename)
        result = {}
        
        for key, data in file.tags.items():
            lines = [str(ln) for ln in data]
            displayable_key = self._tag_to_key(key, self.MAPPING_VORBIS)
            result[displayable_key] = '\n'.join(lines)

        return result

    def after_file_added(self, entry: FileIndexEntry):
        fmt = self._get_format(entry.current_name)

        if fmt == "flac":
            entry.metadata = self._read_tags_flac(entry.current_name)

        elif fmt == "mp3":
            entry.metadata = self._read_tags_mp3(entry.current_name)

    def before_file_ops(self, entry):
        if entry.metadata_modified:
            fmt = self._get_format(entry.current_name)

            if fmt == "flac":
                mapper = self.MAPPING_VORBIS
                writing_function = self._write_tags_flac
            elif fmt == "mp3":
                mapper = self.MAPPING_ID3
                writing_function = self._write_tags_mp3

            target_tags = {}
            for key, value in entry.metadata.items():
                tag_key = self._key_to_tag(key, mapper)

                if tag_key is not None:
                    target_tags[tag_key] = value
                else:
                    target_tags[key] = value

            writing_function(entry.current_name, target_tags)




