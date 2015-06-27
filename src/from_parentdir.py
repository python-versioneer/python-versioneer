import os # --STRIP DURING BUILD
class NotThisMethod(Exception): pass  # --STRIP DURING BUILD


def versions_from_parentdir(parentdir_prefix, root, verbose):
    """Try to determine the version from the parent directory name.

    Source tarballs conventionally unpack into a directory that includes
    both the project name and a version string.
    """
    dirname = os.path.basename(root)
    if not dirname.startswith(parentdir_prefix):
        if verbose:
            print("guessing rootdir is '%s', but '%s' doesn't start with "
                  "prefix '%s'" % (root, dirname, parentdir_prefix))
        raise NotThisMethod("rootdir doesn't start with parentdir_prefix")
    return {"version": dirname[len(parentdir_prefix):],
            "full-revisionid": None,
            "dirty": False, "error": None}
