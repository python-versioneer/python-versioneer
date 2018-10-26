import os
import sys
import unittest

SOURCE_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if not os.path.exists(os.path.join(SOURCE_ROOT, 'versioneer.py')):
    print('Please run "python setup.py make_versioneer"')
    sys.exit(1)

sys.path.insert(0, SOURCE_ROOT)
from versioneer import render


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


class renderer_case_mixin(object):
    """
    This is a mixin object which can be combined with a unittest.TestCase
    which defines a style and an expected dictionary. See Test_pep440 for
    and example.

    """
    def define_pieces(self, closest_tag, distance=0, dirty=False):
        branch = getattr(self, 'branch', 'master')
        if branch:
            replacements = ([' ', '.'], ['(', ''], [')', ''], ['\\', '-'], ['/', '-'])
            for old, new in replacements:
                branch = branch.replace(old, new)

        return {"error": '',
                "closest-tag": closest_tag,
                "distance": distance,
                "dirty": dirty,
                "short": "abc" if distance else '',
                "long": "abcdefg" if distance else '',
                "date": "2016-05-31T13:02:11+0200",
                "branch": branch}

    def assert_rendered(self, pieces, test_case_name):
        version = render(pieces, self.style)['version']
        expected = self.expected[test_case_name]
        msg = ('Versions differ for {0} style with "{1}" case: expected {2}, '
               'got {3}'.format(self.style, test_case_name, expected, version))
        self.assertEqual(version, expected, msg)

    # Naming structure:
    # test_(un)tagged_<n>_commits_(clean|dirty)
    def test_tagged_0_commits_clean(self):
        self.assert_rendered(self.define_pieces('v1.2.3'),
                             'tagged_0_commits_clean')

    def test_tagged_1_commits_clean(self):
        self.assert_rendered(self.define_pieces('v1.2.3', distance=1),
                             'tagged_1_commits_clean')

    def test_tagged_0_commits_dirty(self):
        self.assert_rendered(self.define_pieces('v1.2.3', dirty=True),
                             'tagged_0_commits_dirty')

    def test_tagged_1_commits_dirty(self):
        self.assert_rendered(self.define_pieces('v1.2.3', distance=1,
                                                dirty=True),
                             'tagged_1_commits_dirty')

    def test_untagged_0_commits_clean(self):
        self.assert_rendered(self.define_pieces(None),
                             'untagged_0_commits_clean')

    def test_untagged_1_commits_clean(self):
        self.assert_rendered(self.define_pieces(None, distance=1),
                             'untagged_1_commits_clean')

    def test_untagged_0_commits_dirty(self):
        self.assert_rendered(self.define_pieces(None, dirty=True),
                             'untagged_0_commits_dirty')

    def test_untagged_1_commits_dirty(self):
        self.assert_rendered(self.define_pieces(None, distance=1,
                                                dirty=True),
                             'untagged_1_commits_dirty')

    def test_error_getting_parts(self):
        self.assert_rendered({'error': 'Not a git repo'},
                             'error_getting_parts')


class Test_pep440(unittest.TestCase, renderer_case_mixin):
    style = 'pep440'
    expected = {'tagged_0_commits_clean': 'v1.2.3',
                'tagged_0_commits_dirty': 'v1.2.3+0.g.dirty',
                'tagged_1_commits_clean': 'v1.2.3+1.gabc',
                'tagged_1_commits_dirty': 'v1.2.3+1.gabc.dirty',
                'untagged_0_commits_clean': '0+untagged.0.g',
                'untagged_0_commits_dirty': '0+untagged.0.g.dirty',
                'untagged_1_commits_clean': '0+untagged.1.gabc',
                'untagged_1_commits_dirty': '0+untagged.1.gabc.dirty',
                'error_getting_parts': 'unknown'
                }


class Test_pep440_old(unittest.TestCase, renderer_case_mixin):
    style = 'pep440-old'
    expected = {'tagged_0_commits_clean': 'v1.2.3',
                'tagged_0_commits_dirty': 'v1.2.3.post0.dev0',
                'tagged_1_commits_clean': 'v1.2.3.post1',
                'tagged_1_commits_dirty': 'v1.2.3.post1.dev0',
                'untagged_0_commits_clean': '0.post0',
                'untagged_0_commits_dirty': '0.post0.dev0',
                'untagged_1_commits_clean': '0.post1',
                'untagged_1_commits_dirty': '0.post1.dev0',
                'error_getting_parts': 'unknown'
                }


class Test_pep440_post(unittest.TestCase, renderer_case_mixin):
    style = 'pep440-post'
    expected = {'tagged_0_commits_clean': 'v1.2.3',
                'tagged_0_commits_dirty': 'v1.2.3.post0.dev0+g',
                'tagged_1_commits_clean': 'v1.2.3.post1+gabc',
                'tagged_1_commits_dirty': 'v1.2.3.post1.dev0+gabc',
                'untagged_0_commits_clean': '0.post0+g',
                'untagged_0_commits_dirty': '0.post0.dev0+g',
                'untagged_1_commits_clean': '0.post1+gabc',
                'untagged_1_commits_dirty': '0.post1.dev0+gabc',
                'error_getting_parts': 'unknown'
                }


class Test_pep440_pre(unittest.TestCase, renderer_case_mixin):
    style = 'pep440-pre'
    expected = {'tagged_0_commits_clean': 'v1.2.3',
                'tagged_0_commits_dirty': 'v1.2.3',
                'tagged_1_commits_clean': 'v1.2.3.post.dev1',
                'tagged_1_commits_dirty': 'v1.2.3.post.dev1',
                'untagged_0_commits_clean': '0.post.dev0',
                'untagged_0_commits_dirty': '0.post.dev0',
                'untagged_1_commits_clean': '0.post.dev1',
                'untagged_1_commits_dirty': '0.post.dev1',
                'error_getting_parts': 'unknown'
                }


class Test_git_describe(unittest.TestCase, renderer_case_mixin):
    style = 'git-describe'
    expected = {'tagged_0_commits_clean': 'v1.2.3',
                'tagged_0_commits_dirty': 'v1.2.3-dirty',
                'tagged_1_commits_clean': 'v1.2.3-1-gabc',
                'tagged_1_commits_dirty': 'v1.2.3-1-gabc-dirty',
                'untagged_0_commits_clean': '',
                'untagged_0_commits_dirty': '-dirty',
                'untagged_1_commits_clean': 'abc',
                'untagged_1_commits_dirty': 'abc-dirty',
                'error_getting_parts': 'unknown'
                }


class Test_pep440_branch_based__master(unittest.TestCase,
                                       renderer_case_mixin):
    style = 'pep440-branch-based'
    branch = 'master'
    expected = {'tagged_0_commits_clean': 'v1.2.3',
                'tagged_0_commits_dirty': 'v1.2.3.dev0+0.master.g.dirty',
                'tagged_1_commits_clean': 'v1.2.3.dev0+1.master.gabc',
                'tagged_1_commits_dirty': 'v1.2.3.dev0+1.master.gabc.dirty',
                'untagged_0_commits_clean': '0+untagged.0.master.g',
                'untagged_0_commits_dirty': '0+untagged.0.master.g.dirty',
                'untagged_1_commits_clean': '0+untagged.1.master.gabc',
                'untagged_1_commits_dirty': '0+untagged.1.master.gabc.dirty',
                'error_getting_parts': 'unknown'
                }


class Test_pep440_branch_based__maint(unittest.TestCase,
                                      renderer_case_mixin):
    style = 'pep440-branch-based'
    branch = 'v1.2.x'
    expected = {'tagged_0_commits_clean': 'v1.2.3',
                'tagged_0_commits_dirty': 'v1.2.3.dev0+0.v1.2.x.g.dirty',
                'tagged_1_commits_clean': 'v1.2.3.dev0+1.v1.2.x.gabc',
                'tagged_1_commits_dirty': 'v1.2.3.dev0+1.v1.2.x.gabc.dirty',
                'untagged_0_commits_clean': '0+untagged.0.v1.2.x.g',
                'untagged_0_commits_dirty': '0+untagged.0.v1.2.x.g.dirty',
                'untagged_1_commits_clean': '0+untagged.1.v1.2.x.gabc',
                'untagged_1_commits_dirty': '0+untagged.1.v1.2.x.gabc.dirty',
                'error_getting_parts': 'unknown'
                }


class Test_pep440_branch_based__feature_branch(unittest.TestCase,
                                               renderer_case_mixin):
    style = 'pep440-branch-based'
    branch = 'feature_branch'
    expected = {'tagged_0_commits_clean': 'v1.2.3',
                'tagged_0_commits_dirty': 'v1.2.3.dev0+0.feature_branch.g.dirty',
                'tagged_1_commits_clean': 'v1.2.3.dev0+1.feature_branch.gabc',
                'tagged_1_commits_dirty': 'v1.2.3.dev0+1.feature_branch.gabc.dirty',
                'untagged_0_commits_clean': '0+untagged.0.feature_branch.g',
                'untagged_0_commits_dirty': '0+untagged.0.feature_branch.g.dirty',
                'untagged_1_commits_clean': '0+untagged.1.feature_branch.gabc',
                'untagged_1_commits_dirty': '0+untagged.1.feature_branch.gabc.dirty',
                'error_getting_parts': 'unknown'
                }


class Test_pep440_branch_based__no_branch_info(unittest.TestCase,
                                               renderer_case_mixin):
    style = 'pep440-branch-based'
    branch = None
    expected = {'tagged_0_commits_clean': 'v1.2.3',
                'tagged_0_commits_dirty': 'v1.2.3.dev0+0.unknown_branch.g.dirty',
                'tagged_1_commits_clean': 'v1.2.3.dev0+1.unknown_branch.gabc',
                'tagged_1_commits_dirty': 'v1.2.3.dev0+1.unknown_branch.gabc.dirty',
                'untagged_0_commits_clean': '0+untagged.0.unknown_branch.g',
                'untagged_0_commits_dirty': '0+untagged.0.unknown_branch.g.dirty',
                'untagged_1_commits_clean': '0+untagged.1.unknown_branch.gabc',
                'untagged_1_commits_dirty': '0+untagged.1.unknown_branch.gabc.dirty',
                'error_getting_parts': 'unknown'
                }


class Test_pep440_branch_based__space_in_branch(unittest.TestCase,
                                              renderer_case_mixin):
    style = 'pep440-branch-based'
    branch = 'foo bar'
    expected = {'tagged_0_commits_clean': 'v1.2.3',
                'tagged_0_commits_dirty': 'v1.2.3.dev0+0.foo.bar.g.dirty',
                'tagged_1_commits_clean': 'v1.2.3.dev0+1.foo.bar.gabc',
                'tagged_1_commits_dirty': 'v1.2.3.dev0+1.foo.bar.gabc.dirty',
                'untagged_0_commits_clean': '0+untagged.0.foo.bar.g',
                'untagged_0_commits_dirty': '0+untagged.0.foo.bar.g.dirty',
                'untagged_1_commits_clean': '0+untagged.1.foo.bar.gabc',
                'untagged_1_commits_dirty': '0+untagged.1.foo.bar.gabc.dirty',
                'error_getting_parts': 'unknown'
                }


class Test_pep440_branch_based__forward_slash_in_branch(unittest.TestCase,
                                                        renderer_case_mixin):
    style = 'pep440-branch-based'
    branch = 'foo/bar'
    expected = {'tagged_0_commits_clean': 'v1.2.3',
                'tagged_0_commits_dirty': 'v1.2.3.dev0+0.foo.bar.g.dirty',
                'tagged_1_commits_clean': 'v1.2.3.dev0+1.foo.bar.gabc',
                'tagged_1_commits_dirty': 'v1.2.3.dev0+1.foo.bar.gabc.dirty',
                'untagged_0_commits_clean': '0+untagged.0.foo.bar.g',
                'untagged_0_commits_dirty': '0+untagged.0.foo.bar.g.dirty',
                'untagged_1_commits_clean': '0+untagged.1.foo.bar.gabc',
                'untagged_1_commits_dirty': '0+untagged.1.foo.bar.gabc.dirty',
                'error_getting_parts': 'unknown'
                }


class Test_pep440_branch_based__back_slash_in_branch(unittest.TestCase,
                                                        renderer_case_mixin):
    style = 'pep440-branch-based'
    branch = 'foo\\bar'
    expected = {'tagged_0_commits_clean': 'v1.2.3',
                'tagged_0_commits_dirty': 'v1.2.3.dev0+0.foo.bar.g.dirty',
                'tagged_1_commits_clean': 'v1.2.3.dev0+1.foo.bar.gabc',
                'tagged_1_commits_dirty': 'v1.2.3.dev0+1.foo.bar.gabc.dirty',
                'untagged_0_commits_clean': '0+untagged.0.foo.bar.g',
                'untagged_0_commits_dirty': '0+untagged.0.foo.bar.g.dirty',
                'untagged_1_commits_clean': '0+untagged.1.foo.bar.gabc',
                'untagged_1_commits_dirty': '0+untagged.1.foo.bar.gabc.dirty',
                'error_getting_parts': 'unknown'
                }


class Test_pep440_branch_based__parenthesis_in_branch(unittest.TestCase,
                                                        renderer_case_mixin):
    style = 'pep440-branch-based'
    branch = 'foo(bar)'
    expected = {'tagged_0_commits_clean': 'v1.2.3',
                'tagged_0_commits_dirty': 'v1.2.3.dev0+0.foobar.g.dirty',
                'tagged_1_commits_clean': 'v1.2.3.dev0+1.foobar.gabc',
                'tagged_1_commits_dirty': 'v1.2.3.dev0+1.foobar.gabc.dirty',
                'untagged_0_commits_clean': '0+untagged.0.foobar.g',
                'untagged_0_commits_dirty': '0+untagged.0.foobar.g.dirty',
                'untagged_1_commits_clean': '0+untagged.1.foobar.gabc',
                'untagged_1_commits_dirty': '0+untagged.1.foobar.gabc.dirty',
                'error_getting_parts': 'unknown'
                }


if __name__ == '__main__':
    unittest.main()
