import os

def get_versions(default={"version": "unknown", "full": ""}, verbose=False):
    """This variation of get_versions() will be used in _version.py ."""

    # I am in _version.py, which lives at ROOT/VERSIONFILE_SOURCE. If we have
    # __file__, we can work backwards from there to the root. Some
    # py2exe/bbfreeze/non-CPython implementations don't do __file__, in which
    # case we can only use expanded keywords.

    keywords = { "refnames": git_refnames,
                 "full_revisionid": git_full_revisionid,
                 "short_revisionid": git_short_revisionid }
    ver = git_versions_from_keywords(keywords, tag_prefix, verbose)
    if ver:
        return ver

    try:
        root = os.path.abspath(__file__)
        # versionfile_source is the relative path from the top of the source
        # tree (where the .git directory might live) to this file. Invert
        # this to find the root from __file__.
        for i in range(len(versionfile_source.split(os.sep))):
            root = os.path.dirname(root)
    except NameError:
        return default

    return (git_versions_from_vcs(tag_prefix, root, verbose)
            or versions_from_parentdir(parentdir_prefix, root, verbose)
            or default)
