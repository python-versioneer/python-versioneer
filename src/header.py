
# Version: @VERSIONEER-VERSION@

"""The Versioneer - like a rocketeer, but for versions.

@README@
"""
# pylint:disable=invalid-name,import-outside-toplevel,missing-function-docstring
# pylint:disable=missing-class-docstring,too-many-branches,too-many-statements
# pylint:disable=raise-missing-from,too-many-lines,too-many-locals,import-error
# pylint:disable=too-few-public-methods,redefined-outer-name,consider-using-with
# pylint:disable=attribute-defined-outside-init,too-many-arguments

import configparser
import errno
import json
import os
import re
import subprocess
import sys
from typing import Callable, Dict
import functools

class VersioneerBadRootError(Exception): ... # --STRIP DURING BUILD

class VersioneerConfig:
    """Container for Versioneer configuration parameters."""


def get_root():
    """Get the project root directory.

    We require that all commands are run from the project root, i.e. the
    directory that contains setup.py, setup.cfg, and versioneer.py .
    """
    root = os.path.realpath(os.path.abspath(os.getcwd()))
    setup_py = os.path.join(root, "setup.py")
    versioneer_py = os.path.join(root, "versioneer.py")
    if not (os.path.exists(setup_py) or os.path.exists(versioneer_py)):
        # allow 'python path/to/setup.py COMMAND'
        root = os.path.dirname(os.path.realpath(os.path.abspath(sys.argv[0])))
        setup_py = os.path.join(root, "setup.py")
        versioneer_py = os.path.join(root, "versioneer.py")
    if not (os.path.exists(setup_py) or os.path.exists(versioneer_py)):
        err = ("Versioneer was unable to run the project root directory. "
               "Versioneer requires setup.py to be executed from "
               "its immediate directory (like 'python setup.py COMMAND'), "
               "or in a way that lets it use sys.argv[0] to find the root "
               "(like 'python path/to/setup.py COMMAND').")
        raise VersioneerBadRootError(err)
    try:
        # Certain runtime workflows (setup.py install/develop in a setuptools
        # tree) execute all dependencies in a single python process, so
        # "versioneer" may be imported multiple times, and python's shared
        # module-import table will cache the first one. So we can't use
        # os.path.dirname(__file__), as that will find whichever
        # versioneer.py was first imported, even in later projects.
        my_path = os.path.realpath(os.path.abspath(__file__))
        me_dir = os.path.normcase(os.path.splitext(my_path)[0])
        vsr_dir = os.path.normcase(os.path.splitext(versioneer_py)[0])
        if me_dir != vsr_dir and "VERSIONEER_PEP518" not in globals():
            print("Warning: build in %s is using versioneer.py from %s"
                  % (os.path.dirname(my_path), versioneer_py))
    except NameError:
        pass
    return root


def get_config_from_root(root):
    """Read the project setup.cfg file to determine Versioneer config."""
    # This might raise OSError (if setup.cfg is missing), or
    # configparser.NoSectionError (if it lacks a [versioneer] section), or
    # configparser.NoOptionError (if it lacks "VCS="). See the docstring at
    # the top of versioneer.py for instructions on writing your setup.cfg .
    setup_cfg = os.path.join(root, "setup.cfg")
    parser = configparser.ConfigParser()
    with open(setup_cfg, "r") as cfg_file:
        parser.read_file(cfg_file)
    VCS = parser.get("versioneer", "VCS")  # mandatory

    # Dict-like interface for non-mandatory entries
    section = parser["versioneer"]

    cfg = VersioneerConfig()
    cfg.VCS = VCS
    cfg.style = section.get("style", "")
    cfg.versionfile_source = section.get("versionfile_source")
    cfg.versionfile_build = section.get("versionfile_build")
    cfg.tag_prefix = section.get("tag_prefix")
    if cfg.tag_prefix in ("''", '""', None):
        cfg.tag_prefix = ""
    cfg.parentdir_prefix = section.get("parentdir_prefix")
    cfg.verbose = section.get("verbose")
    return cfg


class NotThisMethod(Exception):
    """Exception raised if a method is not valid for the current scenario."""


# these dictionaries contain VCS-specific tools
LONG_VERSION_PY: Dict[str, str] = {}
HANDLERS: Dict[str, Dict[str, Callable]] = {}


def register_vcs_handler(vcs, method):  # decorator
    """Create decorator to mark a method as the handler of a VCS."""
    def decorate(f):
        """Store f in HANDLERS[vcs][method]."""
        HANDLERS.setdefault(vcs, {})[method] = f
        return f
    return decorate


