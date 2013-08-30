
def unquote(s):
    return s.replace("%", "%%")
def ver(s):
    return s.replace("@VERSIONEER@", "0.8")

def create_script():
    vcs = "git"
    if vcs not in ("git",):
        raise ValueError("Unhandled revision-control system '%s'" % vcs)
    f = open("versioneer.py", "w")
    def get(fn): return open(fn, "r").read()
    f.write(ver(get("src/header.py")))
    f.write('VCS = "%s"\n' % vcs)
    f.write("IN_LONG_VERSION_PY = False\n")
    f.write("\n\n")
    for line in open("src/%s/long-version.py" % vcs, "r").readlines():
        if line.startswith("#### START"):
            f.write("LONG_VERSION_PY = '''\n")
            f.write("IN_LONG_VERSION_PY = True\n")
        elif line.startswith("#### SUBPROCESS_HELPER"):
            f.write(unquote(get("src/subprocess_helper.py")))
        elif line.startswith("#### MIDDLE"):
            f.write(unquote(get("src/%s/middle.py" % vcs)))
        elif line.startswith("#### PARENTDIR"):
            f.write(unquote(get("src/parentdir.py")))
        elif line.startswith("#### END"):
            f.write("'''\n")
        else:
            f.write(ver(line))
    f.write(get("src/subprocess_helper.py"))
    f.write(get("src/%s/middle.py" % vcs))
    f.write(get("src/parentdir.py"))
    f.write(get("src/%s/install.py" % vcs))
    f.write(ver(get("src/trailer.py")))
    f.close()

if __name__ == '__main__':
    create_script()

