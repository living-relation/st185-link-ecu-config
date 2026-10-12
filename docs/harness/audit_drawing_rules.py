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
  S3  a wired cavity with no signal of its own sits on a net with exactly one propagating signal, so
      it inherits that one name (the docs: define a signal once where it originates, set one
      explicitly only where a cavity needs a different label)
  G1  every schematicPosition / layoutPosition / layout point is on the 30-unit grid
  G2  a bundle segment without a length is listed (not a failure; Daniel's own drawing leaves the
      sensor legs unmeasured until the car is measured, 2026-10-12)
  L1  the LAYOUT reads left to right along the physical route (Daniel 2026-10-12): in every layout
      piece, walking away from one end (the leftmost or the rightmost node), x never doubles back -
      a branch may drop straight up or down but never runs back past its parent. The SCHEMATIC has no
      direction rule (center-out around the main connector is fine); it only must not overlap
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


def layout_pieces(d):
    g = collections.defaultdict(set)
    for b in d.get("bundles", []):
        g[b["sourceId"]].add(b["targetId"])
        g[b["targetId"]].add(b["sourceId"])
    seen = set()
    for s in list(g):
        if s in seen:
            continue
        comp, todo = {s}, [s]
        while todo:
            for m in g[todo.pop()] - comp:
                comp.add(m)
                todo.append(m)
        seen |= comp
        yield comp, g


def layout_backtracks(g, p, root, sign):
    """Edges (parent, child) walking away from root where x moves back toward the root side."""
    bad, prev, todo = [], {root: None}, [root]
    while todo:
        n = todo.pop()
        for m in sorted(g[n]):
            if m in prev:
                continue
            prev[m] = n
            todo.append(m)
            if n in p and m in p and sign * (p[m][0] - p[n][0]) < 0:
                bad.append((n, m))
    return bad, prev


todo_len = []


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
            if kind == "C" and not obj.get("signal") and len(prop) != 1:
                bad.append("S3 %s: wired cavity %s.%s has no signal and its net has %d propagating signals"
                           % (loom, n[0], n[1], len(prop)))
    for k in ("connectors", "terminals", "splices", "resistors", "diodes", "branchPoints", "cables",
              "schematicNotes", "layoutNotes"):
        for x in d.get(k, []):
            for pk in ("schematicPosition", "layoutPosition"):
                q = x.get(pk)
                if q and (q["x"] % GRID or q["y"] % GRID):
                    bad.append("G1 %s: %s %s %s (%s, %s) is off the 30-unit grid" % (loom, k, x["id"], pk, q["x"], q["y"]))
    for b in d.get("bundles", []):
        if not (b.get("length") or {}).get("value"):
            todo_len.append("%s: bundle %s" % (loom, b["id"]))
        for lp in b.get("layoutPoints", []):
            q = lp.get("layoutPosition") or {}
            if q.get("x", 0) % GRID or q.get("y", 0) % GRID:
                bad.append("G1 %s: bundle %s layout point off the grid" % (loom, b["id"]))
    p = {x["id"]: (x["layoutPosition"]["x"], x["layoutPosition"]["y"])
         for k in ("connectors", "terminals", "branchPoints") for x in d.get(k, []) if x.get("layoutPosition")}
    for comp, g in layout_pieces(d):
        cand = [n for n in comp if n in p]
        if len(cand) < 2:
            continue
        left = min(cand, key=lambda n: (p[n][0], p[n][1]))
        right = max(cand, key=lambda n: (p[n][0], -p[n][1]))
        a, _ = layout_backtracks(g, p, left, +1)
        b, _ = layout_backtracks(g, p, right, -1)
        if a and b:
            best = a if len(a) <= len(b) else b
            bad.append("L1 %s: layout piece at %s doubles back - %d bundle(s), e.g. %s -> %s"
                       % (loom, left, len(best), best[0][0], best[0][1]))
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
