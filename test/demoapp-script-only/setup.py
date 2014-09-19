
import os, tempfile
from distutils.core import setup
from distutils.command.build_scripts import build_scripts
import versioneer
versioneer.versionfile_source = "src/demo/_version.py"
versioneer.versionfile_build = None
versioneer.tag_prefix = "demo-"
versioneer.parentdir_prefix = "demo-"
versioneer.VCS = "@VCS@"
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
      scripts=["src/dummy"], # this will be replaced by my_build_scripts
      cmdclass=commands,
      )
