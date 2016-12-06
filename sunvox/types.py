from ctypes import Structure, c_ubyte, c_ushort
from enum import IntEnum


class NOTECMD(IntEnum):
    (C0, c0, D0, d0, E0, F0, f0, G0, g0, A0, a0, B0,
     C1, c1, D1, d1, E1, F1, f1, G1, g1, A1, a1, B1,
     C2, c2, D2, d2, E2, F2, f2, G2, g2, A2, a2, B2,
     C3, c3, D3, d3, E3, F3, f3, G3, g3, A3, a3, B3,
     C4, c4, D4, d4, E4, F4, f4, G4, g4, A4, a4, B4,
     C5, c5, D5, d5, E5, F5, f5, G5, g5, A5, a5, B5,
     C6, c6, D6, d6, E6, F6, f6, G6, g6, A6, a6, B6,
     C7, c7, D7, d7, E7, F7, f7, G7, g7, A7, a7, B7,
     C8, c8, D8, d8, E8, F8, f8, G8, g8, A8, a8, B8,
     C9, c9, D9, d9, E9, F9, f9, G9, g9, A9, a9, B9) = range(1, 121)
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
