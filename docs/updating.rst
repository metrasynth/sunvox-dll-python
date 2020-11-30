==========================
Updating sunvox-dll-python
==========================

This is a loose collection of notes for maintaining releases of sunvox-dll-python
and uploading them to the Python Package Index (PyPI).


After new releases of SunVox library
====================================

1.  Copy libraries from the SunVox library distribution, e.g.:
    ``cd sunvox/lib; ./copy-libs.sh ../../../sunvox_dll``

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

1.  ``rm -v dist/*; python setup.py sdist bdist_wheel``.

2.  Create a new virtualenv: ``virtualenv tmp; cd tmp``.

3.  ``bin/pip install ../dist/sunvox_dll_python-….whl`` (use actual filename).

4.  ``bin/pip install numpy scipy tqdm``

5.  ``bin/python -m sunvox.tools.export …``

6.  ``cd ..; rm -rf tmp``


Upload to PyPI
==============

1.  ``git tag <full-version-number>``

2.  ``git push --tags``

3.  ``twine upload dist/*``
