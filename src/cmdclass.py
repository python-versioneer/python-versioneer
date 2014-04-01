def get_vcs_code():
    assert VCS is not None, "please set versioneer.VCS"
    long_ = LONG_VERSION_PY[VCS]
    complete = long_ % { "DOLLAR": "$",
                         "TAG_PREFIX": tag_prefix,
                         "PARENTDIR_PREFIX": parentdir_prefix,
                         "VERSIONFILE_SOURCE": versionfile_source,
                         "VERSION_STRING_TEMPLATE": version_string_template }

    complete = complete.replace('\\\\', '\\')

    try:
        vcs_settings[VCS]
    except KeyError:
        pass
    else:
        new_lines = []
        for k, v in vcs_settings[VCS].items():
            value_escaped = v.replace("\\", "\\\\").replace("\"", "\\\"")
            new_lines.append("%s_%s = \"%s\"" % (VCS, k, value_escaped))

        # Add VCS-specific assignments to top of _version.py .
# TODO(dustin): We might want to put these below the file-version and comments.
        complete = "\n".join(new_lines) + "\n" + complete

    return complete

class cmd_version(Command):
    description = "report generated version string"
    user_options = []
    boolean_options = ["everything", "verbose"]
    def initialize_options(self):
        self.everything = False
        self.verbose = False
    def finalize_options(self):
        pass
    def run(self):
        ver = get_version(verbose=self.verbose)
        print("Version is currently: %s" % ver)
        if self.everything:
            versions = versioneer.get_versions(verbose=self.verbose)
            for k in sorted(versions):
                print("%s:%s" % (k, versions[k]))


class cmd_build(_build):
    def run(self):
        versions = get_versions(verbose=True)
        _build.run(self)
        # now locate _version.py in the new build/ directory and replace it
        # with an updated value
        target_versionfile = os.path.join(self.build_lib, versionfile_build)
        print("UPDATING %s" % target_versionfile)
        os.unlink(target_versionfile)
        with open(target_versionfile, "w") as f:
            f.write(build_short_version_py(versions) % versions)

if 'cx_Freeze' in sys.modules:  # cx_freeze enabled?
    from cx_Freeze.dist import build_exe as _build_exe

    class cmd_build_exe(_build_exe):
        def run(self):
            versions = get_versions(verbose=True)
            target_versionfile = versionfile_source
            print("UPDATING %s" % target_versionfile)
            os.unlink(target_versionfile)
            with open(target_versionfile, "w") as f:
                f.write(build_short_version_py(versions) % versions)

            _build_exe.run(self)
            os.unlink(target_versionfile)
            with open(versionfile_source, "w") as f:
                f.write(get_vcs_code())


class cmd_sdist(_sdist):
    def run(self):
        versions = get_versions(verbose=True)
        self._versioneer_generated_versions = versions
        # unless we update this, the command will keep using the old version
        self.distribution.metadata.version = versions["describe"] # XXX
        return _sdist.run(self)

    def make_release_tree(self, base_dir, files):
# TODO(dustin): Fixed bug by defining this. Can we reduce the two separate 
#               calls in this class to a single one?
        versions = get_versions(verbose=True)
        _sdist.make_release_tree(self, base_dir, files)
        # now locate _version.py in the new base_dir directory (remembering
        # that it may be a hardlink) and replace it with an updated value
        target_versionfile = os.path.join(base_dir, versionfile_source)
        print("UPDATING %s" % target_versionfile)
        os.unlink(target_versionfile)
        with open(target_versionfile, "w") as f:
            f.write(build_short_version_py(versions) % self._versioneer_generated_versions)

INIT_PY_SNIPPET = """
from ._version import get_versions
__version__ = get_versions()['default']
del get_versions
"""


class cmd_versioneer(Command):
    description = "install/upgrade Versioneer files: __init__.py SRC/_version.py"
    user_options = []
    boolean_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        """Create the versioneer.py file."""

        print(" creating %s" % versionfile_source)
        with open(versionfile_source, "w") as f:
            f.write(get_vcs_code())

        ipy = os.path.join(os.path.dirname(versionfile_source), "__init__.py")
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
        if versionfile_source not in simple_includes:
            print(" appending versionfile_source ('%s') to MANIFEST.in" %
                  versionfile_source)
            with open(manifest_in, "a") as f:
                f.write("include %s\n" % versionfile_source)
        else:
            print(" versionfile_source already in MANIFEST.in")

        # Make VCS-specific changes. For git, this means creating/changing
        # .gitattributes to mark _version.py for export-time keyword
        # substitution.
        
        do_vcs_install_f = getattr(sys.modules[__name__], VCS + '_do_vcs_install')
        do_vcs_install_f(manifest_in, versionfile_source, ipy)

def get_cmdclass():
    """Returns a mapping of subcommand handlers for setup.py ."""

    cmds = {'version': cmd_version,
            'versioneer': cmd_versioneer,
            'build': cmd_build,
            'sdist': cmd_sdist,
            }
    if 'cx_Freeze' in sys.modules:  # cx_freeze enabled?
        cmds['build_exe'] = cmd_build_exe
        del cmds['build']

    return cmds
