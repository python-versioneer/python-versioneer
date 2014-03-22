
from distutils.core import setup
import versioneer
versioneer.versionfile_source = "src/demo/_version.py"
versioneer.versionfile_build = "demo/_version.py"
versioneer.tag_prefix = "demo-"
versioneer.parentdir_prefix = "demo-"
versioneer.VCS = "@VCS@"
commands = versioneer.get_cmdclass().copy()

setup(name="demo",
      version=versioneer.get_version(),
      description="Demo",
      url="url",
      author="author",
      author_email="email",
      packages=["demo"],
      package_dir={"demo": "src/demo"},
      scripts=["bin/rundemo"],
      cmdclass=commands,
      )
