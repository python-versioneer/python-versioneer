
from setuptools import setup, Extension
import versioneer
commands = versioneer.get_cmdclass().copy()

extension = Extension('demo.ext',
                      sources=['demo/ext.c'],
)

setup(name="demoappext",
      version=versioneer.get_version(),
      description="Demo",
      url="url",
      author="author",
      author_email="email",
      zip_safe=True,
      packages=["demo"],
      # package_dir={"": "src"},
      entry_points={
          'console_scripts': [ 'rundemo = demo.main:run' ],
          },
      install_requires=["demolib==1.0"],
      cmdclass=commands,
      ext_modules=[extension],
      )
