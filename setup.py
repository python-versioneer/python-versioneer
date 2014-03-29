#!/usr/bin/env python

import os, base64, tempfile, io, sys, json
from os import path
from distutils.core import setup, Command
from distutils.command.build_scripts import build_scripts

LONG="""
Versioneer is a tool to automatically update version strings (in setup.py and
the conventional 'from PROJECT import _version' pattern) by asking your
version-control system about the current tree.
"""

# as nice as it'd be to versioneer ourselves, that sounds messy.
VERSION = "0.10+"

def get(fn):
    with open(fn) as f:
        text = f.read()

    # If we're in Python <3 and have a separate Unicode type, we would've
    # read a non-unicode string. Else, all strings will be unicode strings.
    try:
        __builtins__.unicode
    except AttributeError:
        return text
    else:
        return text.decode('ASCII')

def u(s): # so u("foo") yields unicode on all of py2.6/py2.7/py3.2/py3.3
    return s.encode("ascii").decode("ascii")

def unquote(s):
    return s.replace("%", "%%")
def escape(s):
    return s.replace("\\", "\\\\")
def ver(s):
    return s.replace("@VERSIONEER-VERSION@", VERSION)
def header_replacements(s, vcs_list):
    return s.replace("@README@", get("README.md")).\
             replace("@SUPPORTED_REPOS@", json.dumps(vcs_list))

def get_vcs_list():
    project_path = path.join(path.abspath(path.dirname(__file__)), 'src')

# TODO(dustin): We might have to force this into unicode.
    return [filename
            for filename
            in os.listdir(project_path)
            if path.isdir(path.join(project_path, filename)) and 
               filename != 'vcs_template']

def generate_versioneer():
    vcs_list = get_vcs_list()

    s = io.StringIO()
    s.write(header_replacements(ver(get("src/header.py")), vcs_list))

    # Added VCS-specific detection code, and the function that invokes the detection.

    for VCS in vcs_list:
        s.write(get("src/%s/is_found.py" % VCS))

    s.write(header_replacements(ver(get("src/vcs_detect.py")), vcs_list))
    s.write(u"VCS = _derive_vcs()\n")

    s.write(get("src/subprocess_helper.py"))

# TODO(dustin): At some point, we might consider only implanting VCS support 
#               for the VCS found in the target directory.
# TODO(dustin): Consider using Python string templates so that we can 
#               efficiently replace for more than one token, and so that we 
#               don't have to escape all of the replacement tokens.
    for VCS in vcs_list:
        s.write(u("LONG_VERSION_PY['%s'] = '''\n" % VCS))
        s.write(ver(escape(get("src/%s/long_header.py" % VCS))))
        s.write(unquote(escape(get("src/subprocess_helper.py"))))
        s.write(unquote(escape(get("src/from_parentdir.py"))))
        s.write(unquote(escape(get("src/%s/from_keywords.py" % VCS))))
        s.write(unquote(escape(get("src/%s/from_vcs.py" % VCS))))

        # Deposit a version of get_versions() for use in _version.py .
        s.write(unquote(escape(get("src/%s/long_get_versions.py" % VCS))))

        s.write(u("'''\n"))

        # We're going to double-insert a couple of files so that we have access 
        # to them from versioneer.py, as well as from _version.py (written from 
        # the comment, above).

        s.write(get("src/%s/from_keywords.py" % VCS))
        s.write(get("src/%s/from_vcs.py" % VCS))
        s.write(get("src/%s/install.py" % VCS))

    s.write(get("src/from_parentdir.py"))
    s.write(ver(get("src/from_file.py")))

    # Deposit a version of get_versions() for use in versioneer.py .
    s.write(ver(get("src/get_versions.py")))

    s.write(ver(get("src/cmdclass.py")))

    return s.getvalue().encode("utf-8")


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
