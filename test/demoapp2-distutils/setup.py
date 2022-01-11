
from distutils.core import setup
import versioneer
commands = versioneer.get_cmdclass().copy()

setup(name="demoapp2",
      version=versioneer.get_version(),
      description="Demo",
      url="url",
      author="author",
      author_email="email",
      packages=["demo"],
      package_dir={"": "src"},
      scripts=["bin/rundemo"],
      cmdclass=commands,
      )
