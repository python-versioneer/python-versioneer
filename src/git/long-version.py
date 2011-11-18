#### START
# This file helps to compute a version number in source trees obtained from
# git-archive tarball (such as those provided by githubs download-from-tag
# feature). Distribution tarballs (build by setup.py sdist) and build
# directories (produced by setup.py build) will contain a much shorter file
# that just contains the computed version number.

# this string will be replaced by git during git-archive
verstr = "%(DOLLAR)sFormat:%%d%(DOLLAR)s"

#### SUBPROCESS_HELPER
#### VERSION_FROM_CHECKOUT
#### VERSION_FROM_VARIABLE
tag_prefix = "%(TAG_PREFIX)s"
def get_version(source_root=None):
    ver = version_from_expanded_variable(verstr.strip(), tag_prefix)
    if not ver:
        ver = version_from_vcs(tag_prefix, source_root)
    if not ver:
        ver = "unknown"
    return ver

#### END

