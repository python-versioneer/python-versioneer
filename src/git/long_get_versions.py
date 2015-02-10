
def git2pep440(ver_str):
    """Convert Git version such as "1.2.1-17-gb92cc8d" to PEP440 compliant
    version such as "1.2.1+17.gb92cc8d".
    """
    try:
        tag, suffix = ver_str.split('-', 1)
        suffix = '.'.join(suffix.split('-'))
        return "{0}+{1}".format(tag, suffix)
    except ValueError:
        return ver_str


def rep_by_pep440(ver):
    ver["version"] = git2pep440(ver["version"])
    return ver


def get_versions(default={"version": "unknown", "full": ""}, verbose=False):
    # I am in _version.py, which lives at ROOT/VERSIONFILE_SOURCE. If we have
    # __file__, we can work backwards from there to the root. Some
    # py2exe/bbfreeze/non-CPython implementations don't do __file__, in which
    # case we can only use expanded keywords.

    keywords = {"refnames": git_refnames, "full": git_full}
    ver = git_versions_from_keywords(keywords, tag_prefix, verbose)
    if ver:
        return rep_by_pep440(ver)

    try:
        root = os.path.realpath(__file__)
        # versionfile_source is the relative path from the top of the source
        # tree (where the .git directory might live) to this file. Invert
        # this to find the root from __file__.
        for i in range(len(versionfile_source.split('/'))):
            root = os.path.dirname(root)
    except NameError:
        return default

    return rep_by_pep440(git_versions_from_vcs(tag_prefix, root, verbose)
                         or versions_from_parentdir(parentdir_prefix,
                                                    root, verbose)
                         or default)
