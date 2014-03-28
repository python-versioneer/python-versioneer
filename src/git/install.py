import os.path
import sys

def git_do_vcs_install(manifest_in, versionfile_source, ipy):
    """The versioneer.py file was just written. Do any VCS-specific logic, 
    here.
    """

    GITS = ["git"]
    if sys.platform == "win32":
        GITS = ["git.cmd", "git.exe"]
    files = [manifest_in, versionfile_source, ipy]
    try:
        me = __file__
        if me.endswith(".pyc") or me.endswith(".pyo"):
            me = os.path.splitext(me)[0] + ".py"
        versioneer_file = os.path.relpath(me)
    except NameError:
        versioneer_file = "versioneer.py"
    files.append(versioneer_file)
    present = False
    try:
        with open(".gitattributes") as f:
            for line in f.readlines():
                if line.strip().startswith(versionfile_source):
                    if "export-subst" in line.strip().split()[1:]:
                        present = True
    except EnvironmentError:
        pass    
    if not present:
        with open(".gitattributes", "a+") as f:
            f.write("%s export-subst\n" % versionfile_source)

        files.append(".gitattributes")
    run_command(GITS, ["add", "--"] + files)

