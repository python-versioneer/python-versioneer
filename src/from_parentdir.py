import os # --STRIP DURING BUILD
from .header import NotThisMethod # --STRIP DURING BUILD
from typing import Any, Dict # --STRIP DURING BUILD
def versions_from_parentdir(
    parentdir_prefix: str,
    root: str,
    verbose: bool,
) -> Dict[str, Any]:
    """Try to determine the version from the parent directory name.

    Source tarballs conventionally unpack into a directory that includes both
    the project name and a version string. We will also support searching up
    two directory levels for an appropriately named parent directory
    """
    rootdirs = []

    for _ in range(3):
        dirname = os.path.basename(root)
        if dirname.startswith(parentdir_prefix):
            return {"version": dirname[len(parentdir_prefix):],
                    "full-revisionid": None,
                    "dirty": False, "error": None, "date": None}
        rootdirs.append(root)
        root = os.path.dirname(root)  # up a level

    if verbose:
        print(f"Tried directories {str(rootdirs)} "
              f"but none started with prefix {parentdir_prefix}")
    raise NotThisMethod("rootdir doesn't start with parentdir_prefix")


