#!/usr/bin/env python

import os, sys, base64

VERSIONEER_b64 = """
@VERSIONEER-INSTALLER@
"""

newver = "@VERSIONEER-VERSION@"
v = base64.b64decode(VERSIONEER_b64)
if os.path.exists("versioneer.py"):
    for line in open("versioneer.py").readlines()[:5]:
        if line.startswith("# Version: "):
            oldver = line[len("# Version: "):].strip()
            if oldver != newver:
                print("replacing old versioneer.py (%s)" % oldver)
            break
    else:
        print("overwriting existing versioneer.py")
with open("versioneer.py", "wb") as f:
    f.write(v)
print("versioneer.py (%s) installed into local tree" % newver)
print("Now please follow instructions in the docstring.")
