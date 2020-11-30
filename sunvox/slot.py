import sys
from collections import defaultdict
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from typing import Union, BinaryIO, Optional

from . import dll
from .types import c_uint32_p, c_int16_p, c_float_p, sunvox_note_p

FILENAME_ENCODING = sys.getfilesystemencoding()
MAX_SLOTS = 4
DEFAULT_ALLOCATION_MAP = [False] * MAX_SLOTS

FileOrName = Union[str, Path, bytes, BinaryIO]


class NoSlotsAvailable(Exception):
    """The maximum number of SunVox playback slots are in use."""


class Slot(object):
    """A context manager wrapping slot-specific API calls."""

    allocation_map = defaultdict(DEFAULT_ALLOCATION_MAP.copy)

    def __init__(self, file: FileOrName = None, process=dll):
        self.process = process
        self.number = self.next_available_slot(process)
        if self.number is None:
            raise NoSlotsAvailable()
        self.allocation_map[process][self.number] = True
        self.locks = 0
        process.open_slot(self.number)
        if file is not None:
            self.load(file)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __repr__(self):
        return "<Slot number={} process={!r}>".format(self.number, self.process)

    @classmethod
    def next_available_slot(cls, process):
        i = cls.allocation_map[process].index(False)
        return i if i >= 0 else None

    @property
    def closed(self):
        return self.number is not None

    @contextmanager
    def locked(self):
        self.lock()
        try:
            yield self
        finally:
            self.unlock()

    def close(self):
        i = self.number
        self.number = None
        self.allocation_map[self.process][i] = False
        return self.process.close_slot(i)

    close.__doc__ = dll.close_slot.__doc__

    def lock(self):
        self.locks += 1
        if self.locks == 1:
            return self.process.lock_slot(self.number)

    lock.__doc__ = dll.lock_slot.__doc__

    def unlock(self):
        if self.locks > 0:
            self.locks -= 1
            if self.locks == 0:
                return self.process.unlock_slot(self.number)

    unlock.__doc__ = dll.unlock_slot.__doc__

    def load(self, file_or_name: FileOrName) -> int:
        """Load SunVox project using a filename or file-like object."""
        if isinstance(file_or_name, (str, bytes, Path)):
            return self.load_filename(file_or_name)
        elif callable(getattr(file_or_name, "read", None)):
            return self.load_file(file_or_name)

    def load_file(self, file: BinaryIO) -> int:
        """Load SunVox project from a file-like object."""
        value = file.getvalue() if isinstance(file, BytesIO) else file.read()
        return self.process.load_from_memory(self.number, value, len(value))

    def load_filename(self, filename: Union[str, bytes, Path]) -> int:
        """Load SunVox project using a filename."""
        if isinstance(filename, (str, Path)):
            filename = str(filename).encode("utf8")
        return self.process.load(self.number, filename)

    def play(self) -> int:
        return self.process.play(self.number)

    play.__doc__ = dll.play.__doc__

    def play_from_beginning(self) -> int:
        return self.process.play_from_beginning(self.number)

    play_from_beginning.__doc__ = dll.play_from_beginning.__doc__

    def stop(self) -> int:
        return self.process.stop(self.number)

    stop.__doc__ = dll.stop.__doc__

    def set_autostop(self, autostop: int) -> int:
        return self.process.set_autostop(self.number, autostop)

    set_autostop.__doc__ = dll.set_autostop.__doc__

    def get_autostop(self) -> int:
        return self.process.get_autostop(self.number)

    get_autostop.__doc__ = dll.get_autostop.__doc__

    def end_of_song(self) -> int:
        return self.process.end_of_song(self.number)

    end_of_song.__doc__ = dll.end_of_song.__doc__

    def rewind(self, line_num: int) -> int:
        return self.process.rewind(self.number, line_num)

    rewind.__doc__ = dll.rewind.__doc__

    def volume(self, vol: int) -> int:
        return self.process.volume(self.number, vol)

    volume.__doc__ = dll.volume.__doc__

    def set_event_t(self, set: int, t: int) -> int:
        return self.process.set_event_t(self.number, set, t)

    set_event_t.__doc__ = dll.set_event_t.__doc__

    def send_event(
        self,
        track_num: int,
        note: int,
        vel: int,
        module: int,
        ctl: int,
        ctl_val: int,
    ) -> int:
        module_index = getattr(module, "index", None)
        if module_index is not None:
            module = module_index + 1
        return self.process.send_event(
            self.number, track_num, note, vel, module, ctl, ctl_val
        )

    send_event.__doc__ = dll.send_event.__doc__

    def get_current_line(self) -> int:
        return self.process.get_current_line(self.number)

    get_current_line.__doc__ = dll.get_current_line.__doc__

    def get_current_line2(self) -> int:
        return self.process.get_current_line2(self.number)

    get_current_line2.__doc__ = dll.get_current_line2.__doc__

    def get_current_signal_level(self, channel) -> int:
        return self.process.get_current_signal_level(self.number, channel)

    get_current_signal_level.__doc__ = dll.get_current_signal_level.__doc__

    def get_song_name(self) -> Optional[str]:
        song_name = self.process.get_song_name(self.number)
        return song_name.decode("utf8") if song_name is not None else None

    get_song_name.__doc__ = dll.get_song_name.__doc__

    def get_song_bpm(self) -> int:
        return self.process.get_song_bpm(self.number)

    get_song_bpm.__doc__ = dll.get_song_bpm.__doc__

    def get_song_tpl(self) -> int:
        return self.process.get_song_tpl(self.number)

    get_song_tpl.__doc__ = dll.get_song_tpl.__doc__

    def get_song_length_frames(self) -> int:
        return self.process.get_song_length_frames(self.number)

    get_song_length_frames.__doc__ = dll.get_song_length_frames.__doc__

    def get_song_length_lines(self) -> int:
        return self.process.get_song_length_lines(self.number)

    get_song_length_lines.__doc__ = dll.get_song_length_lines.__doc__

    def get_time_map(
        self,
        start_line: int,
        len: int,
        dest: c_uint32_p,
        flags: int,
    ) -> int:
        return self.process.get_time_map(self.number, start_line, len, dest, flags)

    get_time_map.__doc__ = dll.get_time_map.__doc__

    def new_module(
        self,
        module_type: str,
        name: str,
        x: int,
        y: int,
        z: int,
    ) -> int:
        with self.locked():
            return self.process.new_module(
                self.number, module_type.encode("utf8"), name.encode("utf8"), x, y, z
            )

    new_module.__doc__ = dll.new_module.__doc__

    def remove_module(self, mod_num: int) -> int:
        with self.locked():
            return self.process.remove_module(self.number, mod_num)

    remove_module.__doc__ = dll.remove_module.__doc__

    def connect_module(self, source: int, destination: int) -> int:
        with self.locked():
            return self.process.connect_module(self.number, source, destination)

    connect_module.__doc__ = dll.connect_module.__doc__

    def disconnect_module(self, source: int, destination: int) -> int:
        with self.locked():
            return self.process.disconnect_module(self.number, source, destination)

    disconnect_module.__doc__ = dll.disconnect_module.__doc__

    def load_module(
        self,
        file_or_name: FileOrName,
        x: int = 512,
        y: int = 512,
        z: int = 512,
    ) -> int:
        value = None
        if isinstance(file_or_name, BytesIO):
            value = file_or_name.getvalue()
        elif hasattr(file_or_name, "mtype"):
            # Radiant Voices object: serialize into bytes and load from memory.
            import rv.api

            value = rv.api.Synth(file_or_name).read()
        elif hasattr(file_or_name, "read"):
            value = file_or_name.read()
        if value is not None:
            return self.process.load_module_from_memory(
                slot=self.number,
                data=value,
                data_size=len(value),
                x=x,
                y=y,
                z=z,
            )

    load_module.__doc__ = dll.load_module.__doc__

    def sampler_load(
        self,
        sampler_module: int,
        file_name: str,
        sample_slot: int,
    ) -> int:
        return self.process.sampler_load(
            self.number,
            sampler_module,
            file_name.encode(FILENAME_ENCODING),
            sample_slot,
        )

    sampler_load.__doc__ = dll.sampler_load.__doc__

    def sampler_load_from_memory(
        self,
        sampler_module: int,
        data: bytes,
        sample_slot: int,
    ) -> int:
        return self.process.sampler_load_from_memory(
            self.number, sampler_module, data, len(data), sample_slot
        )

    sampler_load_from_memory.__doc__ = dll.sampler_load_from_memory.__doc__

    def get_number_of_modules(self) -> int:
        return self.process.get_number_of_modules(self.number)

    get_number_of_modules.__doc__ = dll.get_number_of_modules.__doc__

    def find_module(self, name: str) -> int:
        return self.process.find_module(self.number, name.encode("utf8"))

    find_module.__doc__ = dll.find_module.__doc__

    def get_module_flags(self, mod_num: int) -> int:
        return self.process.get_module_flags(self.number, mod_num)

    get_module_flags.__doc__ = dll.get_module_flags.__doc__

    def get_module_inputs(self, mod_num: int) -> int:
        return self.process.get_module_inputs(self.number, mod_num)

    get_module_inputs.__doc__ = dll.get_module_inputs.__doc__

    def get_module_outputs(self, mod_num: int) -> int:
        return self.process.get_module_outputs(self.number, mod_num)

    get_module_outputs.__doc__ = dll.get_module_outputs.__doc__

    def get_module_name(self, mod_num: int) -> Optional[str]:
        module_name = self.process.get_module_name(self.number, mod_num)
        return module_name.decode("utf8") if module_name is not None else None

    get_module_name.__doc__ = dll.get_module_name.__doc__

    def get_module_xy(self, mod_num: int) -> int:
        return self.process.get_module_xy(self.number, mod_num)

    get_module_xy.__doc__ = dll.get_module_xy.__doc__

    def get_module_color(self, mod_num: int) -> int:
        return self.process.get_module_color(self.number, mod_num)

    get_module_color.__doc__ = dll.get_module_color.__doc__

    def get_module_finetune(self, mod_num: int) -> int:
        return self.process.get_module_finetune(self.number, mod_num)

    get_module_finetune.__doc__ = dll.get_module_finetune.__doc__

    def get_module_scope2(
        self,
        mod_num: int,
        channel: int,
        dest_buf: c_int16_p,
        samples_to_read: int,
    ) -> int:
        return self.process.get_module_scope2(
            self.number, mod_num, channel, dest_buf, samples_to_read
        )

    get_module_scope2.__doc__ = dll.get_module_scope2.__doc__

    def module_curve(
        self,
        mod_num: int,
        curve_num: int,
        data: c_float_p,
        len: int,
        w: int,
    ) -> int:
        return self.module_curve(self.number, mod_num, curve_num, data, len, w)

    module_curve.__doc__ = dll.module_curve.__doc__

    def get_number_of_module_ctls(self, mod_num: int) -> int:
        return self.process.get_number_of_module_ctls(self.number, mod_num)

    get_number_of_module_ctls.__doc__ = dll.get_number_of_module_ctls.__doc__

    def get_module_ctl_name(self, mod_num: int, ctl_num: int) -> str:
        ctl_name = self.process.get_module_ctl_name(self.number, mod_num, ctl_num)
        return ctl_name.decode("utf8") if ctl_name is not None else None

    get_module_ctl_name.__doc__ = dll.get_module_ctl_name.__doc__

    def get_module_ctl_value(self, mod_num: int, ctl_num: int, scaled: int) -> int:
        return self.process.get_module_ctl_value(self.number, mod_num, ctl_num, scaled)

    get_module_ctl_value.__doc__ = dll.get_module_ctl_value.__doc__

    def get_number_of_patterns(self) -> int:
        return self.process.get_number_of_patterns(self.number)

    get_number_of_patterns.__doc__ = dll.get_number_of_patterns.__doc__

    def find_pattern(self, name: str) -> int:
        return self.process.find_pattern(self.number, name.encode("utf8"))

    find_pattern.__doc__ = dll.find_pattern.__doc__

    def get_pattern_x(self, pat_num: int) -> int:
        return self.process.get_pattern_x(self.number, pat_num)

    get_pattern_x.__doc__ = dll.get_pattern_x.__doc__

    def get_pattern_y(self, pat_num: int) -> int:
        return self.process.get_pattern_y(self.number, pat_num)

    get_pattern_y.__doc__ = dll.get_pattern_y.__doc__

    def get_pattern_tracks(self, pat_num: int) -> int:
        return self.process.get_pattern_tracks(self.number, pat_num)

    get_pattern_tracks.__doc__ = dll.get_pattern_tracks.__doc__

    def get_pattern_lines(self, pat_num: int) -> int:
        return self.process.get_pattern_lines(self.number, pat_num)

    get_pattern_lines.__doc__ = dll.get_pattern_lines.__doc__

    def get_pattern_name(self, pat_num: int) -> str:
        pattern_name = self.process.get_pattern_name(self.number, pat_num)
        return pattern_name.decode("utf8") if pattern_name is not None else None

    get_pattern_name.__doc__ = dll.get_pattern_name.__doc__

    def get_pattern_data(self, pat_num: int) -> sunvox_note_p:
        return self.process.get_pattern_data(self.number, pat_num)

    get_pattern_data.__doc__ = dll.get_pattern_data.__doc__

    def pattern_mute(self, pat_num: int, mute: int) -> int:
        with self.locked():
            return self.process.pattern_mute(self.number, pat_num, mute)

    pattern_mute.__doc__ = dll.pattern_mute.__doc__


__all__ = ["FILENAME_ENCODING", "MAX_SLOTS", "NoSlotsAvailable", "Slot"]
