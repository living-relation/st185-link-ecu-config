"""Run every repo gate in one go.  Non-zero exit if anything is wrong.

    python tools/check_all.py

Every gate runs read-only (--check mode): it rebuilds in memory and fails if a committed file is stale, but never
writes, so the tree is untouched and CI can trust it.

  docs/harness/tools/check_wiring.py       the ONE wiring check (DECISIONS R221): the master wire list, sot/channels.csv
                                           (ECU settings), the IO table, the route drawings
  docs/harness/tools/build_drawings.py     our own drawing sets and the DRB102 map are current against the master
  docs/sourcing/build_project_bom.py       the ONE project BOM / shopping list is current
  cad/fusebox/src/parts_lists.py           R82: every fuse box part is real and buyable
  cad/fusebox/src/check_clearance.py       Dan's 3 mm rule: no two live fuse box parts closer than 3 mm
  cad/fusebox/src/check_terminal_holes.py  Dan's J2 = B (R94): crimp-sized terminal holes, walls >= 2 mm
  cad/fusebox/src/check_printed_solid.py   R101: every printed part one solid
  cad/check_drawings_current.py            R183: every drawing matches its model
  cad/check_drawing_rules.py               R184-R196: balloons, tangent edges, banned notes
  tools/check_doc_claims.py                R211: no stale documents

After a wiring change: edit docs/harness/MASTER-wirelist.csv, then
    python docs/harness/tools/check_wiring.py
    python docs/harness/tools/build_drawings.py <set>
    python docs/sourcing/build_project_bom.py
and commit the results with the list.
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARD = [["docs/harness/tools/check_wiring.py"],
        ["docs/harness/tools/build_drawings.py", "--check"],
        ["docs/sourcing/build_project_bom.py", "--check"],
        ["cad/fusebox/src/parts_lists.py", "--check"],
        ["cad/fusebox/src/check_clearance.py"],
        ["cad/fusebox/src/check_terminal_holes.py"],
        ["cad/fusebox/src/check_printed_solid.py"],
        ["cad/check_drawings_current.py"],
        ["cad/check_drawing_rules.py"],
        ["tools/check_doc_claims.py"]]


def run(cmd):
    print("=" * 70)
    print(" ".join(cmd))
    print("=" * 70)
    sys.stdout.flush()
    r = subprocess.run([sys.executable, os.path.join(REPO, cmd[0])] + cmd[1:], cwd=REPO)
    print()
    return r.returncode


fails = [c[0] for c in HARD if run(c)]
if fails:
    print("FAILED: " + ", ".join(fails))
    sys.exit(1)
print("all checks passed")
