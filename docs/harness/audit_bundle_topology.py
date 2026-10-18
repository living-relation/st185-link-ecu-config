"""Bundle shape follows the route; the SoT alone defines the circuit ends (DECISIONS R154, Dan
2026-10-17: "always match the route. and always the SoT governs the defined connection end points").

Mechanical signs that a drawing's bundle tree was bent to fit the drawing instead of the route:

  T1  a bundle no wire, cable core or shield runs through (bundles side by side between the same
      two nodes count as one) (an empty leg - e.g. the 2026-10-17 HeavyDC
      starter fan: two copied 1060 mm legs that only gave H5 / H8 a lug to land on)
  T2  copies of one stud drawn apart: terminals whose labels differ only by a trailing number
      ("starter B+", "starter B+ 2", "starter B+ 3") are lugs on ONE stud, so they hang off one
      branch point a short stub away, never more than STUB_MAX mm apart along the bundles
  T3  a wire or core whose two ends are not joined by the bundles (it would have to leave the
      harness to get from one end to the other)

Whether a bundle runs WITH the right neighbours (H5 joining H4 at the firewall) is judged against
the route figure by eye; this gate catches the shapes that cannot be right on any route.

    python docs/harness/audit_bundle_topology.py [A-cabin | ST185-A-cabin ...]
"""
import collections
import heapq
import json
import os
import re
import sys

import model

STUB_MAX = 100   # mm between two lugs of one stud, along the bundles
# Findings waiting on Dan (OPEN-ITEMS Needs Dan): printed, not failing. Remove an entry once
# its drawing is fixed or Dan keeps it (then say so in DECISIONS R154). Anything new fails.
PENDING_DAN = {}   # N28 cleared 2026-10-18 (DECISIONS R179)


def graph(d):
    g = collections.defaultdict(list)
    for b in d.get("bundles", []):
        L = (b.get("length") or {}).get("value") or 0
        g[b["sourceId"]].append((b["targetId"], L, b["id"]))
        g[b["targetId"]].append((b["sourceId"], L, b["id"]))
    for m in d.get("mates") or []:      # a mated pair (RADLOK halves): the wire runs through it
        a, z = m.get("sourceId"), m.get("targetId")
        if a and z:
            g[a].append((z, 0, None))
            g[z].append((a, 0, None))
    return g


def path(g, a, b):
    """bundle ids and mm on the shortest path a -> b along the bundles (and mates), or None."""
    dist, prev, pq = {a: 0}, {a: None}, [(0, a)]
    while pq:
        dn, n = heapq.heappop(pq)
        if n == b:
            ids = []
            while prev[n]:
                p, bid = prev[n]
                if bid:
                    ids.append(bid)
                n = p
            return ids, dn
        if dn > dist[n]:
            continue
        for m, L, bid in g.get(n, ()):
            if dn + L < dist.get(m, 1e18):
                dist[m], prev[m] = dn + L, (n, bid)
                heapq.heappush(pq, (dn + L, m))
    return None


def ends(d):
    """(name, a, b) for every wire and cable core, an end on a splice / resistor / diode moved to
    the node it sits at."""
    loc = {x["id"]: x.get("locationId") for k in ("splices", "resistors", "diodes")
           for x in d.get(k, [])}
    out = [(w["id"], w["source"]["id"], w["target"]["id"]) for w in d.get("wires", [])
           if w.get("source") and w.get("target")]
    for c in d.get("cables", []):
        for i, k in enumerate(c.get("cores", [])):
            if k.get("source") and k.get("target"):
                out.append(("%s core %d" % (c["id"], i + 1), k["source"]["id"], k["target"]["id"]))
        sh = c.get("shield") or {}
        sh_ends = [sh[k]["id"] for k in ("source", "target") if sh.get(k)]
        if len(sh_ends) == 2:
            out.append(("%s shield" % c["id"], sh_ends[0], sh_ends[1]))
        elif sh_ends:   # drain at one end only: it runs with its cable's cores to that end
            for k in c.get("cores", []):
                for e in ("source", "target"):
                    if k.get(e):
                        out.append(("%s shield" % c["id"], sh_ends[0], k[e]["id"]))
    return [(n, loc.get(a) or a, loc.get(b) or b) for n, a, b in out]


def on_bundle(d):
    """bundle id -> its source node, for a splice whose locationId is a bundle (it sits on it)."""
    return {b["id"]: b["sourceId"] for b in d.get("bundles", [])}


def check(loom, d):
    bad = []
    g = graph(d)
    used = set()
    onb = on_bundle(d)
    for name, a, b in ends(d):
        for x in (a, b):
            if x in onb:          # a splice on a bundle: that bundle carries the wire
                used.add(x)
        a, b = onb.get(a, a), onb.get(b, b)
        if a == b or (a not in g and b not in g):
            continue
        if a not in g or b not in g:   # a loose end (no bundle, no location): judged elsewhere;
            for _, _, bid in g[a if a in g else b]:   # count the legs at the known end
                used.add(bid)
            continue
        p = path(g, a, b)
        if p is None:
            bad.append("T3 %s: %s runs %s -> %s, which no bundle joins" % (loom, name, a, b))
            continue
        used.update(p[0])
    pair = collections.defaultdict(set)      # parallel bundles between the same two nodes (a
    for b in d.get("bundles", []):           # labelled sub-group, e.g. A-cabin's INJ COP) count
        pair[frozenset((b["sourceId"], b["targetId"]))].add(b["id"])   # as one
    for b in d.get("bundles", []):
        if not pair[frozenset((b["sourceId"], b["targetId"]))] & used:
            bad.append("T1 %s: bundle %s (%s -> %s) carries no wire" % (loom, b["id"], b["sourceId"], b["targetId"]))
    studs = collections.defaultdict(list)
    for t in d.get("terminals", []):
        base = re.sub(r"\s+\d+$", "", (t.get("signal") or "").strip())
        if base:
            studs[base].append(t["id"])
    for base, ids in sorted(studs.items()):
        if len(ids) < 2 or not any(re.search(r"\s\d+$", (x.get("signal") or "").strip())
                                   for x in d["terminals"] if x["id"] in ids):
            continue
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                p = path(g, a, b)
                if p and p[1] > STUB_MAX:
                    bad.append("T2 %s: %s and %s are lugs of one stud (%s) drawn %g mm apart"
                               % (loom, a, b, base, p[1]))
    return bad


def main(argv):
    files = model.harness_files()
    want = [a for a in argv if not a.startswith("--")]
    looms = sorted(files) if not want else []
    for w in want:
        k = w.replace("ST185-", "").replace(".harness", "")
        if k not in files:
            raise SystemExit("no drawing called %s" % w)
        looms.append(k)
    bad, held = [], []
    for loom in looms:
        with open(os.path.join(model.REB, files[loom]), encoding="utf-8") as f:
            for b in check(loom, json.load(f)):
                bid = b.split()[3] if b.startswith("T1") else None
                (held if bid in PENDING_DAN.get(loom, ()) else bad).append(b)
    for b in held:
        print("pending (Needs Dan N14): " + b)
    for b in bad:
        print(b)
    print("audit_bundle_topology: %d finding(s), %d pending Dan, across %d drawing(s)"
          % (len(bad), len(held), len(looms)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
