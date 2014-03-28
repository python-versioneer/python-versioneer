import os

def get_versions(default={"version": "unknown", "full": ""}, verbose=False):
    """This variation of get_versions() will be used in _version.py ."""

    return (git_versions_from_vcs(tag_prefix, root, verbose)
            or versions_from_parentdir(parentdir_prefix, root, verbose)
            or default)
