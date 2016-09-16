from multiprocessing import sharedctypes

import numpy
from numpy import ctypeslib, int16, float32

from sunvox import SV_INIT_FLAG, Process
from .processor import BufferedProcessor


class BufferedProcess(Process):

    freq = 44100
    channels = 2
    data_type = float32
    size = freq // 60

    processor_class = BufferedProcessor

    def __init__(self, freq=freq, channels=channels, data_type=data_type,
                 size=size):
        super(BufferedProcess, self).__init__()
        self.freq = freq
        self.channels = channels
        self.data_type = data_type
        self.size = size
        flags = SV_INIT_FLAG.USER_AUDIO_CALLBACK | SV_INIT_FLAG.ONE_THREAD
        flags |= {
            int16: SV_INIT_FLAG.AUDIO_INT16,
            float32: SV_INIT_FLAG.AUDIO_FLOAT32,
        }[self.data_type]
        self.init(None, self.freq, self.channels, flags)
        self.init_buffer()

    def _send(self, name, *args, **kwargs):
        return self._conn.send((name, args, kwargs))

    def _recv(self):
        return self._conn.recv()

    @property
    def samples(self):
        return self.size * self.channels

    @property
    def shape(self):
        return self.size, self.channels

    @property
    def type_code(self):
        return {int16: 'h', float32: 'f'}[self.data_type]

    def init_buffer(self):
        self._send('init_buffer', self.size)
        return self._recv()

    def fill_buffer(self):
        self._send('fill_buffer')
        raw = self._recv()
        buffer = numpy.fromstring(raw, self.data_type)
        buffer.shape = self.shape
        return buffer


__all__ = [
    'BufferedProcess',
    'int16',
    'float32',
]
