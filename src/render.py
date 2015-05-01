
def render(pieces):  # style=pep440
    # now build up version string, with post-release "local version
    # identifier". Our goal: TAG[+NUM.gHEX[.dirty]] . Note that if you get a
    # tagged build and then dirty it, you'll get TAG+0.gHEX.dirty

    # exceptions:
    # 1: no tags. git_describe was just HEX. 0+untagged.DISTANCE.gHEX[.dirty]

    if pieces["closest-tag"]:
        version = pieces["closest-tag"]
        if pieces["distance"] or pieces["dirty"]:
            version += "+%d.g%s" % (pieces["distance"], pieces["short"])
            if pieces["dirty"]:
                version += ".dirty"
    else:
        # exception #1
        version = "0+untagged.%d.g%s" % (pieces["distance"],
                                         pieces["short"])
        if pieces["dirty"]:
            version += ".dirty"

    return {"version": version, "full-revisionid": pieces["long"],
            "dirty": pieces["dirty"], "error": None}

