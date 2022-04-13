from extension import Extension, ExtensionParam
from file_index import FileIndex, FileIndexEntry
import hashlib
import io
from extensions.df import Extension_df
from console_output import print_warning


class Extension_cadf_audio(Extension_df):
    READ_CHUNK_SIZE = 16384
    UNIQUE_FILES_POLICIES = ["drop", "ungroup", "group"]

    ID3v2_HEADER_LENGTH = 10
    ID3v2_MAGIC = b'ID3'
    ID3v2_HEADER_REGION_SZ_BEGIN = 6
    ID3v2_HEADER_REGION_SZ_END = 6 + 4
    MP3_SYNC_WORD_SIZE = 2
    MP3_SYNC_WORD_BITMASK = 0xFFF0
    MP3_SYNC_WORD_CONTENT = 0xFFF0

    def __init__(self):
        Extension_df.__init__(self)

    def on_name_query(self):
        return "Content-Aware Duplicate Finder for audio files"

    def on_description_query(self):
        return "Creates groups consisting of audio files that have identical sound data, "\
                "regardless of the differences in the tags. Allows to quickly find" \
                "audio files which have the same content, but may be tagged differently."

    def on_params_query(self):
        return Extension_df.on_params_query(self);

    def before_file_added(self, filename):
        filename_lo = filename.lower()
        if filename_lo.endswith(".mp3"):
            return True

        return False

    def _get_audio_region_mp3(self, filename):
        """
        Determines the offset and length of audio stream in MP3 file, skipping
        ID3 tag block, ID3v2 tag regions and zero paddings.
        """

        # TODO: more in-depth analysis of mp3 audio stream to identify and
        # exclude ID3v2 blocks appearing between MP3 frames. Unlikely scenario,
        # but theoretically possible
        offset = 0
        length = 0
        structure = []
        with open(filename, "rb") as f:
            # save the length of file
            f.seek(0, io.SEEK_END)
            length = f.tell()
            f.seek(0, io.SEEK_SET)
            # There might be more than one ID3v2 regions in the file, so we need
            # to traverse them all
            last_loop_offset = -1
            while offset < length:
                if offset == last_loop_offset:
                    raise Exception("BUG: Loop stuck at offset %d" % offset)
                last_loop_offset = offset
                
                # Check if ID3v2 region is present, and skip it to reach audio data
                # ID3 header consists of 10 bytes: mmmvvxllll
                # where:
                #   * mmm = "ID3"
                #   * vv - version
                #   * x - flags
                #   * llll - length
                id3_header = f.read(self.ID3v2_HEADER_LENGTH)

                if id3_header[0:len(self.ID3v2_MAGIC)] == self.ID3v2_MAGIC:
                    # read remaining bytes of ID3v2 header

                    id3_region_length = 0
                    for byte in range(self.ID3v2_HEADER_REGION_SZ_BEGIN, self.ID3v2_HEADER_REGION_SZ_END):
                        # synch-safe format - only 7 bits are used
                        id3_region_length = (id3_region_length << 7) | id3_header[byte]

                    structure.append( (offset, id3_region_length, "ID3v2") )
                    offset += id3_region_length + self.ID3v2_HEADER_LENGTH

                    length -= offset
                else:
                    # unread the header
                    f.seek(-self.ID3v2_HEADER_LENGTH, io.SEEK_CUR)

                # Check if MP3 sync word is present.
                # We expect to encounter 0xFFFB or 0xFFFA (in case there is an error correction bit set)
                f.seek(offset, io.SEEK_SET)
                mp3_frame_hdr_part = f.read(self.MP3_SYNC_WORD_SIZE)
                sync_word = (mp3_frame_hdr_part[0] << 8) | (mp3_frame_hdr_part[1])

                # If we read something else, it might be another ID3v2 region
                if sync_word & self.MP3_SYNC_WORD_BITMASK == self.MP3_SYNC_WORD_CONTENT:
                    # MP3 data encountered, audio stream begins here
                    break
                else:
                    if mp3_frame_hdr_part == self.ID3v2_MAGIC[0:2]:
                        # another ID3v2 region found, this is okay
                        # rewind back and repeat
                        f.seek(-self.MP3_SYNC_WORD_SIZE, io.SEEK_CUR)

                    elif sync_word == 0:
                        # zero-padding; rewind it all
                        initial_offset = offset
                        offset += 2
                        while True:
                            b = f.read(1)
                            if b != b'\0':
                                f.seek(-1, io.SEEK_CUR)
                                break
                            else:
                                offset += 1
                        structure.append( (initial_offset, offset-initial_offset, "Zero-padding") )
                    else:
                        structure.append( (offset, 0, "Unknown content starting with %04x" % sync_word))
                        print_warning("Unexpected data found in %s, determination of audio content might be inaccurate" % filename)
                        break

            # Check if ID3 (v1) region is present
            f.seek(-128, io.SEEK_END)
            id3_magic = f.read(3)
            if id3_magic == b'TAG':
                length -= 128
        return offset, length, structure

    
    def after_file_added(self, entry):
        if entry.current_name.lower().endswith("mp3"):
            offset, length, structure = self._get_audio_region_mp3(entry.current_name)

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


