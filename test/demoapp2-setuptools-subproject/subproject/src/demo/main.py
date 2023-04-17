#!/usr/bin/env python

import demo
from demo import _version
from demolib import __version__ as libversion

def run(*args, **kwargs):
    print(f"__version__:{demo.__version__}")
    print(f"_version:{str(_version)}")
    versions = _version.get_versions()
    for k in sorted(versions.keys()):
        print(f"{k}:{versions[k]}")
    print(f"demolib:{libversion}")
