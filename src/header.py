
# Version: @VERSIONEER-VERSION@

"""
@README@
"""

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

config = configparser.SafeConfigParser()
try:
    setup_cfg = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             "setup.cfg")
except NameError:
    setup_cfg = "setup.cfg"
try:
    with open(setup_cfg, "r") as f:
        config.readfp(f)
    VCS = config.get("versioneer", "VCS")
except (EnvironmentError,
        configparser.NoSectionError, configparser.NoOptionError):
    raise Exception("Versioneer is now configured with setup.cfg,"
                    " not setup.py. Please see the README or"
                    " versioneer.py for details.")


def get_config_or_none(config, name):
    if config.has_option("versioneer", name):
        return config.get("versioneer", name)
    return None
versionfile_source = get_config_or_none(config, "versionfile_source")
versionfile_build = get_config_or_none(config, "versionfile_build")
tag_prefix = get_config_or_none(config, "tag_prefix")
parentdir_prefix = get_config_or_none(config, "parentdir_prefix")
del setup_cfg, config, get_config_or_none

# these dictionaries contain VCS-specific tools
LONG_VERSION_PY = {}
