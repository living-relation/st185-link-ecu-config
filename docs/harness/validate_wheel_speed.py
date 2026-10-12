"""Front and rear wheel speed are each one Y harness ending at one inline interface.

Checked per side against interfaces.json "wheelSpeed":

  W1  no VRC device or panel connector (vrc_*, cp_m8_panel_*) is drawn on any harness - the
      VRC and its panel connectors belong to the enclosure build. The harness-side M8
      cable plugs that mate them ARE drawn where interfaces.json declares an endpoint
      "connector" (front IN plugs, Daniel 2026-10-12); any other cp_m8_* connector fails
  W2  the side's harness holds exactly its two ABS sensor plugs, the interface source
      half and its declared VRC endpoint plugs as connectors, and draws no cross-reference
  W3  each sensor drop is one screened 2-core cable: c1 to the VRC IN "+" endpoint, c2 to
      "-"; its screen has one end only, on the IN "screen" endpoint (floats at the sensor),
      and that endpoint is part of the VRC enclosure. Where the endpoint is a drawn plug the
      screen may instead end at its SolderSleeve splice whose drain lead reaches the
      endpoint's screen pin, directly or through a drain T-splice and nothing else
      (Daniel 2026-10-12: one sensor drain crimped into IN pin 3, the other T-spliced onto
      it about 6 mm behind the plug). Its layout leg runs from the sensor plug either
      straight to the IN plug or to a branch point that carries only the sensor legs and one
      bundle to the IN plug (the legs meet only by the plug)
  W4  the output cable(s) run from the VRC OUT endpoint to the interface source half; each
      screen lands on its declared drain pin, starting at the enclosure or floating there
  W5  the interface is a Deutsch DT 6-way pair
  W6  the ECU spur: the receiving half is on the spur harness, and each of its pins has one
      conductor to the declared ECU pin or splice (on the spur harness or a harness the
      half is alsoDrawnOn - the front spur's FR core belongs to the B cabin loom)
  W7  once both sides are drawn, the old combined ST185-WheelSpeed drawing is gone
  W8  exactly two VRC M8 cable plugs per side, same part (Daniel 2026-10-12): one IN plug
      shared by both sensor endpoints (both legs land on it) and one OUT plug
  W9  the IN piece and the OUT piece are separate (Daniel 2026-10-12): no bundle, branch
      point, wire or cable joins the IN plug to the OUT plug in the drawing - the VRC box
      that links them is not drawn. Gates that need the electrical link (screens, R2) get
      it from interfaces.json "enclosures", never from a drawn connection

Exit 1 on any finding.
"""
import collections
import sys

import model

reg = model.registry()
ds = model.docs(reg)
spec = reg.get("wheelSpeed") or {}
bad = []
eps = {e["id"]: e for e in reg.get("endpoints", [])}
EP_PLUGS = {(e["harness"], e["connector"]) for e in eps.values() if e.get("connector")}

for loom, d in ds.items():
    for c in d.get("connectors", []):
        m8 = (c.get("partId") or "").startswith("cp_m8")
        if c["id"].startswith("vrc_") or (m8 and (loom, c["id"]) not in EP_PLUGS):
            bad.append("W1 %s draws VRC connector %s - use VRC endpoints or a declared endpoint plug"
                       % (loom, c["id"]))

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
    want = set(s["sensors"]) | {src["connector"]} | {
        eps[e]["connector"] for e in list(s["sensors"].values()) + [s["output"]]
        if e in eps and eps[e].get("connector")}
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
        t = model.endpoint_ends(ep)
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
                frozenset(((sensor, "c1"), t["+"])),
                frozenset(((sensor, "c2"), t["-"]))}:
            bad.append("W3 %s: %s is not a screened pair %s c1/c2 -> %s +/-" % (side, cb["id"], sensor, ep_id))
        sh = cb.get("shield") or {}
        ends = [end(sh.get(k)) for k in ("source", "target") if sh.get(k)]
        if ep.get("connector") and len(ends) == 1 and ends[0][1] == "Splice":
            # follow the drain leads through any T-splice (Daniel 2026-10-12) to the pin
            seen, todo, reach = {ends[0]}, [ends[0]], []
            while todo:
                n = todo.pop()
                for w in d.get("wires", []):
                    a, b = end(w.get("source")), end(w.get("target"))
                    if n not in (a, b):
                        continue
                    o = b if a == n else a
                    if o in seen:
                        continue
                    seen.add(o)
                    (todo if o[1] == "Splice" else reach).append(o)
            if reach == [t["screen"]]:
                ends = [t["screen"]]
        if ends != [t["screen"]]:
            bad.append("W3 %s: %s screen must land on %s only (floats at the sensor), has %s"
                       % (side, cb["id"], t["screen"], ends))
        sk = t["screen"][0] if t["screen"][1] == "Terminal" else "%s.%s" % t["screen"]
        if sk not in enc["screen"]:
            bad.append("W3 %s: %s is not in enclosure %s" % (side, sk, s["enclosure"]))
        if ep.get("connector"):
            legs = {b["sourceId"] if b["targetId"] == sensor else b["targetId"]
                    for b in d.get("bundles", []) if sensor in (b["sourceId"], b["targetId"])}
            if len(legs) == 1 and next(iter(legs)) in {x["id"] for x in d.get("branchPoints", [])}:
                bp = next(iter(legs))
                nb = [b["sourceId"] if b["targetId"] == bp else b["targetId"]
                      for b in d.get("bundles", []) if bp in (b["sourceId"], b["targetId"])]
                if nb.count(ep["connector"]) == 1 and set(nb) - {ep["connector"]} <= set(s["sensors"]):
                    legs = {ep["connector"]}
            if legs != {ep["connector"]}:
                bad.append("W3 %s: %s layout leg must run straight to %s, runs to %s"
                           % (side, sensor, ep["connector"], sorted(legs)))
    oep = eps.get(s["output"]) or {}
    out = model.endpoint_ends(oep) if oep else {}
    out_ids = {v[0] for k, v in out.items() if k != "screen"}
    in_plugs = {(eps.get(e) or {}).get("connector") for e in s["sensors"].values()}
    plugs = [x for x in in_plugs | {oep.get("connector")} if x]
    pparts = {(conns.get(x) or {}).get("partId") for x in plugs}
    if len(in_plugs) != 1 or None in in_plugs or not oep.get("connector") or len(plugs) != 2             or len(pparts) != 1:
        bad.append("W8 %s: want one shared IN plug and one OUT plug, same part; have IN %s, OUT %s, parts %s"
                   % (side, sorted(x or "-" for x in in_plugs), oep.get("connector"), sorted(x or "-" for x in pparts)))
    if len(in_plugs) == 1 and oep.get("connector"):
        link = collections.defaultdict(set)
        for b in d.get("bundles", []):
            link[b["sourceId"]].add(b["targetId"]); link[b["targetId"]].add(b["sourceId"])
        for cond, cable, screen in model.conductors(d):
            a_, b_ = end(cond.get("source"))[0], end(cond.get("target"))[0]
            if a_ and b_:
                link[a_].add(b_); link[b_].add(a_)
        for cb in d.get("cables", []):
            ids = [end(x.get(k))[0] for x in cb["cores"] + ([cb["shield"]] if cb.get("shield") else [])
                   for k in ("source", "target") if x.get(k)]
            for i_ in ids[1:]:
                link[ids[0]].add(i_); link[i_].add(ids[0])
        seen, todo = {next(iter(in_plugs))}, [next(iter(in_plugs))]
        while todo:
            for m_ in link[todo.pop()] - seen:
                seen.add(m_); todo.append(m_)
        if oep["connector"] in seen:
            bad.append("W9 %s: the IN plug %s and the OUT plug %s are joined in the drawing - keep the IN and "
                       "OUT pieces separate" % (side, next(iter(in_plugs)), oep["connector"]))
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
            want_sh.add(out["screen"])
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
