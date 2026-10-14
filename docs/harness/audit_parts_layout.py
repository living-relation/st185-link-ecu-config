"""Parts lists hold only used parts, and the layout never joins separate harnesses
(Daniel, 2026-10-12, standing rule).

  P1  every entry in a drawing's parts lists (wireParts, connectorParts, contactParts, ...)
      is used by that drawing - directly (partId / *PartId on a connector, cavity, wire,
      cable, terminal, splice ...) or through another used part (a connector part's
      configuration contact, lock, mount ...). An unused entry fails.
  P2  never join separate harnesses in the layout: cutting any bundle segment that splits
      its layout piece must cut at least one conductor (wire, cable core or screen; each
      splice sits at its locationId). A segment no conductor crosses joins two pieces that
      are not connected - e.g. the VRC IN cables and the VRC OUT cable meet only at the VRC
      box. Fails even when the join carries no wires - that is the case it catches.

Library sync (pushing new / changed parts to the harness.design ST185 Parts Library) needs
the app connector and is not checked here.

Exit 1 on any finding.
"""
import collections
import sys

import model

CATS = [k for k in ("wireParts", "connectorParts", "contactParts", "terminalParts", "spliceParts",
                    "cavityPlugParts", "lockParts", "cableParts", "resistorParts", "diodeParts",
                    "mountParts", "bootParts", "backshellParts", "dustCoverParts", "sealParts")]


def refs(obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and (k == "partId" or k.endswith("PartId")):
                out.add(v)
            elif k in ("coveringIds", "partIds") and isinstance(v, list):   # partIds: a bundle's coverings
                out.update(x for x in v if isinstance(x, str))
            else:
                refs(v, out)
    elif isinstance(obj, list):
        for v in obj:
            refs(v, out)
    return out


bad = []
for loom, d in model.docs().items():
    # P1
    cats = [k for k in d if k.endswith("Parts") and isinstance(d[k], list)]
    used = refs({k: v for k, v in d.items() if k not in cats}, set())
    byid = {p["id"]: p for k in cats for p in d[k]}
    todo = list(used)
    while todo:
        p = byid.get(todo.pop())
        if p:
            for r in refs(p, set()) - used:
                used.add(r)
                todo.append(r)
    for k in cats:
        for p in d[k]:
            if p["id"] not in used:
                bad.append("P1 %s: %s %s (%s) is not used" % (loom, k, p["id"], p.get("partNumber", "")))

    # P2 - for each bundle segment whose removal splits its layout piece, some conductor
    # must have one end on each side (splices sit at their locationId)
    g = collections.defaultdict(set)
    for b in d.get("bundles", []):
        g[b["sourceId"]].add((b["targetId"], b["id"]))
        g[b["targetId"]].add((b["sourceId"], b["id"]))
    loc = {s["id"]: s["locationId"] for s in d.get("splices", []) if s.get("locationId")}
    cends = []
    for c, _, _ in model.conductors(d):
        e = [loc.get(x["id"], x["id"]) for x in (c.get("source"), c.get("target")) if x and x.get("id")]
        if len(e) == 2:
            cends.append(e)
    for b in d.get("bundles", []):
        side, todo = {b["sourceId"]}, [b["sourceId"]]
        while todo:
            n = todo.pop()
            for m, bid in g[n]:
                if bid != b["id"] and m not in side:
                    side.add(m)
                    todo.append(m)
        if b["targetId"] in side:
            continue  # part of a loop: not a split
        if not any((x in side) != (y in side) for x, y in cends):
            bad.append("P2 %s: bundle %s (%s - %s) joins two pieces no conductor connects - "
                       "separate harnesses drawn as connected" % (loom, b["id"], b["sourceId"], b["targetId"]))

for line in bad:
    print(line)
print("\n%d parts-list / layout finding(s)." % len(bad))
sys.exit(1 if bad else 0)
