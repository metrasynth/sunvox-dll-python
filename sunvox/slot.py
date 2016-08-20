from contextlib import contextmanager
from io import BytesIO

from . import dll


FILENAME_ENCODING = 'utf8'
MAX_SLOTS = 4


class NoSlotsAvailable(Exception):
    """The maximum number of SunVox playback slots are in use."""


class Slot(object):
    """A context manager wrapping slot-specific API calls."""

    allocation_map = [False] * MAX_SLOTS

    def __init__(self, file=None):
        self.number = self.next_available_slot()
        if self.number is None:
            raise NoSlotsAvailable()
        self.allocation_map[self.number] = True
        self.locks = 0
        dll.open_slot(self.number)
        if file is not None:
            self.load(file)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    @classmethod
    def next_available_slot(cls):
        i = cls.allocation_map.index(False)
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
        self.allocation_map[i] = False
        return dll.close_slot(i)

    def connect_module(self, source, destination):
        with self.locked():
            return dll.connect_module(self.number, source, destination)

    def disconnect_module(self, source, destination):
        with self.locked():
            return dll.disconnect_module(self.number, source, destination)

    def end_of_song(self):
        return dll.end_of_song(self.number)
    
    def get_current_line(self):
        return dll.get_current_line(self.number)

    def get_current_line2(self):
        return dll.get_current_line2(self.number)

    def get_current_signal_level(self, channel):
        return dll.get_current_signal_level(self.number, channel)

    def get_module_color(self, mod_num):
        return dll.get_module_color(self.number, mod_num)

    def get_module_ctl_name(self, mod_num, ctl_num):
        return dll.get_module_ctl_name(self.number, mod_num, ctl_num)
    
    def get_module_ctl_value(self, mod_num, ctl_num, scaled):
        return dll.get_module_ctl_value(self.number, mod_num, ctl_num, scaled)

    def get_module_flags(self, mod_num):
        return dll.get_module_flags(self.number, mod_num)
    
    def get_module_inputs(self, mod_num):
        return dll.get_module_inputs(self.number, mod_num)

    def get_module_name(self, mod_num):
        return dll.get_module_name(self.number, mod_num)

    def get_module_outputs(self, mod_num):
        return dll.get_module_outputs(self.number, mod_num)
    
    def get_module_scope(self, mod_num, channel, buffer_offset, buffer_size):
        return dll.get_module_scope(
            self.number, mod_num, channel, buffer_offset, buffer_size)

    def get_module_scope2(self, mod_num, channel, read_buf, samples_to_read):
        return dll.get_module_scope2(
            self.number, mod_num, channel, read_buf, samples_to_read)

    def get_module_xy(self, mod_num):
        return dll.get_module_xy(self.number, mod_num)

    def get_number_of_modules(self):
        return dll.get_number_of_modules(self.number)
    
    def get_number_of_module_ctls(self, mod_num):
        return dll.get_number_of_module_ctls(self.number, mod_num)
    
    def get_number_of_patterns(self):
        return dll.get_number_of_patterns(self.number)

    def get_pattern_data(self, pat_num):
        return dll.get_pattern_data(self.number, pat_num)

    def get_pattern_lines(self, pat_num):
        return dll.get_pattern_lines(self.number, pat_num)

    def get_pattern_tracks(self, pat_num):
        return dll.get_pattern_tracks(self.number, pat_num)
    
    def get_pattern_x(self, pat_num):
        return dll.get_pattern_x(self.number, pat_num)
    
    def get_pattern_y(self, pat_num):
        return dll.get_pattern_y(self.number, pat_num)
    
    def get_song_bpm(self):
        return dll.get_song_bpm(self.number)
    
    def get_song_length_frames(self):
        return dll.get_song_length_frames(self.number)
    
    def get_song_length_lines(self):
        return dll.get_song_length_lines(self.number)

    def get_song_tpl(self):
        return dll.get_song_tpl(self.number)

    def load(self, file_or_name):
        if isinstance(file_or_name, str):
            file_or_name = file_or_name.encode(FILENAME_ENCODING)
        if isinstance(file_or_name, bytes):
            return self.load_filename(file_or_name)
        elif callable(getattr(file_or_name, 'read', None)):
            return self.load_file(file_or_name)

    def load_file(self, file):
        if isinstance(file, BytesIO):
            value = file.getvalue()
        else:
            value = file.read()
        return dll.load_from_memory(self.number, value, len(value))

    def load_filename(self, filename):
        return dll.load(self.number, filename)

    def load_module(self, file_name, x, y, z):
        return dll.load_module(self.number, file_name, x, y, z)

    def lock(self):
        self.locks += 1
        return dll.lock_slot(self.number)

    def new_module(self, module_type, name, x, y, z):
        with self.locked():
            return dll.new_module(self.number, module_type, name, x, y, z)

    def pattern_mute(self, pat_num, mute):
        with self.locked():
            return dll.pattern_mute(self.number, pat_num, mute)

    def play(self):
        return dll.play(self.number)

    def play_from_beginning(self):
        return dll.play_from_beginning(self.number)

    def remove_module(self, mod_num):
        with self.locked():
            return dll.remove_module(self.number, mod_num)

    def rewind(self, line_num):
        return dll.rewind(self.number, line_num)

    def sampler_load(self, sampler_module, file_name, sample_slot):
        return dll.sampler_load(
            self.number, sampler_module, file_name, sample_slot)

    def send_event(self, track_num, note, vel, module, ctl, ctl_val):
        module_index = getattr(module, 'index', None)
        if module_index is not None:
            module = module_index + 1
        return dll.send_event(
            self.number, track_num, note, vel, module, ctl, ctl_val)

    def set_autostop(self, autostop):
        return dll.set_autostop(self.number, autostop)

    def stop(self):
        return dll.stop(self.number)

    def volume(self, vol):
        return dll.volume(self.number, vol)

    def unlock(self):
        if self.locks > 0:
            self.locks -= 1
            return dll.unlock_slot(self.number)
