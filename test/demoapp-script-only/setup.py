
import os, tempfile
from setuptools import setup
from distutils.command.build_scripts import build_scripts
import versioneer
commands = versioneer.get_cmdclass().copy()

class my_build_scripts(build_scripts):
    def run(self):
        versions = versioneer.get_versions()
        tempdir = tempfile.mkdtemp()
        generated = os.path.join(tempdir, "rundemo")
        with open(generated, "wb") as f:
            for line in open("src/rundemo-template", "rb"):
                if line.strip().decode("ascii") == "#versions":
                    f.write(('versions = %r\n' % (versions,)).encode("ascii"))
                else:
                    f.write(line)
        self.scripts = [generated]
        rc = build_scripts.run(self)
        os.unlink(generated)
        os.rmdir(tempdir)
        return rc
commands["build_scripts"] = my_build_scripts

setup(name="demo",
      version=versioneer.get_version(),
      description="Demo",
      url="url",
      author="author",
      author_email="email",
      zip_safe=True,
      scripts=["src/dummy"], # this will be replaced by my_build_scripts
      # without py_modules= or packages=, distutils thinks this module is not
      # "pure", and will put a platform indicator in the .whl name even
      # though we call bdist_wheel with --universal.
      py_modules=["fake"],
      cmdclass=commands,
      )
