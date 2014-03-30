
import re
import sys
import os.path

from xml.etree import ElementTree

def svn_parse_tag_xml(info_xml):
    root = ElementTree.fromstring(info_xml)
    
    release_list = root.find('list')
    releases = {}
    latest_revision = 0
    for release in release_list:
        release = dict([(e.tag, e) for e in release])

        revision = release['commit'].attrib['revision']
        distilled = { 'name': release['name'].text }
        for e in release['commit']:
            distilled[e.tag] = e.text

        releases[revision] = distilled
        latest_revision = max(latest_revision, revision)

    return (releases, latest_revision)

def svn_versions_from_vcs(tag_prefix, root, verbose=False):
    """Return a dictionary of values derived directly from the VCS. This is the
    third attempt to find information by get_versions().
    """

    if not os.path.exists(os.path.join(root, '.svn')):
        if verbose:
            print("no .svn in %s." % root)
        return {}

    current_module = sys.modules[__name__]

    # If we're running from _version.py .
    tag_url = getattr(current_module, 'svn_tag_url', None)
    
    # If we're running from versioneer.py .
    if tag_url is None:
        vcs_settings = getattr(current_module, 'vcs_settings', None)
        if vcs_settings is not None and \
           'svn' in vcs_settings and \
           'tag_url' in vcs_settings['svn']:
            tag_url = vcs_settings['svn']['tag_url']

    if tag_url is None:
        raise ValueError("Please define VCS-specific 'tag_url' setting for "
                         "'svn' within 'versioneer'.")

    print("Retrieving XML tag list.")

    svn_commands = ['svn']
    info_xml = run_command(svn_commands, ['ls', '--xml', tag_url], cwd=root)
# TODO(dustin): This should raise an EnvironmentError upon failure.
    if info_xml is None:
        print("Error accessing Subversion for latest version.")
        return {}

    (releases, latest_revision) = svn_parse_tag_xml(info_xml)

    release_info = releases[latest_revision]
    versions = { 'default': release_info['name'] }

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
