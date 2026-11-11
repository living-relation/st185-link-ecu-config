#!/usr/bin/env python
"""Wireway corridor check (DECISIONS B8 "Wireway corridors", Dan approved 2026-11-11 12:19; Y7 a). Reads, never writes.

Every line of every placement-editor seed (placement_editor/seeds/*.json) must run inside the approved corridor bands of
corridors.json. Only main trunks are held to it (Y7 a): a stretch outside every band is allowed only as a short device
branch, i.e. it runs to the start or the end of its line, that end is one of the harness's own devices, and the stretch
is at most BRANCH_MAX_MM long (injector / coil branches over the head, stubs out to a device); a grey marker (another
harness's hub, a hand-off point) counts as a device end. Anything else outside a band for more than SLACK_MM is a finding.
AB-engine's routes are Dan's own (W4 c, seed key drawRoutes), so its routes of record are read from its route file
(layout route_trees, Route 16), not from its seed's starting picture. A dashed copy of another harness's line (harness C
showing the engine harness's belt-end drop) is checked once, with its owner.

Frames: a seed with "unitMm" 5.3 is in 1993 EWD p.36 points (engine-bay editors), every other seed in car mm. Each
corridor is turned into both frames with the conversion in corridors.json (car_x = 5.3 * y_pt - 1019.1,
car_y = 1519.3 - 5.3 * x_pt). A corridor's "widen" bands (Y6 a, Y8 a) count as part of it.

    python docs/harness/tools/check_corridors.py              the gate (exit 1 on a finding)
    python docs/harness/tools/check_corridors.py -v           also list every exempt device branch
    python docs/harness/tools/check_corridors.py --self-test  prove the check fails on a broken copy (CI)
"""
import copy
import glob
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORRIDORS = os.path.join(HERE, "corridors.json")
SEEDS = os.path.join(HERE, "placement_editor", "seeds")
LAYOUT = os.path.join(HERE, "ST185-harness.layout.json")
ROUTES = os.path.join(os.path.dirname(HERE), "routes")
MMPT = 5.3
BRANCH_MAX_MM = 600.0     # longest device branch allowed outside a band (Y7 a)
SLACK_MM = 25.0           # an outside stretch shorter than this is corner rounding, not a finding
STEP_MM = 5.0             # sample spacing along each line
EPS_MM = 2.0              # band edge tolerance
SPOT_MM = 30.0            # a seed line end this close to a device spot ends on that device
SPUR_MM = 80.0            # the same for a route file, where each device hangs on its own short spur (W4 c)


def to_car(p):
    return (MMPT * p[1] - 1019.1, 1519.3 - MMPT * p[0])


def to_pt(p):
    return ((1519.3 - p[1]) / MMPT, (p[0] + 1019.1) / MMPT)


def bands(doc):
    """[(corridor no, name, polyline in car mm, half width mm)] for every corridor and its widen bands."""
    out = []
    for c in doc["corridors"]:
        for b in [c] + c.get("widen", []):
            if "ewd_pt" in b:          # engine-bay bands: the EWD points are the source, car mm is derived
                pts = [to_car(p) for p in b["ewd_pt"]]
            else:
                pts = [tuple(p) for p in b["car_mm"]]
            w = b.get("width_mm") or b["width_pt"] * MMPT
            out.append((c["n"], c["name"], pts, w / 2.0))
    return out


def seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def inside(p, bl):
    for _n, _name, pts, hw in bl:
        for a, b in zip(pts, pts[1:]):
            if seg_dist(p, a, b) <= hw + EPS_MM:
                return True
    return False


def samples(pts):
    """[(point, distance along)] every STEP_MM, corners included."""
    out, run = [], 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(math.ceil(L / STEP_MM)))
        for i in range(n):
            t = i / n
            out.append(((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])), run + t * L))
        run += L
    out.append((pts[-1], run))
    return out


def route_of_record(seed):
    """Dan draws AB-engine's routes himself (W4 c, drawRoutes): its seed lines are only the editor's starting picture,
    so its routes of record are the route file the layout tree builds it from (route_trees), as (lines, spots) in the
    seed's frame. Every other seed is its own record."""
    if not seed.get("drawRoutes"):
        return seed.get("lines", []), [(d["x"], d["y"]) for d in seed.get("devices", []) + seed.get("refs", [])], SPOT_MM
    with open(LAYOUT, encoding="utf-8") as f:
        trees = json.load(f).get("route_trees", [])
    rf = [t["route"] for t in trees if t.get("harness") == seed.get("harness")]
    with open(os.path.join(ROUTES, rf[0]), encoding="utf-8") as f:
        t = f.read()
    m = re.search(r'<script[^>]*id="route-data"[^>]*>(.*?)</script>', t, re.S)
    rd = json.loads(m.group(1))
    lines = [{"id": "L%d" % r["n"], "name": r["name"], "pts": r["path"]} for r in rd["routes"]]
    lines += [{"id": k.split(" ")[0], "name": k.split(" ", 1)[1], "pts": v} for k, v in rd["runs"].items()]
    spots = [tuple(d["at"]) for d in rd["devices"] if not d.get("moved_to")]
    spots += [(d["x"], d["y"]) for d in seed.get("refs", [])]
    return lines, spots, SPUR_MM


def check_seed(seed, bl, shared=None):
    """(findings, exempt): one text line each. A line end on one of the harness's devices or grey markers (another
    harness's hub, a hand-off point) is a device end. A dashed line that is a copy of another harness's line (shown for
    context, e.g. harness C riding the engine harness's belt-end drop) is checked with its owner, not twice."""
    car = seed.get("unitMm", 1) not in (MMPT,)
    conv = (lambda p: tuple(p)) if car else to_car
    lines, spots, near = route_of_record(seed)
    spots = [conv(s) for s in spots]
    finds, exempt = [], []
    for ln in lines:
        pts = [conv(p) for p in ln["pts"]]
        if len(pts) < 2:
            continue
        key = tuple((round(p[0], 1), round(p[1], 1)) for p in pts)
        if shared is not None:
            if ln.get("dash") and key in shared and shared[key] != seed.get("harness"):
                exempt.append("  shared  %s line %s: a copy of %s's line, checked there" % (seed.get("harness"), ln["id"],
                                                                                      shared[key]))
                continue
            shared.setdefault(key, seed.get("harness"))
        sm = samples(pts)
        total = sm[-1][1]
        dev0 = any(math.hypot(pts[0][0] - s[0], pts[0][1] - s[1]) <= near for s in spots)
        dev1 = any(math.hypot(pts[-1][0] - s[0], pts[-1][1] - s[1]) <= near for s in spots)
        flags = [inside(p, bl) for p, _ in sm]
        i = 0
        while i < len(sm):
            if flags[i]:
                i += 1
                continue
            j = i
            while j + 1 < len(sm) and not flags[j + 1]:
                j += 1
            a = sm[i - 1][1] if i > 0 else 0.0
            b = sm[j + 1][1] if j + 1 < len(sm) else total
            L = b - a
            where = "%s line %s (%s), %.0f-%.0f mm along" % (seed.get("harness"), ln["id"], ln.get("name", ""), a, b)
            # a device branch: the stretch lies in the last (first) BRANCH_MAX_MM of a line that ends (starts) on a device
            branch = (dev1 and a >= total - BRANCH_MAX_MM - STEP_MM) or (dev0 and b <= BRANCH_MAX_MM + STEP_MM)
            if L < SLACK_MM:
                pass
            elif branch:
                exempt.append("  branch  %s: %.0f mm outside, a device branch (Y7 a)" % (where, L))
            else:
                finds.append("  OUTSIDE %s: %.0f mm outside every corridor (main trunk)" % (where, L))
            i = j + 1
    return finds, exempt


def load_seeds():
    out = []
    for p in sorted(glob.glob(os.path.join(SEEDS, "*.json"))):
        with open(p, encoding="utf-8") as f:
            out.append((os.path.basename(p), json.load(f)))
    return out


def run(doc, seeds, verbose=False, quiet=False):
    bl = bands(doc)
    bad = 0
    if doc.get("status", "").split(" ")[0].lower() != "approved":
        bad += 1
        if not quiet:
            print("corridors.json status is not 'approved': %s" % doc.get("status"))
    shared = {}
    for name, seed in sorted(seeds, key=lambda s: (not s[1].get("drawRoutes"), s[0])):   # route owners first
        finds, exempt = check_seed(seed, bl, shared)
        bad += len(finds)
        if quiet:
            continue
        nl = len(seed.get("lines", []))
        print("%-20s %2d lines: %s" % (name, nl, "OK" if not finds else "%d finding(s)" % len(finds)))
        for f in finds:
            print(f)
        if verbose:
            for e in exempt:
                print(e)
    return bad


def self_test():
    with open(CORRIDORS, encoding="utf-8") as f:
        doc = json.load(f)
    seeds = load_seeds()
    bad = []
    if run(doc, seeds, quiet=True):
        bad.append("the real corridors and seeds should pass")
    # a main trunk straight across the middle of the car (no corridor there) must fail
    s = copy.deepcopy(seeds)
    s.append(("broken.json", {"harness": "broken", "lines": [{"id": "X", "pts": [[-1200, -400], [-1200, 400]]}],
                              "devices": []}))
    if not run(doc, s, quiet=True):
        bad.append("a trunk across the cabin floor passed")
    # the same stretch as a short branch ending on a device passes; a long one fails
    ok = {"harness": "branch", "lines": [{"id": "B", "pts": [[-580, 0], [-580, 300], [-900, 300]]}],
          "devices": [{"id": "D", "x": -900, "y": 300}]}
    if run(doc, seeds + [("ok.json", ok)], quiet=True):
        bad.append("a short device branch failed")
    far = copy.deepcopy(ok)
    far["lines"][0]["pts"][-1] = [-1500, 300]
    far["devices"][0]["x"] = -1500
    if not run(doc, seeds + [("far.json", far)], quiet=True):
        bad.append("a 900 mm device branch passed")
    # an engine-bay seed (EWD points) across the top of the block must fail
    eng = {"harness": "eng", "unitMm": MMPT, "lines": [{"id": "E", "pts": [[222.0, 230.0], [341.0, 230.0]]}],
           "devices": []}
    if not run(doc, seeds + [("eng.json", eng)], quiet=True):
        bad.append("a trunk across the engine block passed")
    # a corridor file that is not approved must fail
    d2 = copy.deepcopy(doc)
    d2["status"] = "PROPOSAL"
    if not run(d2, seeds, quiet=True):
        bad.append("a proposal corridor file passed")
    for b in bad:
        print("SELF-TEST FAIL: " + b)
    print("%d self-test failure(s)." % len(bad))
    return 1 if bad else 0


def main(argv):
    if "--self-test" in argv:
        return self_test()
    with open(CORRIDORS, encoding="utf-8") as f:
        doc = json.load(f)
    bad = run(doc, load_seeds(), verbose="-v" in argv)
    print("corridor check: %s" % ("OK" if not bad else "%d finding(s)" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
