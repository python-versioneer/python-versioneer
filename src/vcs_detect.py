SUPPORTED_REPOS = @SUPPORTED_REPOS@

def _derive_vcs():
    for vcs in SUPPORTED_REPOS:
        func_name = vcs + '_is_found'
        is_found_f = getattr(sys.modules[__name__], func_name)
        if is_found_f() is True:
            return vcs

    raise SystemError("Could not identify VCS.")

