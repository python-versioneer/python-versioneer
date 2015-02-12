def git_parse_vcs_describe(git_describe, tag_prefix, verbose=False):
    if not git_describe.startswith(tag_prefix):
        if verbose:
            fmt = "tag '%s' doesn't start with prefix '%s'"
            print(fmt % (git_describe, tag_prefix))
        dirty = bool(git_describe.endswith("-dirty")) # still there
        return None, dirty
    git_version = git_describe[len(tag_prefix):]

    # parse TAG-NUM-gHEX[-dirty], given that TAG might contain "-"

    # dirty
    dirty = git_version.endswith("-dirty")
    if dirty:
        git_version = git_version[:git_version.rindex("-dirty")]

    # commit: short hex revision ID
    idx = git_version.rindex("-g")
    commit = git_version[idx+2:]
    git_version = git_version[:idx]

    # distance: number of commits since tag
    idx = git_version.rindex("-")
    if re.match("^\d+$", git_version[idx+1:]):
        distance = int(git_version[idx+1:])
        git_version = git_version[:idx]

    # tag: stripped of tag_prefix
    tag = git_version

    # now build up version string, with post-release "local version
    # identifier". Our goal: TAG[+NUM.gHEX[-dirty]] . Note that if you get a
    # tagged build and then dirty it, you'll get TAG+0.gHEX-dirty . So you
    # can always test version.endswith("-dirty").
    version = tag
    if distance or dirty:
        version += "+%d.g%s" % (distance, commit)
        if dirty:
            version += "-dirty"

    return version, dirty

def git_versions_from_vcs(tag_prefix, root, verbose=False):
    # this runs 'git' from the root of the source tree. This only gets called
    # if the git-archive 'subst' keywords were *not* expanded, and
    # _version.py hasn't already been rewritten with a short version string,
    # meaning we're inside a checked out source tree.

    if not os.path.exists(os.path.join(root, ".git")):
        if verbose:
            print("no .git in %s" % root)
        return {} # get_versions() will try next method

    GITS = ["git"]
    if sys.platform == "win32":
        GITS = ["git.cmd", "git.exe"]
    # this yields TAG-NUM-gHEX[-dirty]
    stdout = run_command(GITS, ["describe", "--tags", "--dirty",
                                "--always", "--long"],
                         cwd=root)
    # --long was added in git-1.5.5
    if stdout is None:
        return {} # try next method
    version, dirty = git_parse_vcs_describe(stdout, tag_prefix, verbose)

    # build "full", which is FULLHEX[-dirty]
    stdout = run_command(GITS, ["rev-parse", "HEAD"], cwd=root)
    if stdout is None:
        return {}
    full = stdout.strip()
    if dirty:
        full += "-dirty"

    return {"version": version, "full": full}

