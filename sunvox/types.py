from ctypes import Structure, c_ubyte, c_ushort
from enum import IntEnum


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
    SET_PITCH = 133
    PREV_TRACK = 134


class SV_INIT_FLAG(IntEnum):

    NO_DEBUG_OUTPUT = 1 << 0

    # Interaction with sound card is on the user side
    USER_AUDIO_CALLBACK = 1 << 1

    AUDIO_INT16 = 1 << 2

    AUDIO_FLOAT32 = 1 << 3

    # Audio callback and song modification functions are in single thread
    ONE_THREAD = 1 << 4


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
        # 0 - nothing; 1..127 - note num; 128 - note off; 129, 130...
        # - see NOTECMD_xxx defines
        ('note', c_ubyte),

        # Velocity 1..129; 0 - default
        ('vel', c_ubyte),

        # 0 - nothing; 1..255 - module number (real module number + 1)
        ('module', c_ubyte),

        ('nothing', c_ubyte),

        # CCEE. CC - number of a controller (1..255). EE - std effect
        ('ctl', c_ushort),

        # XXYY. Value of controller/effect
        ('ctl_val', c_ushort),
    ]


__all__ = [
    'NOTECMD',
    'SV_INIT_FLAG',
    'SV_MODULE',
    'SV_STYPE',
    'sunvox_note',
]
