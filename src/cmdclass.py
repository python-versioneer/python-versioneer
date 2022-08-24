import os, sys # --STRIP DURING BUILD
LONG_VERSION_PY = {} # --STRIP DURING BUILD
def get_version(): pass # --STRIP DURING BUILD
def get_versions(): pass # --STRIP DURING BUILD
def get_root(): pass # --STRIP DURING BUILD
def get_config_from_root(): pass # --STRIP DURING BUILD
def write_to_version_file(): pass # --STRIP DURING BUILD


def get_cmdclass(cmdclass=None):
    """Get the custom setuptools subclasses used by Versioneer.

    If the package uses a different cmdclass (e.g. one from numpy), it
    should be provide as an argument.
    """
    if "versioneer" in sys.modules:
        del sys.modules["versioneer"]
        # this fixes the "python setup.py develop" case (also 'install' and
        # 'easy_install .'), in which subdependencies of the main project are
        # built (using setup.py bdist_egg) in the same python process. Assume
        # a main project A and a dependency B, which use different versions
        # of Versioneer. A's setup.py imports A's Versioneer, leaving it in
        # sys.modules by the time B's setup.py is executed, causing B to run
        # with the wrong versioneer. Setuptools wraps the sub-dep builds in a
        # sandbox that restores sys.modules to it's pre-build state, so the
        # parent is protected against the child's "import versioneer". By
        # removing ourselves from sys.modules here, before the child build
        # happens, we protect the child from the parent's versioneer too.
        # Also see https://github.com/python-versioneer/python-versioneer/issues/52

    cmds = {} if cmdclass is None else cmdclass.copy()

    # we add "version" to setuptools
    from setuptools import Command

    class cmd_version(Command):
        description = "report generated version string"
        user_options = []
        boolean_options = []

        def initialize_options(self):
            pass

        def finalize_options(self):
            pass

        def run(self):
            vers = get_versions(verbose=True)
            print("Version: %s" % vers["version"])
            print(" full-revisionid: %s" % vers.get("full-revisionid"))
            print(" dirty: %s" % vers.get("dirty"))
            print(" date: %s" % vers.get("date"))
            if vers["error"]:
                print(" error: %s" % vers["error"])
    cmds["version"] = cmd_version

    # we override "build_py" in setuptools
    #
    # most invocation pathways end up running build_py:
    #  distutils/build -> build_py
    #  distutils/install -> distutils/build ->..
    #  setuptools/bdist_wheel -> distutils/install ->..
    #  setuptools/bdist_egg -> distutils/install_lib -> build_py
    #  setuptools/install -> bdist_egg ->..
    #  setuptools/develop -> ?
    #  pip install:
    #   copies source tree to a tempdir before running egg_info/etc
    #   if .git isn't copied too, 'git describe' will fail
    #   then does setup.py bdist_wheel, or sometimes setup.py install
    #  setup.py egg_info -> ?

    # pip install -e . and setuptool/editable_wheel will invoke build_py
    # but the build_py command is not expected to copy any files.

    # we override different "build_py" commands for both environments
    if 'build_py' in cmds:
        _build_py = cmds['build_py']
    else:
        from setuptools.command.build_py import build_py as _build_py

    class cmd_build_py(_build_py):
        def run(self):
            root = get_root()
            cfg = get_config_from_root(root)
            versions = get_versions()
            _build_py.run(self)
            if getattr(self, "editable_mode", False):
                # During editable installs `.py` and data files are
                # not copied to build_lib
                return
            # now locate _version.py in the new build/ directory and replace
            # it with an updated value
            if cfg.versionfile_build:
                target_versionfile = os.path.join(self.build_lib,
                                                  cfg.versionfile_build)
                print("UPDATING %s" % target_versionfile)
                write_to_version_file(target_versionfile, versions)
    cmds["build_py"] = cmd_build_py

    if 'build_ext' in cmds:
        _build_ext = cmds['build_ext']
    else:
        from setuptools.command.build_ext import build_ext as _build_ext

    class cmd_build_ext(_build_ext):
        def run(self):
            root = get_root()
            cfg = get_config_from_root(root)
            versions = get_versions()
            _build_ext.run(self)
            if self.inplace:
                # build_ext --inplace will only build extensions in
                # build/lib<..> dir with no _version.py to write to.
                # As in place builds will already have a _version.py
                # in the module dir, we do not need to write one.
                return
            # now locate _version.py in the new build/ directory and replace
            # it with an updated value
            target_versionfile = os.path.join(self.build_lib,
                                              cfg.versionfile_build)
            if not os.path.exists(target_versionfile):
                print(f"Warning: {target_versionfile} does not exist, skipping "
                      "version update. This can happen if you are running build_ext "
                      "without first running build_py.")
                return
            print("UPDATING %s" % target_versionfile)
            write_to_version_file(target_versionfile, versions)
    cmds["build_ext"] = cmd_build_ext

    if "cx_Freeze" in sys.modules:  # cx_freeze enabled?
        from cx_Freeze.dist import build_exe as _build_exe
        # nczeczulin reports that py2exe won't like the pep440-style string
        # as FILEVERSION, but it can be used for PRODUCTVERSION, e.g.
        # setup(console=[{
        #   "version": versioneer.get_version().split("+", 1)[0], # FILEVERSION
        #   "product_version": versioneer.get_version(),
        #   ...

        class cmd_build_exe(_build_exe):
            def run(self):
                root = get_root()
                cfg = get_config_from_root(root)
                versions = get_versions()
                target_versionfile = cfg.versionfile_source
                print("UPDATING %s" % target_versionfile)
                write_to_version_file(target_versionfile, versions)

                _build_exe.run(self)
                os.unlink(target_versionfile)
                with open(cfg.versionfile_source, "w") as f:
                    LONG = LONG_VERSION_PY[cfg.VCS]
                    f.write(LONG %
                            {"DOLLAR": "$",
                             "STYLE": cfg.style,
                             "TAG_PREFIX": cfg.tag_prefix,
                             "PARENTDIR_PREFIX": cfg.parentdir_prefix,
                             "VERSIONFILE_SOURCE": cfg.versionfile_source,
                             })
        cmds["build_exe"] = cmd_build_exe
        del cmds["build_py"]

    if 'py2exe' in sys.modules:  # py2exe enabled?
        try:
            from py2exe.setuptools_buildexe import py2exe as _py2exe
        except ImportError:
            from py2exe.distutils_buildexe import py2exe as _py2exe

        class cmd_py2exe(_py2exe):
            def run(self):
                root = get_root()
                cfg = get_config_from_root(root)
                versions = get_versions()
                target_versionfile = cfg.versionfile_source
                print("UPDATING %s" % target_versionfile)
                write_to_version_file(target_versionfile, versions)

                _py2exe.run(self)
                os.unlink(target_versionfile)
                with open(cfg.versionfile_source, "w") as f:
                    LONG = LONG_VERSION_PY[cfg.VCS]
                    f.write(LONG %
                            {"DOLLAR": "$",
                             "STYLE": cfg.style,
                             "TAG_PREFIX": cfg.tag_prefix,
                             "PARENTDIR_PREFIX": cfg.parentdir_prefix,
                             "VERSIONFILE_SOURCE": cfg.versionfile_source,
                             })
        cmds["py2exe"] = cmd_py2exe

    # sdist farms its file list building out to egg_info
    if 'egg_info' in cmds:
        _sdist = cmds['egg_info']
    else:
        from setuptools.command.egg_info import egg_info as _egg_info

    class cmd_egg_info(_egg_info):
        def find_sources(self):
            # egg_info.find_sources builds the manifest list and writes it
            # in one shot
            super().find_sources()

            # Modify the filelist and normalize it
            root = get_root()
            cfg = get_config_from_root(root)
            self.filelist.append('versioneer.py')
            if cfg.versionfile_source:
                # There are rare cases where versionfile_source might not be
                # included by default, so we must be explicit
                self.filelist.append(cfg.versionfile_source)
            self.filelist.sort()
            self.filelist.remove_duplicates()

            # The write method is hidden in the manifest_maker instance that
            # generated the filelist and was thrown away
            # We will instead replicate their final normalization (to unicode,
            # and POSIX-style paths)
            from setuptools import unicode_utils
            normalized = [unicode_utils.filesys_decode(f).replace(os.sep, '/')
                          for f in self.filelist.files]

            manifest_filename = os.path.join(self.egg_info, 'SOURCES.txt')
            with open(manifest_filename, 'w') as fobj:
                fobj.write('\n'.join(normalized))

    cmds['egg_info'] = cmd_egg_info

    # we override different "sdist" commands for both environments
    if 'sdist' in cmds:
        _sdist = cmds['sdist']
    else:
        from setuptools.command.sdist import sdist as _sdist

    class cmd_sdist(_sdist):
        def run(self):
            versions = get_versions()
            self._versioneer_generated_versions = versions
            # unless we update this, the command will keep using the old
            # version
            self.distribution.metadata.version = versions["version"]
            return _sdist.run(self)

        def make_release_tree(self, base_dir, files):
            root = get_root()
            cfg = get_config_from_root(root)
            _sdist.make_release_tree(self, base_dir, files)
            # now locate _version.py in the new base_dir directory
            # (remembering that it may be a hardlink) and replace it with an
            # updated value
            target_versionfile = os.path.join(base_dir, cfg.versionfile_source)
            print("UPDATING %s" % target_versionfile)
            write_to_version_file(target_versionfile,
                                  self._versioneer_generated_versions)
    cmds["sdist"] = cmd_sdist

    return cmds
