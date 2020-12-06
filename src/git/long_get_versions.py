import os # --STRIP DURING BUILD
def get_config(): pass # --STRIP DURING BUILD
def get_keywords(): pass # --STRIP DURING BUILD
def git_versions_from_keywords(): pass # --STRIP DURING BUILD
def git_pieces_from_vcs(): pass # --STRIP DURING BUILD
def versions_from_parentdir(): pass # --STRIP DURING BUILD
class NotThisMethod(Exception): pass  # --STRIP DURING BUILD
def override_fallback_or_fail(): pass # --STRIP DURING BUILD
def render(): pass # --STRIP DURING BUILD

def get_versions():
    """Get version information or return default if unable to do so."""
    # I am in _version.py, which lives at ROOT/VERSIONFILE_SOURCE. If we have
    # __file__, we can work backwards from there to the root. Some
    # py2exe/bbfreeze/non-CPython implementations don't do __file__, in which
    # case we can only use expanded keywords.

    cfg = get_config()
    verbose = cfg.verbose

    try:
        return override_fallback_or_fail(
            git_versions_from_keywords(get_keywords(), cfg.tag_prefix, verbose),
            cfg=cfg, verbose=verbose)
    except NotThisMethod:
        pass

    try:
        root = os.path.realpath(__file__)
        # versionfile_source is the relative path from the top of the source
        # tree (where the .git directory might live) to this file. Invert
        # this to find the root from __file__.
        for i in cfg.versionfile_source.split('/'):
            root = os.path.dirname(root)
    except NameError:
        return override_fallback_or_fail(
            {"version": "0+unknown", "full-revisionid": None,
             "dirty": None,
             "error": "unable to find root of source tree",
             "date": None},
            cfg=cfg, verbose=verbose)

    try:
        pieces = git_pieces_from_vcs(cfg.tag_prefix, root, verbose)
        return override_fallback_or_fail(
            render(pieces, cfg.style),
            cfg=cfg, verbose=verbose)
    except NotThisMethod:
        pass

    try:
        if cfg.parentdir_prefix:
            return override_fallback_or_fail(
                versions_from_parentdir(cfg.parentdir_prefix, root, verbose),
                cfg=cfg, verbose=verbose)
    except NotThisMethod:
        pass

    return override_fallback_or_fail(
        {"version": "0+unknown",
         "full-revisionid": None,
         "error": "unable to compute version",
         "dirty": None,
         "date": None},
        cfg=cfg, verbose=verbose)
