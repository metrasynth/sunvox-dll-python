from math import log2
from typing import Tuple


def GET_MODULE_XY(in_xy: int) -> Tuple[int, int]:
    out_x = in_xy & 0xFFFF
    if out_x & 0x8000:
        out_x -= 0x10000
    out_y = (in_xy >> 16) & 0xFFFF
    if out_y & 0x8000:
        out_y -= 0x10000
    return out_x, out_y


def GET_MODULE_FINETUNE(in_finetune: int) -> Tuple[int, int]:
    out_finetune = in_finetune & 0xFFFF
    if out_finetune & 0x8000:
        out_finetune -= 0x10000
    out_relative_note = (in_finetune >> 16) & 0xFFFF
    if out_relative_note & 0x8000:
        out_relative_note -= 0x10000
    return out_finetune, out_relative_note


def PITCH_TO_FREQUENCY(in_pitch: int) -> float:
    return 2 ** ((30720.0 - in_pitch) / 3072.0) * 16.3339


def FREQUENCY_TO_PITCH(in_freq: float) -> int:
    return int(30720 - log2(in_freq / 16.3339) * 3072)


__all__ = [
    "GET_MODULE_XY",
    "GET_MODULE_FINETUNE",
    "PITCH_TO_FREQUENCY",
    "FREQUENCY_TO_PITCH",
]
