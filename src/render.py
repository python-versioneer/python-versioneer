
def plus_or_dot(pieces):
    if "+" in pieces.get("closest-tag", ""):
        return "."
    return "+"


def render_pep440(pieces):
    # now build up version string, with post-release "local version
    # identifier". Our goal: TAG[+DISTANCE.gHEX[.dirty]] . Note that if you
    # get a tagged build and then dirty it, you'll get TAG+0.gHEX.dirty

    # exceptions:
    # 1: no tags. git_describe was just HEX. 0+untagged.DISTANCE.gHEX[.dirty]

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
    # TAG[.post.devDISTANCE] . No -dirty

    # exceptions:
    # 1: no tags. 0.post.devDISTANCE

    if pieces["closest-tag"]:
        rendered = pieces["closest-tag"]
        if pieces["distance"]:
            rendered += ".post.dev%d" % pieces["distance"]
    else:
        # exception #1
        rendered = "0.post.dev%d" % pieces["distance"]
    return rendered


def render_pep440_post(pieces):
    # TAG[.postDISTANCE[.dev0]+gHEX] . The ".dev0" means dirty. Note that
    # .dev0 sorts backwards (a dirty tree will appear "older" than the
    # corresponding clean one), but you shouldn't be releasing software with
    # -dirty anyways.

    # exceptions:
    # 1: no tags. 0.postDISTANCE[.dev0]

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
    # TAG[.postDISTANCE[.dev0]] . The ".dev0" means dirty.

    # exceptions:
    # 1: no tags. 0.postDISTANCE[.dev0]

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
    # TAG[-DISTANCE-gHEX][-dirty], like 'git describe --tags --dirty
    # --always'

    # exceptions:
    # 1: no tags. HEX[-dirty]  (note: no 'g' prefix)

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
    # TAG-DISTANCE-gHEX[-dirty], like 'git describe --tags --dirty
    # --always -long'. The distance/hash is unconditional.

    # exceptions:
    # 1: no tags. HEX[-dirty]  (note: no 'g' prefix)

    if pieces["closest-tag"]:
        rendered = pieces["closest-tag"]
        rendered += "-%d-g%s" % (pieces["distance"], pieces["short"])
    else:
        # exception #1
        rendered = pieces["short"]
    if pieces["dirty"]:
        rendered += "-dirty"
    return rendered


def render(pieces, style):
    if pieces["error"]:
        return {"version": "unknown",
                "full-revisionid": pieces.get("long"),
                "dirty": None,
                "error": pieces["error"]}

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
    elif style == "git-describe":
        rendered = render_git_describe(pieces)
    elif style == "git-describe-long":
        rendered = render_git_describe_long(pieces)
    else:
        raise ValueError("unknown style '%s'" % style)

    return {"version": rendered, "full-revisionid": pieces["long"],
            "dirty": pieces["dirty"], "error": None}

