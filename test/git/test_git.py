#! /usr/bin/python

from __future__ import print_function
import os
import shutil
import tarfile
import unittest
import tempfile
import sys


from pkg_resources import parse_version, SetuptoolsLegacyVersion

sys.path.insert(0, "src")
import common
from render import render
from git import from_vcs, from_keywords
from subprocess_helper import run_command


class Test_ParseGitDescribe(unittest.TestCase):
    def setUp(self):
        self.fakeroot = tempfile.mkdtemp()
        self.fakegit = os.path.join(self.fakeroot, ".git")
        os.mkdir(self.fakegit)

    def test_pieces(self):
        def pv(git_describe, do_error=False, expect_pieces=False, branch_name='HEAD'):
            def fake_run_command(exes, args, cwd=None):
                if args[0] == "describe":
                    if do_error == "describe":
                        return None
                    return git_describe+"\n"
                if args[0] == "rev-parse":
                    if do_error == "rev-parse":
                        return None
                    if args[1] == '--abbrev-ref':
                        return '%s\n' % branch_name
                    else:
                        return "longlong\n"
                if args[0] == "rev-list":
                    return "42\n"
                self.fail("git called in weird way: %s" % (args,))
            return from_vcs.git_pieces_from_vcs(
                "v", self.fakeroot, verbose=False,
                run_command=fake_run_command)
        self.assertRaises(from_vcs.NotThisMethod,
                          pv, "ignored", do_error="describe")
        self.assertRaises(from_vcs.NotThisMethod,
                          pv, "ignored", do_error="rev-parse")
        self.assertEqual(pv("1f"),
                         {"branch": None, "closest-tag": None,
                          "dirty": False, "error": None,
                          "distance": 42,
                          "long": "longlong",
                          "short": "longlon"})
        self.assertEqual(pv("1f-dirty"),
                         {"branch": None, "closest-tag": None,
                          "dirty": True, "error": None,
                          "distance": 42,
                          "long": "longlong",
                          "short": "longlon"})
        self.assertEqual(pv("v1.0-0-g1f"),
                         {"branch": None, "closest-tag": "1.0",
                          "dirty": False, "error": None,
                          "distance": 0,
                          "long": "longlong",
                          "short": "1f"})
        self.assertEqual(pv("v1.0-0-g1f-dirty"),
                         {"branch": None, "closest-tag": "1.0",
                          "dirty": True, "error": None,
                          "distance": 0,
                          "long": "longlong",
                          "short": "1f"})
        self.assertEqual(pv("v1.0-1-g1f"),
                         {"branch": None, "closest-tag": "1.0",
                          "dirty": False, "error": None,
                          "distance": 1,
                          "long": "longlong",
                          "short": "1f"})
        self.assertEqual(pv("v1.0-1-g1f-dirty"),
                         {"branch": None, "closest-tag": "1.0",
                          "dirty": True, "error": None,
                          "distance": 1,
                          "long": "longlong",
                          "short": "1f"})
        self.assertEqual(pv("v1.0-1-g1f-dirty", branch_name="v1.0.x"),
                         {"branch": 'v1.0.x', "closest-tag": "1.0",
                          "dirty": True, "error": None,
                          "distance": 1,
                          "long": "longlong",
                          "short": "1f"})

    def tearDown(self):
        os.rmdir(self.fakegit)
        os.rmdir(self.fakeroot)


class Test_Keywords(unittest.TestCase):
    def parse(self, refnames, full, prefix=""):
        return from_keywords.git_versions_from_keywords(
            {"refnames": refnames, "full": full}, prefix, False)

    def test_parse(self):
        v = self.parse(" (HEAD, 2.0,master  , otherbranch ) ", " full ")
        self.assertEqual(v["branch"], None)
        self.assertEqual(v["version"], "2.0")
        self.assertEqual(v["full-revisionid"], "full")
        self.assertEqual(v["dirty"], False)
        self.assertEqual(v["error"], None)

    def test_prefer_short(self):
        v = self.parse(" (HEAD, 2.0rc1, 2.0, 2.0rc2) ", " full ")
        self.assertEqual(v["branch"], None)
        self.assertEqual(v["version"], "2.0")
        self.assertEqual(v["full-revisionid"], "full")
        self.assertEqual(v["dirty"], False)
        self.assertEqual(v["error"], None)

    def test_prefix(self):
        v = self.parse(" (HEAD, projectname-2.0) ", " full ", "projectname-")
        self.assertEqual(v["branch"], None)
        self.assertEqual(v["version"], "2.0")
        self.assertEqual(v["full-revisionid"], "full")
        self.assertEqual(v["dirty"], False)
        self.assertEqual(v["error"], None)

    def test_unexpanded(self):
        self.assertRaises(from_keywords.NotThisMethod,
                          self.parse, " $Format$ ", " full ", "projectname-")

    def test_no_tags(self):
        v = self.parse("(HEAD, master)", "full")
        self.assertEqual(v["branch"], None)
        self.assertEqual(v["version"], "0+unknown")
        self.assertEqual(v["full-revisionid"], "full")
        self.assertEqual(v["dirty"], False)
        self.assertEqual(v["error"], "no suitable tags")

    def test_no_prefix(self):
        v = self.parse("(HEAD, master, 1.23)", "full", "missingprefix-")
        self.assertEqual(v["branch"], None)
        self.assertEqual(v["version"], "0+unknown")
        self.assertEqual(v["dirty"], False)
        self.assertEqual(v["error"], "no suitable tags")

    def test_branch_heuristics(self):
        v = self.parse("(v0.12.x)", "full", "v")
        self.assertEqual(v["branch"], None)
        # Questionable whether this is desirable.
        self.assertEqual(v["version"], "0.12.x")
        self.assertEqual(v["dirty"], False)
        self.assertEqual(v["error"], None)

    def test_new_tag_style(self):
        v = self.parse("(tag: v0.12.0)", "full", "v")
        self.assertEqual(v["branch"], None)
        self.assertEqual(v["version"], "0.12.0")
        self.assertEqual(v["full-revisionid"], "full")
        self.assertEqual(v["dirty"], False)
        self.assertEqual(v["error"], None)


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
pep440-pre: 1.0.post.dev1
pep440-post: 1.0.post1+g250b7ca
pep440-old: 1.0.post1
git-describe: 1.0-1-g250b7ca
git-describe-long: 1.0-1-g250b7ca

closest-tag: 1.0
distance: 1
dirty: True
pep440: 1.0+1.g250b7ca.dirty
pep440-pre: 1.0.post.dev1
pep440-post: 1.0.post1.dev0+g250b7ca
pep440-old: 1.0.post1.dev0
git-describe: 1.0-1-g250b7ca-dirty
git-describe-long: 1.0-1-g250b7ca-dirty


closest-tag: 1.0+plus
distance: 1
dirty: False
pep440: 1.0+plus.1.g250b7ca
pep440-pre: 1.0+plus.post.dev1
pep440-post: 1.0+plus.post1.g250b7ca
pep440-old: 1.0+plus.post1
git-describe: 1.0+plus-1-g250b7ca
git-describe-long: 1.0+plus-1-g250b7ca

closest-tag: 1.0+plus
distance: 1
dirty: True
pep440: 1.0+plus.1.g250b7ca.dirty
pep440-pre: 1.0+plus.post.dev1
pep440-post: 1.0+plus.post1.dev0.g250b7ca
pep440-old: 1.0+plus.post1.dev0
git-describe: 1.0+plus-1-g250b7ca-dirty
git-describe-long: 1.0+plus-1-g250b7ca-dirty


closest-tag: None
distance: 1
dirty: False
pep440: 0+untagged.1.g250b7ca
pep440-pre: 0.post.dev1
pep440-post: 0.post1+g250b7ca
pep440-old: 0.post1
git-describe: 250b7ca
git-describe-long: 250b7ca

closest-tag: None
distance: 1
dirty: True
pep440: 0+untagged.1.g250b7ca.dirty
pep440-pre: 0.post.dev1
pep440-post: 0.post1.dev0+g250b7ca
pep440-old: 0.post1.dev0
git-describe: 250b7ca-dirty
git-describe-long: 250b7ca-dirty

"""


class Test_RenderPieces(unittest.TestCase):
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


class Test_RepoIntegration(common.Common, unittest.TestCase):

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
        self.run_case("test/demoapp", False)

    def test_script_only(self):
        # This test looks at an application that consists entirely of a
        # script: no libraries (so its setup.py has packages=[]). This sort
        # of app cannot be run from source: you must 'setup.py build' to get
        # anything executable. So of the 3 runtime situations examined by
        # Repo.test_full above, we only care about RB. (RA1 is valid too, but
        # covered by Repo).
        self.run_case("test/demoapp-script-only", True)

    def run_case(self, demoapp_dir, script_only):
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
        setup_cfg_fn = os.path.join(self.subpath("demoapp"), "setup.cfg")
        with open(setup_cfg_fn, "r") as f:
            setup_cfg = f.read()
        setup_cfg = setup_cfg.replace("@VCS@", "git")
        with open(setup_cfg_fn, "w") as f:
            f.write(setup_cfg)
        shutil.copyfile("versioneer.py", self.subpath("demoapp/versioneer.py"))
        self.git("init")
        self.git("add", "--all")
        self.git("commit", "-m", "comment")

        full = self.git("rev-parse", "HEAD")
        v = self.python("setup.py", "--version")
        self.assertEqual(v, "0+untagged.1.g%s" % full[:7])
        v = self.python(os.path.join(self.subpath("demoapp"), "setup.py"),
                        "--version", workdir=self.testdir)
        self.assertEqual(v, "0+untagged.1.g%s" % full[:7])

        out = self.python("versioneer.py", "setup").splitlines()
        self.assertEqual(out[0], "creating src/demo/_version.py")
        if script_only:
            self.assertEqual(out[1], " src/demo/__init__.py doesn't exist, ok")
        else:
            self.assertEqual(out[1], " appending to src/demo/__init__.py")
        self.assertEqual(out[2], " appending 'versioneer.py' to MANIFEST.in")
        self.assertEqual(out[3], " appending versionfile_source ('src/demo/_version.py') to MANIFEST.in")
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

        # "versioneer.py setup" should be idempotent
        out = self.python("versioneer.py", "setup").splitlines()
        self.assertEqual(out[0], "creating src/demo/_version.py")
        if script_only:
            self.assertEqual(out[1], " src/demo/__init__.py doesn't exist, ok")
        else:
            self.assertEqual(out[1], " src/demo/__init__.py unmodified")
        self.assertEqual(out[2], " 'versioneer.py' already in MANIFEST.in")
        self.assertEqual(out[3], " versionfile_source already in MANIFEST.in")
        out = set(self.git("status", "--porcelain").splitlines())
        out.discard("?? versioneer.pyc")
        out.discard("?? __pycache__/")
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
        f = open(self.subpath("demoapp/setup.py"),"a")
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
        self.git("add", "setup.py")
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
        f = open(self.subpath("demoapp/setup.py"),"a")
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
        self.git("add", "setup.py")
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
        f = open(self.subpath("demoapp/setup.py"),"a")
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
        # TA: source tree
        self.check_version(self.subpath("demoapp"), state, "TA", exps["TA"])

        # TB: .git-less copy of source tree
        target = self.subpath("out/demoapp-TB")
        shutil.copytree(self.subpath("demoapp"), target)
        shutil.rmtree(os.path.join(target, ".git"))
        self.check_version(target, state, "TB", exps["TB"])

        # TC: source tree in versionprefix-named parentdir
        target = self.subpath("out/demo-1.1")
        shutil.copytree(self.subpath("demoapp"), target)
        shutil.rmtree(os.path.join(target, ".git"))
        self.check_version(target, state, "TC", ["1.1", None, False, None]) # XXX

        # TD: unpacked git-archive tarball
        target = self.subpath("out/TD/demoapp-TD")
        self.git("archive", "--format=tar", "--prefix=demoapp-TD/",
                 "--output=../demo.tar", "HEAD")
        os.mkdir(self.subpath("out/TD"))
        t = tarfile.TarFile(self.subpath("demo.tar"))
        t.extractall(path=self.subpath("out/TD"))
        t.close()
        self.check_version(target, state, "TD", exps["TD"])

        # TE: unpacked setup.py sdist tarball
        if os.path.exists(self.subpath("demoapp/dist")):
            shutil.rmtree(self.subpath("demoapp/dist"))
        self.python("setup.py", "sdist", "--formats=tar")
        files = os.listdir(self.subpath("demoapp/dist"))
        self.assertTrue(len(files)==1, files)
        distfile = files[0]
        self.assertEqual(distfile, "demo-%s.tar" % exps["TE"][0])
        fn = os.path.join(self.subpath("demoapp/dist"), distfile)
        os.mkdir(self.subpath("out/TE"))
        t = tarfile.TarFile(fn)
        t.extractall(path=self.subpath("out/TE"))
        t.close()
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
        self.assertFalse(isinstance(pv, SetuptoolsLegacyVersion),
                         "%s: '%s' was not pep440-compatible"
                         % (where, got))
        self.assertEqual(str(pv), got,
                         "%s: '%s' pep440-normalized to '%s'"
                         % (where, got, str(pv)))


class Test_GitRepo(common.Common, unittest.TestCase):
    # We care about the following git scenarios:
    #  S1 : master, 0 commits, 0 tags, v0
    #  S2 : master, 1 commits, 0 tags, v0.dev1
    #  S3 : master, 1 commits, 1 tags, v1
    #  S4 : master, 2 commits, 1 tags, v1.dev1
    #  S5 : v1.x, 2 commits, 2 tags, v1.1
    #  S6 : master, 3 commits, 1 tags, v2.pre2
    #       (merge of v1.x back to master)
    #
    # For both clean and dirty situations (uncommitted code changes)
    # We should also check export state.

    expecteds = {'S1': None,
                 'S2': {'branch': 'master',
                        'closest-tag': None,
                        'dirty': False,
                        'distance': 1,
                        'error': None},
                 'S3': {'branch': 'master',
                        'closest-tag': '1.0',
                        'dirty': False,
                        'distance': 0,
                        'error': None},
                 'S4': {'branch': 'master',
                        'closest-tag': '1.0',
                        'dirty': False,
                        'distance': 1,
                        'error': None},
                 'S5': {'branch': 'master',
                        'closest-tag': '2.0',
                        'dirty': False,
                        'distance': 0,
                        'error': None},
                 'S6': {'branch': 'v1.x',
                        'closest-tag': '1.0',
                        'dirty': False,
                        'distance': 1,
                        'error': None},
                 'S7': {'branch': 'v1.x',
                        'closest-tag': '1.1',
                        'dirty': False,
                        'distance': 0,
                        'error': None},
                 'S8': {'branch': 'master',
                        'closest-tag': '2.0',
                        'dirty': False,
                        'distance': 2,
                        'error': None},
                 'S9': {'branch': 'master',
                        'closest-tag': '2.1',
                        'dirty': False,
                        'distance': 0,
                        'error': None},
                 }

    def assert_case(self, case_name, dirty=False):
        tag_prefix = 'v'
        pieces = from_vcs.git_pieces_from_vcs(tag_prefix, self.repo_root,
                                              run_command=run_command)
        pieces.pop('short')
        pieces.pop('long')
        expected = self.expecteds.get(case_name, {})

        if dirty:
            expected['dirty'] = True
        if expected != pieces:
            print('Case: %s' % case_name)

        self.assertEqual(expected, pieces)

    def write_file(self, fname, content):
        with open(os.path.join(self.repo_root, fname), 'w') as fh:
            fh.write(content)

    def test(self):
        tag_prefix = 'v'

        self.testdir = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                    'git_test_repo')
        self.repo_root = os.path.join(self.testdir, 'demoapp')

        # Cleanup
        if os.path.exists(self.repo_root):
            import shutil
            shutil.rmtree(self.repo_root)
        os.makedirs(self.repo_root)

        # S1
        self.git("init")
        self.assertRaises(from_vcs.NotThisMethod,
                          from_vcs.git_pieces_from_vcs,
                          tag_prefix, self.repo_root, run_command=run_command)

        # S2
        self.write_file('a.txt', 'abc')
        self.git("add", "a.txt")
        self.git("commit", "-m", "First commmit.")
        self.assert_case('S2')

        # S3
        self.git("tag", "-a", "v1.0", "-m", "First tag.")
        self.git("branch", "v1.x")
        self.assert_case('S3')

        # S4
        self.write_file('b.txt', 'abc')
        self.git("add", "b.txt")
        self.assert_case('S3', dirty=True)
        self.git("commit", "-m", "Start of 2.0.")
        self.assert_case('S4')

        # S5
        self.git("tag", "-a", "v2.0", "-m", "Second tag.")
        self.assert_case('S5')

        # S6
        self.git("checkout", "v1.x")
        self.write_file('a.txt', 'abcdef')
        self.git("commit", "-am", "Modify 1.x")
        self.assert_case('S6')

        # S7
        self.git("tag", "-a", "v1.1", "-m", "Tag v1.1.")
        self.assert_case('S7')

        # S8
        self.git("checkout", "master")
        # Just check that S5 hasn't been distrupted - we've just added a tag.
        self.assert_case('S5')
        self.git("merge", "v1.x")
        self.assert_case('S8')

        # S9
        self.git("tag", "-a", "v2.1", "-m", "Tag v2.1.")
        self.assert_case('S9')
        self.git("checkout", "v1.x")
        # Again, just check that we haven't disrupted the v1.x branch.
        self.assert_case('S7')


if __name__ == '__main__':
    ver = run_command(common.GITS, ["--version"], ".", True)
    print("git --version: %s" % ver.strip())
    unittest.main()
