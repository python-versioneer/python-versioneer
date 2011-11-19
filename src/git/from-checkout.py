import os.path

def versions_from_vcs(tag_prefix, verbose=False):
    # this runs 'git' from the directory that contains this file. That either
    # means someone ran a setup.py command (and this code is in
    # versioneer.py, thus the containing directory is the root of the source
    # tree), or someone ran a project-specific entry point (and this code is
    # in _version.py, thus the containing directory is somewhere deeper in
    # the source tree). This only gets called if the git-archive 'subst'
    # variables were *not* expanded, and _version.py hasn't already been
    # rewritten with a short version string, meaning we're inside a checked
    # out source tree.

    try:
        source_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        # some py2exe/bbfreeze/non-CPython implementations don't do __file__
        return {} # not always correct
    stdout = run_command(["git", "describe",
                          "--tags", "--dirty", "--always"], cwd=source_dir)
    if stdout is None:
        return {}
    if not stdout.startswith(tag_prefix):
        if verbose:
            print "tag '%s' doesn't start with prefix '%s'" % \
                  (stdout, tag_prefix)
        return {}
    tag = stdout[len(tag_prefix):]
    stdout = run_command(["git", "rev-parse", "HEAD"], cwd=source_dir)
    if stdout is None:
        return {}
    full = stdout.strip()
    if tag.endswith("-dirty"):
        full += "-dirty"
    return {"version": tag, "full": full}

