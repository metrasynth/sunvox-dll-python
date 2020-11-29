Changelog
=========


0.3.0.1.9.6.1
-------------

- Update SunVox DLL to 1.9.6b (1.9.6.1).

- Update minimum version of Python supported to 3.7.

- Update docstrings to match new information in upstream ``sunvox.h``.

- Update ``sunvox.slot.Slot.load_module`` method to always use
  ``load_module_from_memory`` function internally.

- Remove ``SV_`` prefix from enums in ``sunvox.types``.

- Remove functions that were deprecated in DLL 1.9.5c, and remove wrapper methods in
  ``sunvox.slot.Slot`` when relevant:

  - ``sunvox.dll.get_sample_type()``

  - ``sunvox.dll.get_module_scope()``

- Add wrappers for functions added in DLL 1.9.4c, with wrapper methods in
  ``sunvox.slot.Slot`` when relevant:

  - ``sunvox.dll.audio_callback2()``

  - ``sunvox.dll.update_input()``

  - ``sunvox.dll.load_module_from_memory()``

  - ``sunvox.dll.sampler_load_from_memory()``

  - ``sunvox.dll.get_log()``

- Add wrappers for functions added in DLL 1.9.5c, with wrapper methods in
  ``sunvox.slot.Slot`` when relevant:

  - ``sunvox.dll.get_time_map()``

  - ``sunvox.dll.get_autostop()``

  - ``sunvox.dll.get_sample_rate()``

  - ``sunvox.dll.find_module()``

  - ``sunvox.dll.find_pattern()``

  - ``sunvox.dll.get_pattern_name()``

  - ``sunvox.dll.get_module_finetune()``

  - ``sunvox.dll.module_curve()``

  - ``sunvox.dll.set_event_t()``

- Add new constants:

  - ``sunvox.types.MODULE.FLAG_MUTE``

  - ``sunvox.types.MODULE.FLAG_SOLO``

  - ``sunvox.types.MODULE.FLAG_BYPASS``

- Add type annotations to all ``sunvox.dll`` function wrappers.

- Add type annotations and docstrings to ``sunvox.slot.Slot`` methods.

- Add ``sunvox.macros`` module containing ports of C macros introduced in 1.9.4c
  and 1.9.5c:

  - ``sunvox.macros.GET_MODULE_XY``

  - ``sunvox.macros.GET_MODULE_FINETUNE``

  - ``sunvox.macros.PITCH_TO_FREQUENCY``

  - ``sunvox.macros.FREQUENCY_TO_PITCH``

- Format code using black_.

..  _black:
    https://black.readthedocs.io/en/stable/


0.2.1.1.9.3.2 (2018-02-28)
--------------------------

- Add Raspberry Pi version of SunVox DLL.

- Add ``sunvox.SUNVOX_COPYRIGHT_NOTICE`` constant, for use in apps
  that make use of this package.


0.2.0.1.9.3.1 (2017-11-25)
--------------------------

- Update SunVox DLL to 1.9.3b (1.9.3.1).


0.2.0.1.9.3.0 (2017-11-25)
--------------------------

- Update SunVox DLL to 1.9.3.0.

- Add support for Windows 64-bit.

- Correct notation of sharps/flats to match SunVox.

- Improvements to buffered processes.


0.1.0.1.9.2.0 (2016-11-08)
--------------------------

- Initial release.
