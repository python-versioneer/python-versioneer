
import re
import sys
import os.path

def svn_versions_from_vcs(tag_prefix, root, verbose=False):
    """Return a dictionary of values derived directly from the VCS. This is the
    third attempt to find information by get_versions().
    """

    if not os.path.exists(os.path.join(root, '.svn')):
        if verbose:
            print("no .svn in %s." % root)
        return {}

    svn_commands = ['svn']

    info_raw = run_command(svn_commands, ['info'], cwd=root)
# TODO(dustin): This should raise an EnvironmentError upon failure.
    if info_raw is None:
        print("Error accessing Subversion.")
        return {}

    rows = info_raw.split("\n")
    info = {}
    for row in rows:
        pivot = row.index(': ')
        info[row[:pivot].lower()] = row[pivot + 2:]

    versions = { 'default': info['revision'] }

# Examples of strings returned by Git.
#
#    versions["closest_tag"]
#    versions["distance"]
#    versions["short_revisionid"]
#    versions["dirty"]
#    versions["pep440"]
#    versions["describe"]
#    versions["default"]
#    versions["dash_dirty"]
#    versions["closest_tag_or_zero"]
#    versions["dash_distance"]

    return versions

