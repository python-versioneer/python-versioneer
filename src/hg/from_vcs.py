import sys  # --STRIP DURING BUILD
import re  # --STRIP DURING BUILD
  # --STRIP DURING BUILD
  # --STRIP DURING BUILD
def register_vcs_handler(*args):  # --STRIP DURING BUILD
    def nil(f):  # --STRIP DURING BUILD
        return f  # --STRIP DURING BUILD
    return nil  # --STRIP DURING BUILD
  # --STRIP DURING BUILD
  # --STRIP DURING BUILD
def run_command(): pass  # --STRIP DURING BUILD
  # --STRIP DURING BUILD
  # --STRIP DURING BUILD
class NotThisMethod(Exception):  # --STRIP DURING BUILD
    pass  # --STRIP DURING BUILD
@register_vcs_handler("hg", "pieces_from_vcs")
def hg_pieces_from_vcs(tag_prefix, root, verbose, run_command=run_command):
    """Get version from 'git describe' in the root of the source tree.

    This only gets called if _version.py hasn't already been rewritten
    with a short version string, meaning we're inside a checked out source tree.

    Notes:
        1. This is a lot of hg calls. This can probably be done faster with a log template and/or
           more willingness to parse multi-line output
        2. Because tagging a commit in HG creates a new commit, you will almost never work
           with a tagged copy of the repo
    """
    HGS = ["hg"]
    pieces = {}

    # Short SHA + dirtiness
    hg_short, rc = run_command(HGS, ['id', '-q'])
    if rc == 0:
        short = hg_short.strip()
        dirty = short.endswith('+')
        pieces['dirty'] = dirty
        pieces['short'] = short[:-1] if dirty else short
    else:
        if verbose:
            print("Directory %s not under hg control"%root)
        raise NotThisMethod("'hg status' returned error")

    # long SHA
    hg_long, rc = run_command(HGS, ['id', '-q', '--debug'])
    if rc == 0:
        pieces['long'] = hg_long.strip().split()[0]
    else:
        raise NotThisMethod("'hg id -q --debug' failed")

    # Most recent tagged ancestor - https://stackoverflow.com/a/17848126/1958900
    hg_ancestor, rc = run_command(HGS, ['id', '-r',
                                        '::parents(%s) and tag("re:%s.+")'%(pieces['short'],
                                                                            tag_prefix)])
    if rc == 0:
        ancestor_sha, full_tag = hg_ancestor.strip().split()

        # NOTE: copy/paste'd from git/from_vcs.py. Should be refactored
        if not full_tag.startswith(tag_prefix):
            if verbose:
                fmt = "tag '%s' doesn't start with prefix '%s'"
                print(fmt % (full_tag, tag_prefix))
            pieces["error"] = ("tag '%s' doesn't start with prefix '%s'"
                               % (full_tag, tag_prefix))
        else:
            pieces["closest-tag"] = full_tag[len(tag_prefix):]
        # END copy/pate from git/from_vcs.pieces

    else:  # if we didn't find an ancestor tag, we'll just assume that there are none
        pieces['closest-tag'] = None

        ancestor_sha = 0

    hg_distance, rc = run_command(HGS, ['log', '-q', '-r',
                                        '%s::%s'%(ancestor_sha, pieces['short'])])
    if rc == 0:
        pieces['distance'] = len(hg_distance.strip().splitlines())

    hg_date, rc = run_command(HGS, ['log', '-l1', '--template', '{date|isodate}'])
    pieces["date"] = hg_date.strip().replace(" ", "T", 1).replace(" ", "", 1)

    return pieces
