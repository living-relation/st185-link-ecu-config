import json, os, csv, datetime, collections, heapq

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
# The eight current looms. Repointed 2026-09-22 - this used to read the
# pre-split Signal/Power/CAN/EngineRoom-C files, so every build list generated
# before that date described the old two-loom structure, not the built one.
F = (("A-ECU","ST185-A-ECU.harness"), ("A-engine","ST185-A-engine.harness"),
     ("B-ECU","ST185-B-ECU.harness"), ("B-engine","ST185-B-engine.harness"),
     ("CAN","ST185-CAN.harness"), ("EngineRoomC","ST185-EngineRoom-C.harness"),
     ("ClusterLED","ST185-ClusterLED.harness"), ("WheelSpeed","ST185-WheelSpeed.harness"),
     ("AntiTheft","ST185-AntiTheft.harness"))

def load(fn):
    return json.load(open(os.path.join(R, fn), encoding="utf-8"))

def node_index(d):
    """id -> (display label, kind)"""
    ix = {}
    for c in d.get("connectors", []):
        ix[c["id"]] = (c.get("label") or c["id"], "connector")
    for t in d.get("terminals", []):
        ix[t["id"]] = (t.get("signal") or t["id"], "terminal(%s)" % t.get("type",""))
    for s in d.get("splices", []):
        ix[s["id"]] = (s["id"], "splice")
    for b in d.get("branchPoints", []):
        ix[b["id"]] = (b["id"], "branch")
    for r in d.get("resistors", []):
        ix[r["id"]] = (r["id"], "resistor")
    return ix

def cavity_info(d):
    """(connId, cavityId) -> (designation, signal)"""
    out = {}
    for c in d.get("connectors", []):
        for cv in c.get("cavities", []):
            out[(c["id"], cv["id"])] = (cv.get("designation",""), cv.get("signal",""))
    return out

def contact_for(d, conn_id, cav_id=None):
    """connector cavity -> contact part number to crimp: the cavity's own
    contactPartId override first (2026-09-25: ECU power pins, fuse-block and
    relay cavities carry per-cavity contacts), else the part's default."""
    parts = {}
    for k in [x for x in d if x.endswith("Parts")]:
        for q in d[k]:
            parts[q["id"]] = q
    for c in d.get("connectors", []):
        if c["id"] != conn_id:
            continue
        pid = c.get("partId")
        for cv in c.get("cavities", []):
            if cv["id"] == cav_id and cv.get("contactPartId") in parts:
                return parts[cv["contactPartId"]].get("partNumber", "")
        if not pid or pid not in parts:
            return ""
        cfgs = parts[pid].get("configurations") or []
        for cfg in cfgs:
            ct = cfg.get("contactPartId")
            if ct and ct in parts:
                return parts[ct].get("partNumber", "")
    return ""

def bundle_graph(d):
    g = collections.defaultdict(list)
    for b in d.get("bundles", []):
        s, t = b.get("sourceId"), b.get("targetId")
        if not s or not t:
            continue
        ln = (b.get("length") or {}).get("value", 0) or 0
        lbl = b.get("label") or b.get("id")
        g[s].append((t, ln, lbl))
        g[t].append((s, ln, lbl))
    return g

def route(g, a, b):
    """dijkstra on trunk segments -> (segment labels, total mm)"""
    if a == b or a not in g or b not in g:
        return ("", "")
    dist = {a: 0}
    prev = {}
    pq = [(0, a)]
    while pq:
        dcur, n = heapq.heappop(pq)
        if n == b:
            break
        if dcur > dist.get(n, 1e18):
            continue
        for m, ln, lbl in g[n]:
            nd = dcur + ln
            if nd < dist.get(m, 1e18):
                dist[m] = nd
                prev[m] = (n, lbl)
                heapq.heappush(pq, (nd, m))
    if b not in dist:
        return ("", "")
    segs, cur = [], b
    while cur != a:
        p, lbl = prev[cur]
        segs.append(lbl)
        cur = p
    return (" > ".join(reversed(segs)), int(dist[b]))

rows = []
for tag, fn in F:
    d = load(fn)
    ix, cav, g = node_index(d), cavity_info(d), bundle_graph(d)
    ccache = {}
    wparts = {q["id"]: q for k in d if k.endswith("Parts") for q in d[k]}
    cable_part = {cb["id"]: cb.get("partId") for cb in d.get("cables", [])}
    # WheelSpeed has no `wires` at all - every conductor is a cable core or a
    # cable shield - so a loop over `wires` alone dropped the whole loom off the
    # build list, and three A-engine shielded runs with it. Fixed 2026-09-22.
    conds = [(w, "") for w in d.get("wires", [])]
    for cb in d.get("cables", []):
        for co in cb.get("cores", []):
            conds.append((co, cb["id"]))
        if cb.get("shield"):
            conds.append((cb["shield"], cb["id"]))
    for w, cable in conds:
        rec = {"File": tag, "Wire": w["id"], "Cable": cable}
        for end, key in (("From","source"), ("To","target")):
            e = w.get(key) or {}
            nid, h = e.get("id",""), e.get("handle","")
            label, kind = ix.get(nid, (nid, "?"))
            desig, sig = cav.get((nid, h), ("", ""))
            rec[end] = label
            rec[end + " pin"] = (desig or h) if kind == "connector" else ""
            rec[end + " signal"] = sig
            rec[end + " kind"] = kind
            if kind == "connector":
                if (nid, h) not in ccache:
                    ccache[(nid, h)] = contact_for(d, nid, h)
                rec[end + " terminal"] = ccache[(nid, h)]
            else:
                rec[end + " terminal"] = ""
        col = w.get("color","")
        if w.get("stripeColor"):
            col += "/" + w["stripeColor"]
        rec["Colour"] = col
        # gauge comes from the wire's part (cable cores from the cable part)
        gp = wparts.get(w.get("partId")) or {}
        gg = (gp.get("gauge") or {})
        if not gg and cable:
            cp = wparts.get(cable_part.get(cable)) or {}
            gg = next(((k.get("gauge") or {}) for k in cp.get("cores", []) if k.get("gauge")), {})
        rec["AWG"] = ("%s" % gg.get("value", "")) + ("" if gg.get("unit", "AWG") == "AWG" else " mm2")
        segs, mm = route(g, (w.get("source") or {}).get("id"), (w.get("target") or {}).get("id"))
        rec["Route"] = segs
        rec["Est mm"] = mm
        rec["Splice"] = "; ".join(sorted({
            n for n in [(w.get("source") or {}).get("id"), (w.get("target") or {}).get("id")]
            if ix.get(n, ("",""))[1] == "splice"}))
        rec["Done"] = ""
        rows.append(rec)

COLS = ["File","Wire","Cable","From","From pin","From signal","From terminal",
        "To","To pin","To signal","To terminal",
        "Colour","AWG","Route","Est mm","Splice","Done"]

p = os.path.join(os.path.dirname(R), "HARNESS-BUILD-LIST.csv")
with open(p, "w", newline="", encoding="utf-8") as fh:
    wr = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore")
    wr.writeheader()
    for r in sorted(rows, key=lambda x: (x["File"], x["Wire"])):
        wr.writerow(r)

print("wrote", p)
print("wires:", len(rows), collections.Counter(r["File"] for r in rows))
print("no route found:", sum(1 for r in rows if r["Route"] == ""))
print("splice ends:", sum(1 for r in rows if r["Splice"]))
print("missing terminal PN (either end, connector ends only):",
      sum(1 for r in rows if (r["From kind"]=="connector" and not r["From terminal"])
                          or (r["To kind"]=="connector" and not r["To terminal"])))
