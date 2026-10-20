"""Daniel's text-level rules that no other gate reads (docs/harness/redesign/DECISIONS.md
"Binding rules from Daniel", 2026-10-12). Each check names its rule.

  D1  R11  no OEM engine-bay wire is reused: an interfaces.json flying lead on a pure
           engine-bay harness (ECU-engine, HeavyDC, WheelSpeed-*) whose method says it
           splices into a factory lead FAILS. EngineRoom-C flying leads are LISTED (its cabin-side
           landings at J/B1 / IE1 / the blower / the window feed are allowed cabin splices;
           its bay ends must be new wire to the device plug - read the list).
  D2  R29 / R44  no sleeve: no splice / covering / boot / tube part whose number or description
           says SLEEVE, in any drawing or in ST185.harnesslib, and no coveringIds anywhere
  D3  R35  every wire part number is M22759/16-<AWG>-<code> or a BC-* battery cable (no EW-1C*)
  D4  R44  no cavity signal that says "not used", "placeholder", "reserved" or "not wired yet"
  D5  R29 / R12 / R26  no drawing note that still describes a SolderSleeve or a drawn T-splice,
           a J/B2 landing (except as removed), the PMU, gbx_body, HDP2x bulkheads, powder-coat
           masking or a G4+ reference
  D6  R203  every splice has a plain name (its `label`): no unnamed splice in any drawing

HARD: D1 (pure-bay harnesses), D2 (zero since 2026-10-12), D3, D4, D5 (zero since 2026-10-14) and D6 (zero since 2026-10-19). SOFT
(printed, do not fail): the D1 EngineRoom-C list. A SOFT check moves to HARD the day it first
reports zero (check_all.py convention) - edit SOFT below.

Exit 1 on any HARD finding.
"""
import json
import os
import re
import sys

import model

SOFT = set()
BAY = {"ECU-engine", "HeavyDC", "WheelSpeed-Front", "WheelSpeed-Rear"}
SPLICE_INTO = re.compile(r"solder.?sleeve into|splice[sd]? into|tap(ped)? into", re.I)
WIRE_PN = re.compile(r"^(M22759/16-\d+-\d+|BC-)")
BAD_SIGNAL = re.compile(r"\bnot used\b|placeholder|\breserved\b|not wired yet", re.I)
BAD_NOTE = [("R29", re.compile(r"SolderSleeve|solder sleeve", re.I)),   # a T-splice NOTE is build method (R30), allowed
            ("R12", re.compile(r"J/B ?(No\.? ?)?2\b", re.I)),             # unless the note says it is removed
            ("R12", re.compile(r"\bPMU\b|gbx_body")),
            ("R10", re.compile(r"HDP2[46]")),
            ("R31", re.compile(r"\bmask the\b", re.I)),                  # "nothing to mask" is the correct text
            ("R26", re.compile(r"G4\+"))]
REMOVED = re.compile(r"removed|deleted|gone|retired|no longer", re.I)

reg = model.registry()
ds = model.docs(reg)
LIB = os.path.join(model.HERE, "rebuild", "ST185.harnesslib")
hard, soft = [], []


def add(code, msg):
    (soft if code in SOFT else hard).append("%s %s" % (code, msg))


# D1
for fl in reg.get("flyingLeads", []):
    h = fl["harness"]
    m = str((fl.get("ewd") or {}).get("method") or "")
    if h in BAY and SPLICE_INTO.search(m):
        add("D1", "%s/%s splices into a factory lead in the engine bay (R11): %r" % (h, fl["terminal"], m))
    elif h == "EngineRoom-C":
        soft.append("D1 list EngineRoom-C/%s method: %s" % (fl["terminal"], m[:90]))

# D2 - D5 per drawing, D2 also on the library
docs = dict(ds)
with open(LIB, encoding="utf-8") as f:
    docs["ST185.harnesslib"] = json.load(f)
for loom, d in docs.items():
    for k in d:
        if not k.endswith("Parts") or not isinstance(d[k], list):
            continue
        for p in d[k]:
            txt = "%s %s" % (p.get("partNumber", ""), p.get("description", ""))
            if "SLEEVE" in txt.upper():
                add("D2", "%s: %s %s %r is a sleeve (R29 / R44)" % (loom, k, p.get("id"), p.get("partNumber")))
            if k == "wireParts" and not WIRE_PN.match(p.get("partNumber") or ""):
                add("D3", "%s: wire part %s %r is not M22759/16-<AWG>-<code> or BC-* (R35)"
                    % (loom, p.get("id"), p.get("partNumber")))
    if loom == "ST185.harnesslib":
        continue
    for k in ("connectors", "terminals", "splices", "wires", "cables", "bundles"):
        for x in d.get(k, []):
            if x.get("coveringIds"):
                add("D2", "%s: %s %s carries coverings %s (R44)" % (loom, k, x.get("id"), x["coveringIds"]))
    for c in d.get("connectors", []):
        for cv in c.get("cavities", []):
            s = cv.get("signal") or ""
            if BAD_SIGNAL.search(s):
                add("D4", "%s: %s %s signal %r (R44: nothing 'not used' / reserved)" % (loom, c["id"], cv["id"], s[:70]))
    for sp in d.get("splices", []):
        if not (sp.get("label") or "").strip():
            add("D6", "%s: splice %s has no name (R203: every splice needs a name)" % (loom, sp.get("id")))
    for n in d.get("schematicNotes", []) + d.get("layoutNotes", []):
        t = n.get("text") or ""
        for rule, rx in BAD_NOTE:
            if rule == "R12" and "J/B" in rx.pattern and REMOVED.search(t):
                continue
            if rx.search(t):
                add("D5", "%s: note %s still says %r (%s)" % (loom, n.get("id"), rx.search(t).group(0), rule))

for line in hard:
    print(line)
if soft:
    print("SOFT (listed, not failing - fix the drawing, then move the code out of SOFT):")
    for line in soft:
        print("  " + line)
print("\n%d Dan-rule finding(s) (%d soft)." % (len(hard), len(soft)))
sys.exit(1 if hard else 0)
