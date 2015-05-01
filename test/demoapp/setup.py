
from distutils.core import setup
import versioneer
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
