"""Front and rear wheel speed are each one Y harness ending at one inline interface.

Checked per side against interfaces.json "wheelSpeed":

  W1  no VRC connector (cp_m8_*, vrc_*) is drawn on any harness - the VRC and its M8
      panel connectors belong to the enclosure build, not the harness
  W2  the side's harness holds exactly its two ABS sensor plugs and the interface source
      half as connectors, and draws no cross-reference
  W3  each sensor drop is one screened 2-core cable: c1 to the VRC IN "+" endpoint, c2 to
      "-"; its screen has one end only, on the IN "screen" endpoint (floats at the sensor),
      and that endpoint is part of the VRC enclosure
  W4  the output cable(s) run from the VRC OUT endpoint to the interface source half; each
      screen lands on its declared drain pin, starting at the enclosure or floating there
  W5  the interface is a Deutsch DT 6-way pair
  W6  the ECU spur: the receiving half is on the spur harness, and each of its pins has one
      conductor to the declared ECU pin or splice (on the spur harness or a harness the
      half is alsoDrawnOn - the front spur's FR core belongs to the B cabin loom)
  W7  once both sides are drawn, the old combined ST185-WheelSpeed drawing is gone

Exit 1 on any finding.
"""
import sys

import model

reg = model.registry()
ds = model.docs(reg)
spec = reg.get("wheelSpeed") or {}
bad = []

for loom, d in ds.items():
    for c in d.get("connectors", []):
        if (c.get("partId") or "").startswith("cp_m8") or c["id"].startswith("vrc_"):
            bad.append("W1 %s draws VRC connector %s - use VRC endpoints" % (loom, c["id"]))

eps = {e["id"]: e for e in reg.get("endpoints", [])}
encs = {e["id"]: e for e in reg.get("enclosures", [])}
ixs = {i["id"]: i for i in reg.get("interfaces", [])}


def end(e):
    return (e or {}).get("id"), (e or {}).get("handle")


for side, s in sorted(spec.items()):
    d = ds.get(s["harness"])
    if not d:
        bad.append("W2 %s: harness %s is not drawn" % (side, s["harness"]))
        continue
    ix = ixs.get(s["interface"])
    if not ix:
        bad.append("W5 %s: interface %s is not declared" % (side, s["interface"]))
        continue
    src = next(h for h in ix["halves"] if h["role"] == "source")
    rcv = next(h for h in ix["halves"] if h["role"] == "receiving")
    if src["harness"] != s["harness"] or rcv["harness"] != s["spurHarness"]:
        bad.append("W6 %s: interface halves are on %s / %s, want %s / %s"
                   % (side, src["harness"], rcv["harness"], s["harness"], s["spurHarness"]))
    conns = {c["id"]: c for c in d.get("connectors", [])}
    want = set(s["sensors"]) | {src["connector"]}
    if set(conns) != want:
        bad.append("W2 %s: connectors are %s, want %s" % (side, sorted(conns), sorted(want)))
    parts = model.parts(d)
    enc = encs.get(s["enclosure"]) or {"screen": []}
    cables = {cb["id"]: cb for cb in d.get("cables", [])}
    for sensor, ep_id in sorted(s["sensors"].items()):
        ep = eps.get(ep_id)
        if not ep:
            bad.append("W3 %s: endpoint %s is not declared" % (side, ep_id))
            continue
        t = ep["terminals"]
        hit = [cb for cb in cables.values()
               if {end(co.get("source")) for co in cb["cores"]} | {end(co.get("target")) for co in cb["cores"]}
               >= {(sensor, "c1"), (sensor, "c2")}]
        if len(hit) != 1:
            bad.append("W3 %s: %s should be one cable, found %d" % (side, sensor, len(hit)))
            continue
        cb = hit[0]
        cp = parts.get(cb.get("partId")) or {}
        pairs = {frozenset((end(co.get("source")), end(co.get("target")))) for co in cb["cores"]}
        if len(cb["cores"]) != 2 or not cp.get("shielded") or pairs != {
                frozenset(((sensor, "c1"), (t["+"], "Terminal"))),
                frozenset(((sensor, "c2"), (t["-"], "Terminal")))}:
            bad.append("W3 %s: %s is not a screened pair %s c1/c2 -> %s +/-" % (side, cb["id"], sensor, ep_id))
        sh = cb.get("shield") or {}
        ends = [end(sh.get(k)) for k in ("source", "target") if sh.get(k)]
        if ends != [(t["screen"], "Terminal")]:
            bad.append("W3 %s: %s screen must land on %s only (floats at the sensor), has %s"
                       % (side, cb["id"], t["screen"], ends))
        if t["screen"] not in enc["screen"]:
            bad.append("W3 %s: %s is not in enclosure %s" % (side, t["screen"], s["enclosure"]))
    out = (eps.get(s["output"]) or {}).get("terminals", {})
    out_ids = {v for k, v in out.items() if k != "screen"}
    for oc in s["outputCables"]:
        cb = cables.get(oc["cable"])
        if not cb:
            bad.append("W4 %s: output cable %s is not drawn" % (side, oc["cable"]))
            continue
        cp = parts.get(cb.get("partId")) or {}
        if len(cb["cores"]) != oc["cores"] or not cp.get("shielded"):
            bad.append("W4 %s: %s must be a screened %d-core" % (side, cb["id"], oc["cores"]))
        for co in cb["cores"]:
            a, b = end(co.get("source")), end(co.get("target"))
            if not ({a[0], b[0]} & out_ids and src["connector"] in (a[0], b[0])):
                bad.append("W4 %s: core %s does not run VRC OUT -> %s" % (side, co["id"], src["connector"]))
        sh = cb.get("shield") or {}
        got = {end(sh.get(k)) for k in ("source", "target") if sh.get(k)}
        want_sh = {(src["connector"], oc["drainPin"])}
        if oc.get("screenFromEnclosure"):
            want_sh.add((out["screen"], "Terminal"))
        if got != want_sh:
            bad.append("W4 %s: %s screen lands on %s, want %s" % (side, cb["id"], sorted(got), sorted(want_sh)))
    for h in (src, rcv):
        hd = ds.get(h["harness"]) or {}
        c = next((x for x in hd.get("connectors", []) if x["id"] == h["connector"]), None)
        pn = (model.parts(hd).get((c or {}).get("partId")) or {}).get("partNumber", "")
        if not pn.startswith(("DT04-6P", "DT06-6S")) or len((c or {}).get("cavities", [])) != 6:
            bad.append("W5 %s: %s/%s is %r, want a DT 6-way half" % (side, h["harness"], h["connector"], pn))
    spur_conds = [c for loom in [s["spurHarness"]] + rcv.get("alsoDrawnOn", [])
                  for c in model.conductors(ds.get(loom) or {})]
    brk = model.break_ends(reg)
    pair = {}
    for (loom, tid), bid in brk.items():
        pair.setdefault(bid, []).append((loom, tid))

    def follow(loom, far):
        """Across a broken-off pair: the far end of the other section."""
        if far[1] != "Terminal" or (loom, far[0]) not in brk:
            return far
        for oloom, tid in pair[brk[(loom, far[0])]]:
            if oloom == loom:
                continue
            for cond, cable, screen in model.conductors(ds.get(oloom) or {}):
                ends = [end(cond.get("source")), end(cond.get("target"))]
                if (tid, "Terminal") in ends:
                    ends.remove((tid, "Terminal"))
                    return ends[0]
        return far

    for pin, target in sorted(s["spur"].items()):
        hits = []
        for cond, cable, screen in spur_conds:
            ends = {end(cond.get("source")), end(cond.get("target"))}
            if (rcv["connector"], pin) in ends:
                far = ends - {(rcv["connector"], pin)}
                hits.append({follow(s["spurHarness"], x) for x in far})
        tid, _, th = target.partition(".")
        ok = [x for x in hits if x and next(iter(x))[0] in (tid, "dm_%s_Splice" % tid)
              and (not th or next(iter(x))[1] == th)]
        if len(hits) != 1 or not ok:
            bad.append("W6 %s: spur pin %s should have one conductor to %s, has %s"
                       % (side, pin, target, [sorted(x) for x in hits]))

if {"front", "rear"} <= set(spec) and "WheelSpeed" in ds:
    bad.append("W7 both sides are drawn but the combined ST185-WheelSpeed drawing is still listed")

print("wheel-speed sides specified: %s" % (", ".join(sorted(spec)) or "none"))
for line in bad:
    print(line)
print("\n%d wheel-speed finding(s)." % len(bad))
sys.exit(1 if bad else 0)
