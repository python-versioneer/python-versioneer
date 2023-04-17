import os, sys # --STRIP DURING BUILD
from .header import HANDLERS, get_root, get_config_from_root # --STRIP DURING BUILD
from .header import NotThisMethod # --STRIP DURING BUILD
from .from_file import versions_from_file # --STRIP DURING BUILD
from .from_parentdir import versions_from_parentdir # --STRIP DURING BUILD
from .render import render # --STRIP DURING BUILD

class VersioneerBadRootError(Exception):
    """The project root directory is unknown or missing key files."""


def get_versions(verbose=False):
    """Get the project version from whatever source is available.

    Returns dict with two keys: 'version' and 'full'.
    """
    if "versioneer" in sys.modules:
        # see the discussion in cmdclass.py:get_cmdclass()
        del sys.modules["versioneer"]

    root = get_root()
    cfg = get_config_from_root(root)

    assert cfg.VCS is not None, "please set [versioneer]VCS= in setup.cfg"
    handlers = HANDLERS.get(cfg.VCS)
    assert handlers, f"unrecognized VCS '{cfg.VCS}'"
    verbose = verbose or cfg.verbose
    assert cfg.versionfile_source is not None, \
        "please set versioneer.versionfile_source"
    assert cfg.tag_prefix is not None, "please set versioneer.tag_prefix"

    versionfile_abs = os.path.join(root, cfg.versionfile_source)

    # extract version from first of: _version.py, VCS command (e.g. 'git
    # describe'), parentdir. This is meant to work for developers using a
    # source checkout, for users of a tarball created by 'setup.py sdist',
    # and for users of a tarball/zipball created by 'git archive' or github's
    # download-from-tag feature or the equivalent in other VCSes.

    get_keywords_f = handlers.get("get_keywords")
    from_keywords_f = handlers.get("keywords")
    if get_keywords_f and from_keywords_f:
        try:
            keywords = get_keywords_f(versionfile_abs)
            ver = from_keywords_f(keywords, cfg.tag_prefix, verbose)
            if verbose:
                print(f"got version from expanded keyword {ver}")
            return ver
        except NotThisMethod:
            pass

    try:
        ver = versions_from_file(versionfile_abs)
        if verbose:
            print(f"got version from file {versionfile_abs} {ver}")
        return ver
    except NotThisMethod:
        pass

    from_vcs_f = handlers.get("pieces_from_vcs")
    if from_vcs_f:
        try:
            pieces = from_vcs_f(cfg.tag_prefix, root, verbose)
            ver = render(pieces, cfg.style)
            if verbose:
                print(f"got version from VCS {ver}")
            return ver
        except NotThisMethod:
            pass

    try:
        if cfg.parentdir_prefix:
            ver = versions_from_parentdir(cfg.parentdir_prefix, root, verbose)
            if verbose:
                print(f"got version from parentdir {ver}")
            return ver
    except NotThisMethod:
        pass

    if verbose:
        print("unable to compute version")

    return {"version": "0+unknown", "full-revisionid": None,
            "dirty": None, "error": "unable to compute version",
            "date": None}


def get_version():
    """Get the short version string for this project."""
    return get_versions()["version"]
