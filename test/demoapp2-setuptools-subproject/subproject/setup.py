
from setuptools import setup
import versioneer
commands = versioneer.get_cmdclass().copy()

setup(name="demoapp2",
      version=versioneer.get_version(),
      description="Demo",
      url="url",
      author="author",
      author_email="email",
      zip_safe=True,
      packages=["demo"],
      package_dir={"": "src"},
      entry_points={
          'console_scripts': [ 'rundemo = demo.main:run' ],
          },
      install_requires=["demolib==1.0"],
      cmdclass=commands,
      )
