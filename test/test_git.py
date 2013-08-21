#! /usr/bin/python

import os, sys
import shutil
import tarfile
import unittest

sys.path.insert(0, "src")
from git.middle import versions_from_expanded_variables
from subprocess_helper import run_command

class Variables(unittest.TestCase):
    def parse(self, refnames, full, prefix=""):
        return versions_from_expanded_variables({"refnames": refnames,
                                                 "full": full}, prefix)

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
        self.assertEqual(v["version"], "full")
        self.assertEqual(v["full"], "full")

    def test_no_prefix(self):
        v = self.parse("(HEAD, master, 1.23)", "full", "missingprefix-")
        self.assertEqual(v["version"], "full")
        self.assertEqual(v["full"], "full")

VERBOSE = False

class Repo(unittest.TestCase):
    def git(self, *args, **kwargs):
        workdir = kwargs.pop("workdir", "_test/demoapp")
        assert not kwargs, kwargs.keys()
        output = run_command(["git"]+list(args), workdir, True)
        if output is None:
            self.fail("problem running git")
        return output
    def python(self, *args, **kwargs):
        workdir = kwargs.pop("workdir", "_test/demoapp")
        assert not kwargs, kwargs.keys()
        output = run_command([sys.executable]+list(args), workdir, True)
        if output is None:
            self.fail("problem running python")
        return output

    # There are three tree states we're interested in:
    #  SA: sitting on the 1.0 tag
    #  SB: dirtying the tree after 1.0
    #  SC: making a new commit after 1.0, clean tree
    #
    # Then we're interested in 5 kinds of trees:
    #  TA: source tree (with .git)
    #  TB: source tree without .git (should get 'unknown')
    #  TC: source tree without .git unpacked into prefixdir
    #  TD: git-archive tarball
    #  TE: unpacked sdist tarball
    #
    # In two runtime situations:
    #  RA: setup.py --version
    #  RB: setup.py build;  demoapp --version
    #
    # We can only detect dirty files in real git trees, so we don't examine
    # SB for TB/TC/TD/TE, or RB.

    def test_full(self):
        testdir = "_test"
        if os.path.exists(testdir):
            shutil.rmtree(testdir)
        shutil.copytree("test/demoapp", "_test/demoapp")
        shutil.copyfile("versioneer.py", "_test/demoapp/versioneer.py")
        self.git("init")
        self.git("add", "--all")
        self.git("commit", "-m", "comment")

        v = self.python("setup.py", "--version")
        self.assertEqual(v, "unknown")
        out = self.python("setup.py", "update_files").splitlines()
        self.assertEqual(out[0], "running update_files")
        self.assertEqual(out[1], " creating src/demo/_version.py")
        self.assertEqual(out[2], " appending to src/demo/__init__.py")
        out = self.git("status", "--porcelain").splitlines()
        self.assertEqual(out[0], "A  .gitattributes")
        self.assertEqual(out[1], "M  src/demo/__init__.py")
        self.assertEqual(out[2], "A  src/demo/_version.py")
        f = open("_test/demoapp/src/demo/__init__.py")
        i = f.read().splitlines()
        f.close()
        self.assertEqual(i[-3], "from ._version import get_versions")
        self.assertEqual(i[-2], "__version__ = get_versions()['version']")
        self.assertEqual(i[-1], "del get_versions")
        self.git("commit", "-m", "add _version stuff")
        self.git("tag", "demo-1.0")
        short = "1.0"
        full = self.git("rev-parse", "HEAD")
        if VERBOSE: print("FULL %s" % full)
        # SA: the tree is now sitting on the 1.0 tag
        self.do_checks(short, full, dirty=False, state="SA")

        # SB: now we dirty the tree
        f = open("_test/demoapp/setup.py","a")
        f.write("# dirty\n")
        f.close()
        self.do_checks("1.0-dirty", full+"-dirty", dirty=True, state="SB")

        # SC: now we make one commit past the tag
        self.git("add", "setup.py")
        self.git("commit", "-m", "dirty")
        full = self.git("rev-parse", "HEAD")
        short = "1.0-1-g%s" % full[:7]
        self.do_checks(short, full, dirty=False, state="SC")


    def do_checks(self, exp_short, exp_long, dirty, state):
        if os.path.exists("_test/out"):
            shutil.rmtree("_test/out")
        # TA: source tree
        self.check_version("_test/demoapp", exp_short, exp_long,
                           dirty, state, tree="TA")
        if dirty:
            return

        # TB: .git-less copy of source tree
        target = "_test/out/demoapp-TB"
        shutil.copytree("_test/demoapp", target)
        shutil.rmtree(os.path.join(target, ".git"))
        self.check_version(target, "unknown", "unknown", False, state, tree="TB")

        # TC: source tree in versionprefix-named parentdir
        target = "_test/out/demo-1.1"
        shutil.copytree("_test/demoapp", target)
        shutil.rmtree(os.path.join(target, ".git"))
        self.check_version(target, "1.1", "", False, state, tree="TC")

        # TD: unpacked git-archive tarball
        target = "_test/out/TD/demoapp-TD"
        self.git("archive", "--format=tar", "--prefix=demoapp-TD/",
                 "--output=../demo.tar", "HEAD")
        os.mkdir("_test/out/TD")
        t = tarfile.TarFile("_test/demo.tar")
        t.extractall(path="_test/out/TD")
        t.close()
        exp_short_TD = exp_short
        if state == "SC":
            # expanded variables only tell us about tags and full
            # revisionids, not how many patches we are beyond a tag. So we
            # can't expect the short version to be like 1.0-1-gHEXID. The
            # code falls back to short=long
            exp_short_TD = exp_long
        self.check_version(target, exp_short_TD, exp_long, False, state, tree="TD")

        # TE: unpacked setup.py sdist tarball
        if os.path.exists("_test/demoapp/dist"):
            shutil.rmtree("_test/demoapp/dist")
        self.python("setup.py", "sdist", "--formats=tar")
        files = os.listdir("_test/demoapp/dist")
        self.assertTrue(len(files)==1, files)
        distfile = files[0]
        self.assertEqual(distfile, "demo-%s.tar" % exp_short)
        fn = os.path.join("_test/demoapp/dist/", distfile)
        os.mkdir("_test/out/TE")
        t = tarfile.TarFile(fn)
        t.extractall(path="_test/out/TE")
        t.close()
        target = "_test/out/TE/demo-%s" % exp_short
        self.assertTrue(os.path.isdir(target))
        self.check_version(target, exp_short, exp_long, False, state, tree="TE")

    def compare(self, got, expected, state, tree, runtime):
        where = "/".join([state, tree, runtime])
        self.assertEqual(got, expected, "%s: got '%s' != expected '%s'"
                         % (where, got, expected))
        if VERBOSE: print(" good %s" % where)

    def check_version(self, workdir, exp_short, exp_long, dirty, state, tree):
        if VERBOSE: print("== starting %s %s" % (state, tree))
        # RA: setup.py --version
        if VERBOSE:
            # setup.py version invokes cmd_version, which uses verbose=True
            # and has more boilerplate.
            print(self.python("setup.py", "version", workdir=workdir))
        # setup.py --version gives us get_version() with verbose=False.
        v = self.python("setup.py", "--version", workdir=workdir)
        self.compare(v, exp_short, state, tree, "RA")
        if dirty:
            return # cannot detect dirty files in a build

        # RB: setup.py build; rundemo --version
        if os.path.exists(os.path.join(workdir, "build")):
            shutil.rmtree(os.path.join(workdir, "build"))
        self.python("setup.py", "build", "--build-lib=build/lib",
                    "--build-scripts=build/lib", workdir=workdir)
        build_lib = os.path.join(workdir, "build", "lib")
        # copy bin/rundemo into the build libdir, so we don't have to muck
        # with PYTHONPATH when we execute it
        shutil.copyfile(os.path.join(workdir, "bin", "rundemo"),
                        os.path.join(build_lib, "rundemo"))
        out = self.python("rundemo", "--version", workdir=build_lib)
        data = dict([line.split(":",1) for line in out.splitlines()])
        self.compare(data["__version__"], exp_short, state, tree, "RB")
        self.compare(data["shortversion"], exp_short, state, tree, "RB")
        self.compare(data["longversion"], exp_long, state, tree, "RB")


if __name__ == '__main__':
    ver = run_command(["git", "--version"], ".", True)
    print "git --version:", ver.strip()
    unittest.main()
