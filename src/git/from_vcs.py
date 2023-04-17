import sys  # --STRIP DURING BUILD
import re  # --STRIP DURING BUILD
import os  # --STRIP DURING BUILD
import functools  # --STRIP DURING BUILD
from typing import Any, Callable, Dict  # --STRIP DURING BUILD
from .long_header import NotThisMethod, register_vcs_handler  # --STRIP DURING BUILD
from subprocess_helper import run_command  # --STRIP DURING BUILD
  # --STRIP DURING BUILD
  # --STRIP DURING BUILD
@register_vcs_handler("git", "pieces_from_vcs")
def git_pieces_from_vcs(
    tag_prefix: str,
    root: str,
    verbose: bool,
    runner: Callable = run_command
) -> Dict[str, Any]:
    """Get version from 'git describe' in the root of the source tree.

    This only gets called if the git-archive 'subst' keywords were *not*
    expanded, and _version.py hasn't already been rewritten with a short
    version string, meaning we're inside a checked out source tree.
    """
    GITS = ["git"]
    if sys.platform == "win32":
        GITS = ["git.cmd", "git.exe"]

    # GIT_DIR can interfere with correct operation of Versioneer.
    # It may be intended to be passed to the Versioneer-versioned project,
    # but that should not change where we get our version from.
    env = os.environ.copy()
    env.pop("GIT_DIR", None)
    runner = functools.partial(runner, env=env)

    _, rc = runner(GITS, ["rev-parse", "--git-dir"], cwd=root,
                   hide_stderr=not verbose)
    if rc != 0:
        if verbose:
            print(f"Directory {root} not under git control")
        raise NotThisMethod("'git rev-parse --git-dir' returned error")

    # if there is a tag matching tag_prefix, this yields TAG-NUM-gHEX[-dirty]
    # if there isn't one, this yields HEX[-dirty] (no NUM)
    describe_out, rc = runner(GITS, [
        "describe", "--tags", "--dirty", "--always", "--long",
        "--match", f"{tag_prefix}[[:digit:]]*"
    ], cwd=root)
    # --long was added in git-1.5.5
    if describe_out is None:
        raise NotThisMethod("'git describe' failed")
    describe_out = describe_out.strip()
    full_out, rc = runner(GITS, ["rev-parse", "HEAD"], cwd=root)
    if full_out is None:
        raise NotThisMethod("'git rev-parse' failed")
    full_out = full_out.strip()

    pieces: Dict[str, Any] = {}
    pieces["long"] = full_out
    pieces["short"] = full_out[:7]  # maybe improved later
    pieces["error"] = None

    branch_name, rc = runner(GITS, ["rev-parse", "--abbrev-ref", "HEAD"],
                             cwd=root)
    # --abbrev-ref was added in git-1.6.3
    if rc != 0 or branch_name is None:
        raise NotThisMethod("'git rev-parse --abbrev-ref' returned error")
    branch_name = branch_name.strip()

    if branch_name == "HEAD":
        # If we aren't exactly on a branch, pick a branch which represents
        # the current commit. If all else fails, we are on a branchless
        # commit.
        branches, rc = runner(GITS, ["branch", "--contains"], cwd=root)
        # --contains was added in git-1.5.4
        if rc != 0 or branches is None:
            raise NotThisMethod("'git branch --contains' returned error")
        branches = branches.split("\n")

        # Remove the first line if we're running detached
        if "(" in branches[0]:
            branches.pop(0)

        # Strip off the leading "* " from the list of branches.
        branches = [branch[2:] for branch in branches]
        if "master" in branches:
            branch_name = "master"
        elif not branches:
            branch_name = None
        else:
            # Pick the first branch that is returned. Good or bad.
            branch_name = branches[0]

    pieces["branch"] = branch_name

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
            # unparsable. Maybe git-describe is misbehaving?
            pieces["error"] = f"unable to parse git-describe output: '{describe_out}'"
            return pieces

        # tag
        full_tag = mo.group(1)
        if not full_tag.startswith(tag_prefix):
            error = f"tag '{full_tag}' doesn't start with prefix '{tag_prefix}'"
            if verbose:
                print(error)
            pieces["error"] = error
            return pieces
        pieces["closest-tag"] = full_tag[len(tag_prefix):]

        # distance: number of commits since tag
        pieces["distance"] = int(mo.group(2))

        # commit: short hex revision ID
        pieces["short"] = mo.group(3)

    else:
        # HEX: no tags
        pieces["closest-tag"] = None
        out, rc = runner(GITS, ["rev-list", "HEAD", "--left-right"], cwd=root)
        pieces["distance"] = len(out.split())  # total number of commits

    # commit date: see ISO-8601 comment in git_versions_from_keywords()
    date = runner(GITS, ["show", "-s", "--format=%ci", "HEAD"], cwd=root)[0].strip()
    # Use only the last line.  Previous lines may contain GPG signature
    # information.
    date = date.splitlines()[-1]
    pieces["date"] = date.strip().replace(" ", "T", 1).replace(" ", "", 1)

    return pieces

