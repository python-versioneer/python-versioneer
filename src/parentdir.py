
def versions_from_parentdir(parentdir_prefix, versionfile_source, verbose=False):
    if IN_LONG_VERSION_PY:
        # We're running from _version.py. If it's from a source tree
        # (execute-in-place), we can work upwards to find the root of the
        # tree, and then check the parent directory for a version string. If
        # it's in an installed application, there's no hope.
        try:
            here = os.path.abspath(__file__)
        except NameError:
            # py2exe/bbfreeze/non-CPython don't have __file__
            return {} # without __file__, we have no hope
        # versionfile_source is the relative path from the top of the source
        # tree to _version.py. Invert this to find the root from __file__.
        root = here
        for i in range(len(versionfile_source.split("/"))):
            root = os.path.dirname(root)
    else:
        # we're running from versioneer.py, which means we're running from
        # the setup.py in a source tree. sys.argv[0] is setup.py in the root.
        here = os.path.abspath(sys.argv[0])
        root = os.path.dirname(here)

    # Source tarballs conventionally unpack into a directory that includes
    # both the project name and a version string.
    dirname = os.path.basename(root)
    if not dirname.startswith(parentdir_prefix):
        if verbose:
            print("guessing rootdir is '%s', but '%s' doesn't start with prefix '%s'" % \
                  (root, dirname, parentdir_prefix))
        return None
    return {"version": dirname[len(parentdir_prefix):], "full": ""}
