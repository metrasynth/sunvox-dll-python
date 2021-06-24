import ctypes
from typing import Optional

import sunvox.dll
import sunvox.types
from sunvox.processor import Processor


class BufferedProcessor(Processor):
    def __init__(self, conn):
        super().__init__(conn)

    def init(self, device, freq, channels, flags):
        super().init(device, freq, channels, flags)
        self.channels = channels
        if flags & sunvox.types.INIT_FLAG.AUDIO_INT16:
            self.type_code = "h"
        elif flags & sunvox.types.INIT_FLAG.AUDIO_FLOAT32:
            self.type_code = "f"
        self.type_size = {"h": 2, "f": 4}[self.type_code]

    def init_buffer(self, size):
        self._buffer_size = size
        self._buffer_bytes = self.type_size * self.channels * size
        self._buffer = ctypes.create_string_buffer(self._buffer_bytes)

    def fill_buffer(self, input_buffer: Optional[bytes] = None):
        if input_buffer is None:
            sunvox.dll.audio_callback(
                ctypes.byref(self._buffer),
                self._buffer_size,
                0,
                sunvox.dll.get_ticks(),
            )
        else:
            cbuffer = ctypes.create_string_buffer(input_buffer)
            sunvox.dll.audio_callback2(
                ctypes.byref(self._buffer),
                self._buffer_size,
                0,
                sunvox.dll.get_ticks(),
                1,
                2,
                ctypes.byref(cbuffer),
            )
        return self._buffer.raw
