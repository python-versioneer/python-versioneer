from __future__ import print_function
import unittest
import os, tempfile, mock, io

from versioneer import do_setup

base = """
[versioneer]
VCS = git
style = pep440
versionfile_source = src/petmail/xyz.py
versionfile_build = petmail/xyz.py
tag_prefix = v
parentdir_prefix = petmail-
"""

class Setup(unittest.TestCase):
    def populate(self, root, contents):
        with open(os.path.join(root, "setup.cfg"), "w") as f:
            f.write(contents)
        os.mkdir(os.path.join(root, "src"))
        os.mkdir(os.path.join(root, "src", "petmail"))
        with open(os.path.join(root, "src", "petmail", "__init__.py"), "w") as f:
            f.write("")

    def check_contents(self, root, fn, expected):
        with open(os.path.join(root, fn), "r") as f:
            got = f.read()
        self.assertEqual(got, expected)

    def test_init_snippet(self):
        root = tempfile.mkdtemp()
        self.populate(root, base)

        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch("versioneer.get_root", return_value=root):
            with mock.patch("versioneer.run_command") as rc:
                do_setup(stdout, stderr)
                git_add_args, git_add_kwargs = rc.call_args
        self.assertEqual(git_add_args[1][:2], ["add", "--"])
        self.assertEqual(set(git_add_args[1][2:]),
                         set(["MANIFEST.in",
                              "src/petmail/xyz.py",
                              "src/petmail/__init__.py",
                              "versioneer.py",
                              ".gitattributes"]))
        self.check_contents(root, ".gitattributes",
                            "src/petmail/xyz.py export-subst\n")
        self.check_contents(root, "MANIFEST.in",
                            "include versioneer.py\n"
                            "include src/petmail/xyz.py\n")
        self.check_contents(root, os.path.join("src", "petmail", "__init__.py"),
                            "\n"
                            "from ._version import get_versions\n"
                            "__version__ = get_versions()['version']\n"
                            "del get_versions\n"
                            )
        self.assertEqual(stdout.getvalue(),
                         " creating src/petmail/xyz.py\n"
                         " appending to src/petmail/__init__.py\n"
                         " appending 'versioneer.py' to MANIFEST.in\n"
                         " appending versionfile_source ('src/petmail/xyz.py') to MANIFEST.in\n"
                         )
        self.assertEqual(stderr.getvalue(), "")
