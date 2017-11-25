Overview of sunvox-dll-python
=============================

..  start-badges

|buildstatus| |docs|

.. |buildstatus| image:: https://img.shields.io/travis/metrasynth/sunvox-dll-python.svg?style=flat
    :alt: build status
    :scale: 100%
    :target: https://travis-ci.org/metrasynth/sunvox-dll-python

.. |docs| image:: https://readthedocs.org/projects/sunvox-dll-python/badge/?version=latest
    :alt: Documentation Status
    :scale: 100%
    :target: https://sunvox-dll-python.readthedocs.io/en/latest/?badge=latest

..  end-badges

Part of the Metrasynth_ project.

.. _Metrasynth: https://metrasynth.github.io/


Purpose
-------

Provides access to all of the SunVox DLL functions described
in the ``sunvox.h`` header file.

..  uml::

    @startuml
    rectangle "Python Interpreter" as python {
        rectangle "<your_app>" as app
        rectangle "sunvox\nmodule" as sunvox
        rectangle "ctypes\nmodule" as ctypes
    }
    rectangle "SunVox DLL" as dll
    rectangle "SunVox file" as file1
    rectangle "SunVox file" as file2
    rectangle "Audio out\n(hardware)" as audio
    rectangle "Audio out\n(byte stream)" as stream
    file2 -> app : "files can be loaded\nusing byte strings"
    app <-left-> sunvox
    sunvox <-left-> ctypes
    ctypes <-> dll
    file1 -up-> dll : "files can be\nloaded directly"
    dll -> audio : "SunVox can output\naudio directly"
    app -> audio : "Audio output\ncan also be\nsent to a buffer"
    app -> stream
    @enduml


Requirements
------------

- Python 3.5

- One of these supported operating systems:

    - macOS (64-bit)

    - Linux (32-bit, 64-bit)

    - Windows (32-bit, 64-bit)


About SunVox
------------

From the `SunVox home page`_:

    SunVox is a small, fast and powerful modular synthesizer with pattern-based sequencer (tracker).
    It is a tool for those people who like to compose music wherever they are, whenever they wish.
    On any device. SunVox is available for Windows, OS X, Linux, Maemo, Meego, Raspberry Pi,
    Windows Mobile (WindowsCE), PalmOS, iOS and Android.

.. _SunVox home page: http://www.warmplace.ru/soft/sunvox/
