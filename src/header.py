
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

CONFIG_ERROR = """
setup.cfg is missing the necessary Versioneer configuration. You need
a section like:

 [versioneer]
 VCS = git
 versionfile_source = src/myproject/_version.py
 versionfile_build = myproject/_version.py
 tag_prefix = ""
 parentdir_prefix = myproject-

You will also need to edit your setup.py to use the results:

 import versioneer
 setup(version=versioneer.get_version(),
       cmdclass=versioneer.get_cmdclass(), ...)

Please read the docstring in ./versioneer.py for configuration instructions,
edit setup.cfg, and re-run the installer or 'python versioneer.py setup'.
"""

SAMPLE_CONFIG = """
# See the docstring in versioneer.py for instructions. Note that you must
# re-run 'versioneer.py setup' after changing this section, and commit the
# resulting files.

[versioneer]
#VCS = git
#versionfile_source =
#versionfile_build =
#tag_prefix =
#parentdir_prefix =

"""

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
except (EnvironmentError, configparser.NoSectionError,
        configparser.NoOptionError) as e:
    if isinstance(e, (EnvironmentError, configparser.NoSectionError)):
        print("Adding sample versioneer config to setup.cfg", file=sys.stderr)
        with open(setup_cfg, "a") as f:
            f.write(SAMPLE_CONFIG)
    print(CONFIG_ERROR, file=sys.stderr)
    sys.exit(1)


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
