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

from ctypes import POINTER, Structure, cdll, c_char_p, c_int, c_short, c_ubyte, c_ushort, c_uint, c_void_p
from ctypes.util import find_library
from enum import IntEnum
import os
import sys
from textwrap import dedent


DEFAULT_DLL_BASE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'lib')
)

DLL_BASE = os.environ.get('SUNVOX_DLL_BASE', DEFAULT_DLL_BASE)
DLL_PATH = os.environ.get('SUNVOX_DLL_PATH')


if DLL_PATH is not None:
    _sunvox_lib_path = DLL_PATH
elif DLL_BASE is not None:
    platform = sys.platform
    is64bit = sys.maxsize > 2**32
    key = (platform, is64bit)
    rel_path = {
        ('darwin', True): 'osx/lib_x86_64/sunvox.dylib',
        ('linux', True): 'linux/lib_x86_64/sunvox.so',
        ('linux', False): 'linux/lib_x86/sunvox.so',
        ('win32', False): 'windows/lib_x86/sunvox.dll',
    }.get(key)
    if rel_path is not None:
        _sunvox_lib_path = os.path.join(DLL_BASE, rel_path)
    else:
        raise NotImplementedError('SunVox DLL could not be found for your platform.')
else:
    _sunvox_lib_path = find_library('sunvox')
_s = cdll.LoadLibrary(_sunvox_lib_path)


class NOTECMD(IntEnum):
    (C0, d0, D0, e0, E0, F0, g0, G0, a0, A0, b0, B0,
     C1, d1, D1, e1, E1, F1, g1, G1, a1, A1, b1, B1,
     C2, d2, D2, e2, E2, F2, g2, G2, a2, A2, b2, B2,
     C3, d3, D3, e3, E3, F3, g3, G3, a3, A3, b3, B3,
     C4, d4, D4, e4, E4, F4, g4, G4, a4, A4, b4, B4,
     C5, d5, D5, e5, E5, F5, g5, G5, a5, A5, b5, B5,
     C6, d6, D6, e6, E6, F6, g6, G6, a6, A6, b6, B6,
     C7, d7, D7, e7, E7, F7, g7, G7, a7, A7, b7, B7,
     C8, d8, D8, e8, E8, F8, g8, G8, a8, A8, b8, B8,
     C9, d9, D9, e9, E9, F9, g9, G9, a9, A9, b9, B9) = range(1, 121)
    EMPTY = 0
    NOTE_OFF = 128
    ALL_NOTES_OFF = 129     # notes of all synths off
    CLEAN_SYNTHS = 130      # stop and clean all synths
    STOP = 131
    PLAY = 132


class SV_INIT_FLAG(IntEnum):
    NO_DEBUG_OUTPUT = 1 << 0
    USER_AUDIO_CALLBACK = 1 << 1    # Interaction with sound card is on the user side
    AUDIO_INT16 = 1 << 2
    AUDIO_FLOAT32 = 1 << 3
    ONE_THREAD = 1 << 4             # Audio callback and song modification functions are in single thread


class SV_MODULE(IntEnum):
    FLAG_EXISTS = 1
    FLAG_EFFECT = 2
    INPUTS_OFF = 16
    INPUTS_MASK = 255 << INPUTS_OFF
    OUTPUTS_OFF = 16 + 8
    OUTPUTS_MASK = 255 << OUTPUTS_OFF


class SV_STYPE(IntEnum):
    INT16 = 0
    INT32 = 1
    FLOAT32 = 2
    FLOAT64 = 3


class sunvox_note(Structure):
    _fields_ = [
        ('note', c_ubyte),       # 0 - nothing; 1..127 - note num; 128 - note off; 129, 130... - see NOTECMD_xxx defines
        ('vel', c_ubyte),        # Velocity 1..129; 0 - default
        ('module', c_ubyte),     # 0 - nothing; 1..255 - module number (real module number + 1)
        ('nothing', c_ubyte),
        ('ctl', c_ushort),       # CCEE. CC - number of a controller (1..255). EE - std effect
        ('ctl_val', c_ushort),   # XXYY. Value of controller/effect
    ]


def decorated_fn(fn, argtypes, restype, needs_lock, doc):
    fn.argtypes = argtypes
    fn.restype = restype
    fn.needs_lock = needs_lock
    fn.sunvox_dll_fn = True
    fn.__doc__ = dedent(doc).strip()
    return fn


audio_callback = decorated_fn(
    _s.sv_audio_callback, [c_void_p, c_int, c_int, c_uint], c_int, False,
    """
    int sv_audio_callback( void* buf, int frames, int latency, unsigned int out_time ) SUNVOX_FN_ATTR;
    Get the next piece of SunVox audio.
    With sv_audio_callback() you can ignore the built-in SunVox sound output mechanism and use some other sound system.
    Set SV_INIT_FLAG_USER_AUDIO_CALLBACK flag in sv_init() if you want to use sv_audio_callback() function.
    Parameters:
      buf - destination buffer of type signed short (if SV_INIT_FLAG_AUDIO_INT16 used in sv_init())
            or float (if SV_INIT_FLAG_AUDIO_FLOAT32 used in sv_init());
      	  stereo data will be interleaved in this buffer: LRLR... ; where the LR is the one frame (Left+Right channels);
      frames - number of frames in destination buffer;
      latency - audio latency (in frames);
      out_time - output time (in ticks).
    """)


open_slot = decorated_fn(
    _s.sv_open_slot, [c_int], c_int, False,
    """
    int sv_open_slot( int slot ) SUNVOX_FN_ATTR;
    """)


close_slot = decorated_fn(
    _s.sv_close_slot, [c_int], c_int, False,
    """int sv_close_slot( int slot ) SUNVOX_FN_ATTR;""")


lock_slot = decorated_fn(
    _s.sv_lock_slot, [c_int], c_int, False,
    """
    int sv_lock_slot( int slot ) SUNVOX_FN_ATTR;
    """)


unlock_slot = decorated_fn(
    _s.sv_unlock_slot, [c_int], c_int, False,
    """
    int sv_unlock_slot( int slot ) SUNVOX_FN_ATTR;
    """)


init = decorated_fn(
    _s.sv_init, [c_char_p, c_int, c_int, c_int], c_int, False,
    """
    int sv_init( const char* dev, int freq, int channels, int flags ) SUNVOX_FN_ATTR;
    """)


deinit = decorated_fn(
    _s.sv_deinit, [], c_int, False,
    """
    int sv_deinit( void ) SUNVOX_FN_ATTR;
    """)


get_sample_type = decorated_fn(
    _s.sv_get_sample_type, [], c_int, False,
    """
    //sv_get_sample_type() - get internal sample type of the SunVox engine. Return value: one of the SV_STYPE_xxx defines.
    //Use it to get the scope buffer type from get_module_scope() function.
    int sv_get_sample_type( void ) SUNVOX_FN_ATTR;
    """)


load = decorated_fn(
    _s.sv_load, [c_int, c_char_p], c_int, False,
    """
    int sv_load( int slot, const char* name ) SUNVOX_FN_ATTR;
    """)


load_from_memory = decorated_fn(
    _s.sv_load_from_memory, [c_int, c_void_p, c_uint], c_int, False,
    """
    int sv_load_from_memory( int slot, void* data, unsigned int data_size ) SUNVOX_FN_ATTR;
    """)


play = decorated_fn(
    _s.sv_play, [c_int], c_int, False,
    """
    int sv_play( int slot ) SUNVOX_FN_ATTR;
    """)


play_from_beginning = decorated_fn(
    _s.sv_play_from_beginning, [c_int], c_int, False,
    """
    int sv_play_from_beginning( int slot ) SUNVOX_FN_ATTR;
    """)


stop = decorated_fn(
    _s.sv_stop, [c_int], c_int, False,
    """
    int sv_stop( int slot ) SUNVOX_FN_ATTR;
    """)


set_autostop = decorated_fn(
    _s.sv_set_autostop, [c_int, c_int], c_int, False,
    """
    //autostop values: 0 - disable autostop; 1 - enable autostop.
    //When disabled, song is playing infinitely in the loop.
    int sv_set_autostop( int slot, int autostop ) SUNVOX_FN_ATTR;
    """)


end_of_song = decorated_fn(
    _s.sv_end_of_song, [c_int], c_int, False,
    """
    //sv_end_of_song() return values: 0 - song is playing now; 1 - stopped.
    int sv_end_of_song( int slot ) SUNVOX_FN_ATTR;
    """)


rewind = decorated_fn(
    _s.sv_rewind, [c_int, c_int], c_int, False,
    """
    int sv_rewind( int slot, int line_num ) SUNVOX_FN_ATTR;
    """)


volume = decorated_fn(
    _s.sv_volume, [c_int, c_int], c_int, False,
    """
    int sv_volume( int slot, int vol ) SUNVOX_FN_ATTR;
    """)


send_event = decorated_fn(
    _s.sv_send_event, [c_int, c_int, c_int, c_int, c_int, c_int, c_int], c_int, False,
    """
    //ctl - 0xCCEE. CC - number of a controller (1..255). EE - std effect
    //ctl_val - value of controller/effect
    int sv_send_event( int slot, int track_num, int note, int vel, int module, int ctl, int ctl_val ) SUNVOX_FN_ATTR;
    """)


get_current_line = decorated_fn(
    _s.sv_get_current_line, [c_int], c_int, False,
    """
    int sv_get_current_line( int slot ) SUNVOX_FN_ATTR; //Get current line number
    """)


get_current_line2 = decorated_fn(
    _s.sv_get_current_line2, [c_int], c_int, False,
    """
    int sv_get_current_line2( int slot ) SUNVOX_FN_ATTR; //Get current line number in fixed point format 27.5
    """)


get_current_signal_level = decorated_fn(
    _s.sv_get_current_signal_level, [c_int, c_int], c_int, False,
    """
    int sv_get_current_signal_level( int slot, int channel ) SUNVOX_FN_ATTR; //From 0 to 255
    """)


get_song_name = decorated_fn(
    _s.sv_get_song_name, [c_int], c_char_p, False,
    """
    const char* sv_get_song_name( int slot ) SUNVOX_FN_ATTR;
    """)


get_song_bpm = decorated_fn(
    _s.sv_get_song_bpm, [c_int], c_int, False,
    """
    int sv_get_song_bpm( int slot ) SUNVOX_FN_ATTR;
    """)


get_song_tpl = decorated_fn(
    _s.sv_get_song_tpl, [c_int], c_int, False,
    """
    int sv_get_song_tpl( int slot ) SUNVOX_FN_ATTR;
    """)


get_song_length_frames = decorated_fn(
    _s.sv_get_song_length_frames, [c_int], c_uint, False,
    """
    //Frame is one discrete of the sound. Sampling frequency 44100 Hz means, that you hear 44100 frames per second.
    unsigned int sv_get_song_length_frames( int slot ) SUNVOX_FN_ATTR;
    """)


get_song_length_lines = decorated_fn(
    _s.sv_get_song_length_lines, [c_int], c_uint, False,
    """
    unsigned int sv_get_song_length_lines( int slot ) SUNVOX_FN_ATTR;
    """)


new_module = decorated_fn(
    _s.sv_new_module, [c_int, c_char_p, c_char_p, c_int, c_int, c_int], c_int, True,
    """
    //sv_new_module() - create a new module;
    int sv_new_module( int slot, const char* type, const char* name, int x, int y, int z ) SUNVOX_FN_ATTR; //USE LOCK/UNLOCK!
    """)


remove_module = decorated_fn(
    _s.sv_remove_module, [c_int, c_int], c_int, True,
    """
    //sv_remove_module() - remove selected module;
    int sv_remove_module( int slot, int mod_num ) SUNVOX_FN_ATTR; //USE LOCK/UNLOCK!
    """)


connect_module = decorated_fn(
    _s.sv_connect_module, [c_int, c_int, c_int], c_int, True,
    """
    //sv_connect_module() - connect the source to the destination;
    int sv_connect_module( int slot, int source, int destination ) SUNVOX_FN_ATTR; //USE LOCK/UNLOCK!
    """)


disconnect_module = decorated_fn(
    _s.sv_disconnect_module, [c_int, c_int, c_int], c_int, True,
    """
    //sv_disconnect_module() - disconnect the source from the destination;
    int sv_disconnect_module( int slot, int source, int destination ) SUNVOX_FN_ATTR; //USE LOCK/UNLOCK!
    """)

load_module = decorated_fn(
    _s.sv_load_module, [c_int, c_char_p, c_int, c_int, c_int], c_int, False,
    """
    //sv_load_module() - load a module; supported file formats: sunsynth, xi, wav, aiff;
    int sv_load_module( int slot, const char* file_name, int x, int y, int z ) SUNVOX_FN_ATTR;
    """)


sampler_load = decorated_fn(
    _s.sv_sampler_load, [c_int, c_int, c_char_p, c_int], c_int, False,
    """
    //sv_sampler_load() - load a sample to already created Sampler; to replace the whole sampler - set sample_slot to -1;
    int sv_sampler_load( int slot, int sampler_module, const char* file_name, int sample_slot ) SUNVOX_FN_ATTR;
    """)


get_number_of_modules = decorated_fn(
    _s.sv_get_number_of_modules, [c_int], c_int, False,
    """
    int sv_get_number_of_modules( int slot ) SUNVOX_FN_ATTR;
    """)


get_module_flags = decorated_fn(
    _s.sv_get_module_flags, [c_int, c_int], c_int, False,
    """
    int sv_get_module_flags( int slot, int mod_num ) SUNVOX_FN_ATTR;
    """)


get_module_inputs = decorated_fn(
    _s.sv_get_module_inputs, [c_int, c_int], POINTER(c_int), False,
    """
    int* sv_get_module_inputs( int slot, int mod_num ) SUNVOX_FN_ATTR;
    """)


get_module_outputs = decorated_fn(
    _s.sv_get_module_outputs, [c_int, c_int], POINTER(c_int), False,
    """
    int* sv_get_module_outputs( int slot, int mod_num ) SUNVOX_FN_ATTR;
    """)


get_module_name = decorated_fn(
    _s.sv_get_module_name, [c_int, c_int], c_char_p, False,
    """
    const char* sv_get_module_name( int slot, int mod_num ) SUNVOX_FN_ATTR;
    """)


get_module_xy = decorated_fn(
    _s.sv_get_module_xy, [c_int, c_int], c_uint, False,
    """
    unsigned int sv_get_module_xy( int slot, int mod_num ) SUNVOX_FN_ATTR;
    """)


get_module_color = decorated_fn(
    _s.sv_get_module_color, [c_int, c_int], c_int, False,
    """
    int sv_get_module_color( int slot, int mod_num ) SUNVOX_FN_ATTR;
    """)


get_module_scope = decorated_fn(
    _s.sv_get_module_scope, [c_int, c_int, c_int, POINTER(c_int), POINTER(c_int)], c_void_p, False,
    """
    void* sv_get_module_scope( int slot, int mod_num, int channel, int* buffer_offset, int* buffer_size ) SUNVOX_FN_ATTR;
    """)


get_module_scope2 = decorated_fn(
    _s.sv_get_module_scope2, [c_int, c_int, c_int, POINTER(c_short), c_uint], c_uint, False,
    """
    //sv_get_module_scope2() return value = received number of samples (may be less or equal to samples_to_read).
    unsigned int sv_get_module_scope2( int slot, int mod_num, int channel, signed short* read_buf, unsigned int samples_to_read ) SUNVOX_FN_ATTR;
    """)


get_number_of_module_ctls = decorated_fn(
    _s.sv_get_number_of_module_ctls, [c_int, c_int], c_int, False,
    """
    int sv_get_number_of_module_ctls( int slot, int mod_num ) SUNVOX_FN_ATTR;
    """)


get_module_ctl_name = decorated_fn(
    _s.sv_get_module_ctl_name, [c_int, c_int, c_int], c_char_p, False,
    """
    const char* sv_get_module_ctl_name( int slot, int mod_num, int ctl_num ) SUNVOX_FN_ATTR;
    """)


get_module_ctl_value = decorated_fn(
    _s.sv_get_module_ctl_value, [c_int, c_int, c_int, c_int], c_int, False,
    """
    int sv_get_module_ctl_value( int slot, int mod_num, int ctl_num, int scaled ) SUNVOX_FN_ATTR;
    """)


get_number_of_patterns = decorated_fn(
    _s.sv_get_number_of_patterns, [c_int], c_int, False,
    """
    int sv_get_number_of_patterns( int slot ) SUNVOX_FN_ATTR;
    """)


get_pattern_x = decorated_fn(
    _s.sv_get_pattern_x, [c_int, c_int], c_int, False,
    """
    int sv_get_pattern_x( int slot, int pat_num ) SUNVOX_FN_ATTR;
    """)


get_pattern_y = decorated_fn(
    _s.sv_get_pattern_y, [c_int, c_int], c_int, False,
    """
    int sv_get_pattern_y( int slot, int pat_num ) SUNVOX_FN_ATTR;
    """)


get_pattern_tracks = decorated_fn(
    _s.sv_get_pattern_tracks, [c_int, c_int], c_int, False,
    """
    int sv_get_pattern_tracks( int slot, int pat_num ) SUNVOX_FN_ATTR;
    """)


get_pattern_lines = decorated_fn(
    _s.sv_get_pattern_lines, [c_int, c_int], c_int, False,
    """
    int sv_get_pattern_lines( int slot, int pat_num ) SUNVOX_FN_ATTR;
    """)


get_pattern_data = decorated_fn(
    _s.sv_get_pattern_data, [c_int, c_int], POINTER(sunvox_note), False,
    """
    //How to use sv_get_pattern_data():
    //  int pat_tracks = sv_get_pattern_tracks( slot, pat_num );
    //  sunvox_note* data = sv_get_pattern_data( slot, pat_num );
    //  sunvox_note* n = &data[ line_number * pat_tracks + track_number ];
    //  ... and then do someting with note n
    sunvox_note* sv_get_pattern_data( int slot, int pat_num ) SUNVOX_FN_ATTR;
    """)


pattern_mute = decorated_fn(
    _s.sv_pattern_mute, [c_int, c_int, c_int], c_int, True,
    """
    int sv_pattern_mute( int slot, int pat_num, int mute ) SUNVOX_FN_ATTR; //USE LOCK/UNLOCK!
    """)


get_ticks = decorated_fn(
    _s.sv_get_ticks, [], c_uint, False,
    """
    //SunVox engine uses its own time space, measured in ticks.
    //Use sv_get_ticks() to get current tick counter (from 0 to 0xFFFFFFFF).
    unsigned int sv_get_ticks( void ) SUNVOX_FN_ATTR;
    """)


get_ticks_per_second = decorated_fn(
    _s.sv_get_ticks_per_second, [], c_uint, False,
    """
    //SunVox engine uses its own time space, measured in ticks.
    //Use sv_get_ticks_per_second() to get the number of SunVox ticks per second.
    unsigned int sv_get_ticks_per_second( void ) SUNVOX_FN_ATTR;
    """)


__all__ = [
    'DEFAULT_DLL_BASE',
    'DLL_BASE',
    'DLL_PATH',
    'NOTECMD',
    'SV_INIT_FLAG',
    'SV_MODULE',
    'SV_STYPE',
    'sunvox_note',
    'audio_callback',
    'open_slot',
    'close_slot',
    'lock_slot',
    'unlock_slot',
    'init',
    'deinit',
    'get_sample_type',
    'load',
    'load_from_memory',
    'play',
    'play_from_beginning',
    'stop',
    'set_autostop',
    'end_of_song',
    'rewind',
    'volume',
    'send_event',
    'get_current_line',
    'get_current_line2',
    'get_current_signal_level',
    'get_song_name',
    'get_song_bpm',
    'get_song_tpl',
    'get_song_length_frames',
    'get_song_length_lines',
    'new_module',
    'remove_module',
    'connect_module',
    'disconnect_module',
    'load_module',
    'sampler_load',
    'get_number_of_modules',
    'get_module_flags',
    'get_module_inputs',
    'get_module_outputs',
    'get_module_name',
    'get_module_xy',
    'get_module_color',
    'get_module_scope',
    'get_module_scope2',
    'get_number_of_module_ctls',
    'get_module_ctl_name',
    'get_module_ctl_value',
    'get_number_of_patterns',
    'get_pattern_x',
    'get_pattern_y',
    'get_pattern_tracks',
    'get_pattern_lines',
    'get_pattern_data',
    'pattern_mute',
    'get_ticks',
    'get_ticks_per_second',
]
