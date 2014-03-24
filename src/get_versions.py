import sys

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

# TODO(dustin): Fix this comment to be VCS-agnostic.
    # extract version from first of _version.py, 'git describe', parentdir.
    # This is meant to work for developers using a source checkout, for users
    # of a tarball created by 'setup.py sdist', and for users of a
    # tarball/zipball created by 'git archive' or github's download-from-tag
    # feature.

    def vcs_function(vcs, suffix):
        return getattr(sys.modules[__name__], '%s_%s' % (vcs, suffix))

    try:
        get_keywords_f = vcs_function(VCS, 'get_keywords')
        vcs_keywords = get_keywords_f(versionfile_abs)

        versions_from_keywords_f = vcs_function(VCS, 'versions_from_keywords')
        ver = versions_from_keywords_f(vcs_keywords, tag_prefix)
    except AttributeError:
# TODO(dustin): We used to take Non when the VCS was unknown. Now we'll only 
# take None if the VCS-specific function isn't defined. Is this okay?
        ver = None

    if ver:
        if verbose: print("got version from expanded keyword %s" % ver)
        return ver

    ver = versions_from_file(versionfile_abs)
    if ver:
        if verbose: print("got version from file %s %s" % (versionfile_abs,ver))
        return ver

    try:
        versions_from_vcs_f = vcs_function(VCS, 'versions_from_vcs')
        ver = versions_from_vcs_f(tag_prefix, root, verbose)
    except AttributeError:
# TODO(dustin): We used to take Non when the VCS was unknown. Now we'll only 
# take None if the VCS-specific function isn't defined. Is this okay?
        ver = None

    if ver:
        if verbose: print("got version from VCS %s" % ver)
        return ver

    ver = versions_from_parentdir(parentdir_prefix, root, verbose)
    if ver:
        if verbose: print("got version from parentdir %s" % ver)
        return ver

    if verbose: print("got version from default %s" % ver)
    return default

def get_version(verbose=False):
    return get_versions(verbose=verbose)["version"]
