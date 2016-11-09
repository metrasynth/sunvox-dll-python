import multiprocessing as mp
from threading import Lock

import sunvox.dll
from .processor import Processor


def passthrough(name):
    def fn(self, *args, **kw):
        self._lock.acquire()
        try:
            self._conn.send((name, args, kw))
            return self._conn.recv()
        finally:
            self._lock.release()
    fn.__name__ = name
    return fn


class Process(object):
    """Starts SunVox DLL in a separate process, with an API bridge."""

    processor_class = Processor

    def __init__(self, *args, **kwargs):
        self._ctx = mp.get_context('spawn')
        self._conn, child_conn = mp.Pipe()
        self._lock = Lock()
        args = (child_conn,) + args
        self._process = self._ctx.Process(
            target=self.processor_class, args=args, kwargs=kwargs)
        self._process.start()

    _k, _v = None, None
    for _k in sunvox.dll.__all__:
        _v = getattr(sunvox.dll, _k)
        if hasattr(_v, 'sunvox_dll_fn'):
            locals()[_k] = passthrough(_k)
    del _k, _v

    def kill(self):
        self._conn.send(('kill', (), {}))


__all__ = [
    'Process',
]
