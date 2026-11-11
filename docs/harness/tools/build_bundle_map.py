"""The whole-car bundle map (Dan T4 a, 2026-11-10): every harness on one top view of the car, each bundle striped in the
colour of every harness whose wires run in it; tap a bundle to list its wires, search a wire or a device to light its
route.  Built from the master and the layout tree (build_drawings.Harness, the same routes the lengths come from).

    python docs/harness/tools/build_bundle_map.py           write docs/harness/BUNDLE-MAP.html
    python docs/harness/tools/build_bundle_map.py --check   fail if the committed page is stale (tools/check_all.py)

Positions are the layout's drawing positions (front of the car to the RIGHT, driver side UP), not to scale; the
lengths shown are the tree lengths in mm.  A place drawn twice in the tree (EngineRoom-C's C_ copies of Route 16
nodes) is one bundle here when both copies sit on the same spot.
"""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_drawings as B  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "BUNDLE-MAP.html")
ORDER = ["AB-cabin", "AB-engine", "EngineRoom-C", "CabinPower", "Dash", "AntiTheft", "HeavyDC", "RearFuel",
         "WheelSpeed-Front", "WheelSpeed-Rear"]


def key(xy):
    return (round(xy[0] * 2) / 2, round(xy[1] * 2) / 2)


def model():
    H = B.Harness("ST185-harness")
    N = H.layout["nodes"]
    spot = {n: key(v["xy"]) for n, v in N.items()}
    segs = {}      # physical bundle key -> data
    for a, b, mm in H.layout["segments"]:
        ka, kb = sorted([spot[a], spot[b]])
        if ka == kb:
            continue
        s = segs.setdefault((ka, kb), {"a": ka, "b": kb, "mm": mm, "names": set(), "wires": []})
        s["names"].add(tuple(sorted((a, b))))
    wires = []
    for r in H.wires:
        if B.is_removal(r):
            continue
        p, mm = H.route(r)
        if not p:
            continue
        legs = []
        for x, y in zip(p, p[1:]):
            k = tuple(sorted([spot[x], spot[y]]))
            if k in segs and k not in legs:
                legs.append(k)
        w = {"id": r["wire_id"], "h": r["harness"], "c": r["colour"] or ("Shield" if r["from_type"] == "cable screen" else ""),
             "g": r["gauge_awg"], "f": r["from_name"] or r["from_id"], "t": r["to_name"] or r["to_id"],
             "cir": r["circuit"], "pt": [x.strip() for x in r["passes_through"].split("/") if x.strip()],
             "mm": mm, "cab": r["cable"], "fa": list(spot[p[0]]), "ta": list(spot[p[-1]])}
        wires.append((w, legs))
        for k in legs:
            segs[k]["wires"].append(len(wires) - 1)
    keys = sorted(k for k in segs if segs[k]["wires"])
    idx = {k: i for i, k in enumerate(keys)}
    S = []
    for k in keys:
        s = segs[k]
        hs = collections.Counter(wires[i][0]["h"] for i in s["wires"])
        S.append({"a": list(s["a"]), "b": list(s["b"]), "mm": s["mm"],
                  "h": [h for h in ORDER if h in hs] + sorted(h for h in hs if h not in ORDER),
                  "w": s["wires"],
                  "n": [N[x]["short"] or N[x].get("label", x) for x in (sorted(s["names"])[0])]})
    W = []
    for w, legs in wires:
        w["s"] = [idx[k] for k in legs]
        W.append(w)
    used = {tuple(w[k]) for w in W for k in ("fa", "ta")}
    ends = {}
    for n, v in sorted(N.items(), key=lambda x: not x[1].get("end")):     # a device node names its spot before a junction
        if v.get("end") or spot[n] in used:
            ends.setdefault(spot[n], {"xy": list(spot[n]), "l": v.get("label", n), "s": v.get("short") or n, "d": bool(v.get("end"))})
    return {"segs": S, "wires": W, "ends": list(ends.values()), "order": ORDER,
            "count": {h: sum(1 for w in W if w["h"] == h) for h in ORDER}}


def page(M):
    data = json.dumps(M, separators=(",", ":"), sort_keys=True)
    with open(os.path.join(HERE, "bundle_map_template.html"), encoding="utf-8") as f:
        t = f.read().replace("\r\n", "\n")     # a Windows checkout may hand back CRLF
    return t.replace("/*DATA*/null", data)


def build():
    M = model()
    return M, page(M)


if __name__ == "__main__":
    M, text = build()
    if "--check" in sys.argv:
        cur = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if cur.replace("\r\n", "\n") != text:
            print("build_bundle_map --check: docs/harness/BUNDLE-MAP.html is stale; run build_bundle_map.py")
            sys.exit(1)
        print("build_bundle_map --check: OK")
    else:
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("wrote %s: %d bundles, %d wires" % (os.path.relpath(OUT), len(M["segs"]), len(M["wires"])))
