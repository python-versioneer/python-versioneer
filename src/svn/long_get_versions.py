import os

def get_versions(default={"version": "unknown", "full": ""}, verbose=False):
    """This variation of get_versions() will be used in _version.py ."""

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # We isolated the following operations so that debugging would be more 
    # straightforward.

    ver = svn_versions_from_vcs(tag_prefix, root, verbose)
    if ver:
        return ver

    ver = versions_from_parentdir(parentdir_prefix, root, verbose)
    if ver:
        return ver

    return default
