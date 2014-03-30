
def svn_get_keywords(versionfile_abs):
    """Return a dictionary of values replaced by the VCS, automatically. This 
    is the first attempt to find information by get_versions().
    """

    return {} #{ 'revision': svn_revision }

# TODO(dustin): Needs to be tested.
def svn_versions_from_keywords(keywords, tag_prefix, verbose=False):

    return {} # { 'default': keywords['revision'] }
