#!/usr/bin/env python

import os, base64, tempfile, io
from os import path
from setuptools import setup, Command
from setuptools.command.build_py import build_py
from setuptools.dist import Distribution as _Distribution

LONG="""
Versioneer is a tool to automatically update version strings (in setup.py and
the conventional 'from PROJECT import _version' pattern) by asking your
version-control system about the current tree.
"""

# as nice as it'd be to versioneer ourselves, that sounds messy.
VERSION = "0.18"


def ver(s):
    return s.replace("@VERSIONEER-VERSION@", VERSION)

def get(fn, add_ver=False, unquote=False, do_strip=False, do_readme=False):
    with open(fn) as f:
        text = f.read()

    # If we're in Python <3 and have a separate Unicode type, we would've
    # read a non-unicode string. Else, all strings will be unicode strings.
    try:
        __builtins__.unicode
    except AttributeError:
        pass
    else:
        text =  text.decode('ASCII')
    if add_ver:
        text = ver(text)
    if unquote:
        text = text.replace("%", "%%")
    if do_strip:
        lines = [line for line in text.split("\n")
                 if not line.endswith("# --STRIP DURING BUILD")]
        text = "\n".join(lines)
    if do_readme:
        text = text.replace("@README@", get("README.md"))
    return text

def u(s): # so u("foo") yields unicode on all of py2.6/py2.7/py3.2/py3.3
    return s.encode("ascii").decode("ascii")

def get_vcs_list():
    project_path = path.join(path.abspath(path.dirname(__file__)), 'src')
    return [filename
            for filename
            in os.listdir(project_path)
            if path.isdir(path.join(project_path, filename))]

def generate_long_version_py(VCS):
    s = io.StringIO()
    s.write(get("src/%s/long_header.py" % VCS, add_ver=True, do_strip=True))
    for piece in ["src/subprocess_helper.py",
                  "src/from_parentdir.py",
                  "src/%s/from_keywords.py" % VCS,
                  "src/%s/from_vcs.py" % VCS,
                  "src/render.py",
                  "src/%s/long_get_versions.py" % VCS]:
        s.write(get(piece, unquote=True, do_strip=True))
    return s.getvalue()

def generate_versioneer_py():
    s = io.StringIO()
    s.write(get("src/header.py", add_ver=True, do_readme=True))
    s.write(get("src/subprocess_helper.py", do_strip=True))

    for VCS in get_vcs_list():
        s.write(u("LONG_VERSION_PY['%s'] = '''\n" % VCS))
        s.write(generate_long_version_py(VCS))
        s.write(u("'''\n"))
        s.write(u("\n\n"))

        s.write(get("src/%s/from_keywords.py" % VCS, do_strip=True))
        s.write(get("src/%s/from_vcs.py" % VCS, do_strip=True))

        s.write(get("src/%s/install.py" % VCS, do_strip=True))

    s.write(get("src/from_parentdir.py", do_strip=True))
    s.write(get("src/from_file.py", add_ver=True, do_strip=True))
    s.write(get("src/render.py", do_strip=True))
    s.write(get("src/get_versions.py", do_strip=True))
    s.write(get("src/cmdclass.py", do_strip=True))
    s.write(get("src/setupfunc.py", do_strip=True))

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
            f.write(generate_versioneer_py().decode("utf8"))
        return 0

class make_long_version_py_git(Command):
    description = "create standalone _version.py (for git)"
    user_options = []
    boolean_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        assert os.path.exists("versioneer.py")
        long_version = generate_long_version_py("git")
        with open("git_version.py", "w") as f:
            f.write(long_version %
                    {"DOLLAR": "$",
                     "STYLE": "pep440",
                     "TAG_PREFIX": "tag-",
                     "PARENTDIR_PREFIX": "parentdir_prefix",
                     "VERSIONFILE_SOURCE": "versionfile_source",
                     })
        return 0

class my_build_py(build_py):
    def run(self):
        v = generate_versioneer_py()
        v_b64 = base64.b64encode(v).decode("ascii")
        lines = [v_b64[i:i+60] for i in range(0, len(v_b64), 60)]
        v_b64 = "\n".join(lines)+"\n"

        with open("src/installer.py") as f:
            s = f.read()
        s = ver(s.replace("@VERSIONEER-INSTALLER@", v_b64))

        tempdir = tempfile.mkdtemp()
        installer = os.path.join(tempdir, "versioneer.py")
        with open(installer, "w") as f:
            f.write(s)

        self.py_modules = [os.path.splitext(os.path.basename(installer))[0]]
        self.package_dir.update({'': os.path.dirname(installer)})
        rc = build_py.run(self)
        os.unlink(installer)
        os.rmdir(tempdir)
        return rc


# python's distutils treats module-less packages as binary-specific (not
# "pure"), so "setup.py bdist_wheel" creates binary-specific wheels. Override
# this so we get cross-platform wheels instead. More info at:
# https://bitbucket.org/pypa/wheel/issue/116/packages-with-only-filesdata_files-get
class Distribution(_Distribution):
    def is_pure(self): return True

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
    py_modules = ["fake"],
    entry_points={
        'console_scripts': [
            'versioneer = versioneer:main',
        ],
    },
    long_description = LONG,
    distclass=Distribution,
    cmdclass = { "build_py": my_build_py,
                 "make_versioneer": make_versioneer,
                 "make_long_version_py_git": make_long_version_py_git,
                 },
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5"
        ],
    )
