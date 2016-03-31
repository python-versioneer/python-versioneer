from __future__ import print_function
import os
from pyflakes.api import main

def get_filenames():
    for dirpath, dirnames, filenames in os.walk("src"):
        if dirpath.endswith("__pycache__"):
            continue
        for rel_fn in filenames:
            if not rel_fn.endswith(".py"):
                continue
            fn = os.path.join(dirpath, rel_fn)
            if fn in [os.path.join("src", "header.py"),
                      os.path.join("src", "git", "long_header.py"),
                      ]:
                continue
            print("pyflakes on:", fn)
            yield fn

main(args=list(get_filenames()))
