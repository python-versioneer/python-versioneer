import unittest

from versioneer import render


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


if __name__ == '__main__':
    unittest.main()
