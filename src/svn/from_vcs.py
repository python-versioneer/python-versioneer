
import re
import sys
import os.path

def svn_versions_from_vcs(tag_prefix, root, verbose=False):
    """Return a dictionary of values derived directly from the VCS. This is the
    third attempt to find information by get_versions().
    """

    versions = {}

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

