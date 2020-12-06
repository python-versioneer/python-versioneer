import os # --STRIP DURING BUILD

def override_fallback_or_fail(versions, cfg, verbose=False):
    """ Finalize versions dictionary with override or fallback, if applicable

    If ``VERSIONEER_OVERRIDE`` is defined in the environment, any version
    string is overridden.

    If the calling method was unable to provide a valid version, and
    ``fallback_version`` is defined in the configuration file, then the fallback
    version will be used.

    If neither case applies and no version was found, resort to ``0+unknown``.

    Modifies dictionary in-place and returns it.
    """
    # If override environment variable is set, set version,
    # and ignore errors or dirty repositories
    override = os.getenv("VERSIONEER_OVERRIDE")
    if override:
        if verbose:
            print(f"got version from environment variable (VERSIONEER_OVERRIDE={override})")
        versions.update({"version": override, "dirty": False, "error": None})

    # If no version information can be found, apply fallback version
    if versions.get("version") in (None, "0+unknown"):
        if cfg.fallback_version:
            if verbose:
                print(f"Falling back to version {cfg.fallback_version}")
            versions.update({"version": cfg.fallback_version, "error": None})

    return versions
