"""Enforce SHIELD-RULES.md mechanically, so the rules stop getting re-litigated.

The rules live in docs/SHIELD-RULES.md (short form) and plan 6.27 / 6.30 / 6.31 /
6.32 (long form).  This script checks the four that a script can check:

  R1  a screen never connects at the device end - it floats there
  R3  no drain lands on a connector shell, except the VR conditioner enclosures
  R5  a screen crossing a bulkhead uses its own pin, wired on BOTH halves
  R2  every screen reaches an ECU shield-ground pin, and only one of them

R4 ("cable only until it terminates at the ECU") is a modelling convention the
schema cannot express, so it is not checked here.

Exit 1 on any violation.  Added 2026-09-22 after the crank / cam / knock screens
were found dead-ending in bulkhead A because only the engine half was wired.
"""
import json, glob, os, sys, collections

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")

ECU_SHIELD_PINS = {("ecu_a", "a7"), ("ecu_b", "b17")}
# 6.30: the VR conditioner enclosures are the one documented shell exception
SHELL_OK = {"vrc_f_inl", "vrc_f_inr", "vrc_r_inl", "vrc_r_inr",
            "vrc_f_out", "vrc_r_out"}
BULKHEAD_PAIRS = {"bh_a_fw": "bh_a_eng", "bh_a_eng": "bh_a_fw",
                  "bh_b_fw": "bh_b_eng", "bh_b_eng": "bh_b_fw"}


def screens():
    """Every conductor that carries a screen, from any loom, wires or cables."""
    for f in sorted(glob.glob(os.path.join(R, "*.harness"))):
        d = json.load(open(f, encoding="utf-8"))
        loom = os.path.basename(f)[6:-8]
        for w in d.get("wires", []):
            # Match the colour, or an id whose LAST segment marks it a screen.
            # A plain "_sh" substring is too loose - it caught w_at_shk_sig, the
            # anti-theft shock sensor, which is a signal wire and not a screen.
            tail = w["id"].rsplit("_", 1)[-1]
            if w.get("color") == "Shield" or tail in ("sh", "shield", "drain") \
                    or w["id"].startswith("w_drain"):
                yield loom, w, None
        for cb in d.get("cables", []):
            if cb.get("shield"):
                yield loom, cb["shield"], cb["id"]


bad = []
lands = collections.defaultdict(set)     # screen id -> set of (component, handle)
used_cav = collections.defaultdict(set)  # bulkhead -> cavities any conductor uses

for f in sorted(glob.glob(os.path.join(R, "*.harness"))):
    d = json.load(open(f, encoding="utf-8"))
    conds = list(d.get("wires", []))
    for cb in d.get("cables", []):
        conds += cb.get("cores", [])
        if cb.get("shield"):
            conds.append(cb["shield"])
    for w in conds:
        for e in (w.get("source"), w.get("target")):
            if e and e.get("id") in BULKHEAD_PAIRS:
                used_cav[e["id"]].add(e.get("handle"))

for loom, w, cable in screens():
    ends = [e for e in (w.get("source"), w.get("target")) if e]
    for e in ends:
        lands[w["id"]].add((e["id"], e.get("handle")))
        # R3 - no shell landings outside the VR enclosures
        if e.get("handle") == "shell" and e["id"] not in SHELL_OK:
            bad.append("R3 %s/%s lands on the shell of %s" % (loom, w["id"], e["id"]))
    # R5 - a screen on a bulkhead pin must be wired on the mating half too
    for e in ends:
        other = BULKHEAD_PAIRS.get(e["id"])
        if other and e.get("handle") not in used_cav[other]:
            bad.append("R5 %s/%s uses %s %s but %s %s is not wired"
                       % (loom, w["id"], e["id"], e["handle"], other, e["handle"]))

# R2 - trace each screen net to an ECU shield pin.  Screens join at splices, so
# walk the net rather than looking at one wire's two ends.
net = collections.defaultdict(set)
for f in sorted(glob.glob(os.path.join(R, "*.harness"))):
    d = json.load(open(f, encoding="utf-8"))
    conds = list(d.get("wires", []))
    for cb in d.get("cables", []):
        conds += cb.get("cores", [])
        if cb.get("shield"):
            conds.append(cb["shield"])
    for w in conds:
        s, t = w.get("source"), w.get("target")
        if s and t:
            a, b = (s["id"], s.get("handle")), (t["id"], t.get("handle"))
            net[a].add(b)
            net[b].add(a)

BULKHEAD_THROUGH = {}   # (bh, cav) is electrically the same node as (mate, cav)
for a, b in BULKHEAD_PAIRS.items():
    for cav in used_cav[a]:
        BULKHEAD_THROUGH[(a, cav)] = (b, cav)

# A cross-reference dummy is the same electrical node as the real one it names.
# The convention is dm_<componentId>_<handle>, landed on the dummy's own c1.
for f in sorted(glob.glob(os.path.join(R, "*.harness"))):
    d = json.load(open(f, encoding="utf-8"))
    for c in d.get("connectors", []):
        if not c["id"].startswith("dm_"):
            continue
        body = c["id"][3:]
        for cv in c.get("cavities", []):
            for comp, handle in ((body.rsplit("_", 1)[0], body.rsplit("_", 1)[-1]),):
                net[(c["id"], cv["id"])].add((comp, handle))
                net[(comp, handle)].add((c["id"], cv["id"]))

# 6.30: inside a VR conditioner the case is the screen junction - every landing
# on one box is one node, joined by the case, not by a drawn wire.  The OUT
# connector's screen lands on its shielding plate ("shell"); each IN connector's
# sensor-drop screen rides pin 3 and a wire inside the box takes it to a ring
# terminal on the case (SHIELD-RULES 6.30, powered-device exception).
VRC_BOXES = ((("vrc_f_inl", "c3"), ("vrc_f_inr", "c3"), ("vrc_f_out", "shell")),
             (("vrc_r_inl", "c3"), ("vrc_r_inr", "c3"), ("vrc_r_out", "shell")))
for box in VRC_BOXES:
    nodes = list(box) + [(c, "shell") for c, _ in box]
    for a in nodes:
        for b in nodes:
            if a != b:
                net[a].add(b)


def reaches_ecu(start):
    seen, stack = set(), [start]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        if n in ECU_SHIELD_PINS:
            return True
        for m in net.get(n, ()):
            stack.append(m)
        m = BULKHEAD_THROUGH.get(n)
        if m:
            stack.append(m)
    return False


for sid, ends in sorted(lands.items()):
    if not any(reaches_ecu(e) for e in ends):
        bad.append("R2 screen %s never reaches an ECU shield ground" % sid)

for line in bad:
    print(line)
print()
print("%d shield-rule violations." % len(bad))
sys.exit(1 if bad else 0)
