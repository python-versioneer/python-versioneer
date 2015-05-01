
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

class VersioneerConfig:
    pass


def get_config():
    parser = configparser.SafeConfigParser()
    try:
        setup_cfg = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "setup.cfg")
    except NameError:
        setup_cfg = "setup.cfg"
    try:
        with open(setup_cfg, "r") as f:
            parser.readfp(f)
        VCS = parser.get("versioneer", "VCS")
    except (EnvironmentError, configparser.NoSectionError,
            configparser.NoOptionError) as e:
        if isinstance(e, (EnvironmentError, configparser.NoSectionError)):
            print("Adding sample versioneer config to setup.cfg",
                  file=sys.stderr)
            with open(setup_cfg, "a") as f:
                f.write(SAMPLE_CONFIG)
        print(CONFIG_ERROR, file=sys.stderr)
        sys.exit(1)

    def get(parser, name):
        if parser.has_option("versioneer", name):
            return parser.get("versioneer", name)
        return None
    config = VersioneerConfig()
    config.VCS = VCS
    config.versionfile_source = get(parser, "versionfile_source")
    config.versionfile_build = get(parser, "versionfile_build")
    config.tag_prefix = get(parser, "tag_prefix")
    config.parentdir_prefix = get(parser, "parentdir_prefix")
    config.verbose = get(parser, "verbose")
    return config


# these dictionaries contain VCS-specific tools
LONG_VERSION_PY = {}
