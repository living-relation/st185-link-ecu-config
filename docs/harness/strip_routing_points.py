"""Strip the wire routing points from the drawings (DECISIONS R141, Dan 2026-10-16).

A routing point is a wire `layoutPoints` entry - the white cross the app shows on hover, added or
removed by double-clicking a wire. Dan: none unless he asks, and only once the overall layout is
set; harness.design's own auto-routing is preferred (the docs say the same:
https://docs.harness.design/files/harness/positioning.md "Avoid adding layout waypoints to wires").
Bundle layout points are NOT touched (Dan kept the 13 on RearFuel / WheelSpeed-Front / -Rear),
and neither is anything a wire on the allow-list carries (audit_wire_spacing.ROUTING_POINTS_ALLOWED).

    python docs/harness/strip_routing_points.py [loom ...] [--write]

Without --write it only counts. Writes go through a temp file + rename in the file's own key
order and line ending, and refuse a file that changed on disk meanwhile (R50: Dan's saved file wins).
"""
import json
import os
import sys

import audit_wire_spacing
import layout_tree
import model


def strip(loom, d):
    keep = audit_wire_spacing.ROUTING_POINTS_ALLOWED.get(loom, set())
    n = w = 0
    for x in d.get("wires", []):
        if x.get("layoutPoints") and x["id"] not in keep:
            n += len(x["layoutPoints"])
            w += 1
            del x["layoutPoints"]
    return n, w


def main(argv):
    write = "--write" in argv
    only = [a for a in argv if not a.startswith("--")]
    files = model.harness_files()
    total = wires = 0
    for loom, fn in files.items():
        if only and loom not in only:
            continue
        path = os.path.join(model.REB, fn)
        mtime = os.path.getmtime(path)
        with open(path, "rb") as f:
            nl = "\r\n" if b"\r\n" in f.read(4096) else "\n"
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        n, w = strip(loom, d)
        total += n
        wires += w
        print("%-18s %4d routing point(s) on %3d wire(s)" % (loom, n, w))
        if write and n:
            if os.path.getmtime(path) != mtime:
                raise SystemExit("%s changed on disk - not written" % path)
            layout_tree.write_atomic(path, d, nl)
    print("%s %d routing point(s) on %d wire(s)" % ("removed" if write else "found", total, wires))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
