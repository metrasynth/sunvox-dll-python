"""
ctypes wrapper for the SunVox DLL

Naming conventions:

-   Enums are translated from `PREFIX_NAME` to `PREFIX.NAME`:
    `NOTECMD_NOTE_OFF` becomes `NOTECMD.NOTE_OFF`

-   Structure names retain their original case:
    `sunvox_note`, not `SunvoxNote`

-   Function names do not contain a `sv_` prefix:
    `sv_init` becomes `init`
"""
import inspect
import os
import sys
from ctypes import (
    POINTER,
    c_char_p,
    c_int,
    c_short,
    c_uint,
    c_void_p,
    c_uint32,
    c_float,
)
from ctypes.util import find_library
from textwrap import dedent
from typing import Callable, Any

from sunvox.types import sunvox_note


DEFAULT_DLL_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "lib"))

DLL_BASE = os.environ.get("SUNVOX_DLL_BASE", DEFAULT_DLL_BASE)
DLL_PATH = os.environ.get("SUNVOX_DLL_PATH")

if DLL_PATH is not None:
    _sunvox_lib_path = DLL_PATH
elif DLL_BASE is not None:
    platform = sys.platform
    if platform == "linux" and os.uname()[-1] == "armv7l":
        platform = "raspberrypi"
    is64bit = sys.maxsize > 2 ** 32
    key = (platform, is64bit)
    rel_path = {
        ("darwin", True): "osx/lib_x86_64/sunvox.dylib",
        ("linux", True): "linux/lib_x86_64/sunvox.so",
        ("linux", False): "linux/lib_x86/sunvox.so",
        ("raspberrypi", False): "linux/lib_arm_armhf_raspberry_pi/sunvox.so",
        ("win32", True): "sunvox",
        ("win32", False): "sunvox",
    }.get(key)
    if sys.platform == "win32":
        _bit_path = "lib_x86_64" if is64bit else "lib_x86"
        _lib_path = os.path.join(DEFAULT_DLL_BASE, "windows", _bit_path)
        os.environ["PATH"] = _lib_path + ";" + os.environ["PATH"]
        _sunvox_lib_path = rel_path
    else:
        if rel_path is not None:
            _sunvox_lib_path = os.path.join(DLL_BASE, rel_path)
        else:
            raise NotImplementedError(
                "SunVox DLL could not be found for your platform."
            )
else:
    _sunvox_lib_path = find_library("sunvox")

if sys.platform == "win32":
    from ctypes import windll as loader
else:
    from ctypes import cdll as loader
_s = loader.LoadLibrary(_sunvox_lib_path)


GenericFunction = Callable[..., Any]


def decorated_fn(fn, argtypes, restype, needs_lock, doc) -> GenericFunction:
    fn.argtypes = argtypes
    fn.restype = restype
    fn.needs_lock = needs_lock
    fn.sunvox_dll_fn = True
    fn.__doc__ = dedent(doc).strip()
    return fn


def sunvox_fn(c_fn, needs_lock=False):
    """
    Decorate a ctypes function based on a function declaration's type annotations.

    :param c_fn: The function in the loaded SunVox library (`_s` global)
    :return: The decorated function.
    """

    def decorator(fn: GenericFunction) -> GenericFunction:
        spec = inspect.getfullargspec(fn)
        annotations = spec.annotations
        c_fn.argtypes = [annotations[arg] for arg in spec.args]
        c_fn.restype = annotations["return"]
        c_fn.needs_lock = needs_lock
        c_fn.sunvox_dll_fn = True
        c_fn.__doc__ = dedent(fn.__doc__).strip()
        return c_fn

    return decorator


audio_callback = decorated_fn(
    _s.sv_audio_callback,
    [c_void_p, c_int, c_int, c_uint],
    c_int,
    False,
    """
    int sv_audio_callback( void* buf, int frames, int latency, unsigned int out_time );

    Get the next piece of SunVox audio from the Output module.

    With sv_audio_callback() you can ignore the built-in SunVox sound output mechanism and use some other sound system.

    SV_INIT_FLAG_USER_AUDIO_CALLBACK flag in sv_init() mus be set.

    Parameters:
      buf - destination buffer of type signed short (if SV_INIT_FLAG_AUDIO_INT16 used in sv_init())
            or float (if SV_INIT_FLAG_AUDIO_FLOAT32 used in sv_init());
            stereo data will be interleaved in this buffer: LRLR... ; where the LR is the one frame (Left+Right channels);
      frames - number of frames in destination buffer;
      latency - audio latency (in frames);
      out_time - buffer output time (in system ticks);

    Return values:
      0 - silence (buffer filled with zeroes);
      1 - some signal.

    Example:
      user_out_time = ... ; //output time in user time space (NOT SunVox time space!)
      user_cur_time = ... ; //current time (user time space)
      user_ticks_per_second = ... ; //ticks per second (user time space)
      user_latency = user_out_time - use_cur_time; //latency in user time space
      unsigned int sunvox_latency = ( user_latency * sv_get_ticks_per_second() ) / user_ticks_per_second; //latency in SunVox time space
      unsigned int latency_frames = ( user_latency * sample_rate_Hz ) / user_ticks_per_second; //latency in frames
      sv_audio_callback( buf, frames, latency_frames, sv_get_ticks() + sunvox_latency );
    """,
)


audio_callback2 = decorated_fn(
    _s.sv_audio_callback2,
    [c_void_p, c_int, c_int, c_uint, c_int, c_int, c_void_p],
    c_int,
    False,
    """
    int sv_audio_callback2( void* buf, int frames, int latency, unsigned int out_time, int in_type, int in_channels, void* in_buf );

    Send some data to the Input module and receive the filtered data from the Output module.

    It's the same as sv_audio_callback() but you also can specify the input buffer.

    Parameters:
      ...
      in_type - input buffer type: 0 - signed short (16bit integer); 1 - float (32bit floating point);
      in_channels - number of input channels;
      in_buf - input buffer; stereo data will be interleaved in this buffer: LRLR... ; where the LR is the one frame (Left+Right channels);
    """,
)


open_slot = decorated_fn(
    _s.sv_open_slot,
    [c_int],
    c_int,
    False,
    """
    int sv_open_slot( int slot );

    Open sound slot for SunVox.

    You can use several slots simultaneously (each slot with its own SunVox engine)
    """,
)


close_slot = decorated_fn(
    _s.sv_close_slot,
    [c_int],
    c_int,
    False,
    """
    int sv_close_slot( int slot );

    Close sound slot for SunVox.

    You can use several slots simultaneously (each slot with its own SunVox engine)
    """,
)


lock_slot = decorated_fn(
    _s.sv_lock_slot,
    [c_int],
    c_int,
    False,
    """
    int sv_lock_slot( int slot );

    Lock sound slot for SunVox.

    You can use several slots simultaneously (each slot with its own SunVox engine)
    """,
)


unlock_slot = decorated_fn(
    _s.sv_unlock_slot,
    [c_int],
    c_int,
    False,
    """
    int sv_unlock_slot( int slot );

    Unlock sound slot for SunVox.

    You can use several slots simultaneously (each slot with its own SunVox engine)
    """,
)


init = decorated_fn(
    _s.sv_init,
    [c_char_p, c_int, c_int, c_int],
    c_uint,
    False,
    """
    int sv_init( const char* config, int freq, int channels, unsigned int flags );

    Global sound system init.

    Parameters:
      config - string with additional configuration in the following format: "option_name=value|option_name=value";
               example: "buffer=1024|audiodriver=alsa|audiodevice=hw:0,0";
               use null if you agree to the automatic configuration;
      freq - sample rate (Hz); min - 44100;
      channels - only 2 supported now;
      flags - mix of the SV_INIT_FLAG_xxx flags.
    """,
)


deinit = decorated_fn(
    _s.sv_deinit,
    [],
    c_int,
    False,
    """
    int sv_deinit( void );

    Global sound system deinit.
    """,
)


@sunvox_fn(_s.sv_update_input)
def get_sample_rate() -> c_int:
    """
    Get current sampling rate (it may differ from the frequency specified in sv_init())
    """


update_input = decorated_fn(
    _s.sv_update_input,
    [],
    c_int,
    False,
    """
    int sv_update_input( void );

    handle input ON/OFF requests to enable/disable input ports of the sound card
    (for example, after the Input module creation).

    Call it from the main thread only, where the SunVox sound stream is not locked.
    """,
)


load = decorated_fn(
    _s.sv_load,
    [c_int, c_char_p],
    c_int,
    False,
    """
    int sv_load( int slot, const char* name );

    Load SunVox project from the file.
    """,
)


load_from_memory = decorated_fn(
    _s.sv_load_from_memory,
    [c_int, c_void_p, c_uint],
    c_int,
    False,
    """
    int sv_load_from_memory( int slot, void* data, unsigned int data_size );

    Load SunVox project from the memory block.
    """,
)


play = decorated_fn(
    _s.sv_play,
    [c_int],
    c_int,
    False,
    """
    int sv_play( int slot );
    """,
)


play_from_beginning = decorated_fn(
    _s.sv_play_from_beginning,
    [c_int],
    c_int,
    False,
    """
    int sv_play_from_beginning( int slot );
    """,
)


stop = decorated_fn(
    _s.sv_stop,
    [c_int],
    c_int,
    False,
    """
    int sv_stop( int slot );
    """,
)


set_autostop = decorated_fn(
    _s.sv_set_autostop,
    [c_int, c_int],
    c_int,
    False,
    """
    int sv_set_autostop( int slot, int autostop );

    Autostop values:
      0 - disable autostop;
      1 - enable autostop.

    When disabled, song is playing infinitely in the loop.
    """,
)


@sunvox_fn(_s.sv_get_autostop)
def get_autostop(slot: c_int) -> c_int:
    """
    sv_set_autostop(), sv_get_autostop() -
    autostop values: 0 - disable autostop; 1 - enable autostop.
    When disabled, song is playing infinitely in the loop.
    """


end_of_song = decorated_fn(
    _s.sv_end_of_song,
    [c_int],
    c_int,
    False,
    """
    int sv_end_of_song( int slot );

    return values:
      0 - song is playing now;
      1 - stopped.
    """,
)


rewind = decorated_fn(
    _s.sv_rewind,
    [c_int, c_int],
    c_int,
    False,
    """
    int sv_rewind( int slot, int line_num );
    """,
)


volume = decorated_fn(
    _s.sv_volume,
    [c_int, c_int],
    c_int,
    False,
    """
    int sv_volume( int slot, int vol );

    sv_volume() - set volume from 0 (min) to 256 (max 100%);
    negative values are ignored;
    return value: previous volume;
    """,
)


@sunvox_fn(_s.sv_set_event_t)
def set_event_t(slot: c_int, set: c_int, t: c_int) -> c_int:
    """
    sv_set_event_t() - set the time of events to be sent by sv_send_event()
    Parameters:
      slot;
      set: 1 - set; 0 - reset (use automatic time setting - the default mode);
      t: the time when the events occurred (in system ticks, SunVox time space).
    Examples:
      sv_set_event_t( slot, 1, 0 ) //not specified - further events will be processed as quickly as possible
      sv_set_event_t( slot, 1, sv_get_ticks() ) //time when the events will be processed = NOW + sound latancy * 2
    """


send_event = decorated_fn(
    _s.sv_send_event,
    [c_int, c_int, c_int, c_int, c_int, c_int, c_int],
    c_int,
    False,
    """
    int sv_send_event( int slot, int track_num, int note, int vel,
                       int module, int ctl, int ctl_val );

    Send some event (note ON, note OFF, controller change, etc.)

    Parameters:
      slot;
      track_num - track number within the pattern;
      note: 0 - nothing; 1..127 - note num; 128 - note off; 129, 130... - see NOTECMD_xxx defines;
      vel: velocity 1..129; 0 - default;
      module: 0 - nothing; 1..255 - module number + 1;
      ctl: 0xCCEE. CC - number of a controller (1..255). EE - effect;
      ctl_val: value of controller or effect.
    """,
)


get_current_line = decorated_fn(
    _s.sv_get_current_line,
    [c_int],
    c_int,
    False,
    """
    int sv_get_current_line( int slot );

    Get current line number
    """,
)


get_current_line2 = decorated_fn(
    _s.sv_get_current_line2,
    [c_int],
    c_int,
    False,
    """
    int sv_get_current_line2( int slot );

    Get current line number in fixed point format 27.5
    """,
)


get_current_signal_level = decorated_fn(
    _s.sv_get_current_signal_level,
    [c_int, c_int],
    c_int,
    False,
    """
    int sv_get_current_signal_level( int slot, int channel );

    From 0 to 255
    """,
)


get_song_name = decorated_fn(
    _s.sv_get_song_name,
    [c_int],
    c_char_p,
    False,
    """
    const char* sv_get_song_name( int slot );
    """,
)


get_song_bpm = decorated_fn(
    _s.sv_get_song_bpm,
    [c_int],
    c_int,
    False,
    """
    int sv_get_song_bpm( int slot );
    """,
)


get_song_tpl = decorated_fn(
    _s.sv_get_song_tpl,
    [c_int],
    c_int,
    False,
    """
    int sv_get_song_tpl( int slot );
    """,
)


get_song_length_frames = decorated_fn(
    _s.sv_get_song_length_frames,
    [c_int],
    c_uint,
    False,
    """
    unsigned int sv_get_song_length_frames( int slot );

    Get the project length in frames.

    Frame is one discrete of the sound. Sample rate 44100 Hz means, that you hear 44100 frames per second.
    """,
)


get_song_length_lines = decorated_fn(
    _s.sv_get_song_length_lines,
    [c_int],
    c_uint,
    False,
    """
    unsigned int sv_get_song_length_lines( int slot );

    Get the project length in lines.
    """,
)


@sunvox_fn(_s.sv_get_time_map)
def get_time_map(
    slot: c_int, start_line: c_int, len: c_int, dest: POINTER(c_uint32), flags: c_int
) -> c_int:
    """
    sv_get_time_map()
    Parameters:
      slot;
      start_line - first line to read (usually 0);
      len - number of lines to read;
      dest - pointer to the buffer (size = len*sizeof(uint32_t)) for storing the map values;
      flags:
        SV_TIME_MAP_SPEED: dest[X] = BPM | ( TPL << 16 ) (speed at the beginning of line X);
        SV_TIME_MAP_FRAMECNT: dest[X] = frame counter at the beginning of line X;
    Return value: 0 if successful, or negative value in case of some error.
    """


new_module = decorated_fn(
    _s.sv_new_module,
    [c_int, c_char_p, c_char_p, c_int, c_int, c_int],
    c_int,
    True,
    """
    int sv_new_module( int slot, const char* type, const char* name, int x, int y, int z );

    Create a new module.

    USE LOCK/UNLOCK!
    """,
)


remove_module = decorated_fn(
    _s.sv_remove_module,
    [c_int, c_int],
    c_int,
    True,
    """
    int sv_remove_module( int slot, int mod_num );

    Remove selected module.

    USE LOCK/UNLOCK!
    """,
)


connect_module = decorated_fn(
    _s.sv_connect_module,
    [c_int, c_int, c_int],
    c_int,
    True,
    """
    int sv_connect_module( int slot, int source, int destination );

    Connect the source to the destination.

    USE LOCK/UNLOCK!
    """,
)


disconnect_module = decorated_fn(
    _s.sv_disconnect_module,
    [c_int, c_int, c_int],
    c_int,
    True,
    """
    int sv_disconnect_module( int slot, int source, int destination );

    Disconnect the source from the destination.

    USE LOCK/UNLOCK!
    """,
)


load_module = decorated_fn(
    _s.sv_load_module,
    [c_int, c_char_p, c_int, c_int, c_int],
    c_int,
    False,
    """
    int sv_load_module( int slot, const char* file_name, int x, int y, int z );

    Load a module or sample.

    Supported file formats: sunsynth, xi, wav, aiff.

    Return value: new module number or negative value in case of some error.
    """,
)


load_module_from_memory = decorated_fn(
    _s.sv_load_module_from_memory,
    [c_int, c_void_p, c_uint, c_int, c_int, c_int],
    c_int,
    False,
    """
    int sv_load_module_from_memory( int slot, void* data, unsigned int data_size, int x, int y, int z );

    Load a module or sample from the memory block.

    Supported file formats: sunsynth, xi, wav, aiff.

    Return value: new module number or negative value in case of some error.
    """,
)


sampler_load = decorated_fn(
    _s.sv_sampler_load,
    [c_int, c_int, c_char_p, c_int],
    c_int,
    False,
    """
    int sv_sampler_load( int slot, int sampler_module, const char* file_name, int sample_slot );

    Load a sample to already created Sampler.

    To replace the whole sampler - set sample_slot to -1.
    """,
)


sampler_load_from_memory = decorated_fn(
    _s.sv_sampler_load_from_memory,
    [c_int, c_int, c_void_p, c_uint, c_int],
    c_int,
    False,
    """
    int sv_sampler_load_from_memory( int slot, int sampler_module, void* data, unsigned int data_size, int sample_slot );

    Load a sample to already created Sampler.

    To replace the whole sampler - set sample_slot to -1.
    """,
)


get_number_of_modules = decorated_fn(
    _s.sv_get_number_of_modules,
    [c_int],
    c_int,
    False,
    """
    int sv_get_number_of_modules( int slot );
    """,
)


@sunvox_fn(_s.sv_find_module)
def find_module(slot: c_int, name: c_char_p) -> c_int:
    """
    sv_find_module() - find a module by name;
    return value: module number or -1 (if not found);
    """


get_module_flags = decorated_fn(
    _s.sv_get_module_flags,
    [c_int, c_int],
    c_uint,
    False,
    """
    unsigned int sv_get_module_flags( int slot, int mod_num );
    """,
)


get_module_inputs = decorated_fn(
    _s.sv_get_module_inputs,
    [c_int, c_int],
    POINTER(c_int),
    False,
    """
    int* sv_get_module_inputs( int slot, int mod_num );
    """,
)


get_module_outputs = decorated_fn(
    _s.sv_get_module_outputs,
    [c_int, c_int],
    POINTER(c_int),
    False,
    """
    int* sv_get_module_outputs( int slot, int mod_num );
    """,
)


get_module_name = decorated_fn(
    _s.sv_get_module_name,
    [c_int, c_int],
    c_char_p,
    False,
    """
    const char* sv_get_module_name( int slot, int mod_num );
    """,
)


get_module_xy = decorated_fn(
    _s.sv_get_module_xy,
    [c_int, c_int],
    c_uint,
    False,
    """
    unsigned int sv_get_module_xy( int slot, int mod_num );
    """,
)


get_module_color = decorated_fn(
    _s.sv_get_module_color,
    [c_int, c_int],
    c_int,
    False,
    """
    int sv_get_module_color( int slot, int mod_num );
    """,
)


@sunvox_fn(_s.sv_get_module_finetune)
def get_module_finetune(slot: c_int, mod_num: c_int) -> c_uint32:
    """
    sv_get_module_finetune() - get the relative note and finetune of the module;
    return value: ( finetune & 0xFFFF ) | ( ( relative_note & 0xFFFF ) << 16 ).
    Use SV_GET_MODULE_FINETUNE() macro to unpack finetune and relative_note.
    """


get_module_scope2 = decorated_fn(
    _s.sv_get_module_scope2,
    [c_int, c_int, c_int, POINTER(c_short), c_uint],
    c_uint,
    False,
    """
    //sv_get_module_scope2() return value = received number of samples
        (may be less or equal to samples_to_read).
    unsigned int sv_get_module_scope2( int slot, int mod_num, int channel,
                                       signed short* read_buf,
                                       unsigned int samples_to_read );
    """,
)


@sunvox_fn(_s.sv_module_curve)
def module_curve(
    slot: c_int,
    mod_num: c_int,
    curve_num: c_int,
    data: POINTER(c_float),
    len: c_int,
    w: c_int,
) -> c_int:
    """
    sv_module_curve() - access to the curve values of the specified module
    Parameters:
      slot;
      mod_num - module number;
      curve_num - curve number;
      data - destination or source buffer;
      len - number of items to read/write;
      w - read (0) or write (1).
    return value: number of items processed successfully.

    Available curves (Y=CURVE[X]):
      MultiSynth:
        0 - X = note (0..127); Y = velocity (0..1); 128 items;
        1 - X = velocity (0..256); Y = velocity (0..1); 257 items;
      WaveShaper:
        0 - X = input (0..255); Y = output (0..1); 256 items;
      MultiCtl:
        0 - X = input (0..256); Y = output (0..1); 257 items;
      Analog Generator, Generator:
        0 - X = drawn waveform sample number (0..31); Y = volume (-1..1); 32 items;
    """


get_number_of_module_ctls = decorated_fn(
    _s.sv_get_number_of_module_ctls,
    [c_int, c_int],
    c_int,
    False,
    """
    int sv_get_number_of_module_ctls( int slot, int mod_num );
    """,
)


get_module_ctl_name = decorated_fn(
    _s.sv_get_module_ctl_name,
    [c_int, c_int, c_int],
    c_char_p,
    False,
    """
    const char* sv_get_module_ctl_name( int slot, int mod_num, int ctl_num );
    """,
)


get_module_ctl_value = decorated_fn(
    _s.sv_get_module_ctl_value,
    [c_int, c_int, c_int, c_int],
    c_int,
    False,
    """
    int sv_get_module_ctl_value( int slot, int mod_num, int ctl_num,
                                 int scaled );
    """,
)


get_number_of_patterns = decorated_fn(
    _s.sv_get_number_of_patterns,
    [c_int],
    c_int,
    False,
    """
    int sv_get_number_of_patterns( int slot );
    """,
)


@sunvox_fn(_s.sv_find_pattern)
def find_pattern(slot: c_int, name: c_char_p) -> c_int:
    """
    sv_find_pattern() - find a pattern by name;
    return value: pattern number or -1 (if not found);
    """


get_pattern_x = decorated_fn(
    _s.sv_get_pattern_x,
    [c_int, c_int],
    c_int,
    False,
    """
    sv_get_pattern_xxxx - get pattern information
    x - time (line number);
    """,
)


get_pattern_y = decorated_fn(
    _s.sv_get_pattern_y,
    [c_int, c_int],
    c_int,
    False,
    """
    sv_get_pattern_xxxx - get pattern information
    y - vertical position on timeline;
    """,
)


get_pattern_tracks = decorated_fn(
    _s.sv_get_pattern_tracks,
    [c_int, c_int],
    c_int,
    False,
    """
    sv_get_pattern_xxxx - get pattern information
    tracks - number of pattern tracks;
    """,
)


get_pattern_lines = decorated_fn(
    _s.sv_get_pattern_lines,
    [c_int, c_int],
    c_int,
    False,
    """
    sv_get_pattern_xxxx - get pattern information
    lines - number of pattern lines;
    """,
)


@sunvox_fn(_s.sv_get_pattern_name)
def get_pattern_name(slot: c_int, pat_num: c_int) -> c_char_p:
    """
    sv_get_pattern_xxxx - get pattern information
    name - pattern name or NULL;
    """


get_pattern_data = decorated_fn(
    _s.sv_get_pattern_data,
    [c_int, c_int],
    POINTER(sunvox_note),
    False,
    """
    //How to use sv_get_pattern_data():
    //  int pat_tracks = sv_get_pattern_tracks( slot, pat_num );
    //  sunvox_note* data = sv_get_pattern_data( slot, pat_num );
    //  sunvox_note* n = &data[ line_number * pat_tracks + track_number ];
    //  ... and then do someting with note n
    sunvox_note* sv_get_pattern_data( int slot, int pat_num );
    """,
)


pattern_mute = decorated_fn(
    _s.sv_pattern_mute,
    [c_int, c_int, c_int],
    c_int,
    True,
    """
    int sv_pattern_mute( int slot, int pat_num, int mute ); //USE LOCK/UNLOCK!

    sv_pattern_mute() - mute (1) / unmute (0) specified pattern;
    negative values are ignored;
    return value: previous state (1 - muted; 0 - unmuted) or -1 (error);
    """,
)


get_ticks = decorated_fn(
    _s.sv_get_ticks,
    [],
    c_uint,
    False,
    """
    //SunVox engine uses its own time space, measured in ticks.
    //Use sv_get_ticks() to get current tick counter (from 0 to 0xFFFFFFFF).
    unsigned int sv_get_ticks( void );
    """,
)


get_ticks_per_second = decorated_fn(
    _s.sv_get_ticks_per_second,
    [],
    c_uint,
    False,
    """
    //SunVox engine uses its own time space, measured in ticks.
    //Use sv_get_ticks_per_second() to get the number of SunVox
    //  ticks per second.
    unsigned int sv_get_ticks_per_second( void );
    """,
)


get_log = decorated_fn(
    _s.sv_get_log,
    [c_int],
    c_char_p,
    False,
    """
    const char* sv_get_log( int size );

    Get the latest messages from the log.

    Parameters:
      size - max number of bytes to read.

    Return value: pointer to the null-terminated string with the latest log messages.
    """,
)


__all__ = [
    "DEFAULT_DLL_BASE",
    "DLL_BASE",
    "DLL_PATH",
    "audio_callback",
    "audio_callback2",
    "open_slot",
    "close_slot",
    "lock_slot",
    "unlock_slot",
    "init",
    "deinit",
    "get_sample_rate",
    "update_input",
    "load",
    "load_from_memory",
    "play",
    "play_from_beginning",
    "stop",
    "set_autostop",
    "get_autostop",
    "end_of_song",
    "rewind",
    "volume",
    "set_event_t",
    "send_event",
    "get_current_line",
    "get_current_line2",
    "get_current_signal_level",
    "get_song_name",
    "get_song_bpm",
    "get_song_tpl",
    "get_song_length_frames",
    "get_song_length_lines",
    "get_time_map",
    "new_module",
    "remove_module",
    "connect_module",
    "disconnect_module",
    "load_module",
    "load_module_from_memory",
    "sampler_load",
    "sampler_load_from_memory",
    "get_number_of_modules",
    "get_module_flags",
    "get_module_inputs",
    "get_module_outputs",
    "get_module_name",
    "get_module_xy",
    "get_module_color",
    "get_module_finetune",
    "get_module_scope2",
    "module_curve",
    "get_number_of_module_ctls",
    "get_module_ctl_name",
    "get_module_ctl_value",
    "get_number_of_patterns",
    "find_pattern",
    "get_pattern_x",
    "get_pattern_y",
    "get_pattern_tracks",
    "get_pattern_lines",
    "get_pattern_name",
    "get_pattern_data",
    "pattern_mute",
    "get_ticks",
    "get_ticks_per_second",
    "get_log",
]
