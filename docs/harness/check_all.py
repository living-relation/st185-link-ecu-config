"""Run every harness check in one go.  Non-zero exit if anything is wrong.

    python docs/harness/check_all.py

What it runs, in order - every one in HARD is a hard gate:

  validate_sot.py          sot/channels.csv, and every drawing against it
  sync_io_table.py --check XTREMEX-IO-TABLE.html agrees with sot/channels.csv
  lint_v09.py              schema and reference check, every loom
  validate_ownership.py    every drawing registered, one owner per conductor and part
  validate_interfaces.py   inline interfaces are real, matched connector pairs, wired pin for
                           pin (same circuit / named ECU pin on matching cavities, spares on both)
  validate_wheel_speed.py  front/rear wheel-speed Y harnesses, interfaces and spurs
  verify_connectivity.py   every SoT signal pin reaches a LABELLED far end (device plug, flying
                           lead, endpoint lead), across every boundary
  validate_oem_endpoints.py OEM points are flying leads with EWD locators
  audit_cavity_parts.py    right part per cavity, and the contact fits: gender, wire gauge
                           (combined gauge for splices) in range, datasheet contact list (gaps listed)
  audit_logic_gauge.py     no wire heavier than 12 AWG on a LOGIC box fuse / relay cavity; the
                           strip feeds take M5 lugs (Daniel 2026-10-12, moved from the RFRM 2026-10-14)
  audit_shields.py         docs/SHIELD-RULES.md, enforced
  audit_pin_names.py       shield grounds carry drains only; one name per mating cavity
  audit_mating.py          A cabin mates A engine, B mates B
  audit_shared_connectors.py a connector shared by several files is drawn whole in each: same
                           part, full cavity count, other files' cavities N/C (Daniel 2026-10-12)
  validate_bulkhead_letter.py ECU looms follow the ECU connector letter; crossovers a/b/c only
  audit_bulkhead_pairs.py  no bulkhead cavity wired on one side only
  audit_bh_collisions.py   bulkhead pin sharing (direct or pigtail + splice): only one class
                           behind a pin - same rail, ground, shield drain, CAN H or CAN L
                           (self-test: test_gates.py, run in CI)
  part_desc.py             part descriptions describe the part only (standard format)
  audit_parts_layout.py    no unused parts in any parts list; no layout join between separate
                           harnesses (Daniel 2026-10-12)
  check_harnesslib.py      every part a drawing uses is in rebuild/ST185.harnesslib and equal to it
  audit_drawing_rules.py   signals (one propagating per net, terminals never, no empty wired
                           cavity), 30-unit grid, bundle lengths, layout left to right, no overlaps
  audit_wire_spacing.py    W2: layout bundles 30 apart unless they end at the same connector / device
                           (R107); RP1: no wire routing points unless Dan allow-lists the wire (DECISIONS
                           R141, which retired R86's W1 and route_wires.py; strip_routing_points.py)
  audit_ident_bands.py     ident bands (DECISIONS R87): palette, one code per circuit per drawing, one code
                           per circuit name everywhere, both sections of a break on one circuit
  audit_dan_rules.py       Daniel's text-level rules (DECISIONS R11, R26, R29, R35, R44): bay
                           flying leads are new wire, no sleeve parts or coverings, wire part
                           numbers, no "not used" / "reserved" cavity signals, no stale notes;
                           only its D1 EngineRoom-C list is SOFT inside the script (printed)
  buylist.py --check       buy list is current, and the shared-connector consistency check
  buildlist.py --check     per-wire build list is current
  check_route_drawings.py  the approved route drawings in routes/ (red route lines unfilled,
                           no broken attributes, a top view after every figure, no
                           overlapping markers in one figure)
  audit_layout.py          layout view (DECISIONS R107, R140 front right): no node or label on another,
                           no bundle through a node or label (Y5: nor along its own end's label), no
                           bundle on top of another, no lone long diagonal. Re-place with layout_tree.py (one straight tree) or
                           layout_trunk.py (keeps a bent trunk); snapshot render_layout.py.
  audit_destinations.py    short names (DECISIONS R124, R125): labels <= 12, label + designation and
                           every signal <= 20, loose ends "<what> -> <where it lands>" <= 32 and unique,
                           no generic words; long text in full_text.json, read back by model.full_text

SOFT (reported, not failing): none at present.

The generators run in --check mode here: they rebuild in memory and fail
if the committed file is stale, but never write. So check_all.py leaves the tree
untouched and CI can trust it. After a harness change, regenerate locally:

    python docs/harness/buylist.py
    python docs/harness/buildlist.py

(no flag, or --write, writes the file) and commit the results with the drawing.

SOFT gates report but do not fail the run. A gate starts SOFT only while the
drawings it checks are still being migrated; it moves to HARD the day it first reports zero, and a HARD gate never goes back.
"""
import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
HARD = [["validate_sot.py"], ["sync_io_table.py", "--check"], ["lint_v09.py"],
        ["validate_ownership.py"], ["validate_interfaces.py"], ["validate_wheel_speed.py"],
        ["verify_connectivity.py"], ["validate_oem_endpoints.py"], ["audit_cavity_parts.py"], ["audit_logic_gauge.py"], ["audit_shields.py"],
        ["audit_pin_names.py"], ["audit_mating.py"], ["audit_shared_connectors.py"], ["validate_bulkhead_letter.py"],
        ["audit_bulkhead_pairs.py"],
        ["audit_bh_collisions.py"], ["part_desc.py"], ["audit_parts_layout.py"], ["check_harnesslib.py"], ["audit_drawing_rules.py"], ["audit_wire_spacing.py"], ["audit_ident_bands.py"],
        ["audit_dan_rules.py"], ["buylist.py", "--check"],
        ["buildlist.py", "--check"], ["check_route_drawings.py"], ["audit_layout.py"], ["audit_destinations.py"],
        ["../../cad/fusebox/src/parts_lists.py", "--check"],   # DECISIONS R82: every fuse box part is real and buyable
        ["../../cad/fusebox/src/check_clearance.py"],          # Dan's 3 mm rule: no two live fuse box parts closer than 3 mm
        ["../../cad/fusebox/src/check_terminal_holes.py"],     # Dan's J2 = B (R94): crimp-sized terminal holes, walls >= 2 mm
        ["../../cad/fusebox/src/check_printed_solid.py"]]      # R101: every printed part one solid, no floating rib / saddle
SOFT = []
# 2026-10-15: audit_destinations started HARD (Dan: "I need the destination to be clear and list
# the actual destination of that wire"); all 15 drawings shortened in the same PR.
# 2026-10-15: audit_layout went HARD (R107) - all 15 drawings report zero after the G2
# drawings (A-engine, B-engine, CAN, EngineRoom-C) were re-placed with layout_trunk.py.
# 2026-10-15: audit_export_sheet.py (R88 PDF export package) retired - Dan dropped the PDF
# export step (K5); the .harness files in the repo are the deliverable.
# 2026-10-14: check_route_drawings went HARD - its last finding (Route 1 Fig. 4, an EWD
# sheet with no top view) got a top view, so it reported zero (OPEN-ITEMS row 65).
# 2026-09-27: verify_connectivity replaced verify_rebuild, whose frozen legacy
# baseline cannot follow the redesign's intentional ownership and boundary moves.
#
# audit_pin_names went HARD on 2026-09-24, the day it first reported zero, and
# it stays there. Both of Daniel's absolute rules live in it: nothing but a
# drain on a shield ground, and one name per bulkhead cavity across a mating
# pair. Neither may ever go back above zero.
#
# 2026-09-28: validate_bulkhead_letter started HARD - Daniel's ECU loom rule. Its
# Its PENDING list is empty since Q-RAIL was ruled on (rails cross on the A side, now bulkhead A c48 / c49).
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
