
# Version: @VERSIONEER-VERSION@

"""
@README@
"""

import os, sys, re, subprocess, errno
from distutils.core import Command
from distutils.command.sdist import sdist as _sdist
from distutils.command.build import build as _build

# these configuration settings will be overridden by setup.py after it
# imports us
versionfile_source = None
versionfile_build = None
tag_prefix = None
parentdir_prefix = None
VCS = None

# these dictionaries contain VCS-specific tools
LONG_VERSION_PY = {}
