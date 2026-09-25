"""Run every harness check in one go.  Non-zero exit if anything is wrong.

    python docs/harness/check_all.py

What it runs, in order - every one is a hard gate:

  validate_sot.py          sot/channels.csv, and every drawing against it
  sync_io_table.py --check XTREMEX-IO-TABLE.html agrees with sot/channels.csv
  lint_v09.py              schema and reference check, all nine looms
  verify_rebuild.py        no connection lost against the frozen legacy baseline
  audit_cavity_parts.py    no cavity claims both a contact and a sealing plug
  audit_shields.py         docs/SHIELD-RULES.md, enforced
  audit_pin_names.py       shield grounds carry drains only; one name per mating cavity
  audit_mating.py          A cabin mates A engine, B mates B; screens stay in their loom
  audit_bulkhead_pairs.py  no bulkhead cavity wired on one side only
  audit_bh_collisions.py   no two circuits on one half of a bulkhead cavity
  buylist.py               buy list, and the shared-connector consistency check
  buildlist.py             per-wire build list
  make_min.py              the upload copies in min/
"""
import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
HARD = [["validate_sot.py"], ["sync_io_table.py", "--check"], ["lint_v09.py"],
        ["verify_rebuild.py"], ["audit_cavity_parts.py"], ["audit_shields.py"],
        ["audit_pin_names.py"], ["audit_mating.py"], ["audit_bulkhead_pairs.py"],
        ["audit_bh_collisions.py"], ["buylist.py"], ["buildlist.py"], ["make_min.py"]]
# audit_pin_names went HARD on 2026-09-24, the day it first reported zero, and
# it stays there. Both of Daniel's absolute rules live in it: nothing but a
# drain on a shield ground, and one name per bulkhead cavity across a mating
# pair. Neither may ever go back above zero.
#
# 2026-09-25: the pair and collision audits went HARD. The last one-sided
# cavities were EngineRoom-C cross-reference dummies the audit could not read,
# and the CAN pair is now drawn once, in ST185-CAN only.

fails = []
for cmd in HARD:
    name = cmd[0]
    print("=" * 70)
    print(" ".join(cmd))
    print("=" * 70)
    sys.stdout.flush()
    r = subprocess.run([sys.executable, os.path.join(HERE, name)] + cmd[1:])
    if r.returncode:
        fails.append(name)
    print()

if fails:
    print("FAILED: " + ", ".join(fails))
    sys.exit(1)
print("all checks passed")
