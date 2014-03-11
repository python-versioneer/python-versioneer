#!/usr/bin/env python

import base64

VERSIONEER_b64 = """
@VERSIONEER-INSTALLER@
"""

v = base64.b64decode(VERSIONEER_b64)
with open("versioneer.py", "w") as f:
    f.write(v)
print "versioneer.py installed into local tree"
print "Now please follow instructions in the docstring."
