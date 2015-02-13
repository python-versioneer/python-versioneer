import re # --STRIP DURING BUILD

def git_parse_vcs_describe(git_describe, tag_prefix, verbose=False):
    # TAG-NUM-gHEX[-dirty] or HEX[-dirty] . TAG might have hyphens.

    # dirty
    dirty = git_describe.endswith("-dirty")
    if dirty:
        git_describe = git_describe[:git_describe.rindex("-dirty")]
    dirty_suffix = ".dirty" if dirty else ""

    # now we have TAG-NUM-gHEX or HEX

    if "-" not in git_describe:  # just HEX
        return "0+untagged.g"+git_describe+dirty_suffix, dirty

    # just TAG-NUM-gHEX
    mo = re.search(r'^(.+)-(\d+)-g([0-9a-f]+)$', git_describe)
    if not mo:
        # unparseable. Maybe git-describe is misbehaving?
        return "0+unparseable"+dirty_suffix, dirty

    # tag
    full_tag = mo.group(1)
    if not full_tag.startswith(tag_prefix):
        if verbose:
            fmt = "tag '%s' doesn't start with prefix '%s'"
            print(fmt % (full_tag, tag_prefix))
        return None, dirty
    tag = full_tag[len(tag_prefix):]

    # distance: number of commits since tag
    distance = int(mo.group(2))

    # commit: short hex revision ID
    commit = mo.group(3)

    # now build up version string, with post-release "local version
    # identifier". Our goal: TAG[+NUM.gHEX[.dirty]] . Note that if you get a
    # tagged build and then dirty it, you'll get TAG+0.gHEX.dirty . So you
    # can always test version.endswith(".dirty").
    version = tag
    if distance or dirty:
        version += "+%d.g%s" % (distance, commit) + dirty_suffix

    return version, dirty


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
    stdout = run_command(GITS, ["describe", "--tags", "--dirty",
                                "--always", "--long"],
                         cwd=root)
    # --long was added in git-1.5.5
    if stdout is None:
        return {}  # try next method
    version, dirty = git_parse_vcs_describe(stdout, tag_prefix, verbose)

    # build "full", which is FULLHEX[.dirty]
    stdout = run_command(GITS, ["rev-parse", "HEAD"], cwd=root)
    if stdout is None:
        return {}
    full = stdout.strip()
    if dirty:
        full += ".dirty"

    return {"version": version, "full": full}

