import re # --STRIP DURING BUILD

def git_parse_vcs_describe(git_describe, full_out, tag_prefix, verbose=False):
    pieces = {}
    pieces["full-revisionid"] = full_out
    pieces["short-revisionid"] = full_out[:7] # maybe improved later

    # parse git_describe. It will be like TAG-NUM-gHEX[-dirty] or HEX[-dirty]
    # TAG might have hyphens.

    # look for -dirty suffix
    dirty = git_describe.endswith("-dirty")
    pieces["dirty"] = dirty
    if dirty:
        git_describe = git_describe[:git_describe.rindex("-dirty")]

    # now we have TAG-NUM-gHEX or HEX

    if "-" not in git_describe:
        # just HEX: no tags
        pieces["closest-tag"] = None
        pieces["distance"] = 0 # TODO: total number of commits
        # TODO: git-log --oneline|wc -l
        #return "0+untagged.g"+git_describe+dirty_suffix, dirty
        return pieces

    # just TAG-NUM-gHEX
    mo = re.search(r'^(.+)-(\d+)-g([0-9a-f]+)$', git_describe)
    if not mo:
        # unparseable. Maybe git-describe is misbehaving?
        pieces["closest-tag"] = None
        pieces["distance"] = ??
        #return "0+unparseable"+dirty_suffix, dirty
        return pieces

    # tag
    full_tag = mo.group(1)
    if not full_tag.startswith(tag_prefix):
        if verbose:
            fmt = "tag '%s' doesn't start with prefix '%s'"
            print(fmt % (full_tag, tag_prefix))
        pieces["closest-tag"] = None
        pieces["distance"] = ??
        #return None, dirty
    pieces["closest-tag"] = full_tag[len(tag_prefix):]

    # distance: number of commits since tag
    pieces["distance"] = int(mo.group(2))

    # commit: short hex revision ID
    pieces["short-revisionid"] = mo.group(3)

    return pieces

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
    full_out = run_command(GITS, ["rev-parse", "HEAD"], cwd=root)
    if full_out is None:
        return {}
    pieces = git_parse_vcs_describe(describe_out.strip(), full_out.strip(),
                                    tag_prefix, verbose)
    return render(pieces)


def render(pieces): # style=pep440
    # now build up version string, with post-release "local version
    # identifier". Our goal: TAG[+NUM.gHEX[.dirty]] . Note that if you get a
    # tagged build and then dirty it, you'll get TAG+0.gHEX.dirty

    # exceptions:
    # 1: no tags. git_describe was just HEX. 0+untagged.DISTANCE.gHEX[.dirty]
    # 2: unparseable. 0+unparseable[.dirty]
    # 3: tag doesn't start with right prefix. None

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

    full = pieces["full-revisionid"]
