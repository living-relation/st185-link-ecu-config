"""Enforce SHIELD-RULES.md mechanically, so the rules stop getting re-litigated.

The rules live in docs/SHIELD-RULES.md (short form) and plan 6.27 / 6.30 / 6.31 /
6.32 (long form).  This script checks the ones a script can check:

  R1  a screen never lands at the device end: every screen end is an ECU shield
      pin, a splice, a bulkhead or inline-interface cavity, a device-enclosure
      screen lead (the VRC exception), or a legacy cross-reference - never a
      sensor or device cavity
  R3  no screen lands on a connector shell (no connector on this car has one;
      the VRC case is reached through registered enclosure leads instead)
  R5  a screen crossing a bulkhead uses its own pin, wired on BOTH halves
  R2  every screen reaches an ECU shield-ground pin
  R6  a cable screen landed at BOTH ends is allowed only where interfaces.json
      lists it in shieldBothEndsOk (sensor-line continuations: crank, cam, knock)

R1 and R6 together are the single-device shield check: a passive sensor screen
floats at the device, and a both-ended screen that is not a listed sensor
continuation fails. Daniel, 2026-10-01: VRC screens and CSB3 enclosure screens
are excluded from that check. Those circuits include inline active parts; their
screens terminate at the enclosure and at the ECU. cab_fout_fr_sh and its
continuations are excluded with the other VRC screens. They are not added to
the VRC_FRONT enclosure list (that would join A7 to B17). Crank, cam and knock
stay on R1/R6.

R4 ("cable only until it terminates at the ECU") is a modelling convention the
schema cannot express, so it is not checked here. The A7 / B17 separation is
audit_mating.py M4.

Exit 1 on any violation.  Added 2026-09-22 after the crank / cam / knock screens
were found dead-ending in bulkhead A because only the engine half was wired.
2026-09-27: traces on model.Graph, so inline interfaces and VRC enclosures come
from interfaces.json rather than hardcoded VRC connector ids.
2026-10-01: VRC and CSB3 screens excluded from the single-device check.
"""
import collections
import sys

import model

reg = model.registry()
g = model.Graph(reg)
BOTH_ENDS_OK = {s["id"] for s in reg.get("shieldBothEndsOk", [])}
ECU_SHIELD = {("ECU",) + k for k in model.SHIELD_PINS}
WS_OUTPUT_CABLES = {
    oc["cable"]
    for side in (reg.get("wheelSpeed") or {}).values()
    for oc in side.get("outputCables") or []
}
ENC_SCREEN_TERMS = set()
for enc in reg.get("enclosures") or []:
    hid = enc.get("id") or ""
    if hid.startswith("VRC") or "CSB" in hid:
        ENC_SCREEN_TERMS.update(enc.get("screen") or [])


def active_inline_screen(loom, wid, cable, ends):
    """VRC or CSB3 enclosure screen: excluded from the single-device check.

    Daniel, 2026-10-01. Includes cab_fout_fr_sh and its cabin continuations.
    Does not treat crank / cam / knock as active-inline.
    """
    if loom == "CSB3" or loom in ("WheelSpeed-Front", "WheelSpeed-Rear"):
        return True
    if cable in WS_OUTPUT_CABLES:
        return True
    if (cable or wid).startswith(("cab_fspur", "cab_rspur", "cab_fout", "cab_rout")):
        return True
    return any((e or {}).get("id") in ENC_SCREEN_TERMS for e in ends)


bad = []
used_cav = collections.defaultdict(set)
for loom, d in g.docs.items():
    for cond, cable, screen in model.conductors(d):
        for e in (cond.get("source"), cond.get("target")):
            if e and e.get("id") in model.BULKHEAD_MATE:
                used_cav[e["id"]].add(e.get("handle"))

for loom, d in g.docs.items():
    for w, cable, screen in model.conductors(d):
        if not screen:
            continue
        ends = [e for e in (w.get("source"), w.get("target")) if e]
        nodes = [g.node(loom, e) for e in ends]
        skip_single = active_inline_screen(loom, w["id"], cable, ends)
        for e, n in zip(ends, nodes):
            if e.get("handle") == "shell":
                bad.append("R3 %s/%s lands on the shell of %s" % (loom, w["id"], e["id"]))
            elif (not skip_single) and n[0] == "C" and not e["id"].startswith("dm_"):
                bad.append("R1 %s/%s lands on %s %s - a screen floats at the device"
                           % (loom, w["id"], e["id"], e.get("handle")))
            other = model.BULKHEAD_MATE.get(e["id"])
            if other and e.get("handle") not in used_cav[other]:
                bad.append("R5 %s/%s uses %s %s but %s %s is not wired"
                           % (loom, w["id"], e["id"], e["handle"], other, e["handle"]))
        if (not skip_single) and cable and len(ends) == 2 and w["id"] not in BOTH_ENDS_OK:
            bad.append("R6 %s/%s is bonded at both ends - not a listed screen continuation"
                       % (loom, w["id"]))
        if nodes and not any(ECU_SHIELD & g.reach(n) for n in nodes):
            bad.append("R2 screen %s/%s never reaches an ECU shield ground" % (loom, w["id"]))

for sid in sorted(BOTH_ENDS_OK):
    if not any(sid == w["id"] for d in g.docs.values() for w, c, s in model.conductors(d) if s):
        bad.append("R6 shieldBothEndsOk lists %s, which is not a screen on any drawing" % sid)

for line in bad:
    print(line)
print()
print("%d shield-rule violations." % len(bad))
sys.exit(1 if bad else 0)
