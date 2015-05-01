
# Version: @VERSIONEER-VERSION@

"""
@README@
"""

import errno
import json
import os
import re
import subprocess
import sys
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


class VersioneerConfig:
    pass


def get_config():
    cfg = VersioneerConfig()
    cfg.VCS = VCS
    cfg.versionfile_source = versionfile_source
    cfg.versionfile_build = versionfile_build
    cfg.tag_prefix = tag_prefix
    cfg.parentdir_prefix = parentdir_prefix
    cfg.verbose = False
    return cfg


# these dictionaries contain VCS-specific tools
LONG_VERSION_PY = {}
