"""Layout view follows the approved route shape, with nothing hidden (DECISIONS R107, Dan 2026-10-15).

  Y1  no two layout nodes or node labels on top of each other (node 30 x 30, a connector or
      terminal label to its right - estimated size, layout_geometry.py)
  Y2  no bundle runs through a node, or through the label of a node it does not end at
  Y3  no two bundles lie on top of each other (collinear, sharing a stretch): every wire visible.
      Two bundles between the same two nodes may run together (Dan: parallel runs that end at
      the same connector or device may run as one bundle)
  Y4  no long diagonal: a bundle segment that moves more than MAX_RUN units on the canvas and is
      neither near-horizontal nor near-vertical, unless it is one ray of a fan (a node with
      FAN or more bundles - CabinPower's box hubs); readable at fit-to-screen: the 2026-10-15
      A-cabin APS run was a lone ~3,500-unit diagonal
  Y5  no bundle runs over the label of its OWN end node. The app shows a connector / terminal label
      to the right of the node; with the front of the car on the right (R140, 2026-10-16) a bundle
      from the parent comes in from the right, so it must reach the node steeply (from above or
      below) or from the left, never along the label

The shape itself (front of the car to the RIGHT (R140, replaces R107(a)), a true top view: driver side up,
passenger side down (R153), branch order
and branch ends as the route's top view) is judged against the route figure by eye; R42's left to
right is gated by audit_drawing_rules.py L1. The routes carry no bundle lengths, so lengths are not
compared here - a bundle keeps its own `length`.

HARD in check_all.py since 2026-10-15 (every drawing at zero). A harness our own generator draws
(interfaces.json "drawing": "own", DECISIONS R220) has no app layout and is skipped.

    python docs/harness/audit_layout.py [CabinPower | ST185-CabinPower | ST185-CabinPower.harness ...]

A name that matches no drawing is an error (exit 2), never a silent pass.
"""
import collections
import sys

import layout_geometry as lg
import model

MAX_RUN = 1500
FAN = 8


def check(loom, d):
    g = lg.geometry(d)
    bad = []
    ids = sorted(g["boxes"])
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if lg.boxes_overlap(g["boxes"][a], g["boxes"][b]):
                bad.append("Y1 %s: %s overlaps %s" % (loom, a, b))
    nodes = {n: (b[0], b[1], b[0] + lg.NODE, b[3]) for n, b in g["boxes"].items()}
    deg = collections.Counter(n for e in g["ends"].values() for n in set(e))
    for bid, pts in g["segments"].items():
        ends = set(g["ends"][bid])
        for p, q in zip(pts, pts[1:]):
            for n, box in nodes.items():
                if n in ends:
                    if g["kind"][n] in ("connectors", "terminals") and                             lg.seg_hits_box(p, q, (box[2] + 2, box[1] + 8, g["boxes"][n][2], box[3] - 8)):
                        bad.append("Y5 %s: bundle %s runs over the label of its own end %s" % (loom, bid, n))
                    continue
                if lg.seg_hits_box(p, q, box):
                    bad.append("Y2 %s: bundle %s runs through node %s" % (loom, bid, n))
                elif g["kind"][n] in ("connectors", "terminals") and \
                        lg.seg_hits_box(p, q, (box[2], box[1] + 8, g["boxes"][n][2], box[3] - 8)):
                    bad.append("Y2 %s: bundle %s runs through the label of %s" % (loom, bid, n))
            ax, ay = abs(q[0] - p[0]), abs(q[1] - p[1])
            if max(ax, ay) > MAX_RUN and min(ax, ay) > 0.2 * max(ax, ay) and                     max(deg[e] for e in ends) < FAN:
                bad.append("Y4 %s: bundle %s runs %d units on the canvas (max %d)"
                           % (loom, bid, max(abs(q[0] - p[0]), abs(q[1] - p[1])), MAX_RUN))
    segs = [(bid, p, q) for bid, pts in g["segments"].items() for p, q in zip(pts, pts[1:])]
    for i, (a, p, q) in enumerate(segs):
        for b, r, s in segs[i + 1:]:
            if a != b and set(g["ends"][a]) != set(g["ends"][b]) and lg.segs_overlap(p, q, r, s):
                bad.append("Y3 %s: bundles %s and %s lie on top of each other" % (loom, a, b))
    return bad


def loom_name(a):
    a = a.replace("\\", "/").rsplit("/", 1)[-1]
    if a.endswith(".harness"):
        a = a[:-len(".harness")]
    return a[len("ST185-"):] if a.startswith("ST185-") else a


if __name__ == "__main__":
    docs = model.docs()
    want = {loom_name(a) for a in sys.argv[1:]}
    unknown = sorted(want - set(docs))
    if unknown:
        print("audit_layout: no drawing named %s (looms: %s)" % (", ".join(unknown), ", ".join(docs)))
        sys.exit(2)
    bad = []
    own = model.own_drawn()   # drawn by our own generator, not on the app canvas (R220)
    for loom, d in docs.items():
        if (not want or loom in want) and loom not in own:
            bad += check(loom, d)
    for line in bad:
        print(line)
    c = collections.Counter(l.split()[1].rstrip(":") + " " + l.split()[0] for l in bad)
    print("\n%d layout finding(s) %s" % (len(bad), dict(c)))
    sys.exit(1 if bad else 0)
