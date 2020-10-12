#! /usr/bin/python

import os, sys
import shutil
import tarfile
import unittest
import tempfile


from pkg_resources import parse_version

sys.path.insert(0, "src")
import common
from render import render
from git import from_vcs, from_keywords
from subprocess_helper import run_command

class ParseGitDescribe(unittest.TestCase):
    def setUp(self):
        self.fakeroot = tempfile.mkdtemp()
        self.fakegit = os.path.join(self.fakeroot, ".git")
        os.mkdir(self.fakegit)

    def test_pieces(self):
        def pv(git_describe, do_error=False, expect_pieces=False):
            def fake_run_command(exes, args, cwd=None, hide_stderr=None):
                if args[0] == "describe":
                    if do_error == "describe":
                        return None, 0
                    return git_describe+"\n", 0
                if args[0] == "rev-parse":
                    if do_error == "rev-parse":
                        return None, 0
                    return "longlong\n", 0
                if args[0] == "rev-list":
                    return "42\n", 0
                if args[0] == "show":
                    if do_error == "show":
                        return "gpg: signature\n12345\n", 0
                    return "12345\n", 0
                self.fail("git called in weird way: %s" % (args,))
            return from_vcs.git_pieces_from_vcs(
                "v", self.fakeroot, verbose=False,
                run_command=fake_run_command)
        self.assertRaises(from_vcs.NotThisMethod,
                          pv, "ignored", do_error="describe")
        self.assertRaises(from_vcs.NotThisMethod,
                          pv, "ignored", do_error="rev-parse")
        self.assertEqual(pv("1f"),
                         {"closest-tag": None, "dirty": False, "error": None,
                          "distance": 42,
                          "long": "longlong",
                          "short": "longlon",
                          "date": "12345"})
        self.assertEqual(pv("1f", do_error="show"),
                         {"closest-tag": None, "dirty": False, "error": None,
                          "distance": 42,
                          "long": "longlong",
                          "short": "longlon",
                          "date": "12345"})
        self.assertEqual(pv("1f-dirty"),
                         {"closest-tag": None, "dirty": True, "error": None,
                          "distance": 42,
                          "long": "longlong",
                          "short": "longlon",
                          "date": "12345"})
        self.assertEqual(pv("v1.0-0-g1f"),
                         {"closest-tag": "1.0", "dirty": False, "error": None,
                          "distance": 0,
                          "long": "longlong",
                          "short": "1f",
                          "date": "12345"})
        self.assertEqual(pv("v1.0-0-g1f-dirty"),
                         {"closest-tag": "1.0", "dirty": True, "error": None,
                          "distance": 0,
                          "long": "longlong",
                          "short": "1f",
                          "date": "12345"})
        self.assertEqual(pv("v1.0-1-g1f"),
                         {"closest-tag": "1.0", "dirty": False, "error": None,
                          "distance": 1,
                          "long": "longlong",
                          "short": "1f",
                          "date": "12345"})
        self.assertEqual(pv("v1.0-1-g1f-dirty"),
                         {"closest-tag": "1.0", "dirty": True, "error": None,
                          "distance": 1,
                          "long": "longlong",
                          "short": "1f",
                          "date": "12345"})

    def tearDown(self):
        os.rmdir(self.fakegit)
        os.rmdir(self.fakeroot)


class Keywords(unittest.TestCase):
    def parse(self, refnames, full, prefix="", date=None):
        return from_keywords.git_versions_from_keywords(
            {"refnames": refnames, "full": full, "date": date}, prefix, False)

    def test_parse(self):
        v = self.parse(" (HEAD, 2.0,master  , otherbranch ) ", " full ")
        self.assertEqual(v["version"], "2.0")
        self.assertEqual(v["full-revisionid"], "full")
        self.assertEqual(v["dirty"], False)
        self.assertEqual(v["error"], None)
        self.assertEqual(v["date"], None)

    def test_prefer_short(self):
        v = self.parse(" (HEAD, 2.0rc1, 2.0, 2.0rc2) ", " full ")
        self.assertEqual(v["version"], "2.0")
        self.assertEqual(v["full-revisionid"], "full")
        self.assertEqual(v["dirty"], False)
        self.assertEqual(v["error"], None)
        self.assertEqual(v["date"], None)

    def test_prefix(self):
        v = self.parse(" (HEAD, projectname-2.0) ", " full ", "projectname-")
        self.assertEqual(v["version"], "2.0")
        self.assertEqual(v["full-revisionid"], "full")
        self.assertEqual(v["dirty"], False)
        self.assertEqual(v["error"], None)
        self.assertEqual(v["date"], None)

    def test_unexpanded(self):
        self.assertRaises(from_keywords.NotThisMethod,
                          self.parse, " $Format$ ", " full ", "projectname-")

    def test_no_tags(self):
        v = self.parse("(HEAD, master)", "full")
        self.assertEqual(v["version"], "0+unknown")
        self.assertEqual(v["full-revisionid"], "full")
        self.assertEqual(v["dirty"], False)
        self.assertEqual(v["error"], "no suitable tags")
        self.assertEqual(v["date"], None)

    def test_no_prefix(self):
        v = self.parse("(HEAD, master, 1.23)", "full", "missingprefix-")
        self.assertEqual(v["version"], "0+unknown")
        self.assertEqual(v["full-revisionid"], "full")
        self.assertEqual(v["dirty"], False)
        self.assertEqual(v["error"], "no suitable tags")
        self.assertEqual(v["date"], None)

    def test_date(self):
        date = "2017-07-24 16:03:40 +0200"
        result = "2017-07-24T16:03:40+0200"
        v = self.parse(" (HEAD, 2.0,master  , otherbranch ) ", " full ",
                       date=date)
        self.assertEqual(v["date"], result)

    def test_date_gpg(self):
        date = """
        gpg: Signature information
        gpg: ...
        2017-07-24 16:03:40 +0200"""
        result = "2017-07-24T16:03:40+0200"
        v = self.parse(" (HEAD, 2.0,master  , otherbranch ) ", " full ",
                       date=date)
        self.assertEqual(v["date"], result)

expected_renders = """
closest-tag: 1.0
distance: 0
dirty: False
pep440: 1.0
pep440-pre: 1.0
pep440-post: 1.0
pep440-old: 1.0
git-describe: 1.0
git-describe-long: 1.0-0-g250b7ca

closest-tag: 1.0
distance: 0
dirty: True
pep440: 1.0+0.g250b7ca.dirty
pep440-pre: 1.0
pep440-post: 1.0.post0.dev0+g250b7ca
pep440-old: 1.0.post0.dev0
git-describe: 1.0-dirty
git-describe-long: 1.0-0-g250b7ca-dirty

closest-tag: 1.0
distance: 1
dirty: False
pep440: 1.0+1.g250b7ca
pep440-pre: 1.0.post0.dev1
pep440-post: 1.0.post1+g250b7ca
pep440-old: 1.0.post1
git-describe: 1.0-1-g250b7ca
git-describe-long: 1.0-1-g250b7ca

closest-tag: 1.0
distance: 1
dirty: True
pep440: 1.0+1.g250b7ca.dirty
pep440-pre: 1.0.post0.dev1
pep440-post: 1.0.post1.dev0+g250b7ca
pep440-old: 1.0.post1.dev0
git-describe: 1.0-1-g250b7ca-dirty
git-describe-long: 1.0-1-g250b7ca-dirty


closest-tag: 1.0+plus
distance: 1
dirty: False
pep440: 1.0+plus.1.g250b7ca
pep440-pre: 1.0+plus.post0.dev1
pep440-post: 1.0+plus.post1.g250b7ca
pep440-old: 1.0+plus.post1
git-describe: 1.0+plus-1-g250b7ca
git-describe-long: 1.0+plus-1-g250b7ca

closest-tag: 1.0+plus
distance: 1
dirty: True
pep440: 1.0+plus.1.g250b7ca.dirty
pep440-pre: 1.0+plus.post0.dev1
pep440-post: 1.0+plus.post1.dev0.g250b7ca
pep440-old: 1.0+plus.post1.dev0
git-describe: 1.0+plus-1-g250b7ca-dirty
git-describe-long: 1.0+plus-1-g250b7ca-dirty


closest-tag: None
distance: 1
dirty: False
pep440: 0+untagged.1.g250b7ca
pep440-pre: 0.post0.dev1
pep440-post: 0.post1+g250b7ca
pep440-old: 0.post1
git-describe: 250b7ca
git-describe-long: 250b7ca

closest-tag: None
distance: 1
dirty: True
pep440: 0+untagged.1.g250b7ca.dirty
pep440-pre: 0.post0.dev1
pep440-post: 0.post1.dev0+g250b7ca
pep440-old: 0.post1.dev0
git-describe: 250b7ca-dirty
git-describe-long: 250b7ca-dirty

"""

class RenderPieces(unittest.TestCase):
    def do_render(self, pieces):
        out = {}
        for style in ["pep440", "pep440-pre", "pep440-post", "pep440-old",
                      "git-describe", "git-describe-long"]:
            out[style] = render(pieces, style)["version"]
        DEFAULT = "pep440"
        self.assertEqual(render(pieces, ""), render(pieces, DEFAULT))
        self.assertEqual(render(pieces, "default"), render(pieces, DEFAULT))
        return out

    def parse_expected(self):
        base_pieces = {"long": "250b7ca731388d8f016db2e06ab1d6289486424b",
                       "short": "250b7ca",
                       "error": None}
        more_pieces = {}
        expected = {}
        for line in expected_renders.splitlines():
            line = line.strip()
            if not line:
                if more_pieces and expected:
                    pieces = base_pieces.copy()
                    pieces.update(more_pieces)
                    yield (pieces, expected)
                more_pieces = {}
                expected = {}
                continue
            name, value = line.split(":")
            name = name.strip()
            value = value.strip()
            if name == "distance":
                more_pieces["distance"] = int(value)
            elif name == "dirty":
                more_pieces["dirty"] = bool(value.lower() == "true")
            elif name == "closest-tag":
                more_pieces["closest-tag"] = value
                if value == "None":
                    more_pieces["closest-tag"] = None
            else:
                expected[name] = value
        if more_pieces and expected:
            pieces = base_pieces.copy()
            pieces.update(more_pieces)
            yield (pieces, expected)

    def test_render(self):
        for (pieces, expected) in self.parse_expected():
            got = self.do_render(pieces)
            for key in expected:
                self.assertEqual(got[key], expected[key],
                                 (pieces, key, got[key], expected[key]))


VERBOSE = False

class Repo(common.Common, unittest.TestCase):

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
        self.run_test("test/demoapp", False, ".")

    def test_script_only(self):
        # This test looks at an application that consists entirely of a
        # script: no libraries (so its setup.py has packages=[]). This sort
        # of app cannot be run from source: you must 'setup.py build' to get
        # anything executable. So of the 3 runtime situations examined by
        # Repo.test_full above, we only care about RB. (RA1 is valid too, but
        # covered by Repo).
        self.run_test("test/demoapp-script-only", True, ".")

    def test_project_in_subdir(self):
        # This test sets of the git repository so that the python project --
        # i.e. setup.py -- is not located in the root directory
        self.run_test("test/demoapp", False, "project")

    def run_test(self, demoapp_dir, script_only, project_sub_dir):
        # The test dir should live under /tmp/ or /var/ or somewhere that
        # isn't the child of the versioneer repo's .git directory, since that
        # will confuse the tests that check what happens when there is no
        # .git parent. So if you change this to use a fixed directory (say,
        # when debugging problems), use /tmp/_test rather than ./_test .
        self.testdir = tempfile.mkdtemp()
        if VERBOSE: print("testdir: %s" % (self.testdir,))
        if os.path.exists(self.testdir):
            shutil.rmtree(self.testdir)

        # Our tests run from a git repo that lives here. All self.git()
        # operations run from this directory unless overridden.
        self.gitdir = os.path.join(self.testdir, "demoapp")
        # Inside that git repo, the project (with setup.py, setup.cfg, and
        # versioneer.py) lives inside this directory. All self.python() and
        # self.command() operations run from this directory unless
        # overridden.
        self.project_sub_dir = project_sub_dir
        self.projdir = os.path.join(self.testdir, self.gitdir,
                                    self.project_sub_dir)

        os.mkdir(self.testdir)

        shutil.copytree(demoapp_dir, self.projdir)
        setup_cfg_fn = self.project_file("setup.cfg")
        with open(setup_cfg_fn, "r") as f:
            setup_cfg = f.read()
        setup_cfg = setup_cfg.replace("@VCS@", "git")
        with open(setup_cfg_fn, "w") as f:
            f.write(setup_cfg)
        shutil.copyfile("versioneer.py", self.project_file("versioneer.py"))
        self.git("init")
        self.git("add", "--all")
        self.git("commit", "-m", "comment")

        full = self.git("rev-parse", "HEAD")
        v = self.python("setup.py", "--version")
        self.assertEqual(v, "0+untagged.1.g%s" % full[:7])
        v = self.python(self.project_file("setup.py"), "--version",
                        workdir=self.testdir)
        self.assertEqual(v, "0+untagged.1.g%s" % full[:7])

        out = self.python("versioneer.py", "setup").splitlines()
        self.assertEqual(out[0], "creating src/demo/_version.py")
        if script_only:
            self.assertEqual(out[1], " src/demo/__init__.py doesn't exist, ok")
        else:
            self.assertEqual(out[1], " appending to src/demo/__init__.py")
        self.assertEqual(out[2], " appending 'versioneer.py' to MANIFEST.in")
        self.assertEqual(out[3], " appending versionfile_source ('src/demo/_version.py') to MANIFEST.in")

        # Many folks have a ~/.gitignore with ignores .pyc files, but if they
        # don't, it will show up in the status here. Ignore it.
        def remove_pyc(s):
            return [f for f in s
                    if not (f.startswith("?? ")
                            and (f.endswith(".pyc") or
                                 f.endswith("__pycache__/")))
                    ]
        out = set(remove_pyc(self.git("status", "--porcelain").splitlines()))
        def pf(fn):
            return os.path.normpath(os.path.join(self.project_sub_dir, fn))
        expected = set(["A  %s" % pf(".gitattributes"),
                        "M  %s" % pf("MANIFEST.in"),
                        "A  %s" % pf("src/demo/_version.py"),
                        ])
        if not script_only:
            expected.add("M  %s" % pf("src/demo/__init__.py"))
        self.assertEqual(out, expected)
        if not script_only:
            f = open(self.project_file("src/demo/__init__.py"))
            i = f.read().splitlines()
            f.close()
            self.assertEqual(i[-3], "from ._version import get_versions")
            self.assertEqual(i[-2], "__version__ = get_versions()['version']")
            self.assertEqual(i[-1], "del get_versions")
        self.git("commit", "-m", "add _version stuff")

        # "versioneer.py setup" should be idempotent
        out = self.python("versioneer.py", "setup").splitlines()
        self.assertEqual(out[0], "creating src/demo/_version.py")
        if script_only:
            self.assertEqual(out[1], " src/demo/__init__.py doesn't exist, ok")
        else:
            self.assertEqual(out[1], " src/demo/__init__.py unmodified")
        self.assertEqual(out[2], " 'versioneer.py' already in MANIFEST.in")
        self.assertEqual(out[3], " versionfile_source already in MANIFEST.in")
        out = set(remove_pyc(self.git("status", "--porcelain").splitlines()))
        self.assertEqual(out, set([]))

        UNABLE = "unable to compute version"
        NOTAG = "no suitable tags"

        # S1: the tree is sitting on a pre-tagged commit
        full = self.git("rev-parse", "HEAD")
        short = "0+untagged.2.g%s" % full[:7]
        self.do_checks("S1", {"TA": [short, full, False, None],
                              "TB": ["0+unknown", None, None, UNABLE],
                              "TC": [short, full, False, None],
                              "TD": ["0+unknown", full, False, NOTAG],
                              "TE": [short, full, False, None],
                              })

        # TD: expanded keywords only tell us about tags and full revisionids,
        # not how many patches we are beyond a tag. So any TD git-archive
        # tarball from a non-tagged version will give us an error. "dirty" is
        # False, since the tree from which the tarball was created is
        # necessarily clean.

        # S2: dirty the pre-tagged tree
        f = open(self.project_file("setup.py"), "a")
        f.write("# dirty\n")
        f.close()
        full = self.git("rev-parse", "HEAD")
        short = "0+untagged.2.g%s.dirty" % full[:7]
        self.do_checks("S2", {"TA": [short, full, True, None],
                              "TB": ["0+unknown", None, None, UNABLE],
                              "TC": [short, full, True, None],
                              "TD": ["0+unknown", full, False, NOTAG],
                              "TE": [short, full, True, None],
                              })

        # S3: we commit that change, then make the first tag (1.0)
        self.git("add", self.project_file("setup.py"))
        self.git("commit", "-m", "dirty")
        self.git("tag", "demo-1.0")
        # also add an unrelated tag, to test exclusion. git-describe appears
        # to return the highest lexicographically-sorted tag, so make sure
        # the unrelated one sorts earlier
        self.git("tag", "aaa-999")
        full = self.git("rev-parse", "HEAD")
        short = "1.0"
        if VERBOSE: print("FULL %s" % full)
        # the tree is now sitting on the 1.0 tag
        self.do_checks("S3", {"TA": [short, full, False, None],
                              "TB": ["0+unknown", None, None, UNABLE],
                              "TC": [short, full, False, None],
                              "TD": [short, full, False, None],
                              "TE": [short, full, False, None],
                              })

        # S4: now we dirty the tree
        f = open(self.project_file("setup.py"), "a")
        f.write("# dirty\n")
        f.close()
        full = self.git("rev-parse", "HEAD")
        short = "1.0+0.g%s.dirty" % full[:7]
        self.do_checks("S4", {"TA": [short, full, True, None],
                              "TB": ["0+unknown", None, None, UNABLE],
                              "TC": [short, full, True, None],
                              "TD": ["1.0", full, False, None],
                              "TE": [short, full, True, None],
                              })

        # S5: now we make one commit past the tag
        self.git("add", self.project_file("setup.py"))
        self.git("commit", "-m", "dirty")
        full = self.git("rev-parse", "HEAD")
        short = "1.0+1.g%s" % full[:7]
        self.do_checks("S5", {"TA": [short, full, False, None],
                              "TB": ["0+unknown", None, None, UNABLE],
                              "TC": [short, full, False, None],
                              "TD": ["0+unknown", full, False, NOTAG],
                              "TE": [short, full, False, None],
                              })

        # S6: dirty the post-tag tree
        f = open(self.project_file("setup.py"), "a")
        f.write("# more dirty\n")
        f.close()
        full = self.git("rev-parse", "HEAD")
        short = "1.0+1.g%s.dirty" % full[:7]
        self.do_checks("S6", {"TA": [short, full, True, None],
                              "TB": ["0+unknown", None, None, UNABLE],
                              "TC": [short, full, True, None],
                              "TD": ["0+unknown", full, False, NOTAG],
                              "TE": [short, full, True, None],
                              })


    def do_checks(self, state, exps):
        if os.path.exists(self.subpath("out")):
            shutil.rmtree(self.subpath("out"))
        # TA: project tree
        self.check_version(self.projdir, state, "TA", exps["TA"])

        # TB: .git-less copy of project tree
        target = self.subpath("out/demoapp-TB")
        shutil.copytree(self.projdir, target)
        if os.path.exists(os.path.join(target, ".git")):
            shutil.rmtree(os.path.join(target, ".git"))
        self.check_version(target, state, "TB", exps["TB"])

        # TC: project tree in versionprefix-named parentdir
        target = self.subpath("out/demo-1.1")
        shutil.copytree(self.projdir, target)
        if os.path.exists(os.path.join(target, ".git")):
            shutil.rmtree(os.path.join(target, ".git"))
        self.check_version(target, state, "TC", ["1.1", None, False, None]) # XXX

        # TD: project subdir of an unpacked git-archive tarball
        target = self.subpath("out/TD/demoapp-TD")
        self.git("archive", "--format=tar", "--prefix=demoapp-TD/",
                 "--output=../demo.tar", "HEAD")
        os.mkdir(self.subpath("out/TD"))
        with tarfile.TarFile(self.subpath("demo.tar")) as t:
            t.extractall(path=self.subpath("out/TD"))
        self.check_version(os.path.join(target, self.project_sub_dir),
                           state, "TD", exps["TD"])

        # TE: unpacked setup.py sdist tarball
        dist_path = os.path.join(self.projdir, "dist")
        if os.path.exists(dist_path):
            shutil.rmtree(dist_path)
        self.python("setup.py", "sdist", "--formats=tar")
        files = os.listdir(dist_path)
        self.assertTrue(len(files)==1, files)
        distfile = files[0]
        self.assertEqual(distfile, "demo-%s.tar" % exps["TE"][0])
        fn = os.path.join(dist_path, distfile)
        os.mkdir(self.subpath("out/TE"))
        with tarfile.TarFile(fn) as t:
            t.extractall(path=self.subpath("out/TE"))
        target = self.subpath("out/TE/demo-%s" % exps["TE"][0])
        self.assertTrue(os.path.isdir(target))
        self.check_version(target, state, "TE", exps["TE"])

    def check_version(self, workdir, state, tree, exps):
        exp_version, exp_full, exp_dirty, exp_error = exps
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
        self.compare(data["version"], exp_version, state, tree, "RB")
        self.compare(data["dirty"], str(exp_dirty), state, tree, "RB")
        self.compare(data["full-revisionid"], str(exp_full), state, tree, "RB")
        self.compare(data["error"], str(exp_error), state, tree, "RB")

    def compare(self, got, expected, state, tree, runtime):
        where = "/".join([state, tree, runtime])
        self.assertEqual(got, expected, "%s: got '%s' != expected '%s'"
                         % (where, got, expected))
        if VERBOSE: print(" good %s" % where)

    def assertPEP440(self, got, state, tree, runtime):
        where = "/".join([state, tree, runtime])
        pv = parse_version(got)
        # rather than using an undocumented API, setuptools dev recommends this
        self.assertFalse("Legacy" in pv.__class__.__name__,
                         "%s: '%s' was not pep440-compatible"
                         % (where, got))
        self.assertEqual(str(pv), got,
                         "%s: '%s' pep440-normalized to '%s'"
                         % (where, got, str(pv)))

if __name__ == '__main__':
    ver, rc = run_command(common.GITS, ["--version"], ".", True)
    print("git --version: %s" % ver.strip())
    unittest.main()
