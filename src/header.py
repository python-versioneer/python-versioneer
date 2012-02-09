#! /usr/bin/python

"""versioneer.py

(like a rocketeer, but for versions)

* https://github.com/warner/python-versioneer
* Brian Warner
* License: Public Domain
* Version: 0.6

This file helps distutils-based projects manage their version number by just
creating version-control tags.

For developers who work from a VCS-generated tree (e.g. 'git clone' etc),
each 'setup.py version', 'setup.py build', 'setup.py sdist' will compute a
version number by asking your version-control tool about the current
checkout. The version number will be written into a generated _version.py
file of your choosing, where it can be included by your __init__.py

For users who work from a VCS-generated tarball (e.g. 'git archive'), it will
compute a version number by looking at the name of the directory created when
te tarball is unpacked. This conventionally includes both the name of the
project and a version number.

For users who work from a tarball built by 'setup.py sdist', it will get a
version number from a previously-generated _version.py file.

As a result, loading code directly from the source tree will not result in a
real version. If you want real versions from VCS trees (where you frequently
update from the upstream repository, or do new development), you will need to
do a 'setup.py version' after each update, and load code from the build/
directory.

You need to provide this code with a few configuration values:

 versionfile_source:
    A project-relative pathname into which the generated version strings
    should be written. This is usually a _version.py next to your project's
    main __init__.py file. If your project uses src/myproject/__init__.py,
    this should be 'src/myproject/_version.py'. This file should be checked
    in to your VCS as usual: the copy created below by 'setup.py
    update_files' will include code that parses expanded VCS keywords in
    generated tarballs. The 'build' and 'sdist' commands will replace it with
    a copy that has just the calculated version string.

 versionfile_build:
    Like versionfile_source, but relative to the build directory instead of
    the source directory. These will differ when your setup.py uses
    'package_dir='. If you have package_dir={'myproject': 'src/myproject'},
    then you will probably have versionfile_build='myproject/_version.py' and
    versionfile_source='src/myproject/_version.py'.

 tag_prefix: a string, like 'PROJECTNAME-', which appears at the start of all
             VCS tags. If your tags look like 'myproject-1.2.0', then you
             should use tag_prefix='myproject-'. If you use unprefixed tags
             like '1.2.0', this should be an empty string.

 parentdir_prefix: a string, frequently the same as tag_prefix, which
                   appears at the start of all unpacked tarball filenames. If
                   your tarball unpacks into 'myproject-1.2.0', this should
                   be 'myproject-'.

To use it:

 1: include this file in the top level of your project
 2: make the following changes to the top of your setup.py:
     import versioneer
     versioneer.versionfile_source = 'src/myproject/_version.py'
     versioneer.versionfile_build = 'myproject/_version.py'
     versioneer.tag_prefix = '' # tags are like 1.2.0
     versioneer.parentdir_prefix = 'myproject-' # dirname like 'myproject-1.2.0'
 3: add the following arguments to the setup() call in your setup.py:
     version=versioneer.get_version(),
     cmdclass=versioneer.get_cmdclass(),
 4: run 'setup.py update_files', which will create _version.py, and will
    append the following to your __init__.py:
     from _version import __version__
 5: modify your MANIFEST.in to include versioneer.py
 6: add both versioneer.py and the generated _version.py to your VCS
"""

import os, sys, re
from distutils.core import Command
from distutils.command.sdist import sdist as _sdist
from distutils.command.build import build as _build

versionfile_source = None
versionfile_build = None
tag_prefix = None
parentdir_prefix = None

