
## What environments does Versioneer support?

Versioneer may be called upon to calculate version information from one of four different environments.

The first, "from-vcs", is used when run from a checked-out source tree, and asks the version-control tools for information (e.g. `git describe`). This provides the most data: it can examine the commit history, find recent tags, and detect uncommitted changes (a "dirty" tree). In general, source distributions (`setup.py sdist`) are created from this environment, and the calculated version string is embedded into the generated tarball (by replacing `_version.py` with a "short form" that contains literal strings instead of code to run git).

When these tarballs are unpacked, they provide the second environment, "from-file". This environment is also created when you use `setup.py build` and then import code from the generated `build/` directory. All the version strings come from the previous "from-vcs" environment that created the tarball, frozen at that point. `_version.py` might record the fact that the sdist was created from a dirty tree, however it is not possible to detect additional changes.

Sometimes you use the VCS tools to make a tarball directly, like `git archive`, without using `setup.py sdist`. Unpacking such a tarball results in the third environment, "from-keyword". The resulting source tree will contain expanded keywords in the `_version.py` file, which tells it a git revision, and an exact tag (if any), but cannot generally detect things like commits-since-recent-tag, or recent-tag at all. As with from-file, this does not give Versioneer enough information to detect additional changes, and the "dirty" status is always False. In general, you should only use `git archive` on tagged revisions. Creating archives from untagged revisions will result in a version string that's simply a copy of the full SHA1 hash.

If all these methods fail, Versioneer attempts to pull a version string from the name of the parent directory, since tarballs are frequently built this way. This environment is called "from-parentdir". This can provide the main version string, but not a full-revision hash. "dirty" is always False.

If even that fails, Versioneer will either report a version of "0+unknown", and will signal an error.


## What does get_version() return?

It returns `get_versions()["version"]`. See below for what that means.

`get_version()` and `get_versions()` are the main functions through which Versioneer provides version data to your program. Your `setup.py` can do `from versioneer import get_version`, and your top-level runtime modules can do `from ._version import get_version`.

## What does get_versions() return?

`get_versions()` returns a small dictionary of rendered version information, which always contains four keys:

| key | description |
| --- | ---         |
| `version` | The version string as selected by `version-style` |
| `full-revisionid` | A full-length hex SHA1 (for git), or equivalent (for other VCS systems), or None. |
| `dirty` | A boolean, True if the source tree has local changes. None if unknown. |
| `error` | None, or a error description string |

`version` will always be a string (`str` on py3, `unicode` on py2): if Versioneer is unable to compute a version, it will be set to `"0+unknown"`. `full-revisionid` will be a str/unicode, or None if that information is not available. `dirty` will be a boolean, or None if unavailable. `error` will be None, or a str/unicode if there was an error.

If the `error` key is non-None, that indicates that Versioneer was unable to obtain a satisfactory version string. There are several possibilities:

* the closest tag found did not start with the configured `tag_prefix`
* from-keyword mode did not find any tags (e.g. an archive created from a bare SHA1, instead of from a tag)
* the output of `git describe` was unparseable
* all modes failed: the source tree has no `.git` directory, expanded keywords, pre-built version data ("from-file"), or useful parent directory name.

When `error` occurs, `version` will be set to "0+unknown", `full-revisionid` will be set (in from-vcs mode) or None (in other modes), and `dirty` will be None. If you want to prevent builds from happening without solid version information, use a snippet like this in your `__init__.py` or `setup.py`:

```python
v = get_versions()
if v["error"]:
    raise RuntimeError(v["error"])
```

`get_versions()["version"]` is the most useful value, intended for `setup.py` and runtime version introspection to support a CLI command's `--version` argument. This is available in all modes, but has the most fidelity in from-vcs environments.

`get_versions()["full-revisionid"]` is probably useful for an extended form of CLI `--version`, and for including in machine-generated error/crash reports. In from-parentdir mode, its value will be `None`, but in the other modes (from-vcs, from-file, from-keyword) it will be the git SHA1 hash (a 40-character lowercase hexadecimal string), or the equivalent for other VCS systems.

`get_versions()["dirty"]` might be useful when running tests, to remind someone viewing a transcript that there are uncommitted changes which might affect the results. In most cases, this information will also be present in `["version"]` (it will contain a `-dirty` suffix). It may also be useful for `setup.py` decision making:

```python
if versioneer.get_versions()["dirty"]:
    raise MustCommitError("please commit everything before making tarballs")
```

`dirty` is most meaningful in from-vcs mode. In from-file mode, it records the dirty status of the tree from which the setup.py build/sdist command was run, and is not affected by subsequent changes to the generated tree. In from-keyword and from-parentdir mode, it will always be `False`.

## How do I select a version `style`?

In from-vcs mode (inside a git checkout), Versioneer can get a lot of data about the state of the tree: the current tag (if any), the closest historical tag, the number of commits since that tag, the exact revision ID, and the 'dirty' state. These pieces are used by a renderer function to compute the `['version']` in the small dictionary that will be returned by `get_versions()`.

The renderer function is controlled by a configuration value called `style`. You can use this to select the kind of version string you want to use. The available forms are:

| key            | description |
| ---            | ----------- |
| `default`      | same as `pep440` |
| `pep440`       | `TAG[+DISTANCE.gSHORTHASH[.dirty]]`, a PEP-440 compatible version string which uses the "local version identifier" to record the complete non-tag information. This format provides compliant versions even under unusual/error circumstances. It returns `0+untagged.DISTANCE.gHASH[.dirty]` before any tags have been set, `0+unknown` if the tree does not contain enough information to report a version (e.g. the .git directory has been removed), and `0.unparseable[.dirty]` if `git describe` emits something weird. If TAG includes a plus sign, then this will use a dot as a separator instead (`TAG[.DISTANCE.gSHORTHASH[.dirty]]`).|
| `pep440-branch`| `TAG[[.dev0]+DISTANCE.gSHORTHASH[.dirty]]`, a PEP-440 compatible version string, identical to the `pep440` style with the addition of a `.dev0` component if the tree is on a branch other than `master`. Note that PEP-0440 rules indicate that X.dev0 sorts as "older" than X, so feature branches will always appear "older" than the `master` branch in this format, even with `pip install --pre`. |
| `pep440-pre`   | `TAG[.post0.devDISTANCE]`, a PEP-440 compatible version string which loses information but has the useful property that non-tagged versions qualify for `pip install --pre` (by virtue of the `.dev` component). This form does not record the commit hash, nor the `-dirty` flag. |
| `pep440-post`  | `TAG[.postDISTANCE[.dev0]+gSHORTHASH]`, a PEP-440 compatible version string which allows all commits to get installable versions, and retains the commit hash.
| `pep440-post-branch` | `TAG[.postDISTANCE[.dev0]+gHEX[.dirty]]`, a PEP-440 compatible version string, similar to the `pep440-post` style except the `.dev0` component is used to determine if the project tree is on a feature branch. It is appended if the tree is on a non `master` branch so that packages generated are not installed by pip unless `--pre` is specified. |
| `pep440-old`   | `TAG[.postDISTANCE[.dev0]]`, a PEP-440 compatible version string which loses information but enables downstream projects to depend upon post-release versions (by counting commits). The ".dev0" suffix indicates a dirty tree. This form does not record the commit hash. If nothing has been tagged, this will be `0.postDISTANCE[.dev0]`. Note that PEP-0440 rules indicate that `X.dev0` sorts as "older" than `X`, so our -dirty flag is expressed somewhat backwards (usually "dirty" indicates newer changes than the base commit), but PEP-0440 offers no positive post-".postN" component. You should never be releasing software with -dirty anyways. |
| `git-describe` | `TAG[-DISTANCE-gSHORTHASH][-dirty]`, equivalent to `git describe --tags --dirty --always`. The distance and shorthash are only included if the commit is not tagged. If nothing was tagged, this will be the short revisionid, plus "-dirty" if dirty. |
| `git-describe-long` | `TAG-DISTANCE-gSHORTHASH[-dirty]`, equivalent to `git describe --tags --dirty --always --long`. The distance and shorthash are included unconditionally. As with `git-describe`, if nothing was tagged, this will be the short revisionid, possibly with "-dirty". |


## Pieces used by from-vcs

Internally, the from-vcs function is expected to return the following values. The renderer uses these to compute the version string.

| key                   | description |
| ---                   | ----------- |
| `long`     | a full-length id (hex SHA1 for git) for the current revision |
| `short`    | a truncated form of `full-revisionid`, typically 7 characters for git (but might be more in large repositories if necessary to uniquely identify the commit) |
| `error` | a string, if something was unparseable |
| `closest-tag`         | a string (or None if nothing has been tagged), with the name of the closest ancestor tag. The "tag prefix" is stripped off. |
| `distance`            | an integer, the number of commits since the most recent tag. If the current revision is tagged, this will be 0. If nothing has been tagged, this will be the total number of commits. |
| `dirty`            | a boolean, indicating that the working directory has modified files |

If a value is not available (e.g. the source tree does not contain enough information to provide it), the dictionary will not contain that key.

The from-keywords mode will only produce `exact-tag` and `full-revisionid`. If the git-archive tarball was created from a non-tagged revision, `exact-tag` will be None. These tarballs use keyword expansion, and there is no git-attributes keyword that replicates the tag-searching features of git-describe.

`dirty` modification to the source tree can only be detected from a git checkout. A build or sdist created from a dirty tree will be marked as dirty, however an sdist created from a clean tree which is subsequently modified will not be reported as dirty.

## What version strings will we get in each environment?

(note: this is not yet accurate)

| key          | file                | keywords          | git-describe             | parentdir |
| ---          | ------------------- | ----------------- | ------------------------ | --------- |
| pep440       | TAG[+DIST.gHASH]    | TAG or 0.unknown? | TAG[+DIST.gHASH[.dirty]] | TAG or ?  |
| pep440-pre   | TAG[.post0.devDIST] | TAG or ?          | TAG[.post0.devDIST]      | TAG or ?  |
| pep440-old   | TAG[.postDIST]      | TAG or ?          | TAG[.postDIST[.dev0]]    | TAG or ?  |
| git-describe | TAG[-DIST-gHASH]    | TAG or ?          | TAG[-DIST-gHASH][-dirty] | TAG or ?  |
| long         | TAG-DIST-gHASH      | TAG-gHASH or ?    | TAG-DIST-gHASH[-dirty]   | ?         |
