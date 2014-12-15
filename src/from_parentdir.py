
def versions_from_parentdir(parentdir_prefix, root, verbose=False):
    # Source tarballs conventionally unpack into a directory that includes
    # both the project name and a version string.
    dirname = os.path.basename(root)
    if not dirname.startswith(parentdir_prefix):
        if verbose:
            print("guessing rootdir is '%s', but '%s' doesn't start with "
                  "prefix '%s'" % (root, dirname, parentdir_prefix))
        return None
    return {"version": dirname[len(parentdir_prefix):], "full": ""}
