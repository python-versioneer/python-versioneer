import os, sys, re # --STRIP DURING BUILD
def register_vcs_handler(*args): # --STRIP DURING BUILD
    def nil(f): # --STRIP DURING BUILD
        return f # --STRIP DURING BUILD
    return nil # --STRIP DURING BUILD
def run_command(): pass # --STRIP DURING BUILD
class NotThisMethod(Exception): pass  # --STRIP DURING BUILD


@register_vcs_handler("git", "pieces_from_vcs")
def git_pieces_from_vcs(tag_prefix, root, verbose, run_command=run_command):
    """Get version from 'git describe' in the root of the source tree.

    This only gets called if the git-archive 'subst' keywords were *not*
    expanded, and _version.py hasn't already been rewritten with a short
    version string, meaning we're inside a checked out source tree.
    """
    if not os.path.exists(os.path.join(root, ".git")):
        if verbose:
            print("no .git in %s" % root)
        raise NotThisMethod("no .git directory")

    GITS = ["git"]
    if sys.platform == "win32":
        GITS = ["git.cmd", "git.exe"]
    # if there is a tag matching tag_prefix, this yields TAG-NUM-gHEX[-dirty]
    # if there isn't one, this yields HEX[-dirty] (no NUM)
    describe_out = run_command(GITS, ["describe", "--tags", "--dirty",
                                      "--always", "--long",
                                      "--match", "%s*" % tag_prefix],
                               cwd=root)
    # --long was added in git-1.5.5
    if describe_out is None:
        raise NotThisMethod("'git describe' failed")
    describe_out = describe_out.strip()
    full_out = run_command(GITS, ["rev-parse", "HEAD"], cwd=root)
    if full_out is None:
        raise NotThisMethod("'git rev-parse' failed")
    full_out = full_out.strip()

    pieces = {}
    pieces["long"] = full_out
    pieces["short"] = full_out[:7]  # maybe improved later
    pieces["error"] = None

    # abbrev-ref available with git >= 1.7
    branch_name = run_command(GITS, ["rev-parse", "--abbrev-ref", "HEAD"],
                              cwd=root).strip()
    if branch_name == 'HEAD':
        branches = run_command(GITS, ["branch", "--list", "--contains"],
                               cwd=root).split('\n')
        branches = [branch[2:] for branch in branches if branch[4:5] != '(']
        if 'master' in branches:
            branch_name = 'master'
        elif not branches:
            branch_name = None
        else:
            # Pick the first branch that is returned. Good or bad.
            branch_name = branches[0]

    pieces['branch'] = branch_name

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
            pieces["error"] = ("unable to parse git-describe output: '%s'"
                               % describe_out)
            return pieces

        # tag
        full_tag = mo.group(1)
        if not full_tag.startswith(tag_prefix):
            if verbose:
                fmt = "tag '%s' doesn't start with prefix '%s'"
                print(fmt % (full_tag, tag_prefix))
            pieces["error"] = ("tag '%s' doesn't start with prefix '%s'"
                               % (full_tag, tag_prefix))
            return pieces
        pieces["closest-tag"] = full_tag[len(tag_prefix):]

        # distance: number of commits since tag
        pieces["distance"] = int(mo.group(2))

        # commit: short hex revision ID
        pieces["short"] = mo.group(3)

    else:
        # HEX: no tags
        pieces["closest-tag"] = None
        count_out = run_command(GITS, ["rev-list", "HEAD", "--count"],
                                cwd=root)
        pieces["distance"] = int(count_out)  # total number of commits

    return pieces

