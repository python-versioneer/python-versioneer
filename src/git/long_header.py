# This file helps to compute a version number in source trees obtained from
# git-archive tarball (such as those provided by githubs download-from-tag
# feature). Distribution tarballs (built by setup.py sdist) and build
# directories (produced by setup.py build) will contain a much shorter file
# that just contains the computed version number.

# This file is released into the public domain. Generated by
# versioneer-@VERSIONEER-VERSION@ (https://github.com/warner/python-versioneer)

import errno
import os
import re
import subprocess
import sys

# these strings will be replaced by git during git-archive
git_refnames = "%(DOLLAR)sFormat:%%d%(DOLLAR)s"
git_full = "%(DOLLAR)sFormat:%%H%(DOLLAR)s"


class VersioneerConfig:
    pass


def get_config():
    # these strings are filled in when 'setup.py versioneer' creates
    # _version.py
    config = VersioneerConfig()
    config.VCS = "git"
    config.tag_prefix = "%(TAG_PREFIX)s"
    config.parentdir_prefix = "%(PARENTDIR_PREFIX)s"
    config.versionfile_source = "%(VERSIONFILE_SOURCE)s"
    config.verbose = False
    return config
