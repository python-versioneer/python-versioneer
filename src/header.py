"""versioneer.py

(like a rocketeer, but for versions)

* https://github.com/warner/python-versioneer
* Brian Warner
* License: Public Domain
* Version: @VERSIONEER@

This file helps distutils-based projects manage their version number by just
creating version-control tags. Stop manually updating a 'version.py'. Once
you install versioneer into your source tree, then:

* running code from a source checkout (e.g. "git clone") will learn a version
  string by asking your version-control tool about the current checkout ("git
  status" and "git describe")

* running "setup.py version" will report this deduced version string

* creating a distribution tarball ("setup.py sdist") embeds the version in
  the generated file, so downstream users do not need VCS tools or
  versioneer.

* VCS-generated tarballs ("git archive") use $Revision$ annotations to embed
  the version string in the generated file, again allowing downstream users
  to avoid the need for anything special.

* as a last-ditch effort, running code from a non-annotated unpacked tarball
  will still get the right version if the directory name follows the usual
  "$projectname-$version" convention.

This reduces the release engineer's workflow down to "git tag; git push",
followed by an optional tarball-generation step (like "setup.py sdist
upload").

Versioneer works by adding a special "_version.py" file into your source
tree, where your __init__.py can import it. This _version.py knows how to
dynamically ask the VCS tool for version information at import time. However,
when you use "setup.py build" or "setup.py sdist", _version.py in the new
copy is replaced by a small static file that contains just the generated
version data.

"_version.py" also contains $Revision$ markers, and the installation process
marks _version.py to have this marker rewritten with a tag name during the
"git archive" command. As a result, generated tarballs will contain enough
information to get the proper version.


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
    modify your __init__.py to define __version__ (by calling a function
    from _version.py)
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

