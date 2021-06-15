from typing import Optional, Union

import numpy
from numpy import float32, int16, zeros
from sunvox.api import INIT_FLAG, Process

from .processor import BufferedProcessor


DATA_TYPE_FLAGS = {
    int16: INIT_FLAG.AUDIO_INT16,
    float32: INIT_FLAG.AUDIO_FLOAT32,
}


class BufferedProcess(Process):

    freq = 44100
    channels = 2
    data_type = float32
    size = freq // 60

    processor_class = BufferedProcessor

    def __init__(
        self,
        freq=freq,
        channels=channels,
        data_type=data_type,
        size=size,
        extra_flags=0,
    ):
        super(BufferedProcess, self).__init__()
        self.freq = freq
        self.channels = channels
        self.data_type = data_type
        self.size = size
        flags = (
            INIT_FLAG.USER_AUDIO_CALLBACK
            | INIT_FLAG.ONE_THREAD
            | DATA_TYPE_FLAGS[self.data_type]
            | extra_flags
        )
        self.init(None, self.freq, self.channels, flags)
        self.init_buffer()

    def _send(self, name, *args, **kwargs):
        self._lock.acquire()
        try:
            return self._conn.send((name, args, kwargs))
        finally:
            self._lock.release()

    def _recv(self):
        self._lock.acquire()
        try:
            return self._conn.recv()
        finally:
            self._lock.release()

    @property
    def samples(self):
        return self.size * self.channels

    @property
    def shape(self):
        return self.size, self.channels

    @property
    def type_code(self):
        return {int16: "<i2", float32: "<f4"}[self.data_type]

    def init_buffer(self):
        self._send("init_buffer", self.size)
        return self._recv()

    def fill_buffer(self, input_buffer: Optional[Union[bytes, numpy.ndarray]] = None):
        if isinstance(input_buffer, numpy.ndarray):
            input_buffer = input_buffer.tobytes()
        self._send("fill_buffer", input_buffer)
        raw = self._recv()
        if isinstance(raw, bytes):
            buffer = numpy.fromstring(raw, self.type_code)
            buffer.shape = self.shape
        else:
            buffer = zeros(self.shape)
            print("WARNING, got {!r} {!r} instead of bytes".format(type(raw), raw))
        return buffer


__all__ = ["BufferedProcess", "int16", "float32"]
