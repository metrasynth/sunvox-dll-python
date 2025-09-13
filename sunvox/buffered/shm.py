import ctypes
from multiprocessing.managers import SharedMemoryManager
from multiprocessing.shared_memory import SharedMemory

import numpy as np

import sunvox.dll
from sunvox.buffered.process import DATA_TYPE_FLAGS
from sunvox.process import Process
from sunvox.processor import Processor
from sunvox.types import INIT_FLAG


class ShmBufferedProcessor(Processor):
    _frames: int
    _input_buffer_shm: SharedMemory
    _output_buffer_shm: SharedMemory

    def init_buffer(
        self,
        frames: int,
        input_buffer_shm: SharedMemory,
        output_buffer_shm: SharedMemory,
    ):
        """Hook into SHM buffers on child process."""
        self._frames = frames
        self._input_buffer_shm = input_buffer_shm
        self._output_buffer_shm = output_buffer_shm

    def fill_buffer(self, has_input: bool, frames: int | None = None):
        # Use specified frames or default to configured frames
        frames = frames or self._frames

        # Convert memoryview to ctypes pointer
        output_ptr = ctypes.cast(
            ctypes.addressof(ctypes.c_char.from_buffer(self._output_buffer_shm.buf)),
            ctypes.c_void_p,
        )

        if not has_input:
            sunvox.dll.audio_callback(
                output_ptr,
                frames,
                0,
                sunvox.dll.get_ticks(),
            )
        else:
            input_ptr = ctypes.cast(
                ctypes.addressof(ctypes.c_char.from_buffer(self._input_buffer_shm.buf)),
                ctypes.c_void_p,
            )
            sunvox.dll.audio_callback2(
                output_ptr,
                frames,
                0,
                sunvox.dll.get_ticks(),
                1,
                2,
                input_ptr,
            )
        # Return success indicator to parent process
        return True


class ShmBufferedProcess(Process):
    freq = 44100
    channels = 2
    data_type = np.float32
    size = freq // 60

    _input_buffer_shm: SharedMemory
    _output_buffer_shm: SharedMemory
    _input_buffer: np.ndarray
    _output_buffer: np.ndarray

    processor_class = ShmBufferedProcessor

    def __init__(
        self,
        freq=freq,
        channels=channels,
        data_type=data_type,
        size=size,
        extra_flags=0,
        max_size=None,
    ):
        super().__init__()
        self._smm = SharedMemoryManager()
        self._smm.start()
        self.freq = freq
        self.channels = channels
        self.data_type = data_type
        self.size = size
        self.max_size = max_size if max_size is not None else int(size * 1.5)
        self.default_size = size
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
    def buffer_size(self):
        # Use max_size for buffer allocation to support variable frame requests
        max_frames = getattr(self, "max_size", self.size)
        if self.data_type is np.int16:
            return max_frames * self.channels * 2
        elif self.data_type is np.float32:
            return max_frames * self.channels * 4
        raise NotImplementedError()

    def init_buffer(self):
        # Parent process: Prepare SHM buffers for input and output.
        self._input_buffer_shm = self._smm.SharedMemory(self.buffer_size)
        self._output_buffer_shm = self._smm.SharedMemory(self.buffer_size)
        # Use max_size for buffer shape to support variable frame requests
        max_frames = getattr(self, "max_size", self.size)
        max_shape = (max_frames, self.channels)
        self._input_buffer = np.ndarray(
            shape=max_shape, dtype=self.data_type, buffer=self._input_buffer_shm.buf
        )
        self._output_buffer = np.ndarray(
            shape=max_shape, dtype=self.data_type, buffer=self._output_buffer_shm.buf
        )

        # Send SHM context to child process.
        self._send(
            "init_buffer",
            self.size,
            self._input_buffer_shm,
            self._output_buffer_shm,
        )
        return self._recv()

    def fill_buffer(
        self, input_buffer: np.ndarray = None, frames: int | None = None
    ) -> np.ndarray:
        # Use specified frames or default to configured size
        frames = min(frames if frames is not None else self.size, self.max_size)

        if input_buffer is not None:
            assert isinstance(input_buffer, np.ndarray)
            self._input_buffer[:] = input_buffer[:]
            has_input = True
        else:
            has_input = False
        self._send("fill_buffer", has_input, frames)
        self._recv()

        # Always return only the requested number of frames
        return self._output_buffer[:frames]

    def kill(self):
        super().kill()
        if hasattr(self, "_smm"):
            self._smm.shutdown()


__all__ = ["ShmBufferedProcess"]
