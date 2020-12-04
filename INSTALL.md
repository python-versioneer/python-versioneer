# Installation

First, decide on values for the following configuration variables:

* `VCS`: the version control system you use. Currently accepts "git".

* `style`: the style of version string to be produced.
  See [Styles](./README.md#styles) for details.
  Defaults to "pep440", which looks like `TAG[+DISTANCE.gSHORTHASH[.dirty]]`.

* `versionfile_source`:

  A project-relative pathname into which the generated version strings should
  be written. This is usually a `_version.py` next to your project's main
  `__init__.py` file, so it can be imported at runtime. If your project uses
  `src/myproject/__init__.py`, this should be `src/myproject/_version.py`.
  This file should be checked in to your VCS as usual: the copy created below
  by `versioneer install` will include code that parses expanded VCS
  keywords in generated tarballs. The 'build' and 'sdist' commands will
  replace it with a copy that has just the calculated version string.

  This must be set even if your project does not have any modules (and will
  therefore never import `_version.py`), since "setup.py sdist" -based trees
  still need somewhere to record the pre-calculated version strings. Anywhere
  in the source tree should do. If there is a `__init__.py` next to your
  `_version.py`, the `versioneer install` command (described below)
  will append some `__version__`-setting assignments, if they aren't already
  present.

* `versionfile_build`:

  Like `versionfile_source`, but relative to the build directory instead of
  the source directory. These will differ when your setup.py uses
  'package_dir='. If you have `package_dir={'myproject': 'src/myproject'}`,
  then you will probably have `versionfile_build='myproject/_version.py'` and
  `versionfile_source='src/myproject/_version.py'`.

  If this is set to None, then `setup.py build` will not attempt to rewrite
  any `_version.py` in the built tree. If your project does not have any
  libraries (e.g. if it only builds a script), then you should use
  `versionfile_build = None`. To actually use the computed version string,
  your `setup.py` will need to override `distutils.command.build_scripts`
  with a subclass that explicitly inserts a copy of
  `versioneer.get_version()` into your script file. See
  `test/demoapp-script-only/setup.py` for an example.

* `tag_prefix`:

  a string, like 'PROJECTNAME-', which appears at the start of all VCS tags.
  If your tags look like 'myproject-1.2.0', then you should use
  tag_prefix='myproject-'. If you use unprefixed tags like '1.2.0', this
  should be an empty string, using either `tag_prefix=` or `tag_prefix=''`.

* `parentdir_prefix`:

  a optional string, frequently the same as tag_prefix, which appears at the
  start of all unpacked tarball filenames. If your tarball unpacks into
  'myproject-1.2.0', this should be 'myproject-'. To disable this feature,
  just omit the field from your `setup.cfg`.

This tool provides one script, named `versioneer`. That script has one mode,
"install", which writes a copy of `versioneer.py` into the current directory
and runs `versioneer.py setup` to finish the installation.

To versioneer-enable your project:

* 1: Install versioneer with `pip install versioneer`

* 2: Modify your `setup.cfg`, adding a section named `[versioneer]` and
  populating it with the configuration values you decided earlier (note that
  the option names are not case-sensitive):

  ````
  [versioneer]
  VCS = git
  style = pep440
  versionfile_source = src/myproject/_version.py
  versionfile_build = myproject/_version.py
  tag_prefix =
  parentdir_prefix = myproject-
  ````

* 3: Run `versioneer install`. This will do the following:

  * copy `versioneer.py` into the top of your source tree
  * create `_version.py` in the right place (`versionfile_source`)
  * modify your `__init__.py` (if one exists next to `_version.py`) to define
    `__version__` (by calling a function from `_version.py`)
  * modify your `MANIFEST.in` to include both `versioneer.py` and the
    generated `_version.py` in sdist tarballs

  `versioneer install` will complain about any problems it finds with your
  `setup.py` or `setup.cfg`. Run it multiple times until you have fixed all
  the problems.

* 4: add a `import versioneer` to your setup.py, and add the following
  arguments to the setup() call:

        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),

  If your project uses a special `cmdclass`, pass that `cmdclass` as
  a parameter. For example:

        from numpy.distutils.core import numpy_cmdclass
        cmdclass=versioneer.get_cmdclass(numpy_cmdclass),

* 5: commit these changes to your VCS. To make sure you won't forget,
  `versioneer install` will mark everything it touched for addition using
  `git add`. Don't forget to add `setup.py` and `setup.cfg` too.

## Post-Installation Usage

Once established, all uses of your tree from a VCS checkout should get the
current version string. All generated tarballs should include an embedded
version string (so users who unpack them will not need a VCS tool installed).

If you distribute your project through PyPI, then the release process should
boil down to two steps:

* 1: git tag 1.0
* 2: python setup.py register sdist upload

If you distribute it through github (i.e. users use github to generate
tarballs with `git archive`), the process is:

* 1: git tag 1.0
* 2: git push; git push --tags

Versioneer will report "0+untagged.NUMCOMMITS.gHASH" until your tree has at
least one tag in its history.
