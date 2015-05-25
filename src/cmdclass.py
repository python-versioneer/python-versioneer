import os, sys # --STRIP DURING BUILD
from distutils.command.build import build as _build # --STRIP DURING BUILD
from distutils.command.sdist import sdist as _sdist # --STRIP DURING BUILD
from distutils.core import Command # --STRIP DURING BUILD
LONG_VERSION_PY = {} # --STRIP DURING BUILD
def get_version(): pass # --STRIP DURING BUILD
def get_versions(): pass # --STRIP DURING BUILD
def get_config(): pass # --STRIP DURING BUILD
def write_to_version_file(): pass # --STRIP DURING BUILD


class cmd_version(Command):
    description = "report generated version string"
    user_options = []
    boolean_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        vers = get_versions()
        print("Version is currently: %s" % vers["version"])
        if vers["error"]:
            print("error: %s" % vers["error"])


class cmd_build(_build):
    def run(self):
        cfg = get_config()
        versions = get_versions()
        _build.run(self)
        # now locate _version.py in the new build/ directory and replace it
        # with an updated value
        if cfg.versionfile_build:
            target_versionfile = os.path.join(self.build_lib,
                                              cfg.versionfile_build)
            print("UPDATING %s" % target_versionfile)
            write_to_version_file(target_versionfile, versions)

if 'cx_Freeze' in sys.modules:  # cx_freeze enabled?
    from cx_Freeze.dist import build_exe as _build_exe

    class cmd_build_exe(_build_exe):
        def run(self):
            cfg = get_config()
            versions = get_versions()
            target_versionfile = cfg.versionfile_source
            print("UPDATING %s" % target_versionfile)
            write_to_version_file(target_versionfile, versions)

            _build_exe.run(self)
            os.unlink(target_versionfile)
            with open(cfg.versionfile_source, "w") as f:
                assert cfg.VCS is not None, "please set versioneer.VCS"
                LONG = LONG_VERSION_PY[cfg.VCS]
                f.write(LONG % {"DOLLAR": "$",
                                "STYLE": cfg.style,
                                "TAG_PREFIX": cfg.tag_prefix,
                                "PARENTDIR_PREFIX": cfg.parentdir_prefix,
                                "VERSIONFILE_SOURCE": cfg.versionfile_source,
                                })


class cmd_sdist(_sdist):
    def run(self):
        versions = get_versions()
        self._versioneer_generated_versions = versions
        # unless we update this, the command will keep using the old version
        self.distribution.metadata.version = versions["version"]
        return _sdist.run(self)

    def make_release_tree(self, base_dir, files):
        cfg = get_config()
        _sdist.make_release_tree(self, base_dir, files)
        # now locate _version.py in the new base_dir directory (remembering
        # that it may be a hardlink) and replace it with an updated value
        target_versionfile = os.path.join(base_dir, cfg.versionfile_source)
        print("UPDATING %s" % target_versionfile)
        write_to_version_file(target_versionfile,
                              self._versioneer_generated_versions)


def get_cmdclass():
    cmds = {'version': cmd_version,
            'build': cmd_build,
            'sdist': cmd_sdist,
            }
    if 'cx_Freeze' in sys.modules:  # cx_freeze enabled?
        cmds['build_exe'] = cmd_build_exe
        del cmds['build']

    return cmds
