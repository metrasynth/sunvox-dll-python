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
from ctypes import c_char_p, c_int, c_void_p, c_uint32
from ctypes.util import find_library
from textwrap import dedent
from typing import Callable, Any, Optional

from sunvox.types import sunvox_note_p, c_uint32_p, c_int16_p, c_float_p

DEFAULT_DLL_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "lib"))
DLL_BASE = os.environ.get("SUNVOX_DLL_BASE", DEFAULT_DLL_BASE)
DLL_PATH = os.environ.get("SUNVOX_DLL_PATH")

PLATFORM_RELATIVE_PATHS = {
    ("darwin", True): "macos/lib_x86_64/sunvox.dylib",
    ("darwin-arm", True): "macos/lib_arm64/sunvox.dylib",
    ("linux", True): "linux/lib_x86_64/sunvox.so",
    ("linux", False): "linux/lib_x86/sunvox.so",
    ("linux-arm", False): "linux/lib_arm/sunvox.so",
    ("linux-arm", True): "linux/lib_arm64/sunvox.so",
    ("win32", True): "sunvox",
    ("win32", False): "sunvox",
}


def _load_library():
    if DLL_PATH is not None:
        sunvox_lib_path = DLL_PATH
    elif DLL_BASE is not None:
        sunvox_lib_path = _find_sunvox_lib_path_from_dll_base()
    else:
        sunvox_lib_path = find_library("sunvox")

    if sys.platform == "win32":
        from ctypes import windll as loader
    else:
        from ctypes import cdll as loader

    return loader.LoadLibrary(sunvox_lib_path)


def _find_sunvox_lib_path_from_dll_base():
    platform = _platform_with_machine()
    is64bit = sys.maxsize > 2**32
    key = (platform, is64bit)
    rel_path = PLATFORM_RELATIVE_PATHS.get(key)
    if platform == "win32":
        machine_path = "lib_x86_64" if is64bit else "lib_x86"
        lib_path = os.path.join(DEFAULT_DLL_BASE, "windows", machine_path)
        os.environ["PATH"] = f'{lib_path};{os.environ["PATH"]}'
        return f"{lib_path}\\{rel_path}.dll"
    if rel_path is not None:
        return os.path.join(DLL_BASE, rel_path)
    raise NotImplementedError("SunVox library not available for your platform.")


def _platform_with_machine():
    platform = sys.platform
    machine = os.uname().machine if platform != "win32" else None
    if platform == "darwin" and machine == "arm64":
        return "darwin-arm"
    if platform == "linux" and machine in {"armv7l", "aarch64"}:
        return "linux-arm"
    return platform


_s = _load_library()


GenericFunction = Callable[..., Any]


def sunvox_fn(
    c_fn,
    arg_ctypes=None,
    return_ctype=None,
    needs_lock=False,
):
    """
    Decorate a ctypes function based on a function declaration's type annotations.

    :param c_fn: The function in the loaded SunVox library (`_s` global)
    :return: The decorated function.
    """

    def decorator(fn: GenericFunction) -> GenericFunction:
        spec = inspect.getfullargspec(fn)
        annotations = spec.annotations
        ctypes = arg_ctypes or [annotations[arg] for arg in spec.args]
        arg_sig = ", ".join(
            f"{arg}: {ctype}" for (arg, ctype) in zip(spec.args, ctypes)
        )
        signature = f"{fn.__name__}({arg_sig})"
        doc = dedent(fn.__doc__ or "").strip()
        c_fn.argtypes = arg_ctypes
        c_fn.restype = return_ctype or annotations["return"]
        c_fn.needs_lock = needs_lock
        c_fn.sunvox_dll_fn = True
        c_fn.__doc__ = f"{signature}\n\n{doc}"
        return c_fn

    return decorator


@sunvox_fn(
    _s.sv_init,
    [
        c_char_p,
        c_int,
        c_int,
        c_uint32,
    ],
    c_int,
)
def init(
    config: Optional[bytes],
    freq: int,
    channels: int,
    flags: int,
) -> int:
    """
    global sound system init

    Parameters:
      config -
        string with additional configuration in the following format:
          "option_name=value|option_name=value";
        example: "buffer=1024|audiodriver=alsa|audiodevice=hw:0,0";
        use null if you agree to the automatic configuration;
      freq -
        desired sample rate (Hz); min - 44100;
        the actual rate may be different, if INIT_FLAG.USER_AUDIO_CALLBACK is not set;
      channels - only 2 supported now;
      flags - mix of the INIT_FLAG.xxx flags.
    """


@sunvox_fn(
    _s.sv_deinit,
    [],
    c_int,
)
def deinit() -> int:
    """
    global sound system deinit
    """


@sunvox_fn(
    _s.sv_get_sample_rate,
    [],
    c_int,
)
def get_sample_rate() -> int:
    """
    Get current sampling rate (it may differ from the frequency specified in sv_init())
    """


@sunvox_fn(
    _s.sv_update_input,
    [],
    c_int,
)
def update_input() -> int:
    """
    handle input ON/OFF requests to enable/disable input ports of the sound card
    (for example, after the Input module creation).

    Call it from the main thread only, where the SunVox sound stream is not locked.
    """


@sunvox_fn(
    _s.sv_audio_callback,
    [
        c_void_p,
        c_int,
        c_int,
        c_uint32,
    ],
    c_int,
)
def audio_callback(
    buf: bytes,
    frames: int,
    latency: int,
    out_time: int,
) -> int:
    """
    get the next piece of SunVox audio from the Output module.

    With audio_callback() you can ignore the built-in SunVox sound output mechanism
    and use some other sound system.

    INIT_FLAG.USER_AUDIO_CALLBACK flag in sv_init() mus be set.

    Parameters:
      buf -
        destination buffer of type int16_t (if INIT_FLAG.AUDIO_INT16 used in init())
          or float (if INIT_FLAG.AUDIO_FLOAT32 used in init());
        stereo data will be interleaved in this buffer: LRLR... ;
        where the LR is the one frame (Left+Right channels);
      frames - number of frames in destination buffer;
      latency - audio latency (in frames);
      out_time - buffer output time (in system ticks, SunVox time space);

    Return values: 0 - silence (buffer filled with zeroes); 1 - some signal.

    Example 1 (simplified, without accurate time sync) - suitable for most cases:
      sv_audio_callback( buf, frames, 0, sv_get_ticks() );

    Example 2 (accurate time sync) - when you need to maintain exact time intervals
                                     between incoming events (notes, commands, etc.):
      user_out_time = ... ; //output time in user time space
                            //(depends on your own implementation)
      user_cur_time = ... ; //current time in user time space
      user_ticks_per_second = ... ; //ticks per second in user time space
      user_latency = user_out_time - user_cur_time; //latency in user time space
      uint32_t sunvox_latency =
        ( user_latency * sv_get_ticks_per_second() ) / user_ticks_per_second;
        //latency in SunVox time space
      uint32_t latency_frames =
        ( user_latency * sample_rate_Hz ) / user_ticks_per_second;
        //latency in frames
      sv_audio_callback( buf, frames, latency_frames, sv_get_ticks() + sunvox_latency );
    """


@sunvox_fn(
    _s.sv_audio_callback2,
    [
        c_void_p,
        c_int,
        c_int,
        c_uint32,
        c_int,
        c_int,
        c_void_p,
    ],
    c_int,
)
def audio_callback2(
    buf: bytes,
    frames: int,
    latency: int,
    out_time: int,
    in_type: int,
    in_channels: int,
    in_buf: bytes,
) -> int:
    """
    send some data to the Input module and receive the filtered data from the Output
    module.

    It's the same as sv_audio_callback() but you also can specify the input buffer.

    Parameters:
      ...
      in_type - input buffer type:
        0 - int16_t (16bit integer);
        1 - float (32bit floating point);
      in_channels - number of input channels;
      in_buf -
        input buffer;
        stereo data must be interleaved in this buffer: LRLR... ;
        where the LR is the one frame (Left+Right channels);
    """


@sunvox_fn(
    _s.sv_open_slot,
    [
        c_int,
    ],
    c_int,
)
def open_slot(slot: int) -> int:
    """
    open sound slot for SunVox.

    You can use several slots simultaneously (each slot with its own SunVox engine).

    Use lock/unlock when you simultaneously read and modify SunVox data from different
    threads (for the same slot);

    example:
      thread 1: sv_lock_slot(0); sv_get_module_flags(0,mod1); sv_unlock_slot(0);
      thread 2: sv_lock_slot(0); sv_remove_module(0,mod2); sv_unlock_slot(0);

    Some functions (marked as "USE LOCK/UNLOCK") can't work without lock/unlock at all.
    """


@sunvox_fn(
    _s.sv_close_slot,
    [
        c_int,
    ],
    c_int,
)
def close_slot(
    slot: int,
) -> int:
    """
    close sound slot for SunVox.

    You can use several slots simultaneously (each slot with its own SunVox engine).

    Use lock/unlock when you simultaneously read and modify SunVox data from different
    threads (for the same slot);

    example:
      thread 1: sv_lock_slot(0); sv_get_module_flags(0,mod1); sv_unlock_slot(0);
      thread 2: sv_lock_slot(0); sv_remove_module(0,mod2); sv_unlock_slot(0);

    Some functions (marked as "USE LOCK/UNLOCK") can't work without lock/unlock at all.
    """


@sunvox_fn(
    _s.sv_lock_slot,
    [
        c_int,
    ],
    c_int,
)
def lock_slot(
    slot: int,
) -> int:
    """
    lock sound slot for SunVox.

    You can use several slots simultaneously (each slot with its own SunVox engine).

    Use lock/unlock when you simultaneously read and modify SunVox data from different
    threads (for the same slot);

    example:
      thread 1: sv_lock_slot(0); sv_get_module_flags(0,mod1); sv_unlock_slot(0);
      thread 2: sv_lock_slot(0); sv_remove_module(0,mod2); sv_unlock_slot(0);

    Some functions (marked as "USE LOCK/UNLOCK") can't work without lock/unlock at all.
    """


@sunvox_fn(
    _s.sv_unlock_slot,
    [
        c_int,
    ],
    c_int,
)
def unlock_slot(
    slot: int,
) -> int:
    """
    unlock sound slot for SunVox.

    You can use several slots simultaneously (each slot with its own SunVox engine).

    Use lock/unlock when you simultaneously read and modify SunVox data from different
    threads (for the same slot);

    example:
      thread 1: sv_lock_slot(0); sv_get_module_flags(0,mod1); sv_unlock_slot(0);
      thread 2: sv_lock_slot(0); sv_remove_module(0,mod2); sv_unlock_slot(0);

    Some functions (marked as "USE LOCK/UNLOCK") can't work without lock/unlock at all.
    """


@sunvox_fn(
    _s.sv_load,
    [
        c_int,
        c_char_p,
    ],
    c_int,
)
def load(
    slot: int,
    name: bytes,
) -> int:
    """
    load SunVox project from the file.
    """


@sunvox_fn(
    _s.sv_load_from_memory,
    [
        c_int,
        c_void_p,
        c_uint32,
    ],
    c_int,
)
def load_from_memory(
    slot: int,
    data: bytes,
    data_size: int,
) -> int:
    """
    load SunVox project from the memory block.
    """


@sunvox_fn(
    _s.sv_save,
    [
        c_int,
        c_char_p,
    ],
    c_int,
)
def save(
    slot: int,
    name: bytes,
) -> int:
    """
    save project to the file.
    """


@sunvox_fn(
    _s.sv_play,
    [
        c_int,
    ],
    c_int,
)
def play(
    slot: int,
) -> int:
    """
    play from the current position
    """


@sunvox_fn(
    _s.sv_play_from_beginning,
    [
        c_int,
    ],
    c_int,
)
def play_from_beginning(
    slot: int,
) -> int:
    """
    play from the beginning (line 0)
    """


@sunvox_fn(
    _s.sv_stop,
    [
        c_int,
    ],
    c_int,
)
def stop(
    slot: int,
) -> int:
    """
    first call - stop playing;
    second call - reset all SunVox activity and switch the engine to standby mode.
    """


@sunvox_fn(
    _s.sv_pause,
    [
        c_int,
    ],
    c_int,
)
def pause(
    slot: int,
) -> int:
    """
    pause the audio stream on the specified slot
    """


@sunvox_fn(
    _s.sv_resume,
    [
        c_int,
    ],
    c_int,
)
def resume(
    slot: int,
) -> int:
    """
    resume the audio stream on the specified slot
    """


@sunvox_fn(
    _s.sv_sync_resume,
    [
        c_int,
    ],
    c_int,
)
def sync_resume(
    slot: int,
) -> int:
    """
    wait for sync (pattern effect 0x33 on any slot)
    and resume the audio stream on the specified slot
    """


@sunvox_fn(
    _s.sv_set_autostop,
    [
        c_int,
        c_int,
    ],
    c_int,
)
def set_autostop(
    slot: int,
    autostop: int,
) -> int:
    """
    autostop values:
      0 - disable autostop;
      1 - enable autostop.

    When disabled, song is playing infinitely in the loop.
    """


@sunvox_fn(
    _s.sv_get_autostop,
    [
        c_int,
    ],
    c_int,
)
def get_autostop(
    slot: int,
) -> int:
    """
    autostop values:
      0 - disable autostop;
      1 - enable autostop.

    When disabled, song is playing infinitely in the loop.
    """


@sunvox_fn(
    _s.sv_end_of_song,
    [
        c_int,
    ],
    c_int,
)
def end_of_song(
    slot: int,
) -> int:
    """
    return values:
      0 - song is playing now;
      1 - stopped.
    """


@sunvox_fn(
    _s.sv_rewind,
    [
        c_int,
        c_int,
    ],
    c_int,
)
def rewind(
    slot: int,
    line_num: int,
) -> int:
    pass


@sunvox_fn(
    _s.sv_volume,
    [
        c_int,
        c_int,
    ],
    c_int,
)
def volume(
    slot: int,
    vol: int,
) -> int:
    """
    set volume from 0 (min) to 256 (max 100%);

    negative values are ignored;

    return value: previous volume;
    """


@sunvox_fn(
    _s.sv_set_event_t,
    [
        c_int,
        c_int,
        c_int,
    ],
    c_int,
)
def set_event_t(
    slot: int,
    set: int,
    t: int,
) -> int:
    """
    set the time of events to be sent by sv_send_event()

    Parameters:
      slot;
      set:
        1 - set;
        0 - reset (use automatic time setting - the default mode);
      t: the time when the events occurred (in system ticks, SunVox time space).

    Examples:
      sv_set_event_t( slot, 1, 0 )
        //not specified - further events will be processed as quickly as possible
      sv_set_event_t( slot, 1, sv_get_ticks() )
        //time when the events will be processed = NOW + sound latancy * 2
    """


@sunvox_fn(
    _s.sv_send_event,
    [
        c_int,
        c_int,
        c_int,
        c_int,
        c_int,
        c_int,
        c_int,
    ],
    c_int,
)
def send_event(
    slot: int,
    track_num: int,
    note: int,
    vel: int,
    module: int,
    ctl: int,
    ctl_val: int,
) -> int:
    """
    send an event (note ON, note OFF, controller change, etc.)

    Parameters:
      slot;
      track_num - track number within the pattern;
      note:
        0 - nothing;
        1..127 - note num;
        128 - note off;
        129, 130... - see NOTECMD.xxx enums;
      vel: velocity 1..129; 0 - default;
      module: 0 (empty) or module number + 1 (1..65535);
      ctl: 0xCCEE. CC - number of a controller (1..255). EE - effect;
      ctl_val: value of controller or effect.
    """


@sunvox_fn(
    _s.sv_get_current_line,
    [
        c_int,
    ],
    c_int,
)
def get_current_line(slot: int) -> int:
    """
    Get current line number
    """


@sunvox_fn(
    _s.sv_get_current_line2,
    [
        c_int,
    ],
    c_int,
)
def get_current_line2(slot: int) -> int:
    """
    Get current line number in fixed point format 27.5
    """


@sunvox_fn(_s.sv_get_current_signal_level, [c_int, c_int], c_int)
def get_current_signal_level(slot: int, channel: int) -> int:
    """
    From 0 to 255
    """


@sunvox_fn(
    _s.sv_get_song_name,
    [c_int],
    c_char_p,
)
def get_song_name(slot: int) -> bytes:
    pass


@sunvox_fn(
    _s.sv_set_song_name,
    [
        c_int,
        c_char_p,
    ],
    c_int,
)
def set_song_name(slot: int, name: bytes) -> int:
    pass


@sunvox_fn(
    _s.sv_get_song_bpm,
    [
        c_int,
    ],
    c_int,
)
def get_song_bpm(slot: int) -> int:
    pass


@sunvox_fn(
    _s.sv_get_song_tpl,
    [
        c_int,
    ],
    c_int,
)
def get_song_tpl(slot: int) -> int:
    pass


@sunvox_fn(
    _s.sv_get_song_length_frames,
    [c_int],
    c_uint32,
)
def get_song_length_frames(slot: int) -> int:
    """
    Get the project length in frames.

    Frame is one discrete of the sound. Sample rate 44100 Hz means, that you hear 44100
    frames per second.
    """


@sunvox_fn(
    _s.sv_get_song_length_lines,
    [c_int],
    c_uint32,
)
def get_song_length_lines(slot: int) -> int:
    """
    Get the project length in lines.
    """


@sunvox_fn(
    _s.sv_get_time_map,
    [
        c_int,
        c_int,
        c_int,
        c_uint32_p,
        c_int,
    ],
    c_int,
)
def get_time_map(
    slot: int,
    start_line: int,
    len: int,
    dest: c_uint32_p,
    flags: int,
) -> int:
    """
    Parameters:
      slot;
      start_line - first line to read (usually 0);
      len - number of lines to read;
      dest -
        pointer to the buffer
        (size = len*sizeof(uint32_t)) for storing the map values;
      flags:
        TIME_MAP.SPEED: dest[X] = BPM | ( TPL << 16 )
          (speed at the beginning of line X);
        TIME_MAP.FRAMECNT: dest[X] = frame counter at the beginning of line X;

    Return value: 0 if successful, or negative value in case of some error.
    """


@sunvox_fn(
    _s.sv_new_module,
    [
        c_int,
        c_char_p,
        c_char_p,
        c_int,
        c_int,
        c_int,
    ],
    c_int,
    needs_lock=True,
)
def new_module(
    slot: int,
    type: bytes,
    name: bytes,
    x: int,
    y: int,
    z: int,
) -> int:
    """
    Create a new module.
    """


@sunvox_fn(
    _s.sv_remove_module,
    [
        c_int,
        c_int,
    ],
    c_int,
    needs_lock=True,
)
def remove_module(
    slot: int,
    mod_num: int,
) -> int:
    """
    Remove selected module.
    """


@sunvox_fn(
    _s.sv_connect_module,
    [
        c_int,
        c_int,
        c_int,
    ],
    c_int,
    needs_lock=True,
)
def connect_module(
    slot: int,
    source: int,
    destination: int,
) -> int:
    """
    Connect the source to the destination.
    """


@sunvox_fn(
    _s.sv_disconnect_module,
    [
        c_int,
        c_int,
        c_int,
    ],
    c_int,
    needs_lock=True,
)
def disconnect_module(
    slot: int,
    source: int,
    destination: int,
) -> int:
    """
    Disconnect the source from the destination.
    """


@sunvox_fn(
    _s.sv_load_module,
    [
        c_int,
        c_char_p,
        c_int,
        c_int,
        c_int,
    ],
    c_int,
)
def load_module(
    slot: int,
    file_name: bytes,
    x: int,
    y: int,
    z: int,
) -> int:
    """
    load a module or sample;

    supported file formats: sunsynth, xi, wav, aiff;

    return value: new module number or negative value in case of some error;
    """


@sunvox_fn(
    _s.sv_load_module_from_memory,
    [
        c_int,
        c_void_p,
        c_uint32_p,
        c_int,
        c_int,
        c_int,
    ],
    c_int,
)
def load_module_from_memory(
    slot: int,
    data: bytes,
    data_size: int,
    x: int,
    y: int,
    z: int,
) -> int:
    """
    load a module or sample from the memory block
    """


@sunvox_fn(
    _s.sv_sampler_load,
    [
        c_int,
        c_int,
        c_char_p,
        c_int,
    ],
    c_int,
)
def sampler_load(
    slot: int,
    mod_num: int,
    file_name: bytes,
    sample_slot: int,
) -> int:
    """
    load a sample to already created Sampler;
    to replace the whole sampler - set sample_slot to -1;
    """


@sunvox_fn(
    _s.sv_sampler_load_from_memory,
    [
        c_int,
        c_int,
        c_void_p,
        c_uint32,
        c_int,
    ],
    c_int,
)
def sampler_load_from_memory(
    slot: int,
    mod_num: int,
    data: bytes,
    data_size: int,
    sample_slot: int,
) -> int:
    """
    load a sample to already created Sampler;
    to replace the whole sampler - set sample_slot to -1;
    """


@sunvox_fn(
    _s.sv_metamodule_load,
    [
        c_int,
        c_int,
        c_char_p,
    ],
    c_int,
)
def metamodule_load(
    slot: int,
    mod_num: int,
    file_name: bytes,
) -> int:
    """
    load a file into the MetaModule;
    supported file formats: sunvox, mod, xm, midi;
    """


@sunvox_fn(
    _s.sv_metamodule_load_from_memory,
    [
        c_int,
        c_int,
        c_void_p,
        c_int,
    ],
    c_int,
)
def metamodule_load_from_memory(
    slot: int,
    mod_num: int,
    data: bytes,
    data_size: int,
) -> int:
    """
    load a file into the MetaModule;
    supported file formats: sunvox, mod, xm, midi;
    """


@sunvox_fn(
    _s.sv_vplayer_load,
    [
        c_int,
        c_int,
        c_char_p,
    ],
    c_int,
)
def vplayer_load(
    slot: int,
    mod_num: int,
    file_name: bytes,
) -> int:
    """
    load a file into the Vorbis Player;
    supported file formats: ogg;
    """


@sunvox_fn(
    _s.sv_vplayer_load_from_memory,
    [
        c_int,
        c_int,
        c_void_p,
        c_int,
    ],
    c_int,
)
def vplayer_load_from_memory(
    slot: int,
    mod_num: int,
    data: bytes,
    data_size: int,
) -> int:
    """
    load a file into the Vorbis Player;
    supported file formats: ogg;
    """


@sunvox_fn(
    _s.sv_get_number_of_modules,
    [
        c_int,
    ],
    c_int,
)
def get_number_of_modules(slot: int) -> int:
    """
    get the number of module slots (not the actual number of modules).
    The slot can be empty or it can contain a module.
    Here is the code to determine that the module slot X is not empty:
    ( sv_get_module_flags( slot, X ) & SV_MODULE_FLAG_EXISTS ) != 0;
    """


@sunvox_fn(
    _s.sv_find_module,
    [
        c_int,
        c_char_p,
    ],
    c_int,
)
def find_module(
    slot: int,
    name: bytes,
) -> int:
    """
    find a module by name;

    return value: module number or -1 (if not found);
    """


@sunvox_fn(
    _s.sv_get_module_flags,
    [
        c_int,
        c_int,
    ],
    c_uint32,
)
def get_module_flags(
    slot: int,
    mod_num: int,
) -> int:
    """
    sunvox.types.MODULE.FLAG_xxx
    """


@sunvox_fn(
    _s.sv_get_module_inputs,
    [
        c_int,
        c_int,
    ],
    c_int,
)
def get_module_inputs(
    slot: int,
    mod_num: int,
) -> int:
    """
    get pointers to the int[] arrays with the input links.
    Number of input links = ( module_flags & MODULE.INPUTS_MASK ) >> MODULE.INPUTS_OFF
    (this is not the actual number of connections: some links may be empty (value = -1))
    """


@sunvox_fn(
    _s.sv_get_module_outputs,
    [
        c_int,
        c_int,
    ],
    c_int,
)
def get_module_outputs(
    slot: int,
    mod_num: int,
) -> int:
    """
    get pointers to the int[] arrays with the output links.
    Number of output links =
    ( module_flags & MODULE.OUTPUTS_MASK ) >> MODULE.OUTPUTS_OFF
    (this is not the actual number of connections: some links may be empty (value = -1))
    """


@sunvox_fn(
    _s.sv_get_module_type,
    [
        c_int,
        c_int,
    ],
    c_char_p,
)
def get_module_type(
    slot: int,
    mod_num: int,
) -> bytes:
    pass


@sunvox_fn(
    _s.sv_get_module_name,
    [
        c_int,
        c_int,
    ],
    c_char_p,
)
def get_module_name(
    slot: int,
    mod_num: int,
) -> bytes:
    pass


@sunvox_fn(
    _s.sv_set_module_name,
    [
        c_int,
        c_int,
        c_char_p,
    ],
    c_int,
)
def set_module_name(slot: int, mod_num: int, name: bytes) -> int:
    pass


@sunvox_fn(
    _s.sv_get_module_xy,
    [
        c_int,
        c_int,
    ],
    c_uint32,
)
def get_module_xy(
    slot: int,
    mod_num: int,
) -> int:
    """
    get module XY coordinates packed in a single uint32 value:

    ( x & 0xFFFF ) | ( ( y & 0xFFFF ) << 16 )

    Normal working area: 0x0 ... 1024x1024
    Center: 512x512

    Use GET_MODULE_XY() macro to unpack X and Y.
    """


@sunvox_fn(
    _s.sv_set_module_xy,
    [
        c_int,
        c_int,
        c_int,
        c_int,
    ],
    c_int,
)
def set_module_xy(
    slot: int,
    mod_num: int,
    x: int,
    y: int,
) -> int:
    pass


@sunvox_fn(
    _s.sv_get_module_color,
    [
        c_int,
        c_int,
    ],
    c_int,
)
def get_module_color(
    slot: int,
    mod_num: int,
) -> int:
    """
    get module color in the following format: 0xBBGGRR
    """


@sunvox_fn(
    _s.sv_set_module_color,
    [
        c_int,
        c_int,
        c_int,
    ],
    c_int,
)
def set_module_color(
    slot: int,
    mod_num: int,
    color: int,
) -> int:
    """
    set module color in the following format: 0xBBGGRR
    """


@sunvox_fn(
    _s.sv_get_module_finetune,
    [
        c_int,
        c_int,
    ],
    c_uint32,
)
def get_module_finetune(
    slot: int,
    mod_num: int,
) -> int:
    """
    get the relative note and finetune of the module;

    return value: ( finetune & 0xFFFF ) | ( ( relative_note & 0xFFFF ) << 16 ).

    Use GET_MODULE_FINETUNE() macro to unpack finetune and relative_note.
    """


@sunvox_fn(
    _s.sv_set_module_finetune,
    [
        c_int,
        c_int,
        c_int,
    ],
    c_int,
)
def set_module_finetune(
    slot: int,
    mod_num: int,
    finetune: int,
) -> int:
    """
    change the finetune immediately
    """


@sunvox_fn(
    _s.sv_set_module_relnote,
    [
        c_int,
        c_int,
        c_int,
    ],
    c_int,
)
def set_module_relnote(
    slot: int,
    mod_num: int,
    relative_note: int,
) -> int:
    """
    change the relative note immediately
    """


@sunvox_fn(
    _s.sv_get_module_scope2,
    [
        c_int,
        c_int,
        c_int,
        c_int16_p,
        c_uint32,
    ],
    c_uint32,
)
def get_module_scope2(
    slot: int,
    mod_num: int,
    channel: int,
    dest_buf: c_int16_p,
    samples_to_read: int,
) -> int:
    """
    return value = received number of samples (may be less or equal to samples_to_read).

    Example:
      int16_t buf[ 1024 ];
      int received = sv_get_module_scope2( slot, mod_num, 0, buf, 1024 );
      //buf[ 0 ] = value of the first sample (-32768...32767);
      //buf[ 1 ] = value of the second sample;
      //...
      //buf[ received - 1 ] = value of the last received sample;
    """


@sunvox_fn(
    _s.sv_module_curve,
    [
        c_int,
        c_int,
        c_int,
        c_float_p,
        c_int,
        c_int,
    ],
    c_int,
)
def module_curve(
    slot: int,
    mod_num: int,
    curve_num: int,
    data: c_float_p,
    len: int,
    w: int,
) -> int:
    """
    access to the curve values of the specified module

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
        2 - X = note (0..127); Y = pitch (0..1); 128 items;
            pitch range: 0 ... 16384/65535 (note0) ... 49152/65535 (note128) ... 1; semitone = 256/65535;
      WaveShaper:
        0 - X = input (0..255); Y = output (0..1); 256 items;
      MultiCtl:
        0 - X = input (0..256); Y = output (0..1); 257 items;
      Analog Generator, Generator:
        0 - X = drawn waveform sample number (0..31); Y = volume (-1..1); 32 items;
      FMX:
        0 - X = custom waveform sample number (0..255); Y = volume (-1..1); 256 items;
    """


@sunvox_fn(
    _s.sv_get_number_of_module_ctls,
    [
        c_int,
        c_int,
    ],
    c_int,
)
def get_number_of_module_ctls(
    slot: int,
    mod_num: int,
) -> int:
    pass


@sunvox_fn(
    _s.sv_get_module_ctl_name,
    [
        c_int,
        c_int,
        c_int,
    ],
    c_char_p,
)
def get_module_ctl_name(
    slot: int,
    mod_num: int,
    ctl_num: int,
) -> bytes:
    pass


@sunvox_fn(
    _s.sv_get_module_ctl_value,
    [
        c_int,
        c_int,
        c_int,
        c_int,
    ],
    c_int,
)
def get_module_ctl_value(
    slot: int,
    mod_num: int,
    ctl_num: int,
    scaled: int,
) -> int:
    """
    get the value of the specified module controller

    Parameters:
      slot;
      mod_num - module number;
      ctl_num - controller number (from 0);
      scaled - describes the type of the returned value:
        0 - real value (0,1,2...) as it is stored inside the controller;
            but the value displayed in the program interface may be different - you can use scaled=2 to get the displayed value;
        1 - scaled (0x0000...0x8000) if the controller type = 0, or the real value if the controller type = 1 (enum);
            this value can be used in the pattern column XXYY;
        2 - final value displayed in the program interface -
            in most cases it is identical to the real value (scaled=0), and sometimes it has an additional offset;

    return value: value of the specified module controller.
    """


@sunvox_fn(
    _s.sv_set_module_ctl_value,
    [
        c_int,
        c_int,
        c_int,
        c_int,
        c_int,
    ],
    c_int,
)
def set_module_ctl_value(
    slot: int,
    mod_num: int,
    ctl_num: int,
    val: int,
    scaled: int,
) -> int:
    """
    send the value to the specified module controller;
    (sv_send_event() will be used internally)
    """


@sunvox_fn(
    _s.sv_get_module_ctl_min,
    [
        c_int,
        c_int,
        c_int,
        c_int,
    ],
    c_int,
)
def get_module_ctl_min(
    slot: int,
    mod_num: int,
    ctl_num: int,
    scaled: int,
) -> int:
    pass


@sunvox_fn(
    _s.sv_get_module_ctl_max,
    [
        c_int,
        c_int,
        c_int,
        c_int,
    ],
    c_int,
)
def get_module_ctl_max(
    slot: int,
    mod_num: int,
    ctl_num: int,
    scaled: int,
) -> int:
    pass


@sunvox_fn(
    _s.sv_get_module_ctl_offset,
    [
        c_int,
        c_int,
        c_int,
    ],
    c_int,
)
def get_module_ctl_offset(
    slot: int,
    mod_num: int,
    ctl_num: int,
) -> int:
    """Get display value offset"""


@sunvox_fn(
    _s.sv_get_module_ctl_type,
    [
        c_int,
        c_int,
        c_int,
    ],
    c_int,
)
def get_module_ctl_type(
    slot: int,
    mod_num: int,
    ctl_num: int,
) -> int:
    """
    0 - normal (scaled);
    1 - selector (enum);
    """


@sunvox_fn(
    _s.sv_get_module_ctl_group,
    [
        c_int,
        c_int,
        c_int,
    ],
    c_int,
)
def get_module_ctl_group(
    slot: int,
    mod_num: int,
    ctl_num: int,
) -> int:
    pass


@sunvox_fn(
    _s.sv_new_pattern,
    [
        c_int,
        c_int,
        c_int,
        c_int,
        c_int,
        c_int,
        c_int,
        c_char_p,
    ],
    c_int,
    needs_lock=True,
)
def new_pattern(
    slot: int,
    clone: int,
    x: int,
    y: int,
    tracks: int,
    lines: int,
    icon_seed: int,
    name: bytes,
) -> int:
    """create a new pattern"""


@sunvox_fn(
    _s.sv_remove_pattern,
    [
        c_int,
        c_int,
    ],
    c_int,
)
def remove_pattern(slot: int, pat_num: int) -> int:
    """remove selected pattern"""


@sunvox_fn(
    _s.sv_get_number_of_patterns,
    [
        c_int,
    ],
    c_int,
)
def get_number_of_patterns(
    slot: int,
) -> int:
    """
    get the number of pattern slots (not the actual number of patterns).
    The slot can be empty or it can contain a pattern.
    Here is the code to determine that the pattern slot X is not empty:
    sv_get_pattern_lines( slot, X ) > 0;
    """


@sunvox_fn(
    _s.sv_find_pattern,
    [
        c_int,
        c_char_p,
    ],
    c_int,
)
def find_pattern(
    slot: int,
    name: bytes,
) -> int:
    """
    find a pattern by name;

    return value: pattern number or -1 (if not found);
    """


@sunvox_fn(
    _s.sv_get_pattern_x,
    [
        c_int,
        c_int,
    ],
    c_int,
)
def get_pattern_x(
    slot: int,
    pat_num: int,
) -> int:
    """
    get pattern position;

    x - line number (horizontal position on the timeline)
    """


@sunvox_fn(
    _s.sv_get_pattern_y,
    [
        c_int,
        c_int,
    ],
    c_int,
)
def get_pattern_y(
    slot: int,
    pat_num: int,
) -> int:
    """
    get pattern position;

    y - vertical position on the timeline;
    """


@sunvox_fn(
    _s.sv_set_pattern_xy,
    [
        c_int,
        c_int,
        c_int,
        c_int,
    ],
    c_int,
    needs_lock=True,
)
def set_pattern_xy(
    slot: int,
    pat_num: int,
    x: int,
    y: int,
) -> int:
    """
    set pattern position;

    Parameters:
      x - line number (horizontal position on the timeline);
      y - vertical position on the timeline;
    """


@sunvox_fn(
    _s.sv_get_pattern_tracks,
    [
        c_int,
        c_int,
    ],
    c_int,
)
def get_pattern_tracks(
    slot: int,
    pat_num: int,
) -> int:
    """
    get pattern size;

    return value: number of pattern tracks;
    """


@sunvox_fn(
    _s.sv_get_pattern_lines,
    [
        c_int,
        c_int,
    ],
    c_int,
)
def get_pattern_lines(
    slot: int,
    pat_num: int,
) -> int:
    """
    get pattern size;

    return value: number of pattern lines;
    """


@sunvox_fn(
    _s.sv_set_pattern_size,
    [
        c_int,
        c_int,
        c_int,
        c_int,
    ],
    c_int,
    needs_lock=True,
)
def set_pattern_size(slot: int, pat_num: int, tracks: int, lines: int) -> int:
    pass


@sunvox_fn(
    _s.sv_get_pattern_name,
    [
        c_int,
        c_int,
    ],
    c_char_p,
)
def get_pattern_name(
    slot: int,
    pat_num: int,
) -> bytes:
    pass


@sunvox_fn(
    _s.sv_set_pattern_name,
    [
        c_int,
        c_int,
        c_char_p,
    ],
    c_int,
    needs_lock=True,
)
def set_pattern_name(
    slot: int,
    pat_num: int,
    name: bytes,
) -> int:
    pass


@sunvox_fn(
    _s.sv_get_pattern_data,
    [
        c_int,
        c_int,
    ],
    sunvox_note_p,
)
def get_pattern_data(
    slot: int,
    pat_num: int,
) -> sunvox_note_p:
    """
    get the pattern buffer (for reading and writing)

    containing notes (events) in the following order:
      line 0: note for track 0, note for track 1, ... note for track X;
      line 1: note for track 0, note for track 1, ... note for track X;
      ...
      line X: ...

    Example:
      int pat_tracks = sv_get_pattern_tracks( slot, pat_num ); //number of tracks
      sunvox_note* data = sv_get_pattern_data( slot, pat_num );
        //get the buffer with all the pattern events (notes)
      sunvox_note* n = &data[ line_number * pat_tracks + track_number ];
      ... and then do someting with note n ...
    """


@sunvox_fn(
    _s.sv_set_pattern_event,
    [
        c_int,
        c_int,
        c_int,
        c_int,
        c_int,
        c_int,
        c_int,
        c_int,
        c_int,
    ],
    c_int,
)
def set_pattern_event(
    slot: int,
    pat_num: int,
    track: int,
    line: int,
    nn: int,
    vv: int,
    mm: int,
    ccee: int,
    xxyy: int,
) -> int:
    """
    write the pattern event to the cell at the specified line and track
    nn,vv,mm,ccee,xxyy are the same as the fields of sunvox_note structure.
    Only non-negative values will be written to the pattern.
    Return value: 0 (sucess) or negative error code.
    """


@sunvox_fn(
    _s.sv_get_pattern_event,
    [
        c_int,
        c_int,
        c_int,
        c_int,
        c_int,
    ],
    c_int,
)
def get_pattern_event(
    slot: int,
    pat_num: int,
    track: int,
    line: int,
    column: int,
) -> int:
    """
    read a pattern event at the specified line and track
    column (field number):
       0 - note (NN);
       1 - velocity (VV);
       2 - module (MM);
       3 - controller number or effect (CCEE);
       4 - controller value or effect parameter (XXYY);
    Return value: value of the specified field or negative error code.
    """


@sunvox_fn(
    _s.sv_pattern_mute,
    [
        c_int,
        c_int,
        c_int,
    ],
    c_int,
)
def pattern_mute(
    slot: int,
    pat_num: int,
    mute: int,
) -> int:
    """
    mute (1) / unmute (0) specified pattern;

    negative values are ignored;

    return value: previous state (1 - muted; 0 - unmuted) or -1 (error);
    """


@sunvox_fn(
    _s.sv_get_ticks,
    [],
    c_uint32,
)
def get_ticks() -> int:
    """
    SunVox engine uses its own time space, measured in system ticks (don't confuse it
    with the project ticks);

    required when calculating the out_time parameter in the sv_audio_callback().

    Use sv_get_ticks() to get current tick counter (from 0 to 0xFFFFFFFF).
    """


@sunvox_fn(
    _s.sv_get_ticks_per_second,
    [],
    c_uint32,
)
def get_ticks_per_second() -> int:
    """
    SunVox engine uses its own time space, measured in system ticks (don't confuse it
    with the project ticks);

    required when calculating the out_time parameter in the sv_audio_callback().

    Use sv_get_ticks_per_second() to get the number of SunVox ticks per second.
    """


@sunvox_fn(
    _s.sv_get_log,
    [
        c_int,
    ],
    c_char_p,
)
def get_log(
    size: int,
) -> bytes:
    """
    get the latest messages from the log

    Parameters:
      size - max number of bytes to read.

    Return value: pointer to the null-terminated string with the latest log messages.
    """


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
    "pause",
    "resume",
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
