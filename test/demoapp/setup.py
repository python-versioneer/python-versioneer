
from setuptools import setup
import versioneer
commands = versioneer.get_cmdclass().copy()

setup(name="demo",
      version=versioneer.get_version(),
      description="Demo",
      url="url",
      author="author",
      author_email="email",
      zip_safe=True,
      packages=["demo"],
      package_dir={"": "src"},
      scripts=["bin/rundemo"],
      cmdclass=commands,
      )
