
import os, sys  # --STRIP DURING BUILD
def get_config(): pass # --STRIP DURING BUILD
def get_root(): pass # --STRIP DURING BUILD
LONG_VERSION_PY = {} # --STRIP DURING BUILD
def do_vcs_install(): pass # --STRIP DURING BUILD

INIT_PY_SNIPPET = """
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
"""


def do_setup():
    cfg = get_config()
    print(" creating %s" % cfg.versionfile_source)
    with open(cfg.versionfile_source, "w") as f:
        assert cfg.VCS is not None, "please set versioneer.VCS"
        LONG = LONG_VERSION_PY[cfg.VCS]
        f.write(LONG % {"DOLLAR": "$",
                        "TAG_PREFIX": cfg.tag_prefix,
                        "PARENTDIR_PREFIX": cfg.parentdir_prefix,
                        "VERSIONFILE_SOURCE": cfg.versionfile_source,
                        })

    ipy = os.path.join(os.path.dirname(cfg.versionfile_source),
                       "__init__.py")
    if os.path.exists(ipy):
        try:
            with open(ipy, "r") as f:
                old = f.read()
        except EnvironmentError:
            old = ""
        if INIT_PY_SNIPPET not in old:
            print(" appending to %s" % ipy)
            with open(ipy, "a") as f:
                f.write(INIT_PY_SNIPPET)
        else:
            print(" %s unmodified" % ipy)
    else:
        print(" %s doesn't exist, ok" % ipy)
        ipy = None

    # Make sure both the top-level "versioneer.py" and versionfile_source
    # (PKG/_version.py, used by runtime code) are in MANIFEST.in, so
    # they'll be copied into source distributions. Pip won't be able to
    # install the package without this.
    manifest_in = os.path.join(get_root(), "MANIFEST.in")
    simple_includes = set()
    try:
        with open(manifest_in, "r") as f:
            for line in f:
                if line.startswith("include "):
                    for include in line.split()[1:]:
                        simple_includes.add(include)
    except EnvironmentError:
        pass
    # That doesn't cover everything MANIFEST.in can do
    # (http://docs.python.org/2/distutils/sourcedist.html#commands), so
    # it might give some false negatives. Appending redundant 'include'
    # lines is safe, though.
    if "versioneer.py" not in simple_includes:
        print(" appending 'versioneer.py' to MANIFEST.in")
        with open(manifest_in, "a") as f:
            f.write("include versioneer.py\n")
    else:
        print(" 'versioneer.py' already in MANIFEST.in")
    if cfg.versionfile_source not in simple_includes:
        print(" appending versionfile_source ('%s') to MANIFEST.in" %
              cfg.versionfile_source)
        with open(manifest_in, "a") as f:
            f.write("include %s\n" % cfg.versionfile_source)
    else:
        print(" versionfile_source already in MANIFEST.in")

    # Make VCS-specific changes. For git, this means creating/changing
    # .gitattributes to mark _version.py for export-time keyword
    # substitution.
    do_vcs_install(manifest_in, cfg.versionfile_source, ipy)


def scan_setup_py():
    found = set()
    with open("setup.py", "r") as f:
        for line in f.readlines():
            if "import versioneer" in line:
                found.add("import")
            if "versioneer.get_cmdclass()" in line:
                found.add("cmdclass")
            if "versioneer.get_version()" in line:
                found.add("get_version")
    if len(found) != 3:
        print("")
        print("Your setup.py appears to be missing some important items")
        print("(but I might be wrong). Please make sure it has something")
        print("roughly like the following:")
        print("")
        print(" import versioneer")
        print(" setup( version=versioneer.get_version(),")
        print("        cmdclass=versioneer.get_cmdclass(),  ...)")
        print("")

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "setup":
        do_setup()
        scan_setup_py()
