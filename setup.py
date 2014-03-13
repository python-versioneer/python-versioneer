#!/usr/bin/env python

import os, base64, tempfile
from distutils.core import setup, Command
from distutils.command.build_scripts import build_scripts

LONG="""
Versioneer is a tool to automatically update version strings (in setup.py and
the conventional 'from PROJECT import _version' pattern) by asking your
version-control system about the current tree.
"""

# as nice as it'd be to versioneer ourselves, that sounds messy.
VERSION = "0.8+"

def get(fn):
    return open(fn, "r").read()
def unquote(s):
    return s.replace("%", "%%")
def ver(s):
    return s.replace("@VERSIONEER-VERSION@", VERSION)
def readme(s):
    return s.replace("@README@", get("README.md"))

def generate_versioneer():
    vcs = "git"
    if vcs not in ("git",):
        raise ValueError("Unhandled revision-control system '%s'" % vcs)
    out = []
    out.append(readme(ver(get("src/header.py"))))
    out.append('VCS = "%s"\n' % vcs)
    out.append("\n\n")
    for line in open("src/%s/long-version.py" % vcs, "r").readlines():
        if line.startswith("#### START"):
            out.append("LONG_VERSION_PY = '''\n")
        elif line.startswith("#### SUBPROCESS_HELPER"):
            out.append(unquote(get("src/subprocess_helper.py")))
        elif line.startswith("#### MIDDLE"):
            out.append(unquote(get("src/%s/middle.py" % vcs)))
        elif line.startswith("#### PARENTDIR"):
            out.append(unquote(get("src/parentdir.py")))
        elif line.startswith("#### END"):
            out.append("'''\n")
        else:
            out.append(ver(line))
    out.append(get("src/subprocess_helper.py"))
    out.append(get("src/%s/middle.py" % vcs))
    out.append(get("src/parentdir.py"))
    out.append(get("src/%s/install.py" % vcs))
    out.append(ver(get("src/trailer.py")))
    return ("".join(out)).encode("utf-8")


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
            f.write(generate_versioneer().decode("utf8"))
        return 0

class my_build_scripts(build_scripts):
    def run(self):
        v = generate_versioneer()
        v_b64 = base64.b64encode(v).decode("ascii")
        lines = [v_b64[i:i+60] for i in range(0, len(v_b64), 60)]
        v_b64 = "\n".join(lines)+"\n"

        with open("src/installer.py") as f:
            s = f.read()
        s = ver(s.replace("@VERSIONEER-INSTALLER@", v_b64))

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
    version = VERSION,
    description = "Easy VCS-based management of project version strings",
    author = "Brian Warner",
    author_email = "warner-versioneer@lothar.com",
    url = "https://github.com/warner/python-versioneer",
    # "fake" is replaced with versioneer-installer in build_scripts. We need
    # a non-empty list to provoke "setup.py build" into making scripts,
    # otherwise it skips that step.
    scripts = ["fake"],
    long_description = LONG,
    cmdclass = { "build_scripts": my_build_scripts,
                 "make_versioneer": make_versioneer,
                 },
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        ],
    )
