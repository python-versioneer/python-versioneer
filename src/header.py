
# Version: @VERSIONEER-VERSION@

"""
@README@
"""

import os, sys, re

from os import path

from distutils.core import Command
from distutils.command.sdist import sdist as _sdist
from distutils.command.build import build as _build

# these configuration settings will be overridden by setup.py after it
# imports us
versionfile_source = None
versionfile_build = None
tag_prefix = None
parentdir_prefix = None
version_string_template = "%(default)s"
vcs_settings = {}

# these dictionaries contain VCS-specific tools
LONG_VERSION_PY = {}

