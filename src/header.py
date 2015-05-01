
# Version: @VERSIONEER-VERSION@

"""
@README@
"""

from __future__ import print_function
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import errno
import json
import os
import re
import subprocess
import sys
from distutils.command.build import build as _build
from distutils.command.sdist import sdist as _sdist
from distutils.core import Command


class VersioneerConfig:
    pass


def find_setup_cfg():
    try:
        setup_cfg = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "setup.cfg")
    except NameError:
        setup_cfg = "setup.cfg"
    return setup_cfg


def get_config():
    # This might raise EnvironmentError (if setup.cfg is missing), or
    # configparser.NoSectionError (if it lacks a [versioneer] section), or
    # configparser.NoOptionError (if it lacks "VCS="). See the docstring at
    # the top of versioneer.py for instructions on writing your setup.cfg .
    parser = configparser.SafeConfigParser()
    setup_cfg = find_setup_cfg()
    with open(setup_cfg, "r") as f:
        parser.readfp(f)
    VCS = parser.get("versioneer", "VCS")  # mandatory

    def get(parser, name):
        if parser.has_option("versioneer", name):
            return parser.get("versioneer", name)
        return None
    cfg = VersioneerConfig()
    cfg.VCS = VCS
    cfg.versionfile_source = get(parser, "versionfile_source")
    cfg.versionfile_build = get(parser, "versionfile_build")
    cfg.tag_prefix = get(parser, "tag_prefix")
    cfg.parentdir_prefix = get(parser, "parentdir_prefix")
    cfg.verbose = get(parser, "verbose")
    return cfg


# these dictionaries contain VCS-specific tools
LONG_VERSION_PY = {}
