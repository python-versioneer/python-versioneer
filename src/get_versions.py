import os, sys # --STRIP DURING BUILD
def get_root(): pass # --STRIP DURING BUILD
def get_config_from_root(): pass # --STRIP DURING BUILD
def versions_from_file(): pass # --STRIP DURING BUILD
def versions_from_parentdir(): pass # --STRIP DURING BUILD
def render(): pass # --STRIP DURING BUILD
HANDLERS = {} # --STRIP DURING BUILD
class NotThisMethod(Exception): pass  # --STRIP DURING BUILD

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
    assert handlers, "unrecognized VCS '%s'" % cfg.VCS
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
                print("got version from expanded keyword %s" % ver)
            return override_fallback_or_fail(ver, cfg=cfg, verbose=verbose)
        except NotThisMethod:
            pass

    try:
        ver = versions_from_file(versionfile_abs)
        if verbose:
            print("got version from file %s %s" % (versionfile_abs, ver))
        return override_fallback_or_fail(ver, cfg=cfg, verbose=verbose)
    except NotThisMethod:
        pass

    from_vcs_f = handlers.get("pieces_from_vcs")
    if from_vcs_f:
        try:
            pieces = from_vcs_f(cfg.tag_prefix, root, verbose)
            ver = render(pieces, cfg.style)
            if verbose:
                print("got version from VCS %s" % ver)
            return override_fallback_or_fail(ver, cfg=cfg, verbose=verbose)
        except NotThisMethod:
            pass

    try:
        if cfg.parentdir_prefix:
            ver = versions_from_parentdir(cfg.parentdir_prefix, root, verbose)
            if verbose:
                print("got version from parentdir %s" % ver)
            return override_fallback_or_fail(ver, cfg=cfg, verbose=verbose)
    except NotThisMethod:
        pass

    if verbose:
        print("unable to compute version")

    return override_fallback_or_fail(
        {"version": "0+unknown",
         "full-revisionid": None,
         "error": "unable to compute version",
         "dirty": None,
         "date": None},
        cfg=cfg, verbose=verbose)


def override_fallback_or_fail(versions, cfg, verbose=False):
    """ Finalize versions dictionary with override or fallback, if applicable

    If ``VERSIONEER_OVERRIDE`` is defined in the environment, any version
    string is overridden.

    If the calling method was unable to provide a valid version, and
    ``fallback_version`` is defined in the configuration file, then the fallback
    version will be used.

    If neither case applies and no version was found, resort to ``0+unknown``.

    Modifies dictionary in-place and returns it.
    """
    # If override environment variable is set, set version,
    # and ignore errors or dirty repositories
    override = os.getenv("VERSIONEER_OVERRIDE")
    if override:
        if verbose:
            print(f"got version from environment variable (VERSIONEER_OVERRIDE={override})")
        versions.update({"version": override, "dirty": False, "error": None})

    # If no version information can be found, apply fallback version
    if versions.get("version") in (None, "0+unknown"):
        if cfg.fallback_version:
            if verbose:
                print(f"Falling back to version {cfg.fallback_version}")
            versions.update({"version": cfg.fallback_version, "error": None})

    return versions


def get_version():
    """Get the short version string for this project."""
    return get_versions()["version"]
