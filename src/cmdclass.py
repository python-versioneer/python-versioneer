

class cmd_version(Command):
    description = "report generated version string"
    user_options = []
    boolean_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        ver = get_version(verbose=True)
        print("Version is currently: %s" % ver)


class cmd_build(_build):
    def run(self):
        versions = get_versions(verbose=True)
        _build.run(self)
        # now locate _version.py in the new build/ directory and replace it
        # with an updated value
        if versionfile_build:
            target_versionfile = os.path.join(self.build_lib,
                                              versionfile_build)
            print("UPDATING %s" % target_versionfile)
            write_to_version_file(target_versionfile, versions)

if 'cx_Freeze' in sys.modules:  # cx_freeze enabled?
    from cx_Freeze.dist import build_exe as _build_exe

    class cmd_build_exe(_build_exe):
        def run(self):
            versions = get_versions(verbose=True)
            target_versionfile = versionfile_source
            print("UPDATING %s" % target_versionfile)
            write_to_version_file(target_versionfile, versions)

            _build_exe.run(self)
            os.unlink(target_versionfile)
            with open(versionfile_source, "w") as f:
                assert VCS is not None, "please set versioneer.VCS"
                LONG = LONG_VERSION_PY[VCS]
                f.write(LONG % {"DOLLAR": "$",
                                "TAG_PREFIX": tag_prefix,
                                "PARENTDIR_PREFIX": parentdir_prefix,
                                "VERSIONFILE_SOURCE": versionfile_source,
                                })


class cmd_sdist(_sdist):
    def run(self):
        versions = get_versions(verbose=True)
        self._versioneer_generated_versions = versions
        # unless we update this, the command will keep using the old version
        self.distribution.metadata.version = versions["version"]
        return _sdist.run(self)

    def make_release_tree(self, base_dir, files):
        _sdist.make_release_tree(self, base_dir, files)
        # now locate _version.py in the new base_dir directory (remembering
        # that it may be a hardlink) and replace it with an updated value
        target_versionfile = os.path.join(base_dir, versionfile_source)
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
