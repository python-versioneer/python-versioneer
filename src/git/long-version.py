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
__version__ = version_from_expanded_variable(verstr.strip(), tag_prefix)
#### END

