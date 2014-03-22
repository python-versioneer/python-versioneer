
## To add support for a new VCS

So, you want to extend Versioneer to support your favorite version control system? Great! Here's what to do:

* 1: `mkdir src/NEW-VCS/`
* 2: create work-alikes for everything in `src/git/`
* 3: add NEW-VCS to the loop in setup.py `generate_versioneer()`
* 4: add clauses for NEW-VCS to `src/get_versions.py`, for both the from-keywords and from-vcs sections
* 5: add `test/test_NEWVCS.py`, copying the general style of `test_git.py` but using NEWVCS instead of git.
* 6: add a line to .travis.yml to execute your `test_NEWVCS.py` upon checkins

Then file a pull request!


## What does get_versions() return?

`get_versions()` returns a dictionary of version information: strings and other data that may be useful pieces from which you can construct a version string. It can be used to populate a template string:

```python
version = "%(tag)s%(dash_distance)s%(dash_dirty)"% versioneer.get_versions()
```

You can also extract the pieces and programmatically construct a string or make other decisions:

```python
if versioneer.get_versions()["dirty"]:
    raise MustCommitError("commit everything before making tarballs")
```

It also contains some pre-formatted version strings.

```python
setup(...
      version = versioneer.get_versions()["pep440"],
      )
```

The version information is intended to be mostly VCS-neutral, but some VCSes cannot support everything. The keys available are:

* `describe`: `TAG[-DISTANCE-gSHORTHASH][-dirty]`, equivalent to `git describe --tags --dirty --always`. The distance and shorthash are only included if the commit is not tagged.
* `long`: `TAG-DISTANCE-gSHORTHASH[-dirty]`, equivalent to `git describe --tags --dirty --always --long`. The distance and shorthash are included unconditionally.
* `closest_tag`: a string (or None if nothing has been tagged), with the name of the closest ancestor tag
* `distance`: an integer, the number of commits since the most recent tag. If the current revision is tagged, this will be 0
* `dash_distance`: an empty string if `distance==0`, else `"-%d" % distance`
* `dirty`: a boolean, indicating that the working directory has modified files
* `dash_dirty`: ana empty string if `dirty` is False, else the string `"-dirty"`
* `full_revisionid`: a full-length id (hex SHA1 for git) for the current revision
* `pep440`: `TAG[.post0.devDISTANCE]`, a PEP-0440 compatible version string which loses information but is suitable for uploading to PyPI and installing with pip.

## What does get_version() return?

`versioneer.get_version()` returns a single string, configured by setting `versioneer.version_string_template`. `get_version()` will simply format this template with the dictionary returned by `get_versions()`:

```python
def get_version():
    return version_string_template % get_versions()
```

The default value of `version_string_template` is `%(describe)s`, which yields the "git describe" style of version string. To get pep440-compatible strings from `get_version()`, use this:

```python
versioneer.version_string_template = "%(pep440)s"
```
