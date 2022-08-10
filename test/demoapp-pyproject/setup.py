from setuptools import setup
import versioneer

setup(
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    zip_safe=True,
    packages=["demo"],
    package_dir={"": "src"},
    scripts=["bin/rundemo"],
)
