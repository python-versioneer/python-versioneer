
def versions_from_parentdir(parentdir_prefix, versionfile_source, verbose=False):
    try:
        here = os.path.abspath(__file__)
        # versionfile_source is the relative path from the top of the source
        # tree (where the .git directory might live) to _version.py, when
        # this is used by the runtime. Invert this to find the root from
        # __file__.
        root = here
        for i in range(len(versionfile_source.split("/"))):
            root = os.path.dirname(root)
    except NameError:
        # try a couple different things to handle py2exe, bbfreeze, and
        # non-CPython implementations which don't do __file__. This code
        # either lives in versioneer.py (used by setup.py) or _version.py
        # (used by the runtime). In the versioneer.py case, sys.argv[0] will
        # be setup.py, in the root of the source tree. In the _version.py
        # case, we have no idea what sys.argv[0] is (some
        # application-specific runner).
        root = os.path.dirname(os.path.abspath(sys.argv[0]))
    # Source tarballs conventionally unpack into a directory that includes
    # both the project name and a version string.
    dirname = os.path.basename(root)
    if not dirname.startswith(parentdir_prefix):
        if verbose:
            print "dirname '%s' doesn't start with prefix '%s'" % \
                  (dirname, parentdir_prefix)
        return None
    return {"version": dirname[len(parentdir_prefix):], "full": ""}
