#!/usr/bin/env python

import os, base64, tempfile, io
from pathlib import Path
from setuptools import setup, Command
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop

# If versioneer is not installed in the environment, then we will need to
# need to build and exec it. The build requires a VERSION, so we might need
# this before we know its value.
VERSION = "0+bootstrap"


def ver(s):
    return s.replace("@VERSIONEER-VERSION@", VERSION)

def get(fn, add_ver=False, unquote=False, do_strip=False, do_readme=False):
    with open(fn) as f:
        text = f.read()

    if add_ver:
        text = ver(text)
    if unquote:
        text = text.replace("%", "%%")
    if do_strip:
        text = "".join(line for line in text.splitlines(keepends=True)
                         if not line.endswith("# --STRIP DURING BUILD\n"))
    if do_readme:
        text = text.replace("@README@", get("README.md"))
    return text

def get_vcs_list():
    project_path = Path(__file__).absolute().parent / "src"
    return [filename
            for filename
            in os.listdir(str(project_path))
            if Path.is_dir(project_path / filename) and filename != "__pycache__"]

def generate_long_version_py(VCS):
    s = io.StringIO()
    s.write(get(f"src/{VCS}/long_header.py", add_ver=True, do_strip=True))
    for piece in ["src/subprocess_helper.py",
                  "src/from_parentdir.py",
                  f"src/{VCS}/from_keywords.py",
                  f"src/{VCS}/from_vcs.py",
                  "src/render.py",
                  f"src/{VCS}/long_get_versions.py"]:
        s.write(get(piece, unquote=True, do_strip=True))
    return s.getvalue()

def generate_versioneer_py():
    s = io.StringIO()
    s.write(get("src/header.py", add_ver=True, do_readme=True, do_strip=True))
    s.write(get("src/subprocess_helper.py", do_strip=True))

    for VCS in get_vcs_list():
        s.write(f"LONG_VERSION_PY['{VCS}'] = r'''\n")
        s.write(generate_long_version_py(VCS))
        s.write("'''\n")
        s.write("\n\n")

        s.write(get(f"src/{VCS}/from_keywords.py", do_strip=True))
        s.write(get(f"src/{VCS}/from_vcs.py", do_strip=True))

        s.write(get(f"src/{VCS}/install.py", do_strip=True))

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

        s = Path("src/installer.py").read_text()
        s = ver(s.replace("@VERSIONEER-INSTALLER@", v_b64))
        with tempfile.TemporaryDirectory() as tempdir:
            installer = Path(tempdir) / "versioneer.py"
            installer.write_text(s)

            self.package_dir.update({'': os.path.relpath(installer.parent)})
            rc = build_py.run(self)
        return rc

# The structure of versioneer, with its components that are compiled into a single file,
# makes it unsuitable for development mode.
class develop(develop):
    def run(self):
        raise RuntimeError("Versioneer cannot be installed in developer/editable mode.")

try:
    import versioneer
except ImportError:
    # Bootstrap a versioneer module until it's built
    from importlib import util as ilu
    versioneer = ilu.module_from_spec(ilu.spec_from_loader('versioneer', loader=None))
    exec(generate_versioneer_py(), versioneer.__dict__)

VERSION = versioneer.get_version()


setup(
    version=VERSION,
    py_modules=["versioneer"],
    cmdclass=versioneer.get_cmdclass({
        "build_py": my_build_py,
        "make_versioneer": make_versioneer,
        "make_long_version_py_git": make_long_version_py_git,
        "develop": develop,
    })
)
