
def get_root():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return os.path.dirname(os.path.abspath(sys.argv[0]))

def get_versions(default=DEFAULT, verbose=False):
    # returns dict with two keys: 'version' and 'full'
    assert versionfile_source is not None, "please set versioneer.versionfile_source"
    assert tag_prefix is not None, "please set versioneer.tag_prefix"
    assert parentdir_prefix is not None, "please set versioneer.parentdir_prefix"
    assert VCS is not None, "please set versioneer.VCS"

    # I am in versioneer.py, which must live at the top of the source tree,
    # which we use to compute the root directory. py2exe/bbfreeze/non-CPython
    # don't have __file__, in which case we fall back to sys.argv[0] (which
    # ought to be the setup.py script). We prefer __file__ since that's more
    # robust in cases where setup.py was invoked in some weird way (e.g. pip)
    root = get_root()
    versionfile_abs = os.path.join(root, versionfile_source)

    # extract version from first of _version.py, 'git describe', parentdir.
    # This is meant to work for developers using a source checkout, for users
    # of a tarball created by 'setup.py sdist', and for users of a
    # tarball/zipball created by 'git archive' or github's download-from-tag
    # feature.

    if VCS == "git":
        ver = git_versions_from_keywords(git_get_keywords(versionfile_abs),
                                         tag_prefix)
    else:
        ver = None
    if ver:
        if verbose: print("got version from expanded keyword %s" % ver)
        return ver

    ver = versions_from_file(versionfile_abs)
    if ver:
        if verbose: print("got version from file %s %s" % (versionfile_abs,ver))
        return ver

    if VCS == "git":
        ver = git_versions_from_vcs(tag_prefix, root, verbose)
    else:
        ver = None
    if ver:
        if verbose: print("got version from git %s" % ver)
        return ver

    ver = versions_from_parentdir(parentdir_prefix, root, verbose)
    if ver:
        if verbose: print("got version from parentdir %s" % ver)
        return ver

    if verbose: print("got version from default %s" % ver)
    return default

def get_version(verbose=False):
    return get_versions(verbose=verbose)["version"]
