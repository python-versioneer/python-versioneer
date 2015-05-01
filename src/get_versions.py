import os, sys # --STRIP DURING BUILD
def get_config(): pass # --STRIP DURING BUILD
def versions_from_file(): pass # --STRIP DURING BUILD
def versions_from_parentdir(): pass # --STRIP DURING BUILD
class NotThisMethod(Exception): pass  # --STRIP DURING BUILD

def get_root():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return os.path.dirname(os.path.abspath(sys.argv[0]))


def vcs_function(vcs, suffix):
    return getattr(sys.modules[__name__], '%s_%s' % (vcs, suffix), None)


def get_versions():
    # returns dict with two keys: 'version' and 'full'
    cfg = get_config()
    verbose = cfg.verbose
    assert cfg.versionfile_source is not None, \
        "please set versioneer.versionfile_source"
    assert cfg.tag_prefix is not None, "please set versioneer.tag_prefix"
    assert cfg.parentdir_prefix is not None, \
        "please set versioneer.parentdir_prefix"
    assert cfg.VCS is not None, "please set versioneer.VCS"

    # I am in versioneer.py, which must live at the top of the source tree,
    # which we use to compute the root directory. py2exe/bbfreeze/non-CPython
    # don't have __file__, in which case we fall back to sys.argv[0] (which
    # ought to be the setup.py script). We prefer __file__ since that's more
    # robust in cases where setup.py was invoked in some weird way (e.g. pip)
    root = get_root()
    versionfile_abs = os.path.join(root, cfg.versionfile_source)

    get_keywords_f = vcs_function(cfg.VCS, "get_keywords")
    versions_from_keywords_f = vcs_function(cfg.VCS, "versions_from_keywords")
    versions_from_vcs_f = vcs_function(cfg.VCS, "versions_from_vcs")

    # extract version from first of: _version.py, VCS command (e.g. 'git
    # describe'), parentdir. This is meant to work for developers using a
    # source checkout, for users of a tarball created by 'setup.py sdist',
    # and for users of a tarball/zipball created by 'git archive' or github's
    # download-from-tag feature or the equivalent in other VCSes.

    if get_keywords_f and versions_from_keywords_f:
        try:
            vcs_keywords = get_keywords_f(versionfile_abs)
            ver = versions_from_keywords_f(vcs_keywords, cfg.tag_prefix,
                                           verbose)
            if verbose:
                print("got version from expanded keyword %s" % ver)
            return ver
        except NotThisMethod:
            pass

    try:
        ver = versions_from_file(versionfile_abs)
        if verbose:
            print("got version from file %s %s" % (versionfile_abs, ver))
        return ver
    except NotThisMethod:
        pass

    if versions_from_vcs_f:
        try:
            ver = versions_from_vcs_f(cfg.tag_prefix, root, verbose)
            if verbose:
                print("got version from VCS %s" % ver)
            return ver
        except NotThisMethod:
            pass

    try:
        ver = versions_from_parentdir(cfg.parentdir_prefix, root, verbose)
        if verbose:
            print("got version from parentdir %s" % ver)
        return ver
    except NotThisMethod:
        pass

    if verbose:
        print("unable to compute version")

    return {"version": "0+unknown", "full-revisionid": None,
            "dirty": None, "error": "unable to compute version"}


def get_version():
    return get_versions()["version"]
