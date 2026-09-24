#!/usr/bin/env python3
"""Put two circuits on the bulkhead their ECU pin says they belong to.

Daniel, 2026-09-23: "A sensor location must be based on link ECU docs and ECU
IO, because it must be compatible with the ECU pin being assigned to it ...
move knock to the harness that corresponds with the ECU knock pin."

Two circuits were on the wrong side of that rule:

  Knock 1 is ECU pin B9, so it is a loom-B circuit, but all three of its
  conductors crossed on bulkhead A - SIG+ on bh_a c27, SIG- on bh_a c6 and the
  screen on bh_a c35. The screen was the loudest symptom: it crossed bulkhead A
  and then terminated on SHIELD_B at the ECU, which is a screen taking the long
  way round its own loom. All three move to bh_b c16 / c17 / c18.

  Aux 7 MRS speed-out is ECU pin A27, so it is a loom-A circuit, but it crossed
  on bh_b c13. It moves to bh_a c36, and the EngineRoom-C cross-reference dummy
  is renamed to match.

Both bulkheads have room: bh_b c16-c21 were free on both halves, and bh_a
c36-c47 likewise. Cavity contacts and plugs are restamped afterwards by
fix_cavity_parts.py, which stamps the union of every drawing.
"""
import json, pathlib, sys

R = pathlib.Path(__file__).resolve().parent / "rebuild"

# (file, conductor id, old connector, old cavity, new connector, new cavity)
MOVES = [
    ("ST185-A-ECU",    "w205_c",        "bh_a_fw",  "c27", "bh_b_fw",  "c16"),
    ("ST185-A-ECU",    "w12_c",         "bh_a_fw",  "c6",  "bh_b_fw",  "c17"),
    ("ST185-A-ECU",    "w_shc_knock1",  "bh_a_fw",  "c35", "bh_b_fw",  "c18"),
    ("ST185-A-engine", "cab_knock1_c1", "bh_a_eng", "c27", "bh_b_eng", "c16"),
    ("ST185-A-engine", "cab_knock1_c2", "bh_a_eng", "c6",  "bh_b_eng", "c17"),
    ("ST185-A-engine", "cab_knock1_sh", "bh_a_eng", "c35", "bh_b_eng", "c18"),
    ("ST185-A-ECU",    "w_mrs_c",       "bh_b_fw",  "c13", "bh_a_fw",  "c36"),
]

# cavity signal text, applied to every drawing that draws that connector
NAMES = {
    ("bh_b_fw",  "c16"): "Knock 1 SIG+ (ECU B9)",
    ("bh_b_eng", "c16"): "Knock 1 SIG+ (ECU B9)",
    ("bh_b_fw",  "c17"): "Knock 1 SIG- (to Gnd Out B22)",
    ("bh_b_eng", "c17"): "Knock 1 SIG- (to Gnd Out B22)",
    ("bh_b_fw",  "c18"): "Knock 1 screen",
    ("bh_b_eng", "c18"): "Knock 1 screen",
    ("bh_a_fw",  "c36"): "Aux 7 MRS speed-out (ECU A27)",
    ("bh_a_eng", "c36"): "Aux 7 MRS speed-out (ECU A27)",
    ("bh_a_fw",  "c6"):  "spare",
    ("bh_a_eng", "c6"):  "spare",
    ("bh_a_fw",  "c27"): "spare",
    ("bh_a_eng", "c27"): "spare",
    ("bh_a_fw",  "c35"): "spare",
    ("bh_a_eng", "c35"): "spare",
    ("bh_b_fw",  "c13"): "spare",
    ("bh_b_eng", "c13"): "spare",
}

# the EngineRoom-C cross-reference dummy follows the MRS move
RENAME = {"dm_bh_b_eng_c13": "dm_bh_a_eng_c36"}


def conductors(d):
    for w in d.get("wires", []):
        yield w
    for cb in d.get("cables", []):
        for co in cb.get("cores", []):
            yield co
        if cb.get("shield"):
            yield cb["shield"]


def load(stem):
    p = R / (stem + ".harness")
    return p, json.loads(p.read_text(encoding="utf-8"))


changed = {}
problems = []

for stem, cid, oc, ocav, nc, ncav in MOVES:
    p, d = changed.get(stem, (None, None))
    if d is None:
        p, d = load(stem)
    hit = False
    for w in conductors(d):
        if w["id"] != cid:
            continue
        # Set the end explicitly by matching BOTH connector and cavity. Do not
        # assume which of source/target holds the bulkhead: fix_knock_ground.py
        # made that assumption once and shorted A7 to sensor ground.
        for end in ("source", "target"):
            e = w.get(end) or {}
            if e.get("id") == oc and e.get("handle") == ocav:
                w[end] = {"id": nc, "handle": ncav}
                hit = True
    if not hit:
        problems.append("%s: %s is not on %s.%s" % (stem, cid, oc, ocav))
    changed[stem] = (p, d)

if problems:
    print("\n".join(problems))
    sys.exit("nothing written")

# names and the dummy rename, across every drawing
for path in sorted(R.glob("*.harness")):
    stem = path.stem
    if stem in changed:
        p, d = changed[stem]
    else:
        p, d = path, json.loads(path.read_text(encoding="utf-8"))
    touched = stem in changed
    for c in d.get("connectors", []):
        if c["id"] in RENAME:
            c["id"] = RENAME[c["id"]]
            touched = True
        for cav in c.get("cavities", []):
            key = (c["id"], cav["id"])
            if key in NAMES and cav.get("signal") != NAMES[key]:
                cav["signal"] = NAMES[key]
                touched = True
    for w in conductors(d):
        for end in ("source", "target"):
            e = w.get(end) or {}
            if e.get("id") in RENAME:
                e["id"] = RENAME[e["id"]]
                touched = True
    if touched:
        p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n",
                     encoding="utf-8")
        print("wrote", p.name)
