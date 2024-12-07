==========================
Updating sunvox-dll-python
==========================

This is a loose collection of notes for maintaining releases of sunvox-dll-python
and uploading them to the Python Package Index (PyPI).


After new releases of SunVox library
====================================

1.  Copy libraries from the SunVox library distribution, e.g.:
    ``cd sunvox/lib; ./copy-libs.sh ../../../sunvox_lib``

2.  Change ``sunvox/dll.py`` to add, change, or remove any functions,
    based on changes in ``sunvox.h`` in the SunVox library itself.

3.  Change ``sunvox/slot.py`` to mirror any changes made to ``sunvox/dll.py``.

4.  Update ``sunvox/__init__.py:__version__`` to match the new SunVox version.

    The format of the version is ``<python-wrapper-version>.<sunvox-library-version>``,
    where ``<python-wrapper-version>`` is ``<major>.<minor>.<patch>``, and
    ``<sunvox-version>`` is the four-segment representation of the SunVox version.
    (For example, 1.9.6b is 1.9.6.1)

    If changes were made to how the Python wrapper works,
    bump ``<python-wrapper-version>`` accordingly.
    If changes only reflect SunVox library changes,
    bump only the patch number.

5.  Update ``CHANGELOG.rst``.


Prep for PyPI and test
======================

::

    $ devpi login <username> --password=<password>
    $ rm -v dist/*
    $ poetry build
    $ devpi upload dist/*
    $ virtualenv testenv
    $ cd testenv
    $ . bin/activate
    $ devpi install sunvox-dll-python
    $ python
    >>> import sunvox
    >>> sunvox.__version__
    '0.3.6.2.1.2.0'
    >>> from sunvox.api import init
    >>> hex(init(None, 44100, 2, 0))
    '0x20102'
    >>> ^D
    $ deactivate
    $ cd ..
    $ rm -rf testenv


Upload to PyPI
==============

::

    $ git tag <full-version-number>
    $ git push --tags
    $ twine upload dist/*
    $ rm -v dist/*
