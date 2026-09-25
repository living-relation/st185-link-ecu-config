#!/usr/bin/env python3
"""Dump every connector cavity in every rebuild harness with what lands on it.

Read-only. This is the evidence gatherer for authoring sot/channels.csv - it
tells you what the drawings actually say so the SoT is written from verified
data instead of memory. It walks BOTH wires and cable conductors, because
WheelSpeed has no `wires` at all.

Usage:  python docs/harness/dump_nets.py [filter]
"""
import json, sys, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parents[2]
REB = ROOT / "docs" / "harness" / "rebuild"
filt = sys.argv[1].lower() if len(sys.argv) > 1 else ""


def conductors(d):
    out = []
    for w in d.get("wires", []):
        out.append((w, ""))
    for cb in d.get("cables", []):
        for co in cb.get("cores", []):
            out.append((co, cb["id"]))
        sh = cb.get("shield")
        if sh:
            out.append((sh, cb["id"]))
    return out


for path in sorted(REB.glob("*.harness")):
    if filt and filt not in path.name.lower():
        continue
    d = json.loads(path.read_text(encoding="utf-8"))
    conns = {c["id"]: c for c in d.get("connectors", [])}
    hits = collections.defaultdict(list)
    for w, cable in conductors(d):
        for end in ("source", "target"):
            e = w.get(end) or {}
            if e.get("id") in conns:
                other = w.get("target" if end == "source" else "source") or {}
                hits[(e["id"], e.get("handle"))].append(
                    "%s -> %s.%s%s" % (w["id"], other.get("id"), other.get("handle"),
                                       (" [cable %s]" % cable) if cable else ""))
    print("=" * 78)
    print(path.name)
    print("=" * 78)
    for cid, c in conns.items():
        print("  %-16s %-34s part=%s" % (cid, c.get("name", ""), c.get("partId", "-")))
        for cav in c.get("cavities", []):
            h = cav.get("id") or cav.get("handle")
            key = (cid, h)
            lbl = cav.get("name", "")
            if key in hits:
                for line in hits[key]:
                    print("      %-6s %-32s %s" % (h, lbl, line))
            else:
                mark = "PLUG" if cav.get("cavityPlugPartId") else (
                    "nc" if cav.get("notConnected") else "EMPTY")
                print("      %-6s %-32s (%s)" % (h, lbl, mark))
    print()
