import os # --STRIP DURING BUILD

def finalize(versions, verbose=False):
    """Finalize versions dictionary with override, if applicable.

    If ``VERSIONEER_OVERRIDE`` is defined in the environment, any version
    string is overridden.

    Modifies dictionary in-place and returns it.
    """
    # If override environment variable is set, set version,
    # and ignore errors or dirty repositories
    override = os.getenv("VERSIONEER_OVERRIDE")
    if override:
        if verbose:
            print("got version from environment variable "
                  f"(VERSIONEER_OVERRIDE={override})")
        versions.update({"version": override, "dirty": False, "error": None})

    return versions

