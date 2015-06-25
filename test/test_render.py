import unittest

from versioneer import render, add_one_to_version

from versioneer_src.render import add_one_to_version

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


class Testing_renderer_case_mixin(object):
    """
    This is a mixin object which can be combined with a unittest.TestCase
    which defines a style and an expected dictionary. See Test_pep440 for
    and example.

    """
    def define_pieces(self, closest_tag, distance=0, dirty=False):
        return {"error": '',
                "closest-tag": closest_tag,
                "distance": distance,
                "dirty": dirty,
                "short": "abc" if distance else '',
                "long": "abcdefg" if distance else '',
                "date": "2016-05-31T13:02:11+0200"}

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


class Test_pep440(unittest.TestCase, Testing_renderer_case_mixin):
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


class Test_pep440_old(unittest.TestCase, Testing_renderer_case_mixin):
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


class Test_pep440_post(unittest.TestCase, Testing_renderer_case_mixin):
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


class Test_pep440_pre(unittest.TestCase, Testing_renderer_case_mixin):
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


class Test_git_describe(unittest.TestCase, Testing_renderer_case_mixin):
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


class Test_add_one_to_version(unittest.TestCase):
    def test_index_0(self):
        result = add_one_to_version('v1.2.3', 0)
        self.assertEqual(result, 'v2.0.0')

    def test_index_1(self):
        result = add_one_to_version('v1.2.3', 1)
        self.assertEqual(result, 'v1.3.0')

    def test_index_2(self):
        result = add_one_to_version('v1.2.3', 2)
        self.assertEqual(result, 'v1.2.4')

    def test_negative_indexing(self):
        result = add_one_to_version('v1.2.3', -2)
        self.assertEqual(result, 'v1.3.0')

    def test_year_version(self):
        result = add_one_to_version('1066.8', 1)
        self.assertEqual(result, '1066.9')

    def test_index_with_rc(self):
        # Note this is not the result you would want from a style,
        # but it is the expected behaviour of this function.
        result = add_one_to_version('v1.2.3rc4', 2)
        self.assertEqual(result, 'v1.2.4rc0')



#class Test_git_describe(unittest.TestCase, Testing_renderer_case_mixin):
#    style = 'pep440-branch-based'
#    expected = {'tagged_0_commits_clean': 'v1.2.3',
#                'tagged_0_commits_dirty': 'v1.2.3-dirty',
#                'tagged_1_commits_clean': 'v1.2.3-1-gabc',
#                'tagged_1_commits_dirty': 'v1.2.3-1-gabc-dirty',
#                'untagged_0_commits_clean': '',
#                'untagged_0_commits_dirty': '-dirty',
#                'untagged_1_commits_clean': 'abc',
#                'untagged_1_commits_dirty': 'abc-dirty',
#                'error_getting_parts': 'unknown'
#                }


if __name__ == '__main__':
    unittest.main()
