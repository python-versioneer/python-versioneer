
def versions_from_parentdir(parentdir_prefix, root, verbose=False):
    """Return a dictionary of values derived from the name of our parent 
    directory (useful when a thoughtfully-named directory is created from an 
    archive). This is the fourth attempt to find information by get_versions().
    """

    # Source tarballs conventionally unpack into a directory that includes
    # both the project name and a version string.
    dirname = os.path.basename(root)
    if not dirname.startswith(parentdir_prefix):
        if verbose:
            print("guessing rootdir is '%s', but '%s' doesn't start with prefix '%s'" %
                  (root, dirname, parentdir_prefix))
        return None
    version = dirname[len(parentdir_prefix):]
    return { "describe": version,
             "long": version,
             "pep440": version,
             }
