
def unquote(s):
    return s.replace("%", "%%")

def create_script():
    vcs = "git"
    if vcs not in ("git",):
        raise ValueError("Unhandled revision-control system '%s'" % vcs)
    f = open("versioneer.py", "w")
    def get(fn): return open(fn, "r").read()
    f.write(get("src/header.py"))
    f.write('VCS = "%s"\n' % vcs)
    f.write(get("src/subprocess-helper.py"))
    for line in open("src/%s/parse.py" % vcs, "r").readlines():
        if line.startswith("#### START"):
            f.write("LONG_VERSION_PY = '''\n")
        elif line.startswith("#### SUBPROCESS_HELPER"):
            f.write(unquote(get("src/subprocess-helper.py")))
        elif line.startswith("#### VERSION_FROM_CHECKOUT"):
            f.write(unquote(get("src/%s/from-checkout.py" % vcs)))
        elif line.startswith("#### VERSION_FROM_VARIABLE"):
            f.write(unquote(get("src/%s/from-variable.py" % vcs)))
        elif line.startswith("#### END"):
            f.write("'''\n")
        else:
            f.write(line)
    f.write(get("src/%s/from-checkout.py" % vcs))
    f.write(get("src/%s/from-variable.py" % vcs))
    f.write(get("src/%s/setup.py" % vcs))
    f.write(get("src/trailer.py"))
    f.close()

if __name__ == '__main__':
    create_script()

