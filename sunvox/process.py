import multiprocessing as mp

import sunvox
from .processor import Processor


def passthrough(name):
    def fn(self, *args, **kw):
        self._conn.send((name, args, kw))
        return self._conn.recv()
    fn.__name__ = name
    return fn


class Process(object):
    """Starts SunVox DLL in a separate process, with an API bridge."""

    processor_class = Processor

    def __init__(self, *args, **kwargs):
        self._ctx = mp.get_context('forkserver')
        self._conn, child_conn = mp.Pipe()
        args = (child_conn,) + args
        self._process = self._ctx.Process(
            target=Processor, args=args, kwargs=kwargs)
        self._process.start()

    _k, _v = None, None
    for _k, _v in sunvox.__dict__.items():
        if hasattr(_v, 'sunvox_dll_fn'):
            locals()[_k] = passthrough(_k)
    del _k, _v


__all__ = [
    'Process',
]
