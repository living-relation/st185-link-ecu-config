"""Enforce SHIELD-RULES.md mechanically, so the rules stop getting re-litigated.

The rules live in docs/SHIELD-RULES.md (short form) and plan 6.27 / 6.30 / 6.31 /
6.32 (long form).  This script checks the ones a script can check:

  R1  a screen never lands at the device end: every screen end is an ECU shield
      pin, a splice, a bulkhead or inline-interface cavity, a device-enclosure
      screen lead (the VRC exception), or a legacy cross-reference - never a
      sensor or device cavity
  R3  no screen lands on a connector shell (no connector on this car has one;
      the VRC case is reached through registered enclosure leads instead)
  R5  a screen that lands on a bulkhead half continues on the matching pin of
      the other half (that pin carries a screen, not only a core)
  R7  only a signal that already passes through both bulkhead halves must carry
      its shield through both halves on matching pins. A sensor through-screen
      must not stop on either half: it reaches A7 or B17. A CAN-connector
      through-screen (the Link lambda pair) must not stop on either half
      either, but it joins the other CAN-node screens and waits on the
      undrawn four-wire ECU CAN-connector ground - not A7 or B17. A cabin-
      only screen, or a screened cable whose signal does not cross the
      bulkhead, is not required to land on the bulkhead.
  R2  every screen that is not a CAN-connector screen and that has an end
      reaches an ECU shield-ground pin
  R6  withdrawn as an exclusive allowlist. Both-ended cabin continuations of
      through-bulkhead screens are the normal pass-through case, not a special
      permit. interfaces.json shieldBothEndsOk now names those continuations
      for documentation; it does not grant an exception.

R1 is the remaining single-device check for passive sensor screens. Daniel,
2026-10-01: VRC screens and CSB3 enclosure screens are excluded from that
check. Those circuits include inline active parts; their screens terminate at
the enclosure and at the ECU. cab_fout_fr_sh and its continuations are
excluded with the other VRC screens. They are not added to the VRC_FRONT
enclosure list (that would join A7 to B17). Crank, cam and knock stay on R1
and still end on sp_shield_a / sp_shield_b.

CAN-connector screens are the cab_can_* runs (cluster, RealDash, CSB3,
trunk) and the Link lambda 4-core (cab_lam_can_*). They splice only to
each other and wait on the undrawn four-wire ECU CAN-connector ground.
They are not required to reach A7, B17, or ecu_com, and the build fails
if one of them does. ecu_com is the comms / tuning port, not that
connector. Every node uses the existing 4-core 55PC1243-20-2/6/4/5-9
(cab_sh_4c). The lambda power / ground / CAN H/L signal already crosses
bulkhead B, so its shield must pass through both halves on a matching pin
if one is drawn, then join the other CAN-node screens. No matching shield
pin is drawn; the audit reports that as BLOCKED and does not invent a
cavity or land the drain on A7 / B17.

R4 ("cable only until it terminates at the ECU") is a modelling convention the
schema cannot express, so it is not checked here. The A7 / B17 separation is
audit_mating.py M4.

Exit 1 on any violation. BLOCKED lines are misses the drawing cannot finish
without inventing a pin; they are reported and do not fail the build.
2026-09-22: added after crank / cam / knock screens dead-ended in bulkhead A.
2026-09-27: traces on model.Graph.
2026-10-01: VRC / CSB3 enclosure exception; CAN-connector screens (drops +
lambda firewall) off A7 / B17 / ecu_com; R7 narrowed to through-bulkhead
signals only; exclusive R6 withdrawn.
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

CAN_FORBIDDEN = set(ECU_SHIELD)
CAN_FORBIDDEN.add(("SP", "sp_shield_a"))
CAN_FORBIDDEN.add(("SP", "sp_shield_b"))
for cav in ("c1", "c2", "c3", "c4", "c5", "c6"):
    CAN_FORBIDDEN.add(("ECU", "ecu_com", cav))


def can_connector_screen(wid, cable):
    """Screen that waits on the undrawn four-wire ECU CAN-connector ground.

    Cluster, RealDash, CSB3 and trunk (cab_can_*) and the Link lambda
    4-core (cab_lam_can_*). Not crank / cam / knock, and not a VRC
    or CSB3 enclosure screen.
    """
    name = cable or wid or ""
    return name.startswith(("cab_can_", "cab_lam_can"))


def active_inline_screen(loom, wid, cable, ends):
    """VRC or CSB3 enclosure screen: excluded from the single-device check.

    Daniel, 2026-10-01. Includes cab_fout_fr_sh and its cabin continuations.
    Does not treat crank / cam / knock as active-inline.
    Does not treat a CSB3 CAN drop screen as an enclosure screen.
    """
    if loom in ("WheelSpeed-Front", "WheelSpeed-Rear"):
        return True
    if cable in WS_OUTPUT_CABLES:
        return True
    if (cable or wid).startswith(("cab_fspur", "cab_rspur", "cab_fout", "cab_rout")):
        return True
    return any((e or {}).get("id") in ENC_SCREEN_TERMS for e in ends)


def can_forbidden_hits(nodes):
    hits = set()
    for n in nodes:
        hits |= CAN_FORBIDDEN & g.reach(n)
    return hits


def ends_of(cond):
    return [e for e in (cond.get("source"), cond.get("target")) if e]


bad = []
blocked = []
used_cav = collections.defaultdict(set)
core_cav = collections.defaultdict(set)
screen_cav = collections.defaultdict(set)
for loom, d in g.docs.items():
    for cond, cable, screen in model.conductors(d):
        for e in ends_of(cond):
            if e.get("id") in model.BULKHEAD_MATE:
                used_cav[e["id"]].add(e.get("handle"))
                key = (e["id"], e.get("handle"))
                if screen:
                    screen_cav[key].add((loom, cond["id"], cable))
                else:
                    core_cav[key].add((loom, cond["id"], cable))

for loom, d in g.docs.items():
    for w, cable, screen in model.conductors(d):
        if not screen:
            continue
        ends = ends_of(w)
        nodes = [g.node(loom, e) for e in ends]
        skip_single = active_inline_screen(loom, w["id"], cable, ends)
        can_conn = can_connector_screen(w["id"], cable)
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
            elif other and (other, e.get("handle")) not in screen_cav:
                bad.append("R5 %s/%s uses %s %s but %s %s is not a screen"
                           % (loom, w["id"], e["id"], e["handle"], other, e["handle"]))
            if other and (not can_conn) and nodes and not any(ECU_SHIELD & g.reach(x) for x in nodes):
                bad.append("R7 %s/%s stops on the bulkhead - does not reach A7 or B17"
                           % (loom, w["id"]))
        if can_conn:
            hits = can_forbidden_hits(nodes)
            if hits:
                bad.append("CAN screen %s/%s reaches %s - CAN-connector screens "
                           "stay off A7, B17, ecu_com and the ECU shield splices"
                           % (loom, w["id"], ", ".join(sorted(model.fmt(h) for h in hits))))
        elif nodes and not any(ECU_SHIELD & g.reach(n) for n in nodes):
            bad.append("R2 screen %s/%s never reaches an ECU shield ground" % (loom, w["id"]))

# R7: a screened cable whose signal already crosses both bulkhead halves must
# carry its shield through both halves on matching pins.
for loom, d in g.docs.items():
    for cb in d.get("cables") or []:
        sh = cb.get("shield")
        if not sh:
            continue
        through = []
        for co in cb.get("cores") or []:
            for e in ends_of(co):
                bh, h = e.get("id"), e.get("handle")
                if bh not in model.BULKHEAD_MATE:
                    continue
                other = model.BULKHEAD_MATE[bh]
                if (other, h) in core_cav:
                    through.append((bh, h, other))
        if not through:
            continue
        sh_bh = [(e["id"], e.get("handle")) for e in ends_of(sh)
                 if e.get("id") in model.BULKHEAD_MATE]
        cavs = ", ".join(sorted("%s %s" % (bh, h) for bh, h, _ in through))
        can_conn = can_connector_screen(sh.get("id"), cb["id"])
        if not sh_bh:
            if can_conn:
                blocked.append("BLOCKED %s/%s signal crosses %s; no matching "
                               "shield pin is drawn. CAN-connector screen: "
                               "not inventing a cavity, and not landing on "
                               "A7 or B17. It waits with the other CAN-node "
                               "screens on the undrawn four-wire CAN "
                               "connector ground"
                               % (loom, sh.get("id"), cavs))
            else:
                blocked.append("BLOCKED %s/%s signal crosses %s; no matching "
                               "shield pin is drawn. Not inventing a cavity "
                               "or picking A7 or B17"
                               % (loom, sh.get("id"), cavs))
            continue
        for bh, h in sh_bh:
            other = model.BULKHEAD_MATE[bh]
            if (other, h) not in screen_cav:
                bad.append("R7 %s/%s lands on %s %s but %s %s is not a screen"
                           % (loom, sh.get("id"), bh, h, other, h))
        nodes = [g.node(loom, e) for e in ends_of(sh)]
        if can_conn:
            hits = can_forbidden_hits(nodes)
            if hits:
                bad.append("CAN screen %s/%s reaches %s - CAN-connector "
                           "screens stay off A7, B17, ecu_com and the ECU "
                           "shield splices"
                           % (loom, sh.get("id"),
                              ", ".join(sorted(model.fmt(h) for h in hits))))
        elif nodes and not any(ECU_SHIELD & g.reach(n) for n in nodes):
            bad.append("R7 %s/%s crosses the bulkhead but never reaches A7 or B17"
                       % (loom, sh.get("id")))

for sid in sorted(BOTH_ENDS_OK):
    if not any(sid == w["id"] for d in g.docs.values() for w, c, s in model.conductors(d) if s):
        bad.append("shieldBothEndsOk lists %s, which is not a screen on any drawing" % sid)

for line in blocked:
    print(line)
for line in bad:
    print(line)
print()
print("%d shield-rule violations. %d blocked (no pin drawn)." % (len(bad), len(blocked)))
sys.exit(1 if bad else 0)
