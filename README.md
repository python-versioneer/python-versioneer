The Versioneer
==============

* like a rocketeer, but for versions!
* https://github.com/warner/python-versioneer
* Brian Warner
* License: Public Domain
* Compatible With: python2.6, 2.7, 3.2, 3.3, 3.4, and pypy
* [![Latest Version]
(https://pypip.in/version/versioneer/badge.svg?style=flat)
](https://pypi.python.org/pypi/versioneer/)
* [![Build Status]
(https://travis-ci.org/warner/python-versioneer.png?branch=master)
](https://travis-ci.org/warner/python-versioneer)

This is a tool for managing a recorded version number in distutils-based
python projects. The goal is to remove the tedious and error-prone "update
the embedded version string" step from your release process. Making a new
release should be as easy as recording a new tag in your version-control
system, and maybe making new tarballs.


## Quick Install

* `pip install versioneer` to somewhere to your $PATH
* add a `[versioneer]` section to your setup.cfg (see below)
* run `versioneer-installer` in your source tree, commit the results

## Version Identifiers

Source trees come from a variety of places:

* a version-control system checkout (mostly used by developers)
* a nightly tarball, produced by build automation
* a snapshot tarball, produced by a web-based VCS browser, like github's
  "tarball from tag" feature
* a release tarball, produced by "setup.py sdist", distributed through PyPI

Within each source tree, the version identifier (either a string or a number,
this tool is format-agnostic) can come from a variety of places:

* ask the VCS tool itself, e.g. "git describe" (for checkouts), which knows
  about recent "tags" and an absolute revision-id
* the name of the directory into which the tarball was unpacked
* an expanded VCS keyword ($Id$, etc)
* a `_version.py` created by some earlier build step

For released software, the version identifier is closely related to a VCS
tag. Some projects use tag names that include more than just the version
string (e.g. "myproject-1.2" instead of just "1.2"), in which case the tool
needs to strip the tag prefix to extract the version identifier. For
unreleased software (between tags), the version identifier should provide
enough information to help developers recreate the same tree, while also
giving them an idea of roughly how old the tree is (after version 1.2, before
version 1.3). Many VCS systems can report a description that captures this,
for example 'git describe --tags --dirty --always' reports things like
"0.7-1-g574ab98-dirty" to indicate that the checkout is one revision past the
0.7 tag, has a unique revision id of "574ab98", and is "dirty" (it has
uncommitted changes.

The version identifier is used for multiple purposes:

* to allow the module to self-identify its version: `myproject.__version__`
* to choose a name and prefix for a 'setup.py sdist' tarball

## Theory of Operation

Versioneer works by adding a special `_version.py` file into your source
tree, where your `__init__.py` can import it. This `_version.py` knows how to
dynamically ask the VCS tool for version information at import time. However,
when you use "setup.py build" or "setup.py sdist", `_version.py` in the new
copy is replaced by a small static file that contains just the generated
version data.

`_version.py` also contains `$Revision$` markers, and the installation
process marks `_version.py` to have this marker rewritten with a tag name
during the "git archive" command. As a result, generated tarballs will
contain enough information to get the proper version.


## Installation

First, decide on values for the following configuration variables:

* `VCS`: the version control system you use. Currently accepts "git".

* `versionfile_source`:

  A project-relative pathname into which the generated version strings should
  be written. This is usually a `_version.py` next to your project's main
  `__init__.py` file, so it can be imported at runtime. If your project uses
  `src/myproject/__init__.py`, this should be `src/myproject/_version.py`.
  This file should be checked in to your VCS as usual: the copy created below
  by `setup.py setup_versioneer` will include code that parses expanded VCS
  keywords in generated tarballs. The 'build' and 'sdist' commands will
  replace it with a copy that has just the calculated version string.

  This must be set even if your project does not have any modules (and will
  therefore never import `_version.py`), since "setup.py sdist" -based trees
  still need somewhere to record the pre-calculated version strings. Anywhere
  in the source tree should do. If there is a `__init__.py` next to your
  `_version.py`, the `setup.py setup_versioneer` command (described below)
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
  `versionfile_build = None` and override `distutils.command.build_scripts`
  to explicitly insert a copy of `versioneer.get_version()` into your
  generated script.

* `tag_prefix`:

  a string, like 'PROJECTNAME-', which appears at the start of all VCS tags.
  If your tags look like 'myproject-1.2.0', then you should use
  tag_prefix='myproject-'. If you use unprefixed tags like '1.2.0', this
  should be an empty string.

* `parentdir_prefix`:

  a string, frequently the same as tag_prefix, which appears at the start of
  all unpacked tarball filenames. If your tarball unpacks into
  'myproject-1.2.0', this should be 'myproject-'.

This tool provides one script, named `versioneer-installer`. That script does
one thing: write a copy of `versioneer.py` into the current directory.

To versioneer-enable your project:

* 1: Modify your `setup.cfg`, adding a section named `[versioneer]` and
  populating it with the configuration values you decided earlier:

  ````
  [versioneer]
  VCS = git
  versionfile_source = src/myproject/_version.py
  versionfile_build = myproject/_version.py
  tag_prefix = ""
  parentdir_prefix = myproject-
  ````

* 2: Run `versioneer-installer`. This will do the following:

  * copy `versioneer.py` into the top of your source tree
  * create `_version.py` in the right place (`versionfile_source`)
  * modify your `__init__.py` (if one exists next to `_version.py`) to define
    `__version__` (by calling a function from `_version.py`)
  * modify your `MANIFEST.in` to include both `versioneer.py` and the
    generated `_version.py` in sdist tarballs

* 3: add a `import versioneer` to your setup.py, and add the following
  arguments to the setup() call:

        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),

* 4: commit these changes to your VCS. To make sure you won't forget,
  `versioneer-installer` will mark everything it touched for addition using
  `git add`.

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

Currently, all version strings must be based upon a tag. Versioneer will
report "unknown" until your tree has at least one tag in its history. This
restriction will be fixed eventually (see issue #12).

## Version-String Flavors

Code which uses Versioneer can learn about its version string at runtime by
importing `_version` from your main `__init__.py` file and running the
`get_versions()` function. From the "outside" (e.g. in `setup.py`), you can
import the top-level `versioneer.py` and run `get_versions()`.

Both functions return a dictionary with different flavors of version
information:

* `['version']`: A condensed PEP440-compliant string, equal to the
  un-prefixed tag name for actual releases, and containing an additional
  "local version" section with more detail for in-between builds. For Git,
  this is TAG[+DISTANCE.gHEX[.dirty]] , using information from `git describe
  --tags --dirty --always`. For example "0.11+2.g1076c97.dirty" indicates
  that the tree is like the "1076c97" commit but has uncommitted changes
  (".dirty"), and that this commit is two revisions ("+2") beyond the "0.11"
  tag. For released software (exactly equal to a known tag), the identifier
  will only contain the stripped tag, e.g. "0.11".

* `['full-revisionid']`: detailed revision identifier. For Git, this is the
  full SHA1 commit id, e.g. "1076c978a8d3cfc70f408fe5974aa6c092c949ac".

* `['dirty']`: a boolean, True if the tree has uncommitted changes. Note that
  this is only accurate if run in a VCS checkout, otherwise it is likely to
  be False or None

* `['error']`: if the version string could not be computed, this will be set
  to a string describing the problem, otherwise it will be None. It may be
  useful to throw an exception in setup.py if this is set, to avoid e.g.
  creating tarballs with a version string of "unknown".

Some variants are more useful than others. Including `full-revisionid` in a
bug report should allow developers to reconstruct the exact code being tested
(or indicate the presence of local changes that should be shared with the
developers). `version` is suitable for display in an "about" box or a CLI
`--version` output: it can be easily compared against release notes and lists
of bugs fixed in various releases.

The `setup.py setup_versioneer` command adds the following text to your
`__init__.py` to place a basic version in `YOURPROJECT.__version__`:

    from ._version import get_versions
    __version__ = get_versions()['version']
    del get_versions

## Updating Versioneer

To upgrade your project to a new release of Versioneer, do the following:

* install the new Versioneer (`pip install -U versioneer` or equivalent)
* edit `setup.cfg`, if necessary, to include any new configuration settings
  indicated by the release notes
* re-run `versioneer-installer` in your source tree, to replace
  `SRC/_version.py`
* commit any changed files

### Upgrading from 0.10 to 0.11

You must add a `versioneer.VCS = "git"` to your `setup.py` before re-running
`setup.py setup_versioneer`. This will enable the use of additional
version-control systems (SVN, etc) in the future.

### Upgrading from 0.11 to 0.12

Nothing special.

## Upgrading to 0.14

0.14 changes the format of the version string. 0.13 and earlier used
hyphen-separated strings like "0.11-2-g1076c97-dirty". 0.14 and beyond use a
plus-separated "local version" section strings, with dot-separated
components, like "0.11+2.g1076c97". PEP440-strict tools did not like the old
format, but should be ok with the new one.

## Upgrading to XXX

Starting with this version, Versioneer is configured with a `[versioneer]`
section in your `setup.cfg` file. Earlier versions required the `setup.py` to
set attributes on the `versioneer` module immediately after import. The new
version will refuse to run (exception during import) until you have provided
the necessary `setup.cfg` section.

## Future Directions

This tool is designed to make it easily extended to other version-control
systems: all VCS-specific components are in separate directories like
src/git/ . The top-level `versioneer.py` script is assembled from these
components by running make-versioneer.py . In the future, make-versioneer.py
will take a VCS name as an argument, and will construct a version of
`versioneer.py` that is specific to the given VCS. It might also take the
configuration arguments that are currently provided manually during
installation by editing setup.py . Alternatively, it might go the other
direction and include code from all supported VCS systems, reducing the
number of intermediate scripts.


## License

To make Versioneer easier to embed, all its code is hereby released into the
public domain. The `_version.py` that it creates is also in the public
domain.
