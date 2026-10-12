"""Drawing rules for every harness file (Daniel, 2026-10-12, binding).
Format facts from https://docs.harness.design/feature/local-files/json-format and
https://docs.harness.design/feature/signals: a cavity "signal" fills every EMPTY cavity on its net
unless the cavity sets "propagate": false; a net with more than one signal shows all of them on its
empty cavities; both canvases use a 30-unit grid and positions are the top-left corner of a node.

A net here is the conductors (wires, cable cores, cable screens) joined at cavities, terminals and
splices - a connector never joins its own cavities.

  S1  at most one propagating signal per net (no signal conflict)
  S2  a terminal's signal never propagates ("propagate": false): terminal signals are descriptions
      (broken-off ends, flying leads, device endpoints, studs), never a net name
  S3  every wired connector cavity carries its own explicit signal - nothing relies on auto-fill
  G1  every schematicPosition / layoutPosition / layout point is on the 30-unit grid
  G2  every bundle segment has a length
  F1  schematic flow is left to right: on every wire between a device connector and an ECU,
      bulkhead or inline-interface connector, the device is to the left
  G3  no two schematic nodes (connectors, terminals, splices, notes) overlap
      (estimated boxes - connector height = 30 per cavity + header, note height from its text)

Exit 1 on any finding.
"""
import collections
import math
import sys

import model

GRID = 30


def nets(d):
    p = {}

    def find(x):
        p.setdefault(x, x)
        while p[x] != x:
            p[x] = p[p[x]]
            x = p[x]
        return x

    nodes = set()
    for c, _, _ in model.conductors(d):
        e = [(x["id"], x.get("handle")) for x in (c.get("source"), c.get("target")) if x and x.get("id")]
        for n in e:
            nodes.add(n)
            find(n)
        if len(e) == 2:
            p[find(e[0])] = find(e[1])
    out = collections.defaultdict(list)
    for n in nodes:
        out[find(n)].append(n)
    return list(out.values())


def labels(d):
    lab = {}
    for c in d.get("connectors", []):
        for cv in c.get("cavities", []):
            lab[(c["id"], cv["id"])] = ("C", cv)
        if c.get("shell"):
            lab[(c["id"], c["shell"]["id"])] = ("C", c["shell"])
    for t in d.get("terminals", []):
        lab[(t["id"], "Terminal")] = ("T", t)
    return lab


def note_box(n):
    w = n.get("width") or 270
    chars = max(1, w // 7)
    lines = sum(max(1, math.ceil(len(l) / chars)) for l in (n.get("text") or "").split("\n"))
    return w, 30 + 18 * lines


def boxes(d):
    out = []
    for c in d.get("connectors", []):
        p = c.get("schematicPosition")
        if p:
            out.append((c["id"], p["x"], p["y"], c.get("width") or 270, 30 * (len(c.get("cavities", [])) + 1)))
    for t in d.get("terminals", []):
        p = t.get("schematicPosition")
        if p:
            out.append((t["id"], p["x"], p["y"], t.get("width") or 270, 30))
    for s in d.get("splices", []):
        p = s.get("schematicPosition")
        if p:
            out.append((s["id"], p["x"], p["y"], 30, 30))
    for n in d.get("schematicNotes", []):
        p = n.get("schematicPosition")
        if p:
            w, h = note_box(n)
            out.append((n["id"], p["x"], p["y"], w, h))
    return out


def overlaps(bx):
    hits = []
    for i in range(len(bx)):
        a = bx[i]
        for b in bx[i + 1:]:
            if a[1] < b[1] + b[3] and b[1] < a[1] + a[3] and a[2] < b[2] + b[4] and b[2] < a[2] + a[4]:
                hits.append((a[0], b[0]))
    return hits


def flow_pairs(loom, d, reg=None):
    """(wrong-way [(device, right-hand node)], total) for device -> ECU / bulkhead / inline wires."""
    reg = reg or model.registry()
    ix = {(h["harness"], h["connector"]) for i in reg.get("interfaces", []) for h in i["halves"]}
    conns = {c["id"]: c for c in d.get("connectors", [])}

    def right(i):
        return i in ("ecu_a", "ecu_b", "ecu_com") or i in model.BULKHEAD_MATE or (loom, i) in ix
    bad, tot = set(), 0
    for c, _, _ in model.conductors(d):
        e = [x["id"] for x in (c.get("source"), c.get("target")) if x and x.get("id")]
        if len(e) != 2:
            continue
        r = [x for x in e if right(x)]
        o = [x for x in e if not right(x) and x in conns]
        if len(r) == 1 and len(o) == 1 and conns.get(r[0], {}).get("schematicPosition")                 and conns[o[0]].get("schematicPosition"):
            tot += 1
            if conns[o[0]]["schematicPosition"]["x"] > conns[r[0]]["schematicPosition"]["x"]:
                bad.add((o[0], r[0]))
    return sorted(bad), tot


def check(loom, d):
    bad = []
    lab = labels(d)
    for ns in nets(d):
        prop = sorted({lab[n][1]["signal"] for n in ns if n in lab and lab[n][1].get("signal")
                       and lab[n][1].get("propagate", True)})
        if len(prop) > 1:
            bad.append("S1 %s: net %s has %d propagating signals: %s"
                       % (loom, sorted(ns)[0], len(prop), " | ".join(s[:40] for s in prop)))
        for n in ns:
            if n not in lab:
                continue
            kind, obj = lab[n]
            if kind == "T" and obj.get("signal") and obj.get("propagate", True):
                bad.append("S2 %s: terminal %s signal propagates" % (loom, n[0]))
            if kind == "C" and not obj.get("signal"):
                bad.append("S3 %s: wired cavity %s.%s has no explicit signal" % (loom, n[0], n[1]))
    for k in ("connectors", "terminals", "splices", "resistors", "diodes", "branchPoints", "cables",
              "schematicNotes", "layoutNotes"):
        for x in d.get(k, []):
            for pk in ("schematicPosition", "layoutPosition"):
                q = x.get(pk)
                if q and (q["x"] % GRID or q["y"] % GRID):
                    bad.append("G1 %s: %s %s %s (%s, %s) is off the 30-unit grid" % (loom, k, x["id"], pk, q["x"], q["y"]))
    for b in d.get("bundles", []):
        if not (b.get("length") or {}).get("value"):
            bad.append("G2 %s: bundle %s has no length" % (loom, b["id"]))
        for lp in b.get("layoutPoints", []):
            q = lp.get("layoutPosition") or {}
            if q.get("x", 0) % GRID or q.get("y", 0) % GRID:
                bad.append("G1 %s: bundle %s layout point off the grid" % (loom, b["id"]))
    for dev, rgt in flow_pairs(loom, d)[0]:
        bad.append("F1 %s: device %s is right of %s - schematic flows right to left" % (loom, dev, rgt))
    for a, b in overlaps(boxes(d)):
        bad.append("G3 %s: schematic %s overlaps %s" % (loom, a, b))
    return bad


if __name__ == "__main__":
    bad = []
    for loom, d in model.docs().items():
        bad += check(loom, d)
    for line in bad:
        print(line)
    c = collections.Counter(l.split()[0] for l in bad)
    print("\n%d drawing-rule finding(s) %s" % (len(bad), dict(c)))
    sys.exit(1 if bad else 0)
