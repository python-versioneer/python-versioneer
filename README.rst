The Versioneer
==============

This is a tool for managing a recorded version number in distutils-based
python projects. The goal is to remove the tedious and error-prone "update
the embedded version string" step from your release process. Making a new
release should be as easy as recording a new tag in your version-control
system, and maybe making new tarballs.


Version Identifiers
-------------------

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
* a _version.py created by some earlier build step

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

* to allow the module to self-identify its version: myproject.__version__
* to choose a name and prefix for a 'setup.py sdist' tarball


Theory Of Operation
-------------------

This tool currently provides one script, named "versioneer.py". To
versioneer-enable your project, copy it into the top of your source tree,
then follow the instructions in its docstring. This includes adding several
lines to your setup.py (to teach the tool where your _version.py will live,
what tags look like, and to intercept the 'build' and 'sdist' commands), and
running the 'setup.py update_files' command (to create the initial
_version.py, modify your __init__.py to use it, and help get all the new
files into revision control).

Once established, all uses of your tree from a VCS checkout should get the
current version string. All generated tarballs should include an embedded
version string (so users who unpack them will not need a VCS tool installed).

If you distribute your project through PyPI, then the release process should
boil down to two steps:

 1: git tag 1.0
 2: python setup.py register sdist upload

If you distribute it through github (i.e. users use github to generate
tarballs), the process is:

 1: git tag 1.0
 2: git push; git push --tags


Future Directions
-----------------

This tool is designed to make it easily extended to other version-control
systems: all VCS-specific components are in separate directories like
src/git/ . The top-level 'versioneer.py' script is assembled from these
components by running make-versioneer.py . In the future, make-versioneer.py
will take a VCS name as an argument, and will construct a version of
versioneer.py that is specific to the given VCS. It might also take the
configuration arguments that are currently provided manually during
installation by editing setup.py . Alternatively, it might go the other
direction and include code from all supported VCS systems, reducing the
number of intermediate scripts.

Project Home
------------

https://github.com/warner/python-versioneer
