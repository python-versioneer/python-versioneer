import re # --STRIP DURING BUILD

def git_versions_from_vcs(tag_prefix, root, verbose=False):
    # this runs 'git' from the root of the source tree. This only gets called
    # if the git-archive 'subst' keywords were *not* expanded, and
    # _version.py hasn't already been rewritten with a short version string,
    # meaning we're inside a checked out source tree.

    if not os.path.exists(os.path.join(root, ".git")):
        if verbose:
            print("no .git in %s" % root)
        return {}  # get_versions() will try next method

    GITS = ["git"]
    if sys.platform == "win32":
        GITS = ["git.cmd", "git.exe"]
    # if there is a tag, this yields TAG-NUM-gHEX[-dirty]
    # if there are no tags, this yields HEX[-dirty] (no NUM)
    describe_out = run_command(GITS, ["describe", "--tags", "--dirty",
                                      "--always", "--long"],
                               cwd=root)
    # --long was added in git-1.5.5
    if describe_out is None:
        return {}  # try next method
    describe_out = describe_out.strip()
    full_out = run_command(GITS, ["rev-parse", "HEAD"], cwd=root)
    if full_out is None:
        return {}
    full_out = full_out.strip()

    pieces = {}
    pieces["full-revisionid"] = full_out
    pieces["short-revisionid"] = full_out[:7] # maybe improved later

    # parse describe_out. It will be like TAG-NUM-gHEX[-dirty] or HEX[-dirty]
    # TAG might have hyphens.
    git_describe = describe_out

    # look for -dirty suffix
    dirty = git_describe.endswith("-dirty")
    pieces["dirty"] = dirty
    if dirty:
        git_describe = git_describe[:git_describe.rindex("-dirty")]

    # now we have TAG-NUM-gHEX or HEX

    if "-" in git_describe:
        # TAG-NUM-gHEX
        mo = re.search(r'^(.+)-(\d+)-g([0-9a-f]+)$', git_describe)
        if not mo:
            # unparseable. Maybe git-describe is misbehaving?
            return {"version": "unknown",
                    "full-revisionid": full_out,
                    "dirty": None,
                    "error": VersioneerError("unable to parse git-describe output: '%s'" % describe_out),
                    }

        # tag
        full_tag = mo.group(1)
        if not full_tag.startswith(tag_prefix):
            if verbose:
                fmt = "tag '%s' doesn't start with prefix '%s'"
                print(fmt % (full_tag, tag_prefix))
            return {"version": "unknown",
                    "full-revisionid": full_out,
                    "dirty": None,
                    "error": VersioneerError("tag '%s' doesn't start with prefix '%s'" % (full_tag, tag_prefix)),
                    }
        pieces["closest-tag"] = full_tag[len(tag_prefix):]

        # distance: number of commits since tag
        pieces["distance"] = int(mo.group(2))

        # commit: short hex revision ID
        pieces["short-revisionid"] = mo.group(3)

    else:
        # HEX: no tags
        pieces["closest-tag"] = None
        count_out = run_command(GITS, ["rev-list", "HEAD", "--count"],
                                cwd=root)
        pieces["distance"] = int(count_out) # total number of commits

    return render(pieces)


def render(pieces): # style=pep440
    # now build up version string, with post-release "local version
    # identifier". Our goal: TAG[+NUM.gHEX[.dirty]] . Note that if you get a
    # tagged build and then dirty it, you'll get TAG+0.gHEX.dirty

    # exceptions:
    # 1: no tags. git_describe was just HEX. 0+untagged.DISTANCE.gHEX[.dirty]

    if pieces["closest-tag"]:
        version = pieces["closest-tag"]
        if pieces["distance"] or pieces["dirty"]:
            version += "+%d.g%s" % (pieces["distance"],
                                    pieces["short-revisionid"])
            if pieces["dirty"]
                version += ".dirty"
    else:
        # exception #1
        version = "0+untagged.%d.g%s" % (pieces["distance"],
                                         pieces["short-revisionid"])
        if pieces["dirty"]
            version += ".dirty"

    return {"version": version, "full": pieces["full-revisionid"],
            dirty: pieces["dirty"], error: None}
