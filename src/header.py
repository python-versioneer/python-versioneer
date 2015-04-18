
# Version: @VERSIONEER-VERSION@

"""
@README@
"""

import errno
import os
import re
import subprocess
import sys
import json
from distutils.command.build import build as _build
from distutils.command.sdist import sdist as _sdist
from distutils.core import Command

# these configuration settings will be overridden by setup.py after it
# imports us
versionfile_source = None
versionfile_build = None
tag_prefix = None
parentdir_prefix = None
VCS = None

# these dictionaries contain VCS-specific tools
LONG_VERSION_PY = {}
