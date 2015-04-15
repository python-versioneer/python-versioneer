#! /usr/bin/python

import os, sys
import shutil
import tarfile
import unittest
import tempfile
from pkg_resources import parse_version, SetuptoolsLegacyVersion

sys.path.insert(0, "src")
from git.from_vcs import git_parse_vcs_describe
from git.from_keywords import git_versions_from_keywords
from subprocess_helper import run_command

GITS = ["git"]
if sys.platform == "win32":
    GITS = ["git.cmd", "git.exe"]

class ParseGitDescribe(unittest.TestCase):
    def test_parse(self):
        def pv(git_describe):
            return git_parse_vcs_describe(git_describe, "v")
        self.assertEqual(pv("1f"), ("0+untagged.g1f", False))
        self.assertEqual(pv("1f-dirty"), ("0+untagged.g1f.dirty", True))
        self.assertEqual(pv("v1.0-0-g1f"), ("1.0", False))
        self.assertEqual(pv("v1.0-0-g1f-dirty"), ("1.0+0.g1f.dirty", True))
        self.assertEqual(pv("v1.0-1-g1f"), ("1.0+1.g1f", False))
        self.assertEqual(pv("v1.0-1-g1f-dirty"), ("1.0+1.g1f.dirty", True))

        def p(git_describe):
            return git_parse_vcs_describe(git_describe, "")
        self.assertEqual(p("1f"), ("0+untagged.g1f", False))
        self.assertEqual(p("1f-dirty"), ("0+untagged.g1f.dirty", True))
        self.assertEqual(p("1.0-0-g1f"), ("1.0", False))
        self.assertEqual(p("1.0-0-g1f-dirty"), ("1.0+0.g1f.dirty", True))
        self.assertEqual(p("1.0-1-g1f"), ("1.0+1.g1f", False))
        self.assertEqual(p("1.0-1-g1f-dirty"), ("1.0+1.g1f.dirty", True))


class Keywords(unittest.TestCase):
    def parse(self, refnames, full, prefix=""):
        return git_versions_from_keywords({"refnames": refnames, "full": full},
                                          prefix)

    def test_parse(self):
        v = self.parse(" (HEAD, 2.0,master  , otherbranch ) ", " full ")
        self.assertEqual(v["version"], "2.0")
        self.assertEqual(v["full"], "full")

    def test_prefer_short(self):
        v = self.parse(" (HEAD, 2.0rc1, 2.0, 2.0rc2) ", " full ")
        self.assertEqual(v["version"], "2.0")
        self.assertEqual(v["full"], "full")

    def test_prefix(self):
        v = self.parse(" (HEAD, projectname-2.0) ", " full ", "projectname-")
        self.assertEqual(v["version"], "2.0")
        self.assertEqual(v["full"], "full")

    def test_unexpanded(self):
        v = self.parse(" $Format$ ", " full ", "projectname-")
        self.assertEqual(v, {})

    def test_no_tags(self):
        v = self.parse("(HEAD, master)", "full")
        self.assertEqual(v["version"], "0+unknown")
        self.assertEqual(v["full"], "full")

    def test_no_prefix(self):
        v = self.parse("(HEAD, master, 1.23)", "full", "missingprefix-")
        self.assertEqual(v["version"], "0+unknown")
        self.assertEqual(v["full"], "full")

VERBOSE = False

class Repo(unittest.TestCase):
    def git(self, *args, **kwargs):
        workdir = kwargs.pop("workdir", self.subpath("demoapp"))
        assert not kwargs, kwargs.keys()
        output = run_command(GITS, list(args), workdir, True)
        if output is None:
            self.fail("problem running git")
        return output
    def python(self, *args, **kwargs):
        workdir = kwargs.pop("workdir", self.subpath("demoapp"))
        assert not kwargs, kwargs.keys()
        output = run_command([sys.executable], list(args), workdir, True)
        if output is None:
            self.fail("problem running python")
        return output
    def subpath(self, path):
        return os.path.join(self.testdir, path)

    # There are three tree states we're interested in:
    #  S1: sitting on the initial commit, no tags
    #  S2: dirty tree after the initial commit
    #  S3: sitting on the 1.0 tag
    #  S4: dirtying the tree after 1.0
    #  S5: making a new commit after 1.0, clean tree
    #  S6: dirtying the tree after the post-1.0 commit
    #
    # Then we're interested in 5 kinds of trees:
    #  TA: source tree (with .git)
    #  TB: source tree without .git (should get 'unknown')
    #  TC: source tree without .git unpacked into prefixdir
    #  TD: git-archive tarball
    #  TE: unpacked sdist tarball
    #
    # In three runtime situations:
    #  RA1: setup.py --version
    #  RA2: ...path/to/setup.py --version (from outside the source tree)
    #  RB: setup.py build;  rundemo --version
    #
    # We can only detect dirty files in real git trees, so we don't examine
    # S2/S4/S6 for TB/TC/TD/TE, or RB.

    # note that the repo being manipulated is always named "demoapp",
    # regardless of which source directory we copied it from (test/demoapp/
    # or test/demoapp-script-only/)

    def test_full(self):
        self.run_test("test/demoapp", False)

    def test_script_only(self):
        # This test looks at an application that consists entirely of a
        # script: no libraries (so its setup.py has packages=[]). This sort
        # of app cannot be run from source: you must 'setup.py build' to get
        # anything executable. So of the 3 runtime situations examined by
        # Repo.test_full above, we only care about RB. (RA1 is valid too, but
        # covered by Repo).
        self.run_test("test/demoapp-script-only", True)

    def run_test(self, demoapp_dir, script_only):
        self.testdir = tempfile.mkdtemp()
        if VERBOSE: print("testdir: %s" % (self.testdir,))
        if os.path.exists(self.testdir):
            shutil.rmtree(self.testdir)

        # create an unrelated git tree above the testdir. Some tests will run
        # from this directory, and they should use the demoapp git
        # environment instead of the deceptive parent
        os.mkdir(self.testdir)
        self.git("init", workdir=self.testdir)
        f = open(os.path.join(self.testdir, "false-repo"), "w")
        f.write("don't look at me\n")
        f.close()
        self.git("add", "false-repo", workdir=self.testdir)
        self.git("commit", "-m", "first false commit", workdir=self.testdir)
        self.git("tag", "demo-4.0", workdir=self.testdir)

        shutil.copytree(demoapp_dir, self.subpath("demoapp"))
        setup_py_fn = os.path.join(self.subpath("demoapp"), "setup.py")
        with open(setup_py_fn, "r") as f:
            setup_py = f.read()
        setup_py = setup_py.replace("@VCS@", "git")
        with open(setup_py_fn, "w") as f:
            f.write(setup_py)
        shutil.copyfile("versioneer.py", self.subpath("demoapp/versioneer.py"))
        self.git("init")
        self.git("add", "--all")
        self.git("commit", "-m", "comment")

        full = self.git("rev-parse", "HEAD")
        v = self.python("setup.py", "--version")
        self.assertEqual(v, "0+untagged.g%s" % full[:7])
        v = self.python(os.path.join(self.subpath("demoapp"), "setup.py"),
                        "--version", workdir=self.testdir)
        self.assertEqual(v, "0+untagged.g%s" % full[:7])

        out = self.python("setup.py", "versioneer").splitlines()
        self.assertEqual(out[0], "running versioneer")
        self.assertEqual(out[1], " creating src/demo/_version.py")
        if script_only:
            self.assertEqual(out[2], " src/demo/__init__.py doesn't exist, ok")
        else:
            self.assertEqual(out[2], " appending to src/demo/__init__.py")
        self.assertEqual(out[3], " appending 'versioneer.py' to MANIFEST.in")
        self.assertEqual(out[4], " appending versionfile_source ('src/demo/_version.py') to MANIFEST.in")
        out = set(self.git("status", "--porcelain").splitlines())
        # Many folks have a ~/.gitignore with ignores .pyc files, but if they
        # don't, it will show up in the status here. Ignore it.
        out.discard("?? versioneer.pyc")
        out.discard("?? __pycache__/")
        expected = set(["A  .gitattributes",
                        "M  MANIFEST.in",
                        "A  src/demo/_version.py"])
        if not script_only:
            expected.add("M  src/demo/__init__.py")
        self.assertEqual(out, expected)
        if not script_only:
            f = open(self.subpath("demoapp/src/demo/__init__.py"))
            i = f.read().splitlines()
            f.close()
            self.assertEqual(i[-3], "from ._version import get_versions")
            self.assertEqual(i[-2], "__version__ = get_versions()['version']")
            self.assertEqual(i[-1], "del get_versions")
        self.git("commit", "-m", "add _version stuff")

        # "setup.py versioneer" should be idempotent
        out = self.python("setup.py", "versioneer").splitlines()
        self.assertEqual(out[0], "running versioneer")
        self.assertEqual(out[1], " creating src/demo/_version.py")
        if script_only:
            self.assertEqual(out[2], " src/demo/__init__.py doesn't exist, ok")
        else:
            self.assertEqual(out[2], " src/demo/__init__.py unmodified")
        self.assertEqual(out[3], " 'versioneer.py' already in MANIFEST.in")
        self.assertEqual(out[4], " versionfile_source already in MANIFEST.in")
        out = set(self.git("status", "--porcelain").splitlines())
        out.discard("?? versioneer.pyc")
        out.discard("?? __pycache__/")
        self.assertEqual(out, set([]))

        # S1: the tree is sitting on a pre-tagged commit
        full = self.git("rev-parse", "HEAD")
        short = "0+untagged.g%s" % full[:7]
        self.do_checks(short, full, exp_dirty=False, state="S1")

        # S2: dirty the pre-tagged tree
        f = open(self.subpath("demoapp/setup.py"),"a")
        f.write("# dirty\n")
        f.close()
        short = "0+untagged.g%s.dirty" % full[:7]
        self.do_checks(short, full+".dirty", exp_dirty=True, state="S2")

        # S3: we commit that change, then make the first tag (1.0)
        self.git("add", "setup.py")
        self.git("commit", "-m", "dirty")
        self.git("tag", "demo-1.0")
        short = "1.0"
        full = self.git("rev-parse", "HEAD")
        if VERBOSE: print("FULL %s" % full)
        # the tree is now sitting on the 1.0 tag
        self.do_checks(short, full, exp_dirty=False, state="S3")

        # S4: now we dirty the tree
        f = open(self.subpath("demoapp/setup.py"),"a")
        f.write("# dirty\n")
        f.close()
        short = "1.0+0.g%s.dirty" % full[:7]
        self.do_checks(short, full+".dirty", exp_dirty=True, state="S4")

        # S5: now we make one commit past the tag
        self.git("add", "setup.py")
        self.git("commit", "-m", "dirty")
        full = self.git("rev-parse", "HEAD")
        short = "1.0+1.g%s" % full[:7]
        self.do_checks(short, full, exp_dirty=False, state="S5")

        # S6: dirty the post-tag tree
        f = open(self.subpath("demoapp/setup.py"),"a")
        f.write("# more dirty\n")
        f.close()
        full = self.git("rev-parse", "HEAD")
        short = "1.0+1.g%s.dirty" % full[:7]
        self.do_checks(short, full+".dirty", exp_dirty=True, state="S6")


    def do_checks(self, exp_version, exp_full, exp_dirty, state):
        if os.path.exists(self.subpath("out")):
            shutil.rmtree(self.subpath("out"))
        # TA: source tree
        self.check_version(self.subpath("demoapp"), exp_version, exp_full,
                           exp_dirty, state, tree="TA")
        if exp_dirty:
            return

        # TB: .git-less copy of source tree
        target = self.subpath("out/demoapp-TB")
        shutil.copytree(self.subpath("demoapp"), target)
        shutil.rmtree(os.path.join(target, ".git"))
        self.check_version(target, "0+unknown", "unknown", False, state, tree="TB")

        # TC: source tree in versionprefix-named parentdir
        target = self.subpath("out/demo-1.1")
        shutil.copytree(self.subpath("demoapp"), target)
        shutil.rmtree(os.path.join(target, ".git"))
        self.check_version(target, "1.1", "", False, state, tree="TC")

        # TD: unpacked git-archive tarball
        target = self.subpath("out/TD/demoapp-TD")
        self.git("archive", "--format=tar", "--prefix=demoapp-TD/",
                 "--output=../demo.tar", "HEAD")
        os.mkdir(self.subpath("out/TD"))
        t = tarfile.TarFile(self.subpath("demo.tar"))
        t.extractall(path=self.subpath("out/TD"))
        t.close()
        exp_version_TD = exp_version
        if state  in ("S1", "S5"):
            # expanded keywords only tell us about tags and full revisionids,
            # not how many patches we are beyond a tag. So we can't expect
            # the short version to be like 1.0-1-gHEXID. The code falls back
            # to short="unknown"
            exp_version_TD = "0+unknown"
        self.check_version(target, exp_version_TD, exp_full, False, state, tree="TD")

        # TE: unpacked setup.py sdist tarball
        if os.path.exists(self.subpath("demoapp/dist")):
            shutil.rmtree(self.subpath("demoapp/dist"))
        self.python("setup.py", "sdist", "--formats=tar")
        files = os.listdir(self.subpath("demoapp/dist"))
        self.assertTrue(len(files)==1, files)
        distfile = files[0]
        self.assertEqual(distfile, "demo-%s.tar" % exp_version)
        fn = os.path.join(self.subpath("demoapp/dist"), distfile)
        os.mkdir(self.subpath("out/TE"))
        t = tarfile.TarFile(fn)
        t.extractall(path=self.subpath("out/TE"))
        t.close()
        target = self.subpath("out/TE/demo-%s" % exp_version)
        self.assertTrue(os.path.isdir(target))
        self.check_version(target, exp_version, exp_full, False, state, tree="TE")

    def check_version(self, workdir, exp_version, exp_full, exp_dirty, state, tree):
        if VERBOSE: print("== starting %s %s" % (state, tree))
        # RA: setup.py --version
        if VERBOSE:
            # setup.py version invokes cmd_version, which uses verbose=True
            # and has more boilerplate.
            print(self.python("setup.py", "version", workdir=workdir))
        # setup.py --version gives us get_version() with verbose=False.
        v = self.python("setup.py", "--version", workdir=workdir)
        self.compare(v, exp_version, state, tree, "RA1")
        self.assertPEP440(v, state, tree, "RA1")

        # and test again from outside the tree
        v = self.python(os.path.join(workdir, "setup.py"), "--version",
                        workdir=self.testdir)
        self.compare(v, exp_version, state, tree, "RA2")
        self.assertPEP440(v, state, tree, "RA2")

        if exp_dirty:
            return # cannot detect dirty files in a build # XXX really?

        # RB: setup.py build; rundemo --version
        if os.path.exists(os.path.join(workdir, "build")):
            shutil.rmtree(os.path.join(workdir, "build"))
        self.python("setup.py", "build", "--build-lib=build/lib",
                    "--build-scripts=build/lib", workdir=workdir)
        build_lib = os.path.join(workdir, "build", "lib")
        out = self.python("rundemo", "--version", workdir=build_lib)
        data = dict([line.split(":",1) for line in out.splitlines()])
        self.compare(data["__version__"], exp_version, state, tree, "RB")
        self.assertPEP440(data["__version__"], state, tree, "RB")
        self.compare(data["shortversion"], exp_version, state, tree, "RB")
        self.assertPEP440(data["shortversion"], state, tree ,"RB")
        self.compare(data["longversion"], exp_full, state, tree, "RB")

    def compare(self, got, expected, state, tree, runtime):
        where = "/".join([state, tree, runtime])
        self.assertEqual(got, expected, "%s: got '%s' != expected '%s'"
                         % (where, got, expected))
        if VERBOSE: print(" good %s" % where)

    def assertPEP440(self, got, state, tree, runtime):
        where = "/".join([state, tree, runtime])
        pv = parse_version(got)
        self.assertFalse(isinstance(pv, SetuptoolsLegacyVersion),
                         "%s: '%s' was not pep440-compatible"
                         % (where, got))
        self.assertEqual(str(pv), got,
                         "%s: '%s' pep440-normalized to '%s'"
                         % (where, got, str(pv)))

if __name__ == '__main__':
    ver = run_command(GITS, ["--version"], ".", True)
    print("git --version: %s" % ver.strip())
    unittest.main()
