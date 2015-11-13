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

    Eexceptions:
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

    replacements = ([' ', '.'], ['(', ''], [')', ''])
    branch_name = pieces.get('branch') or ''
    for old, new in replacements:
        branch_name = branch_name.replace(old, new)
    master = branch_name == 'master'
    maint = re.match(default_maint_branch_regexp, branch_name)

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

            suffix = []
            # Put the branch name in if it isn't master nor a
            # maintenance branch.
            if not (master or maint):
                suffix.append('%s' % (branch_name or 'unknown_branch'))

            if pieces["dirty"]:
                suffix.append('g%s' % pieces["short"])
            if suffix:
                rendered += '+%s' % '_'.join(suffix)
        else:
            rendered = pieces["closest-tag"]
    return rendered


STYLES = {'default': render_pep440,
          'pep440': render_pep440,
          'pep440-pre': render_pep440_pre,
          'pep440-post': render_pep440_post,
          'pep440-old': render_pep440_old,
          'git-describe': render_git_describe,
          'git-describe-long': render_git_describe_long,
          'pep440-old': render_pep440_old,
          'pep440-branch-based': render_pep440_branch_based,
          }


def render(pieces, style):
    """Render the given version pieces into the requested style."""
    if pieces["error"]:
        return {"version": "unknown",
                "full-revisionid": pieces.get("long"),
                "dirty": None,
                "error": pieces["error"]}

    if not style:
        style = 'default'

    renderer = STYLES.get(style)

    if not renderer:
        raise ValueError("unknown style '%s'" % style)

    rendered = renderer(pieces)

    return {"version": rendered, "full-revisionid": pieces["long"],
            "dirty": pieces["dirty"], "error": None}
