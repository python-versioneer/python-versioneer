#!/usr/bin/env python

import os, sys, base64

VERSIONEER_b64 = """
@VERSIONEER-INSTALLER@
"""
newver = "@VERSIONEER-VERSION@"


def main():
    if len(sys.argv) < 2:
        print("Usage: versioneer install")
        sys.exit(1)

    command = sys.argv[1]
    if command in ("version", "--version"):
        print("versioneer (installer) %s" % newver)
        sys.exit(0)

    if command != "install":
        print("Usage: versioneer install")
        sys.exit(1)

    v = base64.b64decode(VERSIONEER_b64.encode('ASCII'))
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
    print("Now running 'versioneer.py setup' to install the generated files..")
    if " " in sys.executable:
        import subprocess  # Do not import unless absolutely necessary to avoid compatibility issues
        subprocess.call([sys.executable, "versioneer.py", "setup"])
    else:
        os.execl(sys.executable, sys.executable, "versioneer.py", "setup")

if __name__ == '__main__':
    main()
