from ctypes import Structure, c_ubyte, c_ushort, POINTER, c_uint32, c_int16, c_float
from enum import IntEnum


c_float_p = POINTER(c_float)
c_int16_p = POINTER(c_int16)
c_uint32_p = POINTER(c_uint32)


class NOTECMD(IntEnum):
    (
        C0,
        c0,
        D0,
        d0,
        E0,
        F0,
        f0,
        G0,
        g0,
        A0,
        a0,
        B0,
        C1,
        c1,
        D1,
        d1,
        E1,
        F1,
        f1,
        G1,
        g1,
        A1,
        a1,
        B1,
        C2,
        c2,
        D2,
        d2,
        E2,
        F2,
        f2,
        G2,
        g2,
        A2,
        a2,
        B2,
        C3,
        c3,
        D3,
        d3,
        E3,
        F3,
        f3,
        G3,
        g3,
        A3,
        a3,
        B3,
        C4,
        c4,
        D4,
        d4,
        E4,
        F4,
        f4,
        G4,
        g4,
        A4,
        a4,
        B4,
        C5,
        c5,
        D5,
        d5,
        E5,
        F5,
        f5,
        G5,
        g5,
        A5,
        a5,
        B5,
        C6,
        c6,
        D6,
        d6,
        E6,
        F6,
        f6,
        G6,
        g6,
        A6,
        a6,
        B6,
        C7,
        c7,
        D7,
        d7,
        E7,
        F7,
        f7,
        G7,
        g7,
        A7,
        a7,
        B7,
        C8,
        c8,
        D8,
        d8,
        E8,
        F8,
        f8,
        G8,
        g8,
        A8,
        a8,
        B8,
        C9,
        c9,
        D9,
        d9,
        E9,
        F9,
        f9,
        G9,
        g9,
        A9,
        a9,
        B9,
    ) = range(1, 121)

    EMPTY = 0

    NOTE_OFF = 128

    ALL_NOTES_OFF = 129
    'send "note off" to all modules'

    CLEAN_SYNTHS = 130
    "stop all modules - clear their internal buffers and put them into standby mode"

    STOP = 131

    PLAY = 132

    SET_PITCH = 133
    """
    set the pitch specified in column XXYY, where 0x0000
    - highest possible pitch, 0x7800
    - lowest pitch (note C0);
    one semitone = 0x100
    """

    PREV_TRACK = 134

    CLEAN_MODULE = 140
    "stop the module - clear its internal buffers and put it into standby mode"


class INIT_FLAG(IntEnum):
    """Flags for init()"""

    NO_DEBUG_OUTPUT = 1 << 0

    USER_AUDIO_CALLBACK = 1 << 1
    """
    Offline mode:
    system-dependent audio stream will not be created;
    user calls audio_callback() to get the next piece of sound stream
    """

    OFFLINE = 1 << 1
    "Same as INIT_FLAG.USER_AUDIO_CALLBACK"

    AUDIO_INT16 = 1 << 2
    "Desired sample type of the output sound stream : int16_t"

    AUDIO_FLOAT32 = 1 << 3
    """
    Desired sample type of the output sound stream : float
    The actual sample type may be different, if INIT_FLAG.USER_AUDIO_CALLBACK is not set
    """

    ONE_THREAD = 1 << 4
    """
    Audio callback and song modification functions are in single thread
    Use it with INIT_FLAG.USER_AUDIO_CALLBACK only
    """


class TIME_MAP(IntEnum):
    """Flags for get_time_map()"""

    SPEED = 0
    FRAMECNT = 1
    TYPE_MASK = 3


class MODULE(IntEnum):
    """Flags for get_module_flags()"""

    FLAG_EXISTS = 1 << 0

    FLAG_GENERATOR = 1 << 1
    "Note input + Sound output"

    FLAG_EFFECT = 1 << 2
    "Sound input + Sound output"

    FLAG_MUTE = 1 << 3

    FLAG_SOLO = 1 << 4

    FLAG_BYPASS = 1 << 5

    INPUTS_OFF = 16

    INPUTS_MASK = 255 << INPUTS_OFF

    OUTPUTS_OFF = 16 + 8

    OUTPUTS_MASK = 255 << OUTPUTS_OFF


class sunvox_note(Structure):
    _fields_ = [
        # NN: 0 - nothing; 1..127 - note num; 128 - note off; 129, 130...
        # - see NOTECMD enum
        ("note", c_ubyte),
        # VV: Velocity 1..129; 0 - default
        ("vel", c_ubyte),
        # MM: 0 - nothing; 1..65535 - module number + 1
        ("module", c_ushort),
        # 0xCCEE: CC: 1..127 - controller number + 1; EE - effect
        ("ctl", c_ushort),
        # 0xXXYY: value of controller or effect
        ("ctl_val", c_ushort),
    ]


sunvox_note_p = POINTER(sunvox_note)


__all__ = [
    "NOTECMD",
    "INIT_FLAG",
    "MODULE",
    "TIME_MAP",
    "sunvox_note",
    "sunvox_note_p",
    "c_float_p",
    "c_int16_p",
    "c_uint32_p",
]
