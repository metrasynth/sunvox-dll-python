import sunvox.dll
import sunvox.process
import sunvox.slot

from sunvox.dll import *  # NOQA
from sunvox.process import *  # NOQA
from sunvox.slot import *  # NOQA

__all__ = sunvox.dll.__all__ + sunvox.slot.__all__ + sunvox.process.__all__

for __name in __all__:
    setattr(sunvox, __name, locals()[__name])
