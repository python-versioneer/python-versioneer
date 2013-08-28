
import subprocess
import sys

def run_command(args, cwd=None, verbose=False, hide_stderr=False):
    try:
        # remember shell=False, so use git.cmd on windows, not just git
        p = subprocess.Popen(args, cwd=cwd, stdout=subprocess.PIPE,
                             stderr=(subprocess.PIPE if hide_stderr else None))
    except EnvironmentError:
        e = sys.exc_info()[1]
        if verbose:
            print("unable to run %s" % args[0])
            print(e)
        return None
    stdout = p.communicate()[0].strip()
    if sys.version >= '3':
        stdout = stdout.decode()
    if p.returncode != 0:
        if verbose:
            print("unable to run %s (error)" % args[0])
        return None
    return stdout

