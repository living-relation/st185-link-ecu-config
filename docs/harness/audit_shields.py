"""Enforce SHIELD-RULES.md mechanically, so the rules stop getting re-litigated.

The rules are R27-R34 in docs/harness/redesign/DECISIONS.md "Binding rules from Daniel";
docs/SHIELD-RULES.md holds the inventory.  This script checks the ones a script can check:

  R1  a screen never lands at the device end: every screen end is an ECU shield
      pin, a splice, a bulkhead or inline-interface cavity, a device-enclosure
      screen lead (VRC enclosure leads), or a legacy cross-reference - never a
      sensor or device cavity
  R3  no screen lands on a connector shell - never rely on a shell, every drain lands on a
      regular pin (Daniel 2026-10-12, project-wide; the VRC M8 plugs included)
  R5  a screen crossing a bulkhead uses its own pin, wired on BOTH halves
  R2  every screen reaches an ECU shield-ground pin
  S1  ECU comms pin C1 (the CAN screen drain, R207) carries exactly ONE wire: the trunk drain, a plain
      drain wire, never a cable screen core
  S2  the CAN screen net ("Screen CAN") carries CAN-circuit screens and drains only, and every CAN-circuit
      screen is on that net: nothing else shares the CAN screen, and no CAN screen lands on A7 / B17
  S3  loom screens never cross: nothing on Screen A is in a loom B file or lands on a B bulkhead / ECU-B
      pin, nothing on Screen B in a loom A file or on an A pin (R207: no A-B shield bridge)
  S4  every splice on the CAN screen net is a named branch splice, "SP-CAN-SH-<node>" (R207: each node's
      drain splices onto the trunk drain at its own branch)
  S5  a cabin-side external component (pedal, wheel-speed spur / VRC output) joins the loom shield trunk
      at its own named splice sitting where its signal wires join the main loom (the first branch point
      on the way to the ECU), not at the ECU plug (R207). Devices that come through a bulkhead are exempt:
      each drain keeps its own bulkhead pin and runs straight to the splice at the ECU plug (so there is
      no shield splice in the engine bay, and no bulkhead pin shared); the CAN nodes are S4
  R6  a cable screen landed at BOTH ends is allowed only where interfaces.json
      lists it in shieldBothEndsOk (drain connected on both the VRC input and
      the VRC output, and screen continuations through an inline interface)

R4 ("a shield exists only on a cable") is a modelling convention the
schema cannot express, so it is not checked here.

Exit 1 on any violation.  Added 2026-09-22 after the crank / cam / knock screens
were found dead-ending in bulkhead A because only the engine half was wired.
2026-09-27: traces on model.Graph, so inline interfaces and VRC enclosures come
from interfaces.json rather than hardcoded VRC connector ids.
"""
import collections
import os
import sys

import model

reg = model.registry()
g = model.Graph(reg)
BOTH_ENDS_OK = {s["id"] for s in reg.get("shieldBothEndsOk", [])}
ECU_SHIELD = {("ECU",) + k for k in model.SHIELD_PINS}

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
        for e, n in zip(ends, nodes):
            if e.get("handle") == "shell":
                bad.append("R3 %s/%s lands on the shell of %s" % (loom, w["id"], e["id"]))
            elif n[0] == "C" and not e["id"].startswith("dm_"):
                bad.append("R1 %s/%s lands on %s %s - a screen floats at the device"
                           % (loom, w["id"], e["id"], e.get("handle")))
            other = model.BULKHEAD_MATE.get(e["id"])
            if other and e.get("handle") not in used_cav[other]:
                bad.append("R5 %s/%s uses %s %s but %s %s is not wired"
                           % (loom, w["id"], e["id"], e["handle"], other, e["handle"]))
        if cable and len(ends) == 2 and w["id"] not in BOTH_ENDS_OK:
            bad.append("R6 %s/%s is bonded at both ends - not a listed screen continuation"
                       % (loom, w["id"]))
        if nodes and not any(ECU_SHIELD & g.reach(n) for n in nodes):
            bad.append("R2 screen %s/%s never reaches an ECU shield ground" % (loom, w["id"]))

for sid in sorted(BOTH_ENDS_OK):
    if not any(sid == w["id"] for d in g.docs.values() for w, c, s in model.conductors(d) if s):
        bad.append("R6 shieldBothEndsOk lists %s, which is not a screen on any drawing" % sid)

# ---- S1-S4 (R207): read from the master wire lists, which are the wiring SoT (R206)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cleanroom"))
import wirelist as WL  # noqa: E402

LOOM = {"A-cabin": "A", "A-engine": "A", "B-cabin": "B", "B-engine": "B"}
rows = [dict(r, _file=h) for h in LOOM.keys() | {"CAN", "CSB3", "WheelSpeed-Front", "WheelSpeed-Rear"}
        for r in WL.read_rows(h) if r["wire_id"]]
c1 = [r for r in rows if any(r[s + "_type"] == "connector" and r[s + "_conn"] == "ecu_com" and r[s + "_pin"] == "C1"
                             for s in ("from", "to"))]
if len(c1) != 1:
    bad.append("S1 ECU-COMMS C1 carries %d wires (must be exactly one, the trunk drain): %s" % (len(c1), ", ".join(r["wire_id"] for r in c1)))
elif c1[0]["colour"] == "Shield" or c1[0]["cable"]:
    bad.append("S1 the wire on C1 (%s) must be a plain drain wire, not a cable screen core" % c1[0]["wire_id"])
CAN_NET = "Screen CAN"
for r in rows:
    on_can = r["net_name"].startswith(CAN_NET)
    if on_can and r["circuit_id"] != "CAN":
        bad.append("S2 %s/%s is on the CAN screen net but is circuit %s" % (r["_file"], r["wire_id"], r["circuit_id"]))
    if r["circuit_id"] == "CAN" and r["colour"] == "Shield" and not on_can:
        bad.append("S2 %s/%s is a CAN screen but sits on %s" % (r["_file"], r["wire_id"], r["net_name"]))
    for tag, own in (("Screen A", "A"), ("Screen B", "B")):
        if not r["net_name"].startswith(tag):
            continue
        other = "B" if own == "A" else "A"
        pins = [r[s + "_conn"] for s in ("from", "to") if r[s + "_type"] == "connector"]
        own_pin = any(c.startswith(("ecu_" + own.lower(), "bh_" + own.lower())) for c in pins)   # a cable drawn on the other loom's file but wired to this loom's pins (the ETB motor) is this loom's
        if (LOOM.get(r["_file"]) == other and not own_pin) or any(c.startswith(("ecu_" + other.lower(), "bh_" + other.lower())) for c in pins)                 or any(LOOM.get(f) == other for f in r["passes_through"].split(" / ")):
            bad.append("S3 %s/%s is on %s but belongs to loom %s: the loom screens never cross" % (r["_file"], r["wire_id"], tag, other))
for h in ("CAN",):
    for r in WL.read_rows("CAN") + WL.read_rows("B-cabin"):
        for s_ in ("from", "to"):
            if r["wire_id"] and r["net_name"].startswith(CAN_NET) and r[s_ + "_type"] == "splice"                     and not r[s_ + "_conn"].startswith("sp_can_sh_"):
                bad.append("S4 %s lands on splice %s: a CAN screen splice is named sp_can_sh_<node> (SP-CAN-SH-<NODE>)" % (r["wire_id"], r[s_ + "_conn"]))

import heapq  # noqa: E402


def _junction(d, dev, ecu):
    """The first node with 3+ bundles on the shortest bundle path from device node `dev` to `ecu`."""
    adj = collections.defaultdict(list)
    for b in d.get("bundles", []):
        n = (b.get("length") or {}).get("value") or 0
        adj[b["sourceId"]].append((b["targetId"], n))
        adj[b["targetId"]].append((b["sourceId"], n))
    dist, prev, pq = {dev: 0}, {}, [(0, dev)]
    while pq:
        dd, u = heapq.heappop(pq)
        if dd > dist.get(u, 1e18):
            continue
        for v, n in adj[u]:
            if dd + n < dist.get(v, 1e18):
                dist[v], prev[v] = dd + n, u
                heapq.heappush(pq, (dd + n, v))
    if ecu not in dist:
        return None
    path = [ecu]
    while path[-1] != dev:
        path.append(prev[path[-1]])
    return next((n for n in path[::-1][1:] if len(adj[n]) >= 3), None)


for loom, ecu in (("A-cabin", "ecu_a"), ("B-cabin", "ecu_b")):
    d = g.docs[loom]
    loc = {x["id"]: x.get("locationId") or x["id"] for x in d.get("splices", [])}
    mine = [r for r in rows if r["_file"] == loom]
    for r in mine:
        if not r["net_name"].startswith(("Screen A", "Screen B")):
            continue
        sig = [x for x in mine if x["circuit_id"] == r["circuit_id"] and not x["net_name"].startswith("Screen")]
        ends = {x[s_ + "_conn"] for x in sig for s_ in ("from", "to") if x[s_ + "_type"] == "connector"}
        if not sig or any(c.startswith("bh_") for c in ends):
            continue      # no signal wires here, or a bulkhead device: own pin, straight to the ECU splice
        dev = [c for c in ends if not c.startswith("ecu_")]
        for s_ in ("from", "to"):
            sid = r[s_ + "_conn"]
            if r[s_ + "_type"] != "splice" or sid not in loc or len(dev) != 1:
                continue
            j = _junction(d, dev[0], ecu)
            if j and loc[sid] != j:
                bad.append("S5 %s/%s drain joins at %s (%s) but %s's signal wires join the main loom at %s"
                           % (loom, r["wire_id"], sid, loc[sid], dev[0], j))

for line in bad:
    print(line)
print()
print("%d shield-rule violations." % len(bad))
sys.exit(1 if bad else 0)
