import re  # --STRIP DURING BUILD

# Default matches v1.2.x, maint/1.2.x, 1.2.x, 1.x etc.
default_maint_branch_regexp = ".*([0-9]+\.)+x$"


def plus_or_dot(pieces):
    """Return a + if we don't already have one, else return a ."""
    if "+" in pieces.get("closest-tag", ""):
        return "."
    return "+"


def render_pep440(pieces):
    """Build up version string, with post-release "local version identifier".

    Our goal: TAG[+DISTANCE.gHEX[.dirty]] . Note that if you
    get a tagged build and then dirty it, you'll get TAG+0.gHEX.dirty

    Exceptions:
    1: no tags. git_describe was just HEX. 0+untagged.DISTANCE.gHEX[.dirty]
    """
    if pieces["closest-tag"]:
        rendered = pieces["closest-tag"]
        if pieces["distance"] or pieces["dirty"]:
            rendered += plus_or_dot(pieces)
            rendered += "%d.g%s" % (pieces["distance"], pieces["short"])
            if pieces["dirty"]:
                rendered += ".dirty"
    else:
        # exception #1
        rendered = "0+untagged.%d.g%s" % (pieces["distance"],
                                          pieces["short"])
        if pieces["dirty"]:
            rendered += ".dirty"
    return rendered


def render_pep440_pre(pieces):
    """TAG[.post.devDISTANCE] -- No -dirty.

    Exceptions:
    1: no tags. 0.post.devDISTANCE
    """
    if pieces["closest-tag"]:
        rendered = pieces["closest-tag"]
        if pieces["distance"]:
            rendered += ".post.dev%d" % pieces["distance"]
    else:
        # exception #1
        rendered = "0.post.dev%d" % pieces["distance"]
    return rendered


def render_pep440_post(pieces):
    """TAG[.postDISTANCE[.dev0]+gHEX] .

    The ".dev0" means dirty. Note that .dev0 sorts backwards
    (a dirty tree will appear "older" than the corresponding clean one),
    but you shouldn't be releasing software with -dirty anyways.

    Exceptions:
    1: no tags. 0.postDISTANCE[.dev0]
    """
    if pieces["closest-tag"]:
        rendered = pieces["closest-tag"]
        if pieces["distance"] or pieces["dirty"]:
            rendered += ".post%d" % pieces["distance"]
            if pieces["dirty"]:
                rendered += ".dev0"
            rendered += plus_or_dot(pieces)
            rendered += "g%s" % pieces["short"]
    else:
        # exception #1
        rendered = "0.post%d" % pieces["distance"]
        if pieces["dirty"]:
            rendered += ".dev0"
        rendered += "+g%s" % pieces["short"]
    return rendered


def render_pep440_old(pieces):
    """TAG[.postDISTANCE[.dev0]] .

    The ".dev0" means dirty.

    Exceptions:
    1: no tags. 0.postDISTANCE[.dev0]
    """
    if pieces["closest-tag"]:
        rendered = pieces["closest-tag"]
        if pieces["distance"] or pieces["dirty"]:
            rendered += ".post%d" % pieces["distance"]
            if pieces["dirty"]:
                rendered += ".dev0"
    else:
        # exception #1
        rendered = "0.post%d" % pieces["distance"]
        if pieces["dirty"]:
            rendered += ".dev0"
    return rendered


def render_git_describe(pieces):
    """TAG[-DISTANCE-gHEX][-dirty].

    Like 'git describe --tags --dirty --always'.

    Exceptions:
    1: no tags. HEX[-dirty]  (note: no 'g' prefix)
    """
    if pieces["closest-tag"]:
        rendered = pieces["closest-tag"]
        if pieces["distance"]:
            rendered += "-%d-g%s" % (pieces["distance"], pieces["short"])
    else:
        # exception #1
        rendered = pieces["short"]
    if pieces["dirty"]:
        rendered += "-dirty"
    return rendered


def render_git_describe_long(pieces):
    """TAG-DISTANCE-gHEX[-dirty].

    Like 'git describe --tags --dirty --always -long'.
    The distance/hash is unconditional.

    Exceptions:
    1: no tags. HEX[-dirty]  (note: no 'g' prefix)
    """
    if pieces["closest-tag"]:
        rendered = pieces["closest-tag"]
        rendered += "-%d-g%s" % (pieces["distance"], pieces["short"])
    else:
        # exception #1
        rendered = pieces["short"]
    if pieces["dirty"]:
        rendered += "-dirty"
    return rendered


def add_one_to_version(version_string, number_index_to_increment=-1):
    """
    Add one to a version string at the given numeric indices.

    >>> add_one_to_version('v1.2.3')
    'v1.2.4'

    """
    # Break up the tag by number groups (preserving multi-digit
    # numbers as multidigit)
    parts = re.split("([0-9]+)", version_string)

    digit_parts = [(i, part) for i, part in enumerate(parts)
                   if part.isdigit()]

    # Deal with negative indexing.
    increment_at_index = ((number_index_to_increment + len(digit_parts))
                          % len(digit_parts))
    for n_seen, (i, part) in enumerate(digit_parts):
        if n_seen == increment_at_index:
            parts[i] = str(int(part) + 1)
        elif n_seen > increment_at_index:
            parts[i] = '0'
    return ''.join(parts)


def render_pep440_branch_based(pieces):
    # [TAG+1 of minor number][.devDISTANCE][+gHEX]. The git short is
    # included for dirty.

    # exceptions:
    # 1: no tags. 0.0.0.devDISTANCE[+gHEX]

    master = pieces.get('branch') == 'master'
    maint = re.match(default_maint_branch_regexp,
                     pieces.get('branch') or '')

    # If we are on a tag, just pep440-pre it.
    if pieces["closest-tag"] and not (pieces["distance"] or
                                      pieces["dirty"]):
        rendered = pieces["closest-tag"]
    else:
        # Put a default closest-tag in.
        if not pieces["closest-tag"]:
            pieces["closest-tag"] = '0.0.0'

        if pieces["distance"] or pieces["dirty"]:
            if maint:
                rendered = pieces["closest-tag"]
                if pieces["distance"]:
                    rendered += ".post%d" % pieces["distance"]
            else:
                rendered = add_one_to_version(pieces["closest-tag"])
                if pieces["distance"]:
                    rendered += ".dev%d" % pieces["distance"]
                # Put the branch name in if it isn't master nor a
                # maintenance branch.

            if not (master or maint):
                rendered += "+%s" % (pieces.get('branch') or
                                     'unknown_branch')

            if pieces["dirty"]:
                rendered += "+g%s" % pieces["short"]
        else:
            rendered = pieces["closest-tag"]
    return rendered


def render(pieces, style):
    """Render the given version pieces into the requested style."""
    if pieces["error"]:
        return {"version": "unknown",
                "full-revisionid": pieces.get("long"),
                "dirty": None,
                "error": pieces["error"],
                "date": None}

    if not style or style == "default":
        style = "pep440"  # the default

    if style == "pep440":
        rendered = render_pep440(pieces)
    elif style == "pep440-pre":
        rendered = render_pep440_pre(pieces)
    elif style == "pep440-post":
        rendered = render_pep440_post(pieces)
    elif style == "pep440-old":
        rendered = render_pep440_old(pieces)
    elif style == "pep440-branch-based":
        rendered = render_pep440_branch_based(pieces)
    elif style == "git-describe":
        rendered = render_git_describe(pieces)
    elif style == "git-describe-long":
        rendered = render_git_describe_long(pieces)
    else:
        raise ValueError("unknown style '%s'" % style)

    return {"version": rendered, "full-revisionid": pieces["long"],
            "dirty": pieces["dirty"], "error": None,
            "date": pieces.get("date")}
