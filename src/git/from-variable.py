def version_from_expanded_variable(s, tag_prefix):
    s = s.strip()
    if "$Format" in s: # unexpanded
        return version_from_vcs(tag_prefix)
    refs = set([r.strip() for r in s.strip("()").split(",")])
    refs.discard("HEAD") ; refs.discard("master")
    for r in reversed(sorted(refs)):
        if r.startswith(tag_prefix):
            return r[len(tag_prefix):]
    return "unknown"

