import unittest
import os, tempfile, shutil
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from versioneer import get_config_from_root

base = """
[versioneer]
VCS = git
style = pep440
versionfile_source = petmail/_version.py
versionfile_build = petmail/_version.py
tag_prefix = v
parentdir_prefix = petmail-
"""

class Parser(unittest.TestCase):
    def parse(self, contents):
        root = tempfile.mkdtemp()
        try:
            with open(os.path.join(root, "setup.cfg"), "w") as f:
                f.write(contents)
            return get_config_from_root(root)
        finally:
            shutil.rmtree(root)

    def test_base(self):
        cfg = self.parse(base)
        self.assertEqual(cfg.VCS, "git")
        self.assertEqual(cfg.style, "pep440")
        self.assertEqual(cfg.versionfile_source, "petmail/_version.py")
        self.assertEqual(cfg.versionfile_build, "petmail/_version.py")
        self.assertEqual(cfg.tag_prefix, "v")
        self.assertEqual(cfg.parentdir_prefix, "petmail-")
        self.assertEqual(cfg.verbose, None)

    def test_empty(self):
        self.assertRaises(configparser.NoSectionError,
                          self.parse, "")

    def test_mostly_empty(self):
        self.assertRaises(configparser.NoOptionError,
                          self.parse, "[versioneer]\n")

    def test_minimal(self):
        cfg = self.parse("[versioneer]\nvcs = git\n")
        self.assertEqual(cfg.VCS, "git")
        self.assertEqual(cfg.style, "")
        self.assertEqual(cfg.versionfile_source, None)
        self.assertEqual(cfg.versionfile_build, None)
        self.assertEqual(cfg.tag_prefix, None)
        self.assertEqual(cfg.parentdir_prefix, None)
        self.assertEqual(cfg.verbose, None)

    def test_empty_tag_prefixes(self):
        # all three of these should give an empty tag_prefix:
        #  tag_prefix =
        #  tag_prefix = ''
        #  tag_prefix = ""
        cfg = self.parse("[versioneer]\nVCS=git\ntag_prefix=")
        self.assertEqual(cfg.tag_prefix, "")
        cfg = self.parse("[versioneer]\nVCS=git\ntag_prefix=''")
        self.assertEqual(cfg.tag_prefix, "")
        cfg = self.parse("[versioneer]\nVCS=git\ntag_prefix=\"\"")
        self.assertEqual(cfg.tag_prefix, "")
