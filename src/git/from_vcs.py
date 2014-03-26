
import re
import sys
import os.path

def git_versions_from_vcs(tag_prefix, root, verbose=False):
    # this runs 'git' from the root of the source tree. This only gets called
    # if the git-archive 'subst' keywords were *not* expanded, and
    # _version.py hasn't already been rewritten with a short version string,
    # meaning we're inside a checked out source tree.

    if not os.path.exists(os.path.join(root, ".git")):
        if verbose:
            print("no .git in %s" % root)
        return {}

    GITS = ["git"]
    if sys.platform == "win32":
        GITS = ["git.cmd", "git.exe"]

    versions = {}

    full_revisionid = run_command(GITS, ["rev-parse", "HEAD"], cwd=root)
    if full_revisionid is None:
        return {}
    versions["full_revisionid"] = full_revisionid.strip()

    d = run_command(GITS,
                    ["describe", "--tags", "--dirty", "--always", "--long"],
                    cwd=root)
    if d is None:
        return {}
    d = d.strip()
    # "TAG-DIST-gHASH[-dirty]" , where DIST might be "0"
    # or just "HASH[-dirty]" if there are no ancestor tags

    versions["long"] = d

    mo1 = re.search(r"^(.*)-(\d+)-g([0-9a-f]+)(-dirty)?$", d)
    mo2 = re.search(r"^([0-9a-f]+)(-dirty)?$", d)
    if mo1:
        rawtag = mo1.group(1)
        if not rawtag.startswith(tag_prefix):
            if verbose:
                print("tag '%s' doesn't start with prefix '%s'" % (rawtag, tag_prefix))
            return {}
        tag = rawtag[len(tag_prefix):]
        versions["closest_tag"] = tag
        versions["distance"] = int(mo1.group(2))
        versions["short_revisionid"] = mo1.group(3)
        versions["dirty"] = bool(mo1.group(4))
        versions["pep440"] = tag
        if versions["distance"]:
            versions["describe"] = d
            versions["pep440"] += ".post%d" % versions["distance"]
        else:
            versions["describe"] = tag
            if versions["dirty"]:
                versions["describe"] += "-dirty"
        if versions["dirty"]:
            # not strictly correct, as X.dev0 sorts "earlier" than X, but we
            # need some way to distinguish the two. You shouldn't be shipping
            # -dirty code anyways.
            versions["pep440"] += ".dev0"
        versions["default"] = versions["describe"]

    elif mo2: # no ancestor tags
        versions["closest_tag"] = None
        versions["short_revisionid"] = mo2.group(1)
        versions["dirty"] = bool(mo2.group(2))
        # count revisions to compute ["distance"]
        commits = run_command(GITS, ["rev-list", "--count", "HEAD"], cwd=root)
        if commits is None:
            return {}
        versions["distance"] = int(commits.strip())
        versions["pep440"] = "0"
        if versions["distance"]:
            versions["pep440"] += ".post%d" % versions["distance"]
        if versions["dirty"]:
            versions["pep440"] += ".dev0" # same concern as above
        versions["describe"] = d
        versions["default"] = "0-%d-g%s" % (versions["distance"], d)
    else:
        return {}
    versions["dash_dirty"] = "-dirty" if versions["dirty"] else ""
    versions["closest_tag_or_zero"] = versions["closest_tag"] or "0"
    if versions["distance"] == 0:
        versions["dash_distance"] = ""
    else:
        versions["dash_distance"] = "-%d" % versions["distance"]

    return versions

