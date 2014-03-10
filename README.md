The Versioneer
==============

* like a rocketeer, but for versions!
* https://github.com/warner/python-versioneer
* Brian Warner
* License: Public Domain
* Compatible With: python2.6, 2.7, and 3.2, 3.3

[![Build Status](https://travis-ci.org/warner/python-versioneer.png?branch=master)](https://travis-ci.org/warner/python-versioneer)

This is a tool for managing a recorded version number in distutils-based
python projects. The goal is to remove the tedious and error-prone "update
the embedded version string" step from your release process. Making a new
release should be as easy as recording a new tag in your version-control
system, and maybe making new tarballs.


## Quick Install

* download https://github.com/warner/python-versioneer/raw/master/versioneer.py
* copy `versioneer.py` into the top of your source tree
* follow the instructions below

## Version Identifiers

Source trees come from a variety of places:

* a version-control system checkout (mostly used by developers or eager
  followers)
* a nightly tarball, produced by build automation
* a snapshot tarball, produced by a web-based VCS browser, like hgweb or
  github's "tarball from tag" feature
* a release tarball, produced by "setup.py sdist", and perhaps distributed
  through PyPI

Within each source tree, the version identifier (either a string or a number,
this tool is format-agnostic) can come from a variety of places:

* ask the VCS tool itself, e.g. "git describe" (for checkouts), which knows
  about recent "tags" and an absolute revision-id
* the name of the directory into which the tarball was unpacked
* an expanded VCS variable ($Id$, etc)
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
tree, where your `__init__.py` can import it. This _version.py knows how to
dynamically ask the VCS tool for version information at import time. However,
when you use "setup.py build" or "setup.py sdist", `_version.py` in the new
copy is replaced by a small static file that contains just the generated
version data.

`_version.py` also contains `$Revision$` markers, and the installation
process marks _version.py to have this marker rewritten with a tag name
during the "git archive" command. As a result, generated tarballs will
contain enough information to get the proper version.


## Installation

You will need to provide versioneer with a few configuration variables:

* `versionfile_source`:

  A project-relative pathname into which the generated version strings should
  be written. This is usually a _version.py next to your project's main
  `__init__.py` file. If your project uses `src/myproject/__init__.py`, this
  should be `src/myproject/_version.py`. This file should be checked in to
  your VCS as usual: the copy created below by 'setup.py update_files' will
  include code that parses expanded VCS keywords in generated tarballs. The
  'build' and 'sdist' commands will replace it with a copy that has just the
  calculated version string.

*  `versionfile_build`:

  Like `versionfile_source`, but relative to the build directory instead of
  the source directory. These will differ when your setup.py uses
  'package_dir='. If you have `package_dir={'myproject': 'src/myproject'}`,
  then you will probably have `versionfile_build='myproject/_version.py'` and
  `versionfile_source='src/myproject/_version.py'`.

* `tag_prefix`:

  a string, like 'PROJECTNAME-', which appears at the start of all VCS tags.
  If your tags look like 'myproject-1.2.0', then you should use
  tag_prefix='myproject-'. If you use unprefixed tags like '1.2.0', this
  should be an empty string.

* `parentdir_prefix`:

  a string, frequently the same as tag_prefix, which appears at the start of
  all unpacked tarball filenames. If your tarball unpacks into
  'myproject-1.2.0', this should be 'myproject-'.

This tool provides one script, named `versioneer.py`.

To versioneer-enable your project:

1: copy `versioneer.py` into the top of your source tree

2: add the following lines to the top of your `setup.py`, with suitable
   values for each configuration setting:

    import versioneer
    versioneer.versionfile_source = 'src/myproject/_version.py'
    versioneer.versionfile_build = 'myproject/_version.py'
    versioneer.tag_prefix = '' # tags are like 1.2.0
    versioneer.parentdir_prefix = 'myproject-' # dirname like 'myproject-1.2.0'

3: add the following arguments to the setup() call in your setup.py:

    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),

4: run `setup.py update_files`, which will create `_version.py`, and will
   modify your `__init__.py` to define `__version__` (by calling a function
   from `_version.py`)

5: modify your MANIFEST.in to include `versioneer.py` in sdist tarballs

6: commit these changes to your VCS. `update_files` will mark both
`versioneer.py` and the generated `_version.py` for addition.

## Post-Installation Usage

Once established, all uses of your tree from a VCS checkout should get the
current version string. All generated tarballs should include an embedded
version string (so users who unpack them will not need a VCS tool installed).

If you distribute your project through PyPI, then the release process should
boil down to two steps:

 1: git tag 1.0
 2: python setup.py register sdist upload

If you distribute it through github (i.e. users use github to generate
tarballs with `git archive`), the process is:

 1: git tag 1.0
 2: git push; git push --tags

Currently, all version strings must be based upon a tag. Versioneer will
report "unknown" until your tree has at least one tag in its history. This
restriction will be fixed eventually (see issue #12).


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
public domain. The `_version.py` that it creates is also in the public domain.
