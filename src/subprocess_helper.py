import sys, subprocess, errno # --STRIP DURING BUILD
def run_command(commands, args, cwd=None, verbose=False, hide_stderr=False,
                env=None):
    """Call the given command(s)."""
    assert isinstance(commands, list)
    process = None

    popen_kwargs = {}
    if sys.platform == "win32":
        # This hides the console window if pythonw.exe is used
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        popen_kwargs["startupinfo"] = startupinfo

    for command in commands:
        try:
            dispcmd = str([command] + args)
            # remember shell=False, so use git.cmd on windows, not just git
            process = subprocess.Popen([command] + args, cwd=cwd, env=env,
                                       stdout=subprocess.PIPE,
                                       stderr=(subprocess.PIPE if hide_stderr
                                               else None), **popen_kwargs)
            break
        except OSError:
            e = sys.exc_info()[1]
            if e.errno == errno.ENOENT:
                continue
            if verbose:
                print(f"unable to run {dispcmd}")
                print(e)
            return None, None
    else:
        if verbose:
            print(f"unable to find command, tried {commands}")
        return None, None
    stdout = process.communicate()[0].strip().decode()
    if process.returncode != 0:
        if verbose:
            print(f"unable to run {dispcmd} (error)")
            print(f"stdout was {stdout}")
        return None, process.returncode
    return stdout, process.returncode


