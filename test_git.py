#! /usr/bin/python

import unittest

execfile("src/git/middle.py")

class Variables(unittest.TestCase):
    def parse(self, refnames, full, prefix=""):
        return versions_from_expanded_variables({"refnames": refnames,
                                                 "full": full}, prefix)

    def test_parse(self):
        v = self.parse(" (HEAD, 2.0,master  , otherbranch ) ", " full ")
        self.failUnlessEqual(v["version"], "2.0")
        self.failUnlessEqual(v["full"], "full")

    def test_prefer_short(self):
        v = self.parse(" (HEAD, 2.0rc1, 2.0, 2.0rc2) ", " full ")
        self.failUnlessEqual(v["version"], "2.0")
        self.failUnlessEqual(v["full"], "full")

    def test_prefix(self):
        v = self.parse(" (HEAD, projectname-2.0) ", " full ", "projectname-")
        self.failUnlessEqual(v["version"], "2.0")
        self.failUnlessEqual(v["full"], "full")

    def test_unexpanded(self):
        v = self.parse(" $Format$ ", " full ", "projectname-")
        self.failUnlessEqual(v, {})

    def test_no_tags(self):
        v = self.parse("(HEAD, master)", "full")
        self.failUnlessEqual(v["version"], "full")
        self.failUnlessEqual(v["full"], "full")

    def test_no_prefix(self):
        v = self.parse("(HEAD, master, 1.23)", "full", "missingprefix-")
        self.failUnlessEqual(v["version"], "full")
        self.failUnlessEqual(v["full"], "full")

if __name__ == '__main__':
    unittest.main()
