import json, os, csv, collections, heapq

import model

R = model.REB
READ = [model.REGISTRY]
# Every harness in interfaces.json. Hardcoded file lists went stale twice (the
# 2026-09-22 repoint, then the wheel-speed split), so the registry is the list.
F = tuple(model.harness_files().items())

def load(fn):
    path = os.path.join(R, fn)
    READ.append(path)
    return json.load(open(path, encoding="utf-8"))

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

REG = model.registry()
IX = {(h["harness"], h["connector"]): (ix["id"], [o["harness"] for o in ix["halves"] if o is not h][0])
      for ix in REG.get("interfaces", []) for h in ix["halves"]}
FL = {(f["harness"], f["terminal"]): f["ewd"] for f in REG.get("flyingLeads", [])}
EP = {(e["harness"], t): e["id"] for e in REG.get("endpoints", []) for t in e["terminals"].values()}
REF = {(x["harness"], x["connector"]): x["realOn"] for x in REG.get("references", [])}
BH = {"bh_a_fw": "bulkhead A (mates engine half)", "bh_a_eng": "bulkhead A (mates cabin half)",
      "bh_b_fw": "bulkhead B (mates engine half)", "bh_b_eng": "bulkhead B (mates cabin half)"}


def classify(tag, nid, kind):
    """(endpoint type, handoff text, EWD locator) for one conductor end."""
    if (tag, nid) in IX:
        i, other = IX[(tag, nid)]
        return "inline_interface", "%s -> %s" % (i, other), ""
    if (tag, nid) in FL:
        e = FL[(tag, nid)]
        return "oem_flying_lead", "", "EWD %s %s-%s %s" % (e["page"], e["connector"], e["pin"], e["color"])
    if (tag, nid) in EP:
        return "device_endpoint", EP[(tag, nid)], ""
    if (tag, nid) in REF:
        return "reference_only", "cavity on %s" % REF[(tag, nid)], ""
    if nid in BH:
        return "real_connector", BH[nid], ""
    if kind == "connector":
        return "real_connector", "", ""
    return kind.split("(")[0], "", ""


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
            rec[end + " type"], hand, ewd = classify(tag, nid, kind)
            rec.setdefault("Handoff", [])
            rec.setdefault("EWD", [])
            if hand:
                rec["Handoff"].append(hand)
            if ewd:
                rec["EWD"].append(ewd)
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
        rec["Part"] = gp.get("partNumber") or ""
        gg = (gp.get("gauge") or {})
        if not gg and cable:
            cp = wparts.get(cable_part.get(cable)) or {}
            gg = next(((k.get("gauge") or {}) for k in cp.get("cores", []) if k.get("gauge")), {})
            if not rec["Part"]:
                rec["Part"] = cp.get("partNumber") or ""
        rec["AWG"] = ("%s" % gg.get("value", "")) + ("" if gg.get("unit", "AWG") == "AWG" else " mm2")
        segs, mm = route(g, (w.get("source") or {}).get("id"), (w.get("target") or {}).get("id"))
        rec["Route"] = segs
        rec["Est mm"] = mm
        rec["Splice"] = "; ".join(sorted({
            n for n in [(w.get("source") or {}).get("id"), (w.get("target") or {}).get("id")]
            if ix.get(n, ("",""))[1] == "splice"}))
        rec["Owner"] = tag
        rec["Handoff"] = "; ".join(rec["Handoff"])
        rec["EWD"] = "; ".join(rec["EWD"])
        rec["Done"] = ""
        rows.append(rec)

COLS = ["File","Owner","Wire","Cable","From","From type","From pin","From signal","From terminal",
        "To","To type","To pin","To signal","To terminal",
        "Colour","AWG","Part","Route","Est mm","Splice","Handoff","EWD","Done"]

DIGEST = model.files_sha256(READ)
p = os.path.join(os.path.dirname(R), "HARNESS-BUILD-LIST.csv")
with open(p, "w", newline="", encoding="utf-8") as fh:
    fh.write("# Generated from SHA-256 %s of the files actually read\n" % DIGEST)
    wr = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore")
    wr.writeheader()
    for r in sorted(rows, key=lambda x: (x["File"], x["Wire"])):
        wr.writerow(r)

print("wrote", p)
print("wires:", len(rows), collections.Counter(r["File"] for r in rows))
print("no route found:", sum(1 for r in rows if r["Route"] == "" and not r["Handoff"]),
      "(plus %d deliberate handoffs)" % sum(1 for r in rows if r["Route"] == "" and r["Handoff"]))
print("splice ends:", sum(1 for r in rows if r["Splice"]))
print("missing terminal PN (either end, connector ends only):",
      sum(1 for r in rows if (r["From kind"]=="connector" and not r["From terminal"])
                          or (r["To kind"]=="connector" and not r["To terminal"])))
