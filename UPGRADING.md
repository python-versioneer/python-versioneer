# Upgrading Versioneer In Your Project

Some releases of Versioneer change the way your setup.py and setup.cfg
must be configured. This document contains a list of releases where,
when upgrading from an older release, you must make changes in your
project.

## Upgrading to 0.27 through 0.29

Nothing special.

## Upgrading to 0.26

Versioneer now supports configuration through `pyproject.toml` using a
`[tool.versioneer]` table. To use this feature, you will need to add the
`[toml]` extra to `build-system.requires`, e.g.,

```toml
[build-system]
requires = ["setuptools", "versioneer[toml]==0.26"]
```

## Upgrading to 0.24

If you are transitioning to a non-vendored mode for versioneer, add
`"versioneer"` to your `pyproject.toml`. You now update the version file
by using `versioneer install --no-vendor` instead of
`python versioneer.py setup`. Consider using `"versioneer @ 0.24"` to
ensure future breaking changes don't affect your build.

For vendored installations, nothing changes.

## Upgrading to 0.16 through 0.23

Nothing special.

## Upgrading to 0.15

Starting with this version, Versioneer is configured with a `[versioneer]`
section in your `setup.cfg` file. Earlier versions required the `setup.py` to
set attributes on the `versioneer` module immediately after import. The new
version will refuse to run (raising an exception during import) until you
have provided the necessary `setup.cfg` section.

In addition, the Versioneer package provides an executable named
`versioneer`, and the installation process is driven by running `versioneer
install`. In 0.14 and earlier, the executable was named
`versioneer-installer` and was run without an argument.

## Upgrading to 0.14

0.14 changes the format of the version string. 0.13 and earlier used
hyphen-separated strings like "0.11-2-g1076c97-dirty". 0.14 and beyond use a
plus-separated "local version" section strings, with dot-separated
components, like "0.11+2.g1076c97". PEP440-strict tools did not like the old
format, but should be ok with the new one.

## Upgrading from 0.11 to 0.12

Nothing special.

## Upgrading from 0.10 to 0.11

You must add a `versioneer.VCS = "git"` to your `setup.py` before re-running
`setup.py setup_versioneer`. This will enable the use of additional
version-control systems (SVN, etc) in the future.
