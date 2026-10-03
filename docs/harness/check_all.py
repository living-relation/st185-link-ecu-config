"""Run every harness check in one go.  Non-zero exit if anything is wrong.

    python docs/harness/check_all.py

What it runs, in order - every one in HARD is a hard gate:

  validate_sot.py          sot/channels.csv, and every drawing against it
  sync_io_table.py --check XTREMEX-IO-TABLE.html agrees with sot/channels.csv
  lint_v09.py              schema and reference check, every loom
  validate_ownership.py    every drawing registered, one owner per conductor and part
  validate_interfaces.py   inline interfaces are real, matched connector pairs
  validate_wheel_speed.py  front/rear wheel-speed Y harnesses, interfaces and spurs
  verify_connectivity.py   every SoT signal pin reaches a device, across every boundary
  validate_oem_endpoints.py OEM points are flying leads with EWD locators
  audit_cavity_parts.py    no cavity claims both a contact and a sealing plug
  audit_shields.py         docs/SHIELD-RULES.md, enforced
  audit_pin_names.py       shield grounds carry drains only; one name per mating cavity
  audit_mating.py          A cabin mates A engine, B mates B
  validate_bulkhead_letter.py ECU looms follow the ECU connector letter; crossovers a/b/c only
  audit_bulkhead_pairs.py  no bulkhead cavity wired on one side only
  audit_bh_collisions.py   no two circuits on one half of a bulkhead cavity
  part_desc.py             part descriptions describe the part only (standard format)
  buylist.py --check       buy list is current, and the shared-connector consistency check
  buildlist.py --check     per-wire build list is current
  make_min.py --check      the upload copies in min/ are current

The three generators run in --check mode here: they rebuild in memory and fail
if the committed file is stale, but never write. So check_all.py leaves the tree
untouched and CI can trust it. After a harness change, regenerate locally:

    python docs/harness/buylist.py
    python docs/harness/buildlist.py
    python docs/harness/make_min.py

(no flag, or --write, writes the file) and commit the results with the drawing.

SOFT gates report but do not fail the run. A gate starts SOFT only while the
drawings it checks are still being migrated (redesign/IMPLEMENTATION-PLAN.md);
it moves to HARD the day it first reports zero, and a HARD gate never goes back.
"""
import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
HARD = [["validate_sot.py"], ["sync_io_table.py", "--check"], ["lint_v09.py"],
        ["validate_ownership.py"], ["validate_interfaces.py"], ["validate_wheel_speed.py"],
        ["verify_connectivity.py"], ["validate_oem_endpoints.py"], ["audit_cavity_parts.py"], ["audit_shields.py"],
        ["audit_pin_names.py"], ["audit_mating.py"], ["validate_bulkhead_letter.py"],
        ["audit_bulkhead_pairs.py"],
        ["audit_bh_collisions.py"], ["part_desc.py"], ["buylist.py", "--check"],
        ["buildlist.py", "--check"], ["make_min.py", "--check"]]
SOFT = []
# 2026-09-27: verify_connectivity replaced verify_rebuild, whose frozen legacy
# baseline cannot follow the redesign's intentional ownership and boundary moves.
#
# audit_pin_names went HARD on 2026-09-24, the day it first reported zero, and
# it stays there. Both of Daniel's absolute rules live in it: nothing but a
# drain on a shield ground, and one name per bulkhead cavity across a mating
# pair. Neither may ever go back above zero.
#
# 2026-09-28: validate_bulkhead_letter started HARD - Daniel's ECU loom rule. Its
# Its PENDING list is empty since Q-RAIL was ruled on (rails cross on the A side, IX_RAIL_A).
#
# 2026-09-28: part_desc started HARD - Daniel's rule that a part description names
# the part itself, never the net, device or circuit it is used on.
#
# 2026-09-25: the pair and collision audits went HARD. The last one-sided
# cavities were EngineRoom-C cross-reference dummies the audit could not read,
# and the CAN pair is now drawn once, in ST185-CAN only.


def run(cmd):
    print("=" * 70)
    print(" ".join(cmd))
    print("=" * 70)
    sys.stdout.flush()
    r = subprocess.run([sys.executable, os.path.join(HERE, cmd[0])] + cmd[1:])
    print()
    return r.returncode


fails = [c[0] for c in HARD if run(c)]
soft = [c[0] for c in SOFT if run(c)]

if soft:
    print("SOFT (reported, not failing): " + ", ".join(soft))
if fails:
    print("FAILED: " + ", ".join(fails))
    sys.exit(1)
print("all checks passed")
