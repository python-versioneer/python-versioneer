#!/usr/bin/env python

import os, base64, tempfile, StringIO
from distutils.core import setup, Command
from distutils.command.build_scripts import build_scripts

LONG="""
Versioneer is a tool to automatically update version strings (in setup.py and
the conventional 'from PROJECT import _version' pattern) by asking your
version-control system about the current tree.
"""

def get(fn):
    return open(fn, "r").read()
def unquote(s):
    return s.replace("%", "%%")
def ver(s):
    return s.replace("@VERSIONEER@", "0.8+")
def readme(s):
    return s.replace("@README@", get("README.md"))

def generate_versioneer():
    vcs = "git"
    if vcs not in ("git",):
        raise ValueError("Unhandled revision-control system '%s'" % vcs)
    f = StringIO.StringIO()
    f.write(readme(ver(get("src/header.py"))))
    f.write('VCS = "%s"\n' % vcs)
    f.write("\n\n")
    for line in open("src/%s/long-version.py" % vcs, "r").readlines():
        if line.startswith("#### START"):
            f.write("LONG_VERSION_PY = '''\n")
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
    return f.getvalue()


class make_versioneer(Command):
    description = "create standalone versioneer.py"
    user_options = []
    boolean_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        with open("versioneer.py", "w") as f:
            f.write(generate_versioneer())
        return 0

class my_build_scripts(build_scripts):
    def run(self):
        v = generate_versioneer()
        v_b64 = base64.b64encode(v)
        lines = [v_b64[i:i+60] for i in range(0, len(v_b64), 60)]
        v_b64 = "\n".join(lines)+"\n"

        with open("src/installer.py") as f:
            s = f.read()
        s = s.replace("@VERSIONEER-INSTALLER@", v_b64)

        tempdir = tempfile.mkdtemp()
        installer = os.path.join(tempdir, "versioneer-installer")
        with open(installer, "w") as f:
            f.write(s)

        self.scripts = [installer]
        rc = build_scripts.run(self)
        os.unlink(installer)
        os.rmdir(tempdir)
        return rc

setup(
    name = "versioneer",
    license = "public domain",
    version = "0.8+",
    description = "Easy VCS-based management of project version strings",
    author = "Brian Warner",
    author_email = "warner@lothar.com",
    url = "https://github.com/warner/python-versioneer",
    # "fake" is replaced with versioneer-installer in build_scripts. We need
    # a non-empty list to provoke "setup.py build" into making scripts,
    # otherwise it skips that step.
    scripts = ["fake"],
    long_description = LONG,
    cmdclass = { "build_scripts": my_build_scripts,
                 "make_versioneer": make_versioneer,
                 },
    )
