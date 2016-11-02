"""
Wrapper for the SunVox DLL.
"""

from setuptools import find_packages, setup

dependencies = []

setup(
    name='sunvox-dll-python',
    version='0.1.1-1.9.2.beta2',
    url='https://github.com/metrasynth/sunvox-dll-python',
    license='MIT',
    author='Matthew Scott',
    author_email='matt@11craft.com',
    description='Wrapper for the SunVox DLL',
    long_description=__doc__,
    packages=find_packages(exclude=['docs', 'tests']),
    package_data={
        'sunvox': [
            'lib/linux/lib_x86/sunvox.so',
            'lib/linux/lib_x86_64/sunvox.so',
            'lib/osx/lib_x86_64/sunvox.dylib',
            'lib/windows/lib_x86/sunvox.dll',
        ],
    },
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=dependencies,
    entry_points={},
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Operating System :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
