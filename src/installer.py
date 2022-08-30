#!/usr/bin/env python

import sys, base64

VERSIONEER_b64 = """
@VERSIONEER-INSTALLER@
"""
newver = "@VERSIONEER-VERSION@"

VERSIONEER_PEP518 = True

VERSIONEER = base64.b64decode(VERSIONEER_b64.encode('ASCII'))


# Stub overwritten by exec()
def setup_command(): ...

# Make versioneer usable via import
exec(VERSIONEER.decode(), globals())


def detect_installed_version() -> str:
    """Find version string in vendored versioneer

    Raises FileNotFoundError if missing.
    """
    with open("versioneer.py") as fobj:
        for i, line in enumerate(fobj):
            if line.startswith("# Version: "):
                return line[len("# Version: "):].strip()
            if i > 5:
                break
    return "unknown version"


def vendor():
    """Install versioneer into current directory"""
    try:
        oldver = detect_installed_version()
    except FileNotFoundError:
        pass
    else:
        print(f"replacing old versioneer.py ({oldver})")

    with open("versioneer.py", "wb") as fobj:
        fobj.write(VERSIONEER)
    print(f"versioneer.py ({newver}) installed into local tree")


def main():
    usage = "Usage: versioneer install [--vendor|--no-vendor]"
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(usage)
        sys.exit(1)

    command = sys.argv[1]
    mode = "--vendor" if len(sys.argv) == 2 else sys.argv[2]

    if command in ("version", "--version"):
        print("versioneer (installer) %s" % newver)
        sys.exit(0)
    elif command in ("help", "-help", "--help"):
        print(usage)
        sys.exit(0)
    elif command != "install" or mode not in ("--vendor", "--no-vendor"):
        print(usage)
        sys.exit(1)

    if mode == "--vendor":
        vendor()
        print("Now running 'versioneer.py setup' to install the generated files..")

    setup_command()


if __name__ == '__main__':
    main()
