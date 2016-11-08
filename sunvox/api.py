import sunvox.dll
import sunvox.slot
import sunvox.process

from sunvox.dll import *
from sunvox.slot import *
from sunvox.process import *

__all__ = sunvox.dll.__all__ + sunvox.slot.__all__ + sunvox.process.__all__

for __name in __all__:
    setattr(sunvox, __name, locals()[__name])
