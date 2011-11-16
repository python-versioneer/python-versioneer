
def do_vcs_install(versionfile_source, ipy):
    run_command(["git", "add", "versioneer.py"])
    run_command(["git", "add", versionfile_source])
    run_command(["git", "add", ipy])
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
        run_command(["git", "add", ".gitattributes"])
    
