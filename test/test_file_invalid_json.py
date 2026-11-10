import os, tempfile, unittest
from versioneer import NotThisMethod, versions_from_file


class CorruptVersionJson(unittest.TestCase):
    def test_truncated_json(self):
        with tempfile.TemporaryDirectory() as root:
            fn = os.path.join(root, "_version.py")
            with open(fn, "w") as f:
                f.write("version_json = '''\n{truncated\n'''  # END VERSION_JSON\n")
            with self.assertRaises(NotThisMethod):
                versions_from_file(fn)

    def test_not_json_at_all(self):
        with tempfile.TemporaryDirectory() as root:
            fn = os.path.join(root, "_version.py")
            with open(fn, "w") as f:
                f.write("version_json = '''\nnot json at all\n'''  # END VERSION_JSON\n")
            with self.assertRaises(NotThisMethod):
                versions_from_file(fn)
