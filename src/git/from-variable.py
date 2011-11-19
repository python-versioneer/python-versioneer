def versions_from_expanded_variables(variables, tag_prefix):
    refnames = variables["refnames"].strip()
    if refnames.startswith("$Format"):
        return {} # unexpanded, so not in an unpacked git-archive tarball
    refs = set([r.strip() for r in refnames.strip("()").split(",")])
    refs.discard("HEAD") ; refs.discard("master")
    for r in reversed(sorted(refs)):
        if r.startswith(tag_prefix):
            return { "version": r[len(tag_prefix):],
                     "full": variables["full"].strip() }
    return {}

