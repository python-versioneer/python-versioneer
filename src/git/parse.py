#### START
# This file helps to compute a version number in source trees obtained from
# git-archive tarball (such as those provided by githubs download-from-tag
# feature). Distribution tarballs (build by setup.py sdist) and build
# directories (produced by setup.py build) will contain a much shorter file
# that just contains the computed version number.

# this string will be replaced by git during git-archive
verstr = "%(DOLLAR)sFormat:%%d%(DOLLAR)s"

#### VERSION_FROM_CHECKOUT

def parse(s):
    tag_prefix = "%(TAG_PREFIX)s"
    if "%(DOLLAR)sFormat" in s: # unexpanded
        return version_from_vcs(tag_prefix)
    refs = set([r.strip() for r in s.strip("()").split(",")])
    refs.discard("HEAD") ; refs.discard("master")
    for r in reversed(sorted(refs)):
        if r.startswith(tag_prefix):
            return r[len(tag_prefix):]
    return "unknown"

__version__ = parse(verstr.strip())
#### END

