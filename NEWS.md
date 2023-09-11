## Release 0.30 (??-???-2023)

This release adds formal support for Python 3.12.

* MNT: Update `Cython` generated `.c` in `demoappext-setuptools` test project. by @Callek (#376)
* CI: Add Python 3.12 to CI (initially at it's rc1 version). by @Callek (#376)
* CI: End testing on the end-of-life Python 3.7. by @effigies (#378)

## Release 0.29 (7-Jul-2023)

This release allows for `pyproject.toml`-only build systems to allow versioneer to find
the project root, despite an absense of a `setup.py`. Provides some error message support
when the pyproject.toml is malformed. Finally we added basic type-hinting to the project,
which should help users of type-checking systems ensure correct code when vendoring.

With thanks to Dimitri Papadopoulos Orfanos, Mike Taves, '@gamecss' and '@GCS-ZHN' for contributions.

* FIX: Add error output when `pyproject.toml` is malformed. by @GCS-ZHN (#361)
* FIX: Add name to `setup.py` to work around a github dependency graph bug. by @mwtwoes. (#360)
* ENH: Add basic type information throughout project. by @Callek (#365 and #367)
* ENH: Detect `pyproject.toml` as project root (to support `PDM`). by @gamecss (#371)
* MNT: Overwrite version file instead of delete/unlink. by @DimitriPapadopoulos (#353)
* MNT: Use `https` for the unlicense url. by @DimitriPapadopoulos (#356)
* MNT: Removal of CJM as maintainer. by @effigies (#359)
* MNT: Prepare release 0.29. by @Callek (#373)
* CI: Use 3.11 release (not rc). by @DimitriPapadopoulos (#355)

## Release 0.28 (27-Oct-2022)

This release adds official support for Python 3.11, including using the built-in tomllib
instead of the third-party tomli, when available.

With thanks to Michał Górny for contributions.

* FIX: Handle unset `versionfile_build` in `build_ext` by @mgorny (#347)
* ENH: Support built-in tomllib for Python 3.11+ by @mgorny (#348)

## Release 0.27 (19-Oct-2022)

This release fixes a bug with non-isolated builds of Versioneer and for packages that
provide their own `sdist` command.

With thanks to Dimitri Papadopoulos and Michał Górny for contributions.

* FIX: Always bootstrap in setup.py to avoid incompatibility with old versioneer by @mgorny (#344)
* FIX: Mixup between `_egg_info` and `_sdist` by @DimitriPapadopoulos (#342)
* STY: Merge `endswith` checks by @DimitriPapadopoulos (#337)
* STY: Useless inheritance from object by @DimitriPapadopoulos (#336)
* CI: python-version should be a string, not a float by @DimitriPapadopoulos (#340)
* CI: Automatically update GitHub Actions in the future by @DimitriPapadopoulos (#341)

## Release 0.26 (6-Sep-2022)

This release adds support for configuring versioneer through pyproject.toml and
removes itself from the list of explicit build requirements, which caused problems
with `--no-binary` installations.

* FIX: Remove versioneer from build-system.requires by @effigies (#334)
* ENH: Support configuration in pyproject.toml by @effigies (#330)

## Release 0.25 (2-Sep-2022)

This release makes minor changes to the metadata, ensures tests run correctly from sdist
packages, and uses non-vendored versioneer to version itself.

With thanks to Simão Afonso for contributions.

* FIX: Include pyproject.toml in MANIFEST.in by @effigies (#326)
* STY: Appease flake8 by @simaoafonso-pwt (#327)
* MNT: Version versioneer with versioneer by @effigies (#323)
* CI: Build package and push to PyPI on tag by @effigies (#328)
* CI: Explicitly test sdist by @effigies (#329)

## Release 0.24 (30-Aug-2022)

This release adds support for a non-vendored use of Versioneer.

With thanks to Stefan Appelhoff and Yaroslav Halchenko for contributions.

* MNT: Relicense to Unlicense by @effigies (#317)
* ENH: in verbose mode do not hide stderr of git rev-parse by @yarikoptic (#318)
* DOC: clarify upgrading to 0.23 doesn't require special actions by @sappelhoff (#321)
* ENH: Prepare for py2exe dropping distutils support by @effigies (#319)
* ENH: Allow versioneer to be used as a module in PEP-518 mode by @effigies (#294)

## Release 0.23 (12-Aug-2022)

This release adds support for Setuptools' PEP-660 editable installations,
drops support for Python 3.6, and supports startlingly old git versions.

With thanks to Biastian Zim, Michał Górny, Igor S. Gerasimov, Christian Clauss,
Anderson Bravalheri and Simão Afonso for contributions.

* FIX: Adequate custom `build_py` command to changes in setuptools v64 by @abravalheri (#313)
* FIX: skip version update on `build_ext` if .py does not exist by @mgorny (#297)
* FIX: old GIT (<1.7.2) does not know about `--count` flag by @foxtran (#306)
* FIX: Use only numeric versions in Git, ignore other tags with the same prefix by @effigies (#256)
* FIX: Handle missing `tag_prefix` gracefully by @effigies (#308)
* FIX: Restore `py_modules` field to setup.py by @effigies (#293)
* ENH: Patch versioneer files into manifest at runtime by @effigies (#309)
* STY: Undefined name: VersioneerBadRootError on line 51 by @cclauss (#305)
* STY: Appease flake8 by @simaoafonso-pwt (#312)
* MNT: Drop 3.6 support, remove old hacks by @effigies (#288)
* MNT: Clarify license as CC0-1.0 by @BastianZim (#292)
* MNT: Drop distutils by @effigies (#289)
* MNT: Disable editable installs of versioneer (they will not work) by @effigies (#307)
* CI: Update gh-actions PLATFORM variable to avoid double-testing by @effigies (#311)

## Release 0.22 (07-Mar-2022)

This release fixes failures in Windows related to different handling of
asterisk characters depending on the shell and the presence of a prefix.

This release explicitly has been tested on Python 3.10 and is the final
release that will support Python 3.6 or distutils.

With thanks to John Wodder, Mathijs van der Vlies and Christian Schulze for
their contributions.

* FIX: Unset `GIT_DIR` environment variable while retrieving version information from git (#280)
* FIX: Hide console window if pythonw.exe is used (#285)
* FIX: Broken tag prefix on Windows and add CI (#283)
* FIX: Default to setuptools, only falling back to distutils (#276)
* TEST: Verify and note Python 3.10 support (#272)
* MNT: Run CI weekly to catch upstream deprecations quickly (#281)

## Release 0.21 (13-Oct-2021)

With thanks to Dimitri Papadopoulos Orfanos, Andrew Tolmie, Michael Niklas,
Mike Taves, Ryan Mast, and Yaroslav Halchenko for contributions.

* FIX: Escape asterisk in `git describe` call on Windows (#262)
* ENH: Add some type annotations to play nicely with mypy (#269)
* ENH: Respect tags with `.postN` in pep440-pre style (#261)
* TEST: Subproject installations fixed in Pip 21.3, remove expected failure marks (#271)
* STY: Fix typos (#260 and #266)
* STY: Centralize pylint hints in header (#270)
* MNT: Use `os.path` and `pathlib` consistently (#267)

## Release 0.20 (13-Jul-2021)

With thanks to Tanvi Moharir, Ashutosh Varma, Benjamin Rüth, Lucas Jansen,
Timothy Lusk and Barret O'Brock for contributions.

* Respect `versionfile_source` in `__init__.py` snippet (#241)
* Add `pep440-branch` and `pep440-post-branch` styles (#164)
* Stop testing deprecated `easy_install`, support left in for now (#237)
* Use `versionfile_build` instead of `versionfile_source` where needed (#242)
* Improve handling of refname edge cases (#229)
* Clarify installation in docs (#235)
* Play nicely with custom `build_ext`s (#232)

## Release 0.19 (10-Nov-2020)

Versioneer's 0.19 release is the first under new maintainership, and most of the work
done has been maintenance along with a few features and bug fixes. No significant
changes to the mode of operation have been included here.

The current maintainers are Nathan Buckner, Yaroslav Halchenko, Chris Markiewicz,
Kevin Sheppard and Brian Warner.

* Drop support for Python < 3.6, test up to Python 3.9
* Strip GPG signature information from date (#222)
* Add `bdist_ext` cmdclass, to support native code extensions (#171)
* Canonicalize pep440-pre style (#163)
* Take arguments to `get_cmdclass`

## Release 0.18 (01-Jan-2017)

* switch to entrypoints to get the right executable suffix on windows (#131)
* update whitespace to appease latest flake8

Thanks to xoviat for the windows patch.
