
def versions_from_parentdir(parentdir_prefix, root, verbose=False):
    # Source tarballs conventionally unpack into a directory that includes
    # both the project name and a version string. We will also support searching
    # up two directory levels for an appropriately named parent directory
    rootdirs = []

    for i in range(3):
        dirname = os.path.basename(root)
        if dirname.startswith(parentdir_prefix):
            return {"version": dirname[len(parentdir_prefix):], "full": ""}
        else:
            rootdirs.append(root)
            root = os.path.dirname(root) # up a level
    if verbose:
        print("Tried directories %s but none started with prefix %s" %
            (str(rootdirs), parentdir_prefix) )
    return None
