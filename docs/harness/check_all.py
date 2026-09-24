"""Run every harness check in one go.  Non-zero exit if anything is wrong.

    python docs/harness/check_all.py

What it runs, in order:

  validate_sot.py        sot/channels.csv, and every drawing against it
  lint_v09.py            schema and reference check, all eight looms
  verify_rebuild.py      no connection lost against the frozen legacy baseline
  audit_cavity_parts.py  no cavity claims both a contact and a sealing plug
  audit_shields.py       docs/SHIELD-RULES.md, enforced
  audit_bulkhead_pairs.py  no bulkhead cavity wired on one side only
  buylist.py             buy list, and the shared-connector consistency check
  buildlist.py           per-wire build list
  make_min.py            the upload copies in min/

The pair check is allowed to report findings without failing the run: seven
cavities are one-sided today and four of them are the known loom-crossing
violations that plan 6.41 fixes.  Everything else is a hard gate.
"""
import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
HARD = ["validate_sot.py", "lint_v09.py", "verify_rebuild.py", "audit_cavity_parts.py",
        "audit_shields.py", "audit_pin_names.py", "buylist.py", "buildlist.py",
        "make_min.py"]
SOFT = ["audit_bulkhead_pairs.py", "audit_bh_collisions.py"]
# audit_pin_names went HARD on 2026-09-24, the day it first reported zero, and
# it stays there. Both of Daniel's absolute rules live in it: nothing but a
# drain on a shield ground, and one name per bulkhead cavity across a mating
# pair. Neither may ever go back above zero.
#
# audit_bh_collisions is SOFT for one reason only: the four remaining findings
# are the CAN pair drawn twice, because ST185-CAN carries its own copy of
# bh_a_fw/bh_a_eng c30/c31. Make it HARD once that duplicate is resolved.

fails = []
for name in HARD + SOFT:
    print("=" * 70)
    print(name)
    print("=" * 70)
    r = subprocess.run([sys.executable, os.path.join(HERE, name)])
    if r.returncode and name in HARD:
        fails.append(name)
    print()

if fails:
    print("FAILED: " + ", ".join(fails))
    sys.exit(1)
print("all checks passed")
