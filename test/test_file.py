import os, shutil, tempfile, unittest
from versioneer import versions_from_file

class Parser(unittest.TestCase):
    def test_lf(self):
        root = tempfile.mkdtemp()
        try:
            fn = os.path.join(root, "_version.py")
            with open(fn, "wb") as f:
                f.write(b"version_json = '''\n{}\n'''  # END VERSION_JSON\n")
            data = versions_from_file(fn)
            self.assertEqual(data, {})
        finally:
            shutil.rmtree(root)

    def test_cflf(self):
        root = tempfile.mkdtemp()
        try:
            fn = os.path.join(root, "_version.py")
            with open(fn, "wb") as f:
                f.write(b"version_json = '''\r\n{}\r\n'''  # END VERSION_JSON\r\n")
            data = versions_from_file(fn)
            self.assertEqual(data, {})
        finally:
            shutil.rmtree(root)
