from __future__ import print_function

import os, sys, shutil, unittest, tempfile, tarfile

sys.path.insert(0, "src")
from from_file import versions_from_file
import common

pyver_major = "py%d" % sys.version_info[0]
pyver = "py%d.%d" % sys.version_info[:2]

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
        # virtualenv.create_environment() clears this as a side-effect, and
        # anyways I've switched to 'import venv' on py3 (which may not be
        # sensitive to this problem), but to make things safe I'll just clear
        # this now. See https://github.com/pypa/virtualenv/issues/322 and
        # https://bugs.python.org/issue22490 for some hints.
        os.environ.pop("__PYVENV_LAUNCHER__", None)
        if sys.version_info[0] == 2:
            import virtualenv
            virtualenv.logger = virtualenv.Logger([]) # hush
            virtualenv.create_environment(venv_dir)
            # virtualenv installs "wheel" into the new environment
        else:
            assert sys.version_info[0] == 3
            import venv
            venv.EnvBuilder(with_pip=True).create(venv_dir)
            # venv doesn't include wheel, which we need for some tests
            self.run_in_venv(venv_dir, venv_dir, "pip", "install", "wheel")
        return venv_dir

    def run_in_venv(self, venv, workdir, command, *args):
        bins = {"python": os.path.join(venv, "bin", "python"),
                "pip": os.path.join(venv, "bin", "pip"),
                "rundemo": os.path.join(venv, "bin", "rundemo"),
                "easy_install": os.path.join(venv, "bin", "easy_install"),
                }
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
        self.git("commit", "-m", "commemt", workdir=libdir)
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
        self.git("commit", "-m", "commemt", workdir=repodir)
        self.git("tag", "demoapp2-2.0", workdir=repodir)
        return repodir

    def make_distutils_wheel_with_pip(self):
        # create an wheel of demoapp2-distutils at 2.0
        wheelname = "demoapp2-2.0-%s-none-any.whl" % pyver_major
        demoapp2_distutils_wheel = self.subpath("cache", "distutils", wheelname)
        if os.path.exists(demoapp2_distutils_wheel):
            return demoapp2_distutils_wheel
        repodir = self.make_distutils_repo()
        venv = self.make_venv("make-distutils-wheel-with-pip")
        self.run_in_venv(venv, repodir,
                         "pip", "--isolated", "wheel",
                         "--no-index",# "--find-links", linkdir,
                         ".")
        created = os.path.join(repodir, "wheelhouse", wheelname)
        self.assertTrue(os.path.exists(created))
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
        self.assertTrue(os.path.exists(created))
        shutil.copyfile(created, demoapp2_distutils_sdist)
        return demoapp2_distutils_sdist

    def make_distutils_unpacked(self):
        sdist = self.make_distutils_sdist()
        unpack_into = self.subpath("demoapp2-distutils-unpacked")
        if os.path.exists(unpack_into):
            shutil.rmtree(unpack_into)
        os.mkdir(unpack_into)
        t = tarfile.TarFile(sdist)
        t.extractall(path=unpack_into)
        t.close()
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
        self.git("commit", "-m", "commemt", workdir=repodir)
        self.git("tag", "demoapp2-2.0", workdir=repodir)
        return repodir

    def make_setuptools_sdist(self):
        # create an sdist tarball of demoapp2-setuptools at 2.0
        demoapp2_setuptools_sdist = self.subpath("cache", "setuptools",
                                                 "demoapp2-2.0.tar")
        if os.path.exists(demoapp2_setuptools_sdist):
            return demoapp2_setuptools_sdist
        repodir = self.make_setuptools_repo()
        self.python("setup.py", "sdist", "--format=tar", workdir=repodir)
        created = os.path.join(repodir, "dist", "demoapp2-2.0.tar")
        self.assertTrue(os.path.exists(created))
        shutil.copyfile(created, demoapp2_setuptools_sdist)
        return demoapp2_setuptools_sdist

    def make_setuptools_unpacked(self):
        sdist = self.make_setuptools_sdist()
        unpack_into = self.subpath("demoapp2-setuptools-unpacked")
        if os.path.exists(unpack_into):
            shutil.rmtree(unpack_into)
        os.mkdir(unpack_into)
        t = tarfile.TarFile(sdist)
        t.extractall(path=unpack_into)
        t.close()
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
        self.assertTrue(os.path.exists(created))
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
        self.assertTrue(os.path.exists(created))
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
                         "pip", "--isolated", "wheel",
                         "--no-index", "--find-links", linkdir,
                         ".")
        created = os.path.join(repodir, "wheelhouse", wheelname)
        self.assertTrue(os.path.exists(created))
        shutil.copyfile(created, demoapp2_setuptools_wheel)
        return demoapp2_setuptools_wheel


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

    def test_pip_wheel(self):
        self.make_distutils_wheel_with_pip()
        # asserts version as a side-effect

    def test_sdist(self):
        self.make_distutils_sdist() # asserts version as a side-effect

    def test_pip_install(self):
        repodir = self.make_distutils_repo()
        venv = self.make_venv("distutils-repo-pip-install")
        self.run_in_venv(venv, repodir, "pip", "--isolated", "install", ".")
        self.check_in_venv(venv)

    def test_pip_install_from_afar(self):
        repodir = self.make_distutils_repo()
        venv = self.make_venv("distutils-repo-pip-install-from-afar")
        self.run_in_venv(venv, venv, "pip", "--isolated", "install", repodir)
        self.check_in_venv(venv)

    def test_pip_install_editable(self):
        repodir = self.make_distutils_repo()
        venv = self.make_venv("distutils-repo-pip-install-editable")
        self.run_in_venv(venv, repodir, "pip", "--isolated",
                         "install", "--editable", ".")
        self.check_in_venv(venv)

class SetuptoolsRepo(_Invocations, unittest.TestCase):
    def test_install(self):
        repodir = self.make_setuptools_repo()
        demolib = self.make_demolib_sdist()
        venv = self.make_venv("setuptools-repo-install")
        # "setup.py install" doesn't take --no-index or --find-links, so we
        # pre-install the dependency
        self.run_in_venv(venv, venv, "pip", "--isolated", "install", demolib)
        self.run_in_venv(venv, repodir, "python", "setup.py", "install")
        self.check_in_venv_withlib(venv)

    def test_easy_install(self):
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

    def test_egg(self):
        self.make_setuptools_egg() # asserts version as a side-effect

    def test_pip_wheel(self):
        self.make_setuptools_wheel_with_pip()
        # asserts version as a side-effect

    def test_bdist_wheel(self):
        self.make_setuptools_wheel_with_setup_py()
        # asserts version as a side-effect

    def test_sdist(self):
        self.make_setuptools_sdist() # asserts version as a side-effect

    def test_pip_install(self):
        linkdir = self.make_linkdir()
        repodir = self.make_setuptools_repo()
        venv = self.make_venv("setuptools-repo-pip-install")
        self.run_in_venv(venv, repodir, "pip", "--isolated", "install", ".",
                         "--no-index", "--find-links", linkdir)
        self.check_in_venv_withlib(venv)

    def test_pip_install_from_afar(self):
        linkdir = self.make_linkdir()
        repodir = self.make_setuptools_repo()
        venv = self.make_venv("setuptools-repo-pip-install-from-afar")
        self.run_in_venv(venv, venv, "pip", "--isolated", "install", repodir,
                         "--no-index", "--find-links", linkdir)
        self.check_in_venv_withlib(venv)

    def test_pip_install_editable(self):
        linkdir = self.make_linkdir()
        repodir = self.make_setuptools_repo()
        venv = self.make_venv("setuptools-repo-pip-install-editable")
        self.run_in_venv(venv, repodir, "pip", "--isolated",
                         "install", "--editable", ".",
                         "--no-index", "--find-links", linkdir)
        self.check_in_venv_withlib(venv)

class DistutilsSdist(_Invocations, unittest.TestCase):
    def test_pip_install(self):
        sdist = self.make_distutils_sdist()
        venv = self.make_venv("distutils-sdist-pip-install")
        self.run_in_venv(venv, venv,
                         "pip", "--isolated", "install",
                         sdist)
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
                         "pip", "--isolated", "install",
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
                         "pip", "--isolated", "install",
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

    def test_pip_wheel(self):
        unpacked = self.make_distutils_unpacked()
        wheelname = "demoapp2-2.0-%s-none-any.whl" % pyver_major
        venv = self.make_venv("distutils-unpacked-pip-wheel")
        self.run_in_venv(venv, unpacked,
                         "pip", "--isolated", "wheel",
                         "--no-index",# "--find-links", linkdir,
                         ".")
        created = os.path.join(unpacked, "wheelhouse", wheelname)
        self.assertTrue(os.path.exists(created))

    def test_pip_install(self):
        repodir = self.make_distutils_unpacked()
        venv = self.make_venv("distutils-unpacked-pip-install")
        self.run_in_venv(venv, repodir, "pip", "--isolated", "install", ".")
        self.check_in_venv(venv)

    def test_pip_install_from_afar(self):
        repodir = self.make_distutils_unpacked()
        venv = self.make_venv("distutils-unpacked-pip-install-from-afar")
        self.run_in_venv(venv, venv, "pip", "--isolated", "install", repodir)
        self.check_in_venv(venv)

class SetuptoolsUnpacked(_Invocations, unittest.TestCase):
    def test_install(self):
        unpacked = self.make_setuptools_unpacked()
        demolib = self.make_demolib_sdist()
        venv = self.make_venv("setuptools-unpacked-install")
        # "setup.py install" doesn't take --no-index or --find-links, so we
        # pre-install the dependency
        self.run_in_venv(venv, venv, "pip", "--isolated", "install", demolib)
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
                         "pip", "--isolated", "wheel",
                         "--no-index", "--find-links", linkdir,
                         ".")
        created = os.path.join(unpacked, "wheelhouse", wheelname)
        self.assertTrue(os.path.exists(created))

    def test_pip_install(self):
        linkdir = self.make_linkdir()
        repodir = self.make_setuptools_unpacked()
        venv = self.make_venv("setuptools-unpacked-pip-install")
        self.run_in_venv(venv, repodir, "pip", "--isolated", "install", ".",
                         "--no-index", "--find-links", linkdir)
        self.check_in_venv_withlib(venv)

    def test_pip_install_from_afar(self):
        linkdir = self.make_linkdir()
        repodir = self.make_setuptools_unpacked()
        venv = self.make_venv("setuptools-unpacked-pip-install-from-afar")
        self.run_in_venv(venv, venv, "pip", "--isolated", "install", repodir,
                         "--no-index", "--find-links", linkdir)
        self.check_in_venv_withlib(venv)


if __name__ == '__main__':
    unittest.main()
