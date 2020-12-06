import os, tempfile, unittest
from versioneer import versions_from_file

class Parser(unittest.TestCase):
    def test_lf(self):
        with tempfile.TemporaryDirectory() as root:
            fn = os.path.join(root, "_version.py")
            with open(fn, "wb") as f:
                f.write(b"version_json = '''\n{}\n'''  # END VERSION_JSON\n")
            data = versions_from_file(fn)
            self.assertEqual(data, {})

    def test_crlf(self):
        with tempfile.TemporaryDirectory() as root:
            fn = os.path.join(root, "_version.py")
            with open(fn, "wb") as f:
                f.write(b"version_json = '''\r\n{}\r\n'''  # END VERSION_JSON\r\n")
            data = versions_from_file(fn)
            self.assertEqual(data, {})
