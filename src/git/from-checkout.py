import os.path

def version_from_vcs(tag_prefix, verbose=False):
    if not os.path.isdir(".git"):
        if verbose:
            print "This does not appear to be a Git repository."
        return None
    stdout = run_command(["git", "describe",
                          "--tags", "--dirty", "--always"])
    if stdout is None:
        return None
    if not stdout.startswith(tag_prefix):
        if verbose:
            print "tag '%s' doesn't start with prefix '%s'" % \
                  (stdout, tag_prefix)
        return None
    return stdout[len(tag_prefix):]

