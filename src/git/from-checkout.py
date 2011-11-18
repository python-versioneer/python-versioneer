import os.path

def version_from_vcs(tag_prefix, source_root=None, verbose=False):
    # this looks for a .git directory inside the source tree, either because
    # someone ran some project-specific entry point (and this code is in
    # _version.py), or because someone ran a setup.py command (and this code
    # is in versioneer.py).

    # For now, we require that somebody tell us how to get to the source
    # tree's root directory, both to find the one .git directory, and to
    # quickly rule out the case where we're running from an extracted
    # .git-less tarball. For the first purpose, in the future, for git (and
    # probably everything except SVN), it's enough to find *any* directory in
    # the source tree.

    if not source_root:
        source_root = os.getcwd()
    if not os.path.isdir(os.path.join(source_root, ".git")):
        if verbose:
            print "This does not appear to be a Git repository."
        return None
    stdout = run_command(["git", "describe",
                          "--tags", "--dirty", "--always"], cwd=source_root)
    if stdout is None:
        return None
    if not stdout.startswith(tag_prefix):
        if verbose:
            print "tag '%s' doesn't start with prefix '%s'" % \
                  (stdout, tag_prefix)
        return None
    return stdout[len(tag_prefix):]

