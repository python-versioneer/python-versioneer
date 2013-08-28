import os.path
import sys

# os.path.relpath only appeared in Python-2.6 . Define it here for 2.5.
def os_path_relpath(path, start=os.path.curdir):
    """Return a relative version of a path"""

    if not path:
        raise ValueError("no path specified")

    start_list = [x for x in os.path.abspath(start).split(os.path.sep) if x]
    path_list = [x for x in os.path.abspath(path).split(os.path.sep) if x]

    # Work out how much of the filepath is shared by start and path.
    i = len(os.path.commonprefix([start_list, path_list]))

    rel_list = [os.path.pardir] * (len(start_list)-i) + path_list[i:]
    if not rel_list:
        return os.path.curdir
    return os.path.join(*rel_list)

def do_vcs_install(versionfile_source, ipy):
    GIT = "git"
    if sys.platform == "win32":
        GIT = "git.cmd"
    files = [versionfile_source, ipy]
    try:
        me = __file__
        if me.endswith(".pyc") or me.endswith(".pyo"):
            me = os.path.splitext(me)[0] + ".py"
        versioneer_file = os_path_relpath(me)
    except NameError:
        versioneer_file = "versioneer.py"
    files.append(versioneer_file)
    present = False
    try:
        f = open(".gitattributes", "r")
        for line in f.readlines():
            if line.strip().startswith(versionfile_source):
                if "export-subst" in line.strip().split()[1:]:
                    present = True
        f.close()
    except EnvironmentError:
        pass    
    if not present:
        f = open(".gitattributes", "a+")
        f.write("%s export-subst\n" % versionfile_source)
        f.close()
        files.append(".gitattributes")
    run_command([GIT, "add", "--"] + files)
