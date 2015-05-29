#!/usr/bin/env python

import demo
from demo import _version
from demolib import __version__ as libversion

def run(*args, **kwargs):
    print("__version__:%s" % demo.__version__)
    print("_version:%s" % str(_version))
    versions = _version.get_versions()
    for k in sorted(versions.keys()):
        print("%s:%s" % (k,versions[k]))
    print("demolib:%s" % libversion)
