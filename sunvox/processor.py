import sunvox


def passthrough(name):
    def fn(self, *args, **kw):
        return getattr(sunvox, name)(*args, **kw)
    fn.__name__ = name
    return fn


class Processor(object):

    def __init__(self, conn):
        self.conn = conn
        self._process_commands()

    def _process_commands(self):
        while True:
            name, args, kwargs = self.conn.recv()
            fn = getattr(self, name)
            self.conn.send(fn(*args, **kwargs))

    _k, _v = None, None
    for _k, _v in sunvox.__dict__.items():
        if hasattr(_v, 'sunvox_dll_fn'):
            locals()[_k] = passthrough(_k)
    del _k, _v
