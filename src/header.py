
# Version: @VERSIONEER-VERSION@

"""
@README@
"""

import os, sys, re
from distutils.core import Command
from distutils.command.sdist import sdist as _sdist
from distutils.command.build import build as _build

# Compatibility with cx_Freeze
try:
  from cx_Freeze.dist import build_exe as _build_exe
except ImportError:
  pass

versionfile_source = None
versionfile_build = None
tag_prefix = None
parentdir_prefix = None

