
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
from pathlib import Path
from typing import Any, Callable, cast, Dict, List, Optional, Tuple, Union
from typing import NoReturn
import functools

have_tomllib = True
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        have_tomllib = False

from .get_versions import VersioneerBadRootError # --STRIP DURING BUILD

class VersioneerConfig:
    """Container for Versioneer configuration parameters."""

    VCS: str
    style: str
    tag_prefix: str
    versionfile_source: str
    versionfile_build: Optional[str]
    parentdir_prefix: Optional[str]
    verbose: Optional[bool]


def get_root() -> str:
    """Get the project root directory.

    We require that all commands are run from the project root, i.e. the
    directory that contains setup.py, setup.cfg, and versioneer.py .
    """
    root = os.path.realpath(os.path.abspath(os.getcwd()))
    setup_py = os.path.join(root, "setup.py")
    pyproject_toml = os.path.join(root, "pyproject.toml")
    versioneer_py = os.path.join(root, "versioneer.py")
    if not (
        os.path.exists(setup_py)
        or os.path.exists(pyproject_toml)
        or os.path.exists(versioneer_py)
    ):
        # allow 'python path/to/setup.py COMMAND'
        root = os.path.dirname(os.path.realpath(os.path.abspath(sys.argv[0])))
        setup_py = os.path.join(root, "setup.py")
        pyproject_toml = os.path.join(root, "pyproject.toml")
        versioneer_py = os.path.join(root, "versioneer.py")
    if not (
        os.path.exists(setup_py)
        or os.path.exists(pyproject_toml)
        or os.path.exists(versioneer_py)
    ):
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


def get_config_from_root(root: str) -> VersioneerConfig:
    """Read the project setup.cfg file to determine Versioneer config."""
    # This might raise OSError (if setup.cfg is missing), or
    # configparser.NoSectionError (if it lacks a [versioneer] section), or
    # configparser.NoOptionError (if it lacks "VCS="). See the docstring at
    # the top of versioneer.py for instructions on writing your setup.cfg .
    root_pth = Path(root)
    pyproject_toml = root_pth / "pyproject.toml"
    setup_cfg = root_pth / "setup.cfg"
    section: Union[Dict[str, Any], configparser.SectionProxy, None] = None
    if pyproject_toml.exists() and have_tomllib:
        try:
            with open(pyproject_toml, 'rb') as fobj:
                pp = tomllib.load(fobj)
            section = pp['tool']['versioneer']
        except (tomllib.TOMLDecodeError, KeyError) as e:
            print(f"Failed to load config from {pyproject_toml}: {e}")
            print("Try to load it from setup.cfg")
    if not section:
        parser = configparser.ConfigParser()
        with open(setup_cfg) as cfg_file:
            parser.read_file(cfg_file)
        parser.get("versioneer", "VCS")  # raise error if missing

        section = parser["versioneer"]

    # `cast`` really shouldn't be used, but its simplest for the
    # common VersioneerConfig users at the moment. We verify against
    # `None` values elsewhere where it matters

    cfg = VersioneerConfig()
    cfg.VCS = section['VCS']
    cfg.style = section.get("style", "")
    cfg.versionfile_source = cast(str, section.get("versionfile_source"))
    cfg.versionfile_build = section.get("versionfile_build")
    cfg.tag_prefix = cast(str, section.get("tag_prefix"))
    if cfg.tag_prefix in ("''", '""', None):
        cfg.tag_prefix = ""
    cfg.parentdir_prefix = section.get("parentdir_prefix")
    if isinstance(section, configparser.SectionProxy):
        # Make sure configparser translates to bool
        cfg.verbose = section.getboolean("verbose")
    else:
        cfg.verbose = section.get("verbose")

    return cfg


class NotThisMethod(Exception):
    """Exception raised if a method is not valid for the current scenario."""


# these dictionaries contain VCS-specific tools
LONG_VERSION_PY: Dict[str, str] = {}
HANDLERS: Dict[str, Dict[str, Callable]] = {}


def register_vcs_handler(vcs: str, method: str) -> Callable:  # decorator
    """Create decorator to mark a method as the handler of a VCS."""
    def decorate(f: Callable) -> Callable:
        """Store f in HANDLERS[vcs][method]."""
        HANDLERS.setdefault(vcs, {})[method] = f
        return f
    return decorate


