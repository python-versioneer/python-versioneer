
import re

def git_get_keywords(versionfile_abs):
    """Return a dictionary of values replaced by the VCS, automatically. This 
    is the first attempt to find information by get_versions().
    """

    # the code embedded in _version.py can just fetch the value of these
    # keywords. When used from setup.py, we don't want to import _version.py,
    # so we do it with a regexp instead. This function is not used from
    # _version.py.
    keywords = {}
    try:
        with open(versionfile_abs) as f:
            for line in f.readlines():
                if line.strip().startswith("git_refnames ="):
                    mo = re.search(r'=\s*"(.*)"', line)
                    if mo:
                        keywords["refnames"] = mo.group(1)
                if line.strip().startswith("git_full_revisionid ="):
                    mo = re.search(r'=\s*"(.*)"', line)
                    if mo:
                        keywords["full_revisionid"] = mo.group(1)
                if line.strip().startswith("git_short_revisionid ="):
                    mo = re.search(r'=\s*"(.*)"', line)
                    if mo:
                        keywords["short_revisionid"] = mo.group(1)
    except EnvironmentError:
        pass
    return keywords

def git_versions_from_keywords(keywords, tag_prefix, verbose=False):
    if not keywords:
        return {} # keyword-finding function failed to find keywords
    refnames = keywords["refnames"].strip()
    if refnames.startswith("$Format"):
        if verbose:
            print("keywords are unexpanded, not using")
        return {} # unexpanded, so not in an unpacked git-archive tarball
    refs = set([r.strip() for r in refnames.strip("()").split(",")])
    # starting in git-1.8.3, tags are listed as "tag: foo-1.0" instead of
    # just "foo-1.0". If we see a "tag: " prefix, prefer those.
    TAG = "tag: "
    tags = set([r[len(TAG):] for r in refs if r.startswith(TAG)])
    if not tags:
        # Either we're using git < 1.8.3, or there really are no tags. We use
        # a heuristic: assume all version tags have a digit. The old git %d
        # expansion behaves like git log --decorate=short and strips out the
        # refs/heads/ and refs/tags/ prefixes that would let us distinguish
        # between branches and tags. By ignoring refnames without digits, we
        # filter out many common branch names like "release" and
        # "stabilization", as well as "HEAD" and "master".
        tags = set([r for r in refs if re.search(r'\d', r)])
        if verbose:
            print("discarding '%s', no digits" % ",".join(refs-tags))
    if verbose:
        print("likely tags: %s" % ",".join(sorted(tags)))
    shortest_tag = None
    for ref in sorted(tags):
        # sorting will prefer e.g. "2.0" over "2.0rc1"
        if ref.startswith(tag_prefix):
            shortest_tag = ref[len(tag_prefix):]
            if verbose:
                print("picking %s" % shortest_tag)
            break
    versions = {
        "full_revisionid": keywords["full_revisionid"].strip(),
        "short_revisionid": keywords["short_revisionid"].strip(),
        "dirty": False, "dash_dirty": "",
        "closest_tag": shortest_tag,
        "closest_tag_or_zero": shortest_tag or "0",
        # "distance" is not provided: cannot deduce from keyword expansion
        }
    if not shortest_tag and verbose:
        print("no suitable tags, using full revision id")
    composite = shortest_tag or versions["full_revisionid"]
    versions["describe"] = composite
    versions["long"] = composite
    versions["default"] = composite
    versions["pep440"] = composite
    return versions
