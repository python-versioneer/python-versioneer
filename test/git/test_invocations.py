import os, sys, shutil, unittest, tempfile, tarfile, virtualenv, warnings
from wheel.bdist_wheel import get_abi_tag, get_platform
from packaging.tags import interpreter_name, interpreter_version

sys.path.insert(0, "src")
from from_file import versions_from_file
import common


pyver_major = "py%d" % sys.version_info[0]
pyver = "py%d.%d" % sys.version_info[:2]


# For binary wheels with native code
impl, impl_ver = interpreter_name(), interpreter_version()
abi = get_abi_tag()
try:
    plat = get_platform(None)
except TypeError:  # wheel < 0.34
    plat = get_platform()


class _Invocations(common.Common):
    def setUp(self):
        if False:
            # when debugging, put the generated files in a predictable place
            self.testdir = os.path.abspath("t")
            if os.path.exists(self.testdir):
                return
            os.mkdir(self.testdir)
        else:
            self.testdir = tempfile.mkdtemp()
        os.mkdir(self.subpath("cache"))
        os.mkdir(self.subpath("cache", "distutils"))
        os.mkdir(self.subpath("cache", "setuptools"))
        self.gitdir = None
        self.projdir = None

    def make_venv(self, mode):
        if not os.path.exists(self.subpath("venvs")):
            os.mkdir(self.subpath("venvs"))
        venv_dir = self.subpath("venvs/%s" % mode)
        # python3 on OS-X uses a funky two-part executable and an environment
        # variable to communicate between them. If this variable is still set
        # by the time a virtualenv's 'pip' or 'python' is run, and if that
        # command spawns another sys.executable underneath it, that second
        # child may use the wrong python, and can install things into the
        # real system library instead of the virtualenv. Invoking
        # virtualenv.create_environment() clears this as a side-effect, but
        # to make things safe I'll just clear this now. See
        # https://github.com/pypa/virtualenv/issues/322 and
        # https://bugs.python.org/issue22490 for some hints. I tried
        # switching to 'venv' on py3, but only py3.4 includes pip, and even
        # then it's an ancient version.
        os.environ.pop("__PYVENV_LAUNCHER__", None)
        virtualenv.logger = virtualenv.Logger([]) # hush
        # virtualenv causes DeprecationWarning/ResourceWarning on py3
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            virtualenv.create_environment(venv_dir)
            self.run_in_venv(venv_dir, venv_dir,
                             'pip', 'install', '-U',
                             'pip', 'wheel', 'packaging')
        return venv_dir

    def run_in_venv(self, venv, workdir, command, *args):
        bins = {"python": os.path.join(venv, "bin", "python"),
                "pip": os.path.join(venv, "bin", "pip"),
                "rundemo": os.path.join(venv, "bin", "rundemo"),
                "easy_install": os.path.join(venv, "bin", "easy_install"),
                }
        if command == "pip":
            args = ["--isolated", "--no-cache-dir"] + list(args)
        return self.command(bins[command], *args, workdir=workdir)

    def check_in_venv(self, venv):
        out = self.run_in_venv(venv, venv, "rundemo")
        v = dict([line.split(":", 1) for line in out.splitlines()])
        self.assertEqual(v["version"], "2.0")
        return v

    def check_in_venv_withlib(self, venv):
        v = self.check_in_venv(venv)
        self.assertEqual(v["demolib"], "1.0")

    # "demolib" has a version of 1.0 and is built with distutils
    # "demoapp2-distutils" is v2.0, uses distutils, and has no deps
    # "demoapp2-setuptools" is v2.0, uses setuptools, and depends on demolib

    # repos and unpacked git-archive tarballs come in two flavors: normal (in
    # which the setup.py/setup.cfg/versioneer.py files live in the root of
    # the source tree), and "subproject" (where they live in a subdirectory).
    # sdists are always "normal" (although they might have come from either
    # normal or subproject -style source trees), and wheels/eggs don't have
    # these files at all.

    # TODO: git-archive subproject-flavor

    def make_demolib_sdist(self):
        # create an sdist of demolib-1.0 . for the *lib*, we only use the
        # tarball, never the repo.
        demolib_sdist = self.subpath("cache", "demolib-1.0.tar")
        if os.path.exists(demolib_sdist):
            return demolib_sdist
        libdir = self.subpath("build-demolib")
        shutil.copytree("test/demolib", libdir)
        shutil.copy("versioneer.py", libdir)
        self.git("init", workdir=libdir)
        self.python("versioneer.py", "setup", workdir=libdir)
        self.git("add", "--all", workdir=libdir)
        self.git("commit", "-m", "comment", workdir=libdir)
        self.git("tag", "demolib-1.0", workdir=libdir)
        self.python("setup.py", "sdist", "--format=tar", workdir=libdir)
        created = os.path.join(libdir, "dist", "demolib-1.0.tar")
        self.assertTrue(os.path.exists(created))
        shutil.copyfile(created, demolib_sdist)
        return demolib_sdist

    def make_linkdir(self):
        # create/populate a fake pypi directory for use with --find-links
        linkdir = self.subpath("linkdir")
        if os.path.exists(linkdir):
            return linkdir
        os.mkdir(linkdir)
        demolib_sdist = self.make_demolib_sdist()
        shutil.copy(demolib_sdist, linkdir)
        return linkdir

    def make_empty_indexdir(self):
        indexdir = self.subpath("indexdir")
        if os.path.exists(indexdir):
            return indexdir
        os.mkdir(indexdir)
        return indexdir

    def make_distutils_repo(self):
        # create a clean repo of demoapp2-distutils at 2.0
        repodir = self.subpath("demoapp2-distutils-repo")
        if os.path.exists(repodir):
            shutil.rmtree(repodir)
        shutil.copytree("test/demoapp2-distutils", repodir)
        shutil.copy("versioneer.py", repodir)
        self.git("init", workdir=repodir)
        self.python("versioneer.py", "setup", workdir=repodir)
        self.git("add", "--all", workdir=repodir)
        self.git("commit", "-m", "comment", workdir=repodir)
        self.git("tag", "demoapp2-2.0", workdir=repodir)
        return repodir

    def make_distutils_repo_subproject(self):
        # create a clean repo of demoapp2-distutils at 2.0
        repodir = self.subpath("demoapp2-distutils-repo-subproject")
        if os.path.exists(repodir):
            shutil.rmtree(repodir)
        shutil.copytree("test/demoapp2-distutils-subproject", repodir)
        projectdir = os.path.join(repodir, "subproject")
        shutil.copy("versioneer.py", projectdir)
        self.git("init", workdir=repodir)
        self.python("versioneer.py", "setup", workdir=projectdir)
        self.git("add", "--all", workdir=repodir)
        self.git("commit", "-m", "comment", workdir=repodir)
        self.git("tag", "demoapp2-2.0", workdir=repodir)
        return projectdir

    def make_distutils_wheel_with_pip(self):
        # create an wheel of demoapp2-distutils at 2.0
        wheelname = "demoapp2-2.0-%s-none-any.whl" % pyver_major
        demoapp2_distutils_wheel = self.subpath("cache", "distutils", wheelname)
        if os.path.exists(demoapp2_distutils_wheel):
            return demoapp2_distutils_wheel
        repodir = self.make_distutils_repo()
        venv = self.make_venv("make-distutils-wheel-with-pip")
        self.run_in_venv(venv, repodir,
                         "pip", "wheel", "--wheel-dir", "wheelhouse",
                         "--no-index",# "--find-links", linkdir,
                         ".")
        created = os.path.join(repodir, "wheelhouse", wheelname)
        self.assertTrue(os.path.exists(created), created)
        shutil.copyfile(created, demoapp2_distutils_wheel)
        return demoapp2_distutils_wheel

    def make_distutils_sdist(self):
        # create an sdist tarball of demoapp2-distutils at 2.0
        demoapp2_distutils_sdist = self.subpath("cache", "distutils",
                                                "demoapp2-2.0.tar")
        if os.path.exists(demoapp2_distutils_sdist):
            return demoapp2_distutils_sdist
        repodir = self.make_distutils_repo()
        self.python("setup.py", "sdist", "--format=tar", workdir=repodir)
        created = os.path.join(repodir, "dist", "demoapp2-2.0.tar")
        self.assertTrue(os.path.exists(created), created)
        shutil.copyfile(created, demoapp2_distutils_sdist)
        return demoapp2_distutils_sdist

    def make_distutils_sdist_subproject(self):
        demoapp2_distutils_sdist = self.subpath("cache", "distutils",
                                                "demoapp2-subproject-2.0.tar")
        if os.path.exists(demoapp2_distutils_sdist):
            return demoapp2_distutils_sdist
        projectdir = self.make_distutils_repo_subproject()
        self.python("setup.py", "sdist", "--format=tar", workdir=projectdir)
        created = os.path.join(projectdir, "dist", "demoapp2-2.0.tar")
        # if that gets the version wrong, it will make the wrong tarball, and
        # this check will fail
        self.assertTrue(os.path.exists(created), created)
        shutil.copyfile(created, demoapp2_distutils_sdist)
        return demoapp2_distutils_sdist

    def make_distutils_unpacked(self):
        sdist = self.make_distutils_sdist()
        unpack_into = self.subpath("demoapp2-distutils-unpacked")
        if os.path.exists(unpack_into):
            shutil.rmtree(unpack_into)
        os.mkdir(unpack_into)
        with tarfile.TarFile(sdist) as t:
            t.extractall(path=unpack_into)
        unpacked = os.path.join(unpack_into, "demoapp2-2.0")
        self.assertTrue(os.path.exists(unpacked))
        return unpacked

    def make_distutils_subproject_unpacked(self):
        sdist = self.make_distutils_sdist_subproject()
        unpack_into = self.subpath("demoapp2-distutils-unpacked-subproject")
        if os.path.exists(unpack_into):
            shutil.rmtree(unpack_into)
        os.mkdir(unpack_into)
        with tarfile.TarFile(sdist) as t:
            t.extractall(path=unpack_into)
        unpacked = os.path.join(unpack_into, "demoapp2-2.0")
        self.assertTrue(os.path.exists(unpacked))
        return unpacked

    def make_setuptools_repo(self):
        # create a clean repo of demoapp2-setuptools at 2.0
        repodir = self.subpath("demoapp2-setuptools-repo")
        if os.path.exists(repodir):
            shutil.rmtree(repodir)
        shutil.copytree("test/demoapp2-setuptools", repodir)
        shutil.copy("versioneer.py", repodir)
        self.git("init", workdir=repodir)
        self.python("versioneer.py", "setup", workdir=repodir)
        self.git("add", "--all", workdir=repodir)
        self.git("commit", "-m", "comment", workdir=repodir)
        self.git("tag", "demoapp2-2.0", workdir=repodir)
        return repodir

    def make_setuptools_extension_unpacked(self):
        sdist = self.make_setuptools_extension_sdist()
        unpack_into = self.subpath("demoappext-setuptools-unpacked")
        if os.path.exists(unpack_into):
            shutil.rmtree(unpack_into)
        os.mkdir(unpack_into)
        with tarfile.TarFile(sdist) as t:
            t.extractall(path=unpack_into)
        unpacked = os.path.join(unpack_into, "demoappext-2.0")
        self.assertTrue(os.path.exists(unpacked))
        return unpacked

    def make_setuptools_extension_sdist(self):
        # create an sdist tarball of demoappext-setuptools at 2.0
        demoappext_setuptools_sdist = self.subpath("cache", "setuptools",
                                                   "demoappext-2.0.tar")
        if os.path.exists(demoappext_setuptools_sdist):
            return demoappext_setuptools_sdist
        repodir = self.make_setuptools_extension_repo()
        self.python("setup.py", "sdist", "--format=tar", workdir=repodir)
        created = os.path.join(repodir, "dist", "demoappext-2.0.tar")
        self.assertTrue(os.path.exists(created), created)
        shutil.copyfile(created, demoappext_setuptools_sdist)
        return demoappext_setuptools_sdist

    def make_setuptools_extension_repo(self):
        # create a clean repo of demoappext-setuptools at 2.0
        repodir = self.subpath("demoappext-setuptools-repo")
        if os.path.exists(repodir):
            shutil.rmtree(repodir)
        # import ipdb; ipdb.set_trace()
        shutil.copytree("test/demoappext-setuptools", repodir)
        shutil.copy("versioneer.py", repodir)
        self.git("init", workdir=repodir)
        self.python("versioneer.py", "setup", workdir=repodir)
        self.git("add", "--all", workdir=repodir)
        self.git("commit", "-m", "comment", workdir=repodir)
        self.git("tag", "demoappext-2.0", workdir=repodir)
        return repodir

    def make_setuptools_repo_subproject(self):
        # create a clean repo of demoapp2-setuptools at 2.0
        repodir = self.subpath("demoapp2-setuptools-repo-subproject")
        if os.path.exists(repodir):
            shutil.rmtree(repodir)
        shutil.copytree("test/demoapp2-setuptools-subproject", repodir)
        projectdir = os.path.join(repodir, "subproject")
        shutil.copy("versioneer.py", projectdir)
        self.git("init", workdir=repodir)
        self.python("versioneer.py", "setup", workdir=projectdir)
        self.git("add", "--all", workdir=repodir)
        self.git("commit", "-m", "comment", workdir=repodir)
        self.git("tag", "demoapp2-2.0", workdir=repodir)
        return projectdir

    def make_setuptools_sdist(self):
        # create an sdist tarball of demoapp2-setuptools at 2.0
        demoapp2_setuptools_sdist = self.subpath("cache", "setuptools",
                                                 "demoapp2-2.0.tar")
        if os.path.exists(demoapp2_setuptools_sdist):
            return demoapp2_setuptools_sdist
        repodir = self.make_setuptools_repo()
        self.python("setup.py", "sdist", "--format=tar", workdir=repodir)
        created = os.path.join(repodir, "dist", "demoapp2-2.0.tar")
        self.assertTrue(os.path.exists(created), created)
        shutil.copyfile(created, demoapp2_setuptools_sdist)
        return demoapp2_setuptools_sdist

    def make_setuptools_sdist_subproject(self):
        demoapp2_setuptools_sdist = self.subpath("cache", "setuptools",
                                                 "demoapp2-subproject-2.0.tar")
        if os.path.exists(demoapp2_setuptools_sdist):
            return demoapp2_setuptools_sdist
        projectdir = self.make_setuptools_repo_subproject()
        self.python("setup.py", "sdist", "--format=tar", workdir=projectdir)
        created = os.path.join(projectdir, "dist", "demoapp2-2.0.tar")
        self.assertTrue(os.path.exists(created), created)
        shutil.copyfile(created, demoapp2_setuptools_sdist)
        return demoapp2_setuptools_sdist

    def make_setuptools_unpacked(self):
        sdist = self.make_setuptools_sdist()
        unpack_into = self.subpath("demoapp2-setuptools-unpacked")
        if os.path.exists(unpack_into):
            shutil.rmtree(unpack_into)
        os.mkdir(unpack_into)
        with tarfile.TarFile(sdist) as t:
            t.extractall(path=unpack_into)
        unpacked = os.path.join(unpack_into, "demoapp2-2.0")
        self.assertTrue(os.path.exists(unpacked))
        return unpacked

    def make_setuptools_subproject_unpacked(self):
        sdist = self.make_setuptools_sdist_subproject()
        unpack_into = self.subpath("demoapp2-setuptools-unpacked-subproject")
        if os.path.exists(unpack_into):
            shutil.rmtree(unpack_into)
        os.mkdir(unpack_into)
        with tarfile.TarFile(sdist) as t:
            t.extractall(path=unpack_into)
        unpacked = os.path.join(unpack_into, "demoapp2-2.0")
        self.assertTrue(os.path.exists(unpacked))
        return unpacked

    def make_setuptools_egg(self):
        # create an egg of demoapp2-setuptools at 2.0
        demoapp2_setuptools_egg = self.subpath("cache", "setuptools",
                                               "demoapp2-2.0-%s.egg" % pyver)
        if os.path.exists(demoapp2_setuptools_egg):
            return demoapp2_setuptools_egg
        repodir = self.make_setuptools_repo()
        self.python("setup.py", "bdist_egg", workdir=repodir)
        created = os.path.join(repodir, "dist", "demoapp2-2.0-%s.egg" % pyver)
        self.assertTrue(os.path.exists(created), created)
        shutil.copyfile(created, demoapp2_setuptools_egg)
        return demoapp2_setuptools_egg

    def make_setuptools_wheel_with_setup_py(self):
        # create an wheel of demoapp2-setuptools at 2.0
        wheelname = "demoapp2-2.0-%s-none-any.whl" % pyver_major
        demoapp2_setuptools_wheel = self.subpath("cache", "setuptools",
                                                 wheelname)
        if os.path.exists(demoapp2_setuptools_wheel):
            # there are two ways to make this .whl, and we need to exercise
            # both, so don't actually cache the results
            os.unlink(demoapp2_setuptools_wheel)
        repodir = self.make_setuptools_repo()
        self.python("setup.py", "bdist_wheel", workdir=repodir)
        created = os.path.join(repodir, "dist", wheelname)
        self.assertTrue(os.path.exists(created), created)
        shutil.copyfile(created, demoapp2_setuptools_wheel)
        return demoapp2_setuptools_wheel

    def make_setuptools_wheel_with_pip(self):
        # create an wheel of demoapp2-setuptools at 2.0
        wheelname = "demoapp2-2.0-%s-none-any.whl" % pyver_major
        demoapp2_setuptools_wheel = self.subpath("cache", "setuptools",
                                                 wheelname)
        if os.path.exists(demoapp2_setuptools_wheel):
            # there are two ways to make this .whl, and we need to exercise
            # both, so don't actually cache the results
            os.unlink(demoapp2_setuptools_wheel)
        linkdir = self.make_linkdir()
        repodir = self.make_setuptools_repo()
        venv = self.make_venv("make-setuptools-wheel-with-pip")
        self.run_in_venv(venv, repodir,
                         "pip", "wheel", "--wheel-dir", "wheelhouse",
                         "--no-index", "--find-links", linkdir,
                         ".")
        created = os.path.join(repodir, "wheelhouse", wheelname)
        self.assertTrue(os.path.exists(created), created)
        shutil.copyfile(created, demoapp2_setuptools_wheel)
        return demoapp2_setuptools_wheel

    def make_binary_wheelname(self, app):
        return "%s-2.0-%s-%s-%s.whl" % (app,
            "".join([impl, impl_ver]), abi, plat.replace("-", "_"))


class DistutilsRepo(_Invocations, unittest.TestCase):
    def test_build(self):
        repodir = self.make_distutils_repo()
        self.python("setup.py", "build", workdir=repodir)
        # test that the built _version.py is correct. Ideally we'd actually
        # run PYTHONPATH=.../build/lib build/scripts-PYVER/rundemo and check
        # the output, but that's more fragile than I want to deal with today
        fn = os.path.join(repodir, "build", "lib", "demo", "_version.py")
        data = versions_from_file(fn)
        self.assertEqual(data["version"], "2.0")

    def test_install(self):
        repodir = self.make_distutils_repo()
        venv = self.make_venv("distutils-repo-install")
        self.run_in_venv(venv, repodir, "python", "setup.py", "install")
        self.check_in_venv(venv)

    def test_install_subproject(self):
        projectdir = self.make_distutils_repo_subproject()
        venv = self.make_venv("distutils-repo-install-subproject")
        self.run_in_venv(venv, projectdir, "python", "setup.py", "install")
        self.check_in_venv(venv)

    def test_pip_wheel(self):
        self.make_distutils_wheel_with_pip()
        # asserts version as a side-effect

    def test_sdist(self):
        sdist = self.make_distutils_sdist() # asserts version as a side-effect
        # make sure we used distutils/sdist, not setuptools/sdist
        with tarfile.TarFile(sdist) as t:
            self.assertFalse("demoapp2-2.0/src/demoapp2.egg-info/PKG-INFO" in
                             t.getnames())

    def test_sdist_subproject(self):
        sdist = self.make_distutils_sdist_subproject()
        # make sure we used distutils/sdist, not setuptools/sdist
        with tarfile.TarFile(sdist) as t:
            self.assertFalse("demoapp2-2.0/src/demoapp2.egg-info/PKG-INFO" in
                             t.getnames())

    def test_pip_install(self):
        repodir = self.make_distutils_repo()
        venv = self.make_venv("distutils-repo-pip-install")
        self.run_in_venv(venv, repodir, "pip", "install", ".")
        self.check_in_venv(venv)

    @unittest.expectedFailure
    def test_pip_install_subproject(self):
        projectdir = self.make_distutils_repo_subproject()
        venv = self.make_venv("distutils-repo-pip-install-subproject")
        self.run_in_venv(venv, projectdir, "pip", "install", ".")
        self.check_in_venv(venv)

    def test_pip_install_from_afar(self):
        repodir = self.make_distutils_repo()
        venv = self.make_venv("distutils-repo-pip-install-from-afar")
        self.run_in_venv(venv, venv, "pip", "install", repodir)
        self.check_in_venv(venv)

    @unittest.expectedFailure
    def test_pip_install_from_afar_subproject(self):
        projectdir = self.make_distutils_repo_subproject()
        venv = self.make_venv("distutils-repo-pip-install-from-afar-subproject")
        self.run_in_venv(venv, venv, "pip", "install", projectdir)
        self.check_in_venv(venv)

    def test_pip_install_editable(self):
        repodir = self.make_distutils_repo()
        venv = self.make_venv("distutils-repo-pip-install-editable")
        self.run_in_venv(venv, repodir, "pip", "install", "--editable", ".")
        self.check_in_venv(venv)

    def test_pip_install_editable_subproject(self):
        projectdir = self.make_distutils_repo_subproject()
        venv = self.make_venv("distutils-repo-pip-install-editable-subproject")
        self.run_in_venv(venv, projectdir, "pip", "install", "--editable", ".")
        self.check_in_venv(venv)

class SetuptoolsRepo(_Invocations, unittest.TestCase):
    def test_install(self):
        repodir = self.make_setuptools_repo()
        demolib = self.make_demolib_sdist()
        venv = self.make_venv("setuptools-repo-install")
        # "setup.py install" doesn't take --no-index or --find-links, so we
        # pre-install the dependency
        self.run_in_venv(venv, venv, "pip", "install", demolib)
        self.run_in_venv(venv, repodir, "python", "setup.py", "install")
        self.check_in_venv_withlib(venv)

    def test_install_subproject(self):
        projectdir = self.make_setuptools_repo_subproject()
        demolib = self.make_demolib_sdist()
        venv = self.make_venv("setuptools-repo-install-subproject")
        # "setup.py install" doesn't take --no-index or --find-links, so we
        # pre-install the dependency
        self.run_in_venv(venv, venv, "pip", "install", demolib)
        self.run_in_venv(venv, projectdir, "python", "setup.py", "install")
        self.check_in_venv_withlib(venv)

    @unittest.skip("setuptools 'easy_install .': known to be broken")
    def test_easy_install(self):
        # This case still fails: the 'easy_install' command modifies the
        # repo's setup.cfg (copying our --index-url and --find-links
        # arguments into [easy_install]index_url= settings, so that any
        # dependencies setup_requires= builds will use them), which means the
        # repo is always "dirty", which creates an .egg with the wrong
        # version. I have not yet found a clean way to hook the easy_install
        # command to fix this: there is very little linkage between the
        # parent command (which could calculate the version before setup.cfg
        # is modified) and the command which builds the .egg. Leave it broken
        # for now.
        linkdir = self.make_linkdir()
        indexdir = self.make_empty_indexdir()
        repodir = self.make_setuptools_repo()
        venv = self.make_venv("setuptools-repo-easy-install")
        self.run_in_venv(venv, repodir,
                         "python", "setup.py", "easy_install",
                         "--index-url", indexdir, "--find-links", linkdir,
                         "."
                         )
        self.check_in_venv_withlib(venv)

    def test_develop(self):
        linkdir = self.make_linkdir()
        indexdir = self.make_empty_indexdir()
        repodir = self.make_setuptools_repo()
        venv = self.make_venv("setuptools-repo-develop")
        # "setup.py develop" takes --find-links and --index-url but not
        # --no-index
        self.run_in_venv(venv, repodir,
                         "python", "setup.py", "develop",
                         "--index-url", indexdir, "--find-links", linkdir,
                         )
        self.check_in_venv_withlib(venv)

    def test_develop_subproject(self):
        linkdir = self.make_linkdir()
        indexdir = self.make_empty_indexdir()
        projectdir = self.make_setuptools_repo_subproject()
        venv = self.make_venv("setuptools-repo-develop-subproject")
        # "setup.py develop" takes --find-links and --index-url but not
        # --no-index
        self.run_in_venv(venv, projectdir,
                         "python", "setup.py", "develop",
                         "--index-url", indexdir, "--find-links", linkdir,
                         )
        self.check_in_venv_withlib(venv)

    def test_egg(self):
        self.make_setuptools_egg() # asserts version as a side-effect

    def test_pip_wheel(self):
        self.make_setuptools_wheel_with_pip()
        # asserts version as a side-effect

    def test_bdist_wheel(self):
        self.make_setuptools_wheel_with_setup_py()
        # asserts version as a side-effect

    def test_sdist(self):
        sdist = self.make_setuptools_sdist() # asserts version as a side-effect
        # make sure we used setuptools/sdist, not distutils/sdist
        with tarfile.TarFile(sdist) as t:
            self.assertIn("demoapp2-2.0/src/demoapp2.egg-info/PKG-INFO", t.getnames())

    def test_sdist_subproject(self):
        sdist = self.make_setuptools_sdist_subproject()
        # make sure we used setuptools/sdist, not distutils/sdist
        with tarfile.TarFile(sdist) as t:
            self.assertIn("demoapp2-2.0/src/demoapp2.egg-info/PKG-INFO", t.getnames())

    def test_pip_install(self):
        linkdir = self.make_linkdir()
        repodir = self.make_setuptools_repo()
        venv = self.make_venv("setuptools-repo-pip-install")
        self.run_in_venv(venv, repodir, "pip", "install", ".",
                         "--no-index", "--find-links", linkdir)
        self.check_in_venv_withlib(venv)

    @unittest.expectedFailure
    def test_pip_install_subproject(self):
        linkdir = self.make_linkdir()
        projectdir = self.make_setuptools_repo_subproject()
        venv = self.make_venv("setuptools-repo-pip-install-subproject")
        self.run_in_venv(venv, projectdir, "pip", "install", ".",
                         "--no-index", "--find-links", linkdir)
        self.check_in_venv_withlib(venv)

    def test_pip_install_from_afar(self):
        linkdir = self.make_linkdir()
        repodir = self.make_setuptools_repo()
        venv = self.make_venv("setuptools-repo-pip-install-from-afar")
        self.run_in_venv(venv, venv, "pip", "install", repodir,
                         "--no-index", "--find-links", linkdir)
        self.check_in_venv_withlib(venv)

    @unittest.expectedFailure
    def test_pip_install_from_afar_subproject(self):
        linkdir = self.make_linkdir()
        projectdir = self.make_setuptools_repo_subproject()
        venv = self.make_venv("setuptools-repo-pip-install-from-afar-subproject")
        self.run_in_venv(venv, venv, "pip", "install", projectdir,
                         "--no-index", "--find-links", linkdir)
        self.check_in_venv_withlib(venv)

    def test_pip_install_editable(self):
        linkdir = self.make_linkdir()
        repodir = self.make_setuptools_repo()
        venv = self.make_venv("setuptools-repo-pip-install-editable")
        self.run_in_venv(venv, repodir, "pip", "install", "--editable", ".",
                         "--no-index", "--find-links", linkdir)
        self.check_in_venv_withlib(venv)

    def test_pip_install_editable_subproject(self):
        linkdir = self.make_linkdir()
        projectdir = self.make_setuptools_repo_subproject()
        venv = self.make_venv("setuptools-repo-pip-install-editable-subproject")
        self.run_in_venv(venv, projectdir, "pip", "install", "--editable", ".",
                         "--no-index", "--find-links", linkdir)
        self.check_in_venv_withlib(venv)

class DistutilsSdist(_Invocations, unittest.TestCase):
    def test_pip_install(self):
        sdist = self.make_distutils_sdist()
        venv = self.make_venv("distutils-sdist-pip-install")
        self.run_in_venv(venv, venv,
                         "pip", "install", sdist)
        self.check_in_venv(venv)

    def test_pip_install_subproject(self):
        sdist = self.make_distutils_sdist_subproject()
        venv = self.make_venv("distutils-sdist-pip-install-subproject")
        self.run_in_venv(venv, venv,
                         "pip", "install", sdist)
        self.check_in_venv(venv)

    def test_easy_install(self):
        linkdir = self.make_linkdir()
        indexdir = self.make_empty_indexdir()
        sdist = self.make_distutils_sdist()
        venv = self.make_venv("distutils-sdist-easy-install")
        self.run_in_venv(venv, venv,
                         "easy_install",
                         "--index-url", indexdir, "--find-links", linkdir,
                         sdist)
        self.check_in_venv(venv)

class SetuptoolsSdist(_Invocations, unittest.TestCase):
    def test_pip_install(self):
        linkdir = self.make_linkdir()
        sdist = self.make_setuptools_sdist()
        venv = self.make_venv("setuptools-sdist-pip-install")
        self.run_in_venv(venv, venv,
                         "pip", "install",
                         "--no-index", "--find-links", linkdir,
                         sdist)
        self.check_in_venv_withlib(venv)

    def test_pip_install_subproject(self):
        linkdir = self.make_linkdir()
        sdist = self.make_setuptools_sdist_subproject()
        venv = self.make_venv("setuptools-sdist-pip-install-subproject")
        self.run_in_venv(venv, venv,
                         "pip", "install",
                         "--no-index", "--find-links", linkdir,
                         sdist)
        self.check_in_venv_withlib(venv)

    def test_easy_install(self):
        linkdir = self.make_linkdir()
        indexdir = self.make_empty_indexdir()
        sdist = self.make_setuptools_sdist()
        venv = self.make_venv("setuptools-sdist-easy-install")
        self.run_in_venv(venv, venv,
                         "easy_install",
                         "--index-url", indexdir, "--find-links", linkdir,
                         sdist)
        self.check_in_venv_withlib(venv)

class SetuptoolsWheel(_Invocations, unittest.TestCase):
    def test_pip_install(self):
        linkdir = self.make_linkdir()
        wheel = self.make_setuptools_wheel_with_setup_py()
        venv = self.make_venv("setuptools-wheel-pip-install")
        self.run_in_venv(venv, venv,
                         "pip", "install",
                         "--no-index", "--find-links", linkdir,
                         wheel)
        self.check_in_venv_withlib(venv)

class Egg(_Invocations, unittest.TestCase):
    def test_easy_install(self):
        linkdir = self.make_linkdir()
        indexdir = self.make_empty_indexdir()
        egg = self.make_setuptools_egg()
        venv = self.make_venv("setuptools-egg-easy-install")
        self.run_in_venv(venv, venv,
                         "easy_install",
                         "--index-url", indexdir, "--find-links", linkdir,
                         egg)
        self.check_in_venv_withlib(venv)

class DistutilsUnpacked(_Invocations, unittest.TestCase):
    def test_build(self):
        unpacked = self.make_distutils_unpacked()
        self.python("setup.py", "build", workdir=unpacked)
        # test that the built _version.py is correct. Ideally we'd actually
        # run PYTHONPATH=.../build/lib build/scripts-PYVER/rundemo and check
        # the output, but that's more fragile than I want to deal with today
        fn = os.path.join(unpacked, "build", "lib", "demo", "_version.py")
        data = versions_from_file(fn)
        self.assertEqual(data["version"], "2.0")

    def test_install(self):
        unpacked = self.make_distutils_unpacked()
        venv = self.make_venv("distutils-unpacked-install")
        self.run_in_venv(venv, unpacked, "python", "setup.py", "install")
        self.check_in_venv(venv)

    def test_install_subproject(self):
        unpacked = self.make_distutils_subproject_unpacked()
        venv = self.make_venv("distutils-subproject-unpacked-install")
        self.run_in_venv(venv, unpacked, "python", "setup.py", "install")
        self.check_in_venv(venv)

    def test_pip_wheel(self):
        unpacked = self.make_distutils_unpacked()
        wheelname = "demoapp2-2.0-%s-none-any.whl" % pyver_major
        venv = self.make_venv("distutils-unpacked-pip-wheel")
        self.run_in_venv(venv, unpacked,
                         "pip", "wheel", "--wheel-dir", "wheelhouse",
                         "--no-index",# "--find-links", linkdir,
                         ".")
        created = os.path.join(unpacked, "wheelhouse", wheelname)
        self.assertTrue(os.path.exists(created), created)

    def test_pip_install(self):
        repodir = self.make_distutils_unpacked()
        venv = self.make_venv("distutils-unpacked-pip-install")
        self.run_in_venv(venv, repodir, "pip", "install", ".")
        self.check_in_venv(venv)

    def test_pip_install_subproject(self):
        unpacked = self.make_distutils_subproject_unpacked()
        venv = self.make_venv("distutils-subproject-unpacked-pip-install")
        self.run_in_venv(venv, unpacked, "pip", "install", ".")
        self.check_in_venv(venv)

    def test_pip_install_from_afar(self):
        repodir = self.make_distutils_unpacked()
        venv = self.make_venv("distutils-unpacked-pip-install-from-afar")
        self.run_in_venv(venv, venv, "pip", "install", repodir)
        self.check_in_venv(venv)

class SetuptoolsUnpacked(_Invocations, unittest.TestCase):
    def test_install(self):
        unpacked = self.make_setuptools_unpacked()
        demolib = self.make_demolib_sdist()
        venv = self.make_venv("setuptools-unpacked-install")
        # "setup.py install" doesn't take --no-index or --find-links, so we
        # pre-install the dependency
        self.run_in_venv(venv, venv, "pip", "install", demolib)
        self.run_in_venv(venv, unpacked,
                         "python", "setup.py", "install")
        self.check_in_venv_withlib(venv)

    def test_install_subproject(self):
        unpacked = self.make_setuptools_subproject_unpacked()
        demolib = self.make_demolib_sdist()
        venv = self.make_venv("setuptools-subproject-unpacked-install")
        # "setup.py install" doesn't take --no-index or --find-links, so we
        # pre-install the dependency
        self.run_in_venv(venv, venv, "pip", "install", demolib)
        self.run_in_venv(venv, unpacked,
                         "python", "setup.py", "install")
        self.check_in_venv_withlib(venv)

    def test_easy_install(self):
        linkdir = self.make_linkdir()
        indexdir = self.make_empty_indexdir()
        unpacked = self.make_setuptools_unpacked()
        venv = self.make_venv("setuptools-unpacked-easy-install")
        self.run_in_venv(venv, unpacked,
                         "python", "setup.py", "easy_install",
                         "--index-url", indexdir, "--find-links", linkdir,
                         "."
                         )
        self.check_in_venv_withlib(venv)

    def test_wheel(self):
        unpacked = self.make_setuptools_unpacked()
        self.python("setup.py", "bdist_wheel", workdir=unpacked)
        wheelname = "demoapp2-2.0-%s-none-any.whl" % pyver_major
        wheel = os.path.join(unpacked, "dist", wheelname)
        self.assertTrue(os.path.exists(wheel))

    def test_pip_wheel(self):
        unpacked = self.make_setuptools_unpacked()
        linkdir = self.make_linkdir()
        wheelname = "demoapp2-2.0-%s-none-any.whl" % pyver_major
        venv = self.make_venv("setuptools-unpacked-pip-wheel")
        self.run_in_venv(venv, unpacked,
                         "pip", "wheel", "--wheel-dir", "wheelhouse",
                         "--no-index", "--find-links", linkdir,
                         ".")
        created = os.path.join(unpacked, "wheelhouse", wheelname)
        self.assertTrue(os.path.exists(created), created)

    def test_pip_install(self):
        linkdir = self.make_linkdir()
        repodir = self.make_setuptools_unpacked()
        venv = self.make_venv("setuptools-unpacked-pip-install")
        self.run_in_venv(venv, repodir, "pip", "install", ".",
                         "--no-index", "--find-links", linkdir)
        self.check_in_venv_withlib(venv)

    def test_pip_install_subproject(self):
        linkdir = self.make_linkdir()
        unpacked = self.make_setuptools_subproject_unpacked()
        venv = self.make_venv("setuptools-subproject-unpacked-pip-install")
        self.run_in_venv(venv, unpacked, "pip", "install", ".",
                         "--no-index", "--find-links", linkdir)
        self.check_in_venv_withlib(venv)

    def test_pip_install_from_afar(self):
        linkdir = self.make_linkdir()
        repodir = self.make_setuptools_unpacked()
        venv = self.make_venv("setuptools-unpacked-pip-install-from-afar")
        self.run_in_venv(venv, venv, "pip", "install", repodir,
                         "--no-index", "--find-links", linkdir)
        self.check_in_venv_withlib(venv)

    def test_extension_wheel_setuptools(self):
        # create an wheel of demoappext-setuptools at 2.0
        wheelname = self.make_binary_wheelname('demoappext')
        demoappext_setuptools_wheel = self.subpath("cache", "setuptools",
                                                   wheelname)
        if os.path.exists(demoappext_setuptools_wheel):
            # there are two ways to make this .whl, and we need to exercise
            # both, so don't actually cache the results
            os.unlink(demoappext_setuptools_wheel)
        repodir = self.make_setuptools_extension_repo()
        self.python("setup.py", "bdist_wheel", workdir=repodir)
        created = os.path.join(repodir, "dist", wheelname)
        self.assertTrue(os.path.exists(created), created)

    def test_extension_inplace(self):
        # build extensions in place. No wheel package
        unpacked = self.make_setuptools_extension_unpacked()
        venv = self.make_venv("setuptools-unpacked-pip-wheel-extension")
        self.run_in_venv(venv, unpacked,
                         "python", "setup.py", "build_ext", "-i")
        # No wheel package is created, _version.py should exist in
        # module dir only
        version_file = os.path.join(unpacked, "demo", "_version.py")
        self.assertTrue(os.path.exists(version_file))

    def test_extension_wheel_pip(self):
        # create an wheel of demoappext-setuptools at 2.0 with pip
        wheelname = self.make_binary_wheelname('demoappext')
        demoappext_setuptools_wheel = self.subpath("cache", "setuptools",
                                                   wheelname)
        if os.path.exists(demoappext_setuptools_wheel):
            # there are two ways to make this .whl, and we need to exercise
            # both, so don't actually cache the results
            os.unlink(demoappext_setuptools_wheel)
        unpacked = self.make_setuptools_extension_unpacked()
        linkdir = self.make_linkdir()
        venv = self.make_venv("setuptools-unpacked-pip-wheel-extension")
        self.run_in_venv(venv, unpacked,
                         "pip", "wheel", "--wheel-dir", "wheelhouse",
                         "--no-index", "--find-links", linkdir,
                         ".")
        created = os.path.join(unpacked, "wheelhouse", wheelname)
        self.assertTrue(os.path.exists(created), created)


if __name__ == '__main__':
    unittest.main()
