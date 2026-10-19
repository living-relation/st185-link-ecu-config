"""Assign the DRB102 bulkhead cavities (DECISIONS R208; Dan, 2026-10-19).

    python docs/harness/cleanroom/bulkhead_assign.py            # dry run: the new map and a before / after table
    python docs/harness/cleanroom/bulkhead_assign.py --apply    # write the wire lists, the four bulkhead drawings, the
                                                                 # cavity map; then run build_harness.py on the files

Dan's method: "imagine there is no bulkhead connector and the wires just go straight through in one piece to the
engine bay as if it was a pass through grommet. and then once everything is lined up and finished cut the wires right
at the bulkhead and insert whatever bulkhead connector you want." So:

  1. every engine <-> cabin circuit is ONE continuous wire (its cabin row and its engine row share the cavity number);
  2. the wires are grouped by DEVICE (the device the engine end reaches, a rail pin joins the nearest device it feeds),
     the devices in route order (shortest bundle distance from the bulkhead in the engine drawing), inside a device:
     supply, signal, return, then its own shield pin;
  3. only then are they "cut" at the bulkhead: each device gets a contiguous run of cavities in one column of the
     connector (columns of the TE drawing: DRB102-CAVITY-MAP.md); a device that needs a column's worth more than is left
     starts the next column. Both halves keep the same cavity number, so cabin and engine always agree.

Hard limits (the script checks every one and stops on a failure):
  - the cavity's contact size takes the wire: size 16 = 16-20 AWG, 13 A; size 12 = 12-14 AWG, 25 A (size 8 / 4 cavities
    stay spare); a wire thinner than 16 AWG (14 / 12) needs a size 12 cavity, and a wire keeps its contact size class
    (so its current rating is the one it had before);
  - an ECU loom's wires stay on that loom's drawn bulkhead connector (bh_a_* = loom A, bh_b_* = loom B, the ECU letter rule
    on loom OWNERSHIP, DECISIONS R1); only the cavity placement ignores A / B (Dan: "it is technically a signal
    connector on the bulkhead you don't even have to organize it by A and B sections").
"""
import argparse
import collections
import csv
import heapq
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, HARNESS)
import model  # noqa: E402
import wirelist as WL  # noqa: E402

BH = {"bh_a_fw": "A", "bh_a_eng": "A", "bh_b_fw": "B", "bh_b_eng": "B"}
CABIN = {"A": "bh_a_fw", "B": "bh_b_fw"}
ENGINE = {"A": "bh_a_eng", "B": "bh_b_eng"}
LOOM_FILES = {"A": ("A-cabin", "A-engine"), "B": ("B-cabin", "B-engine")}
MAP_MD = os.path.join(HARNESS, "DRB102-CAVITY-MAP.md")
FULL_TEXT = os.path.join(HARNESS, "full_text.json")

# TE customer drawing DRB12-102PXE-L018 rev C3: sizes and the 12 columns (cavity numbers top to bottom)
SIZE = {n: 16 for n in range(1, 103)}
SIZE.update({n: 12 for n in list(range(1, 9)) + list(range(95, 103))})
SIZE.update({48: 8, 49: 8, 54: 8, 55: 8, 43: 4, 60: 4})
COLUMNS = {1: range(102, 94, -1), 2: range(94, 82, -1), 3: range(82, 70, -1), 4: [70, 69, 68, 67, 66, 65, 64, 63],
           5: [62, 61, 60, 59, 58], 6: [57, 56, 55, 54, 53, 52], 7: [51, 50, 49, 48, 47, 46], 8: [45, 44, 43, 42, 41],
           9: [40, 39, 38, 37, 36, 35, 34, 33], 10: range(32, 20, -1), 11: range(20, 8, -1), 12: range(8, 0, -1)}
WEDGE = lambda n: "left (52-102)" if n >= 52 else "right (1-51)"  # noqa: E731
RATING = {16: ("16-20 AWG", 13), 12: ("12-14 AWG", 25), 8: ("8-10 AWG", None), 4: ("6 AWG", None)}
CONTACT = {("fw", 16): "ct_hdp16p", ("fw", 12): "ct_hdp12p", ("eng", 16): "ct_hdp16s", ("eng", 12): "ct_hdp12s"}
# a rail pin whose engine end is an inline plug: the device it really feeds (the inline mates a sensor in B-engine)
DESC_DEVICE = {"+5 V oil pressure": "oilp", "+5 V fuel pressure": "fuelp", "+5 V coolant press": "clntp"}
# devices whose members are one device: injectors, coils
MERGE = (("inj", re.compile(r"^inj\d+$")), ("cop", re.compile(r"^cop\d+$")))


def read_all():
    return {h: WL.read_rows(h) for h in model.harness_files() if os.path.exists(WL.csv_path(h))}


def gauge(r):
    return int(r["gauge_awg"]) if r["gauge_awg"].strip().isdigit() else None


def role(desc, wire_id=""):
    t = desc.lower()
    if "shield" in t or "screen" in t:
        return 3
    if re.search(r"gnd|ground", t):
        return 2
    if re.search(r"\+\s?\d+ ?v|feed|power|supply|12 ?v in|vcc", t) and "signal" not in t and "coil" not in t:
        return 0
    return 1


def distances():
    """device connector id -> shortest bundle distance from its bulkhead plug in the engine drawing it is drawn on."""
    out = {}
    for h, root in (("A-engine", "bh_a_eng"), ("B-engine", "bh_b_eng")):
        d = json.load(open(os.path.join(HARNESS, "rebuild", model.harness_files()[h]), encoding="utf-8"))
        adj = collections.defaultdict(list)
        for b in d["bundles"]:
            n = (b.get("length") or {}).get("value") or 0
            adj[b["sourceId"]].append((b["targetId"], n))
            adj[b["targetId"]].append((b["sourceId"], n))
        dist, pq = {root: 0}, [(0, root)]
        while pq:
            dd, u = heapq.heappop(pq)
            if dd > dist.get(u, 1e18):
                continue
            for v, n in adj[u]:
                if dd + n < dist.get(v, 1e18):
                    dist[v] = dd + n
                    heapq.heappush(pq, (dd + n, v))
        for k in ("connectors", "terminals", "splices"):
            for x in d.get(k, []):
                loc = x["id"] if x["id"] in dist else x.get("locationId")
                if loc in dist:
                    out.setdefault(x["id"], dist[loc])
    return out


def collect(lists):
    """pin -> dict(loom, cab=[rows], eng=[rows]) from every wired bulkhead end; spare pins -> loom."""
    pins, spare = {}, {}
    for h, rs in lists.items():
        for r in rs:
            for s in ("from", "to"):
                if r[s + "_type"] == "connector" and r[s + "_conn"] in BH:
                    n, conn = int(r[s + "_pin"]), r[s + "_conn"]
                    if r["wire_id"]:
                        p = pins.setdefault(n, {"loom": BH[conn], "cab": [], "eng": []})
                        p["cab" if conn.endswith("fw") else "eng"].append((h, r, s))
                    else:
                        spare[n] = BH[conn]
    return pins, spare


def far_devices(lists, h, r, s):
    """The device connector ids an engine row reaches from its bulkhead end, through splices."""
    o = "to" if s == "from" else "from"
    out, seen, todo = set(), set(), [(r[o + "_type"], r[o + "_conn"])]
    allrows = [x for rs in lists.values() for x in rs if x["wire_id"]]
    if r["colour"] == "Shield" and r["cable"]:      # a shield pin goes with the device its cable carries
        for x in allrows:
            if x["cable"] == r["cable"] and x["colour"] != "Shield":
                for e in ("from", "to"):
                    if x[e + "_type"] == "connector" and x[e + "_conn"] not in BH and not x[e + "_conn"].startswith("ecu_"):
                        out.add(x[e + "_conn"])
        if not out:      # the cores end on a splice (the CAN-Lambda pair): follow them to the device
            for x in allrows:
                if x["cable"] == r["cable"] and x["colour"] != "Shield":
                    for e in ("from", "to"):
                        if x[e + "_type"] == "connector" and x[e + "_conn"] in BH:
                            out |= far_devices(lists, h, x, e)
        if out:
            return out
    while todo:
        t, c = todo.pop()
        if t == "splice":
            if c in seen:
                continue
            seen.add(c)
            for x in allrows:
                for e in ("from", "to"):
                    if x[e + "_type"] == "splice" and x[e + "_conn"] == c:
                        o2 = "to" if e == "from" else "from"
                        if not (x[o2 + "_type"] == "connector" and x[o2 + "_conn"] in BH):
                            todo.append((x[o2 + "_type"], x[o2 + "_conn"]))
        elif t in ("connector", "terminal", "OEM") and c not in BH:
            out.add(c)
    return out


def group_key(dev):
    for k, rx in MERGE:
        if rx.match(dev):
            return k
    return dev


def plan(lists):
    pins, spare = collect(lists)
    dist = distances()
    items = []
    for n, p in sorted(pins.items()):
        eng = p["eng"]
        h, r, s = eng[0] if eng else p["cab"][0]
        desc = r[s + "_desc"]
        devs = far_devices(lists, h, r, s) if eng else set()
        dev = DESC_DEVICE.get(desc)
        if dev is None:
            cand = sorted(devs, key=lambda c: (dist.get(c, 1e9), c))
            dev = cand[0] if cand else "pin%d" % n
        key = group_key(dev)
        gs = [g for _, rr, _ in p["cab"] + p["eng"] for g in [gauge(rr)] if g]
        cls = 12 if gs and min(gs) < 16 else 16
        items.append({"old": n, "loom": p["loom"], "desc": desc, "dev": key, "role": role(desc), "cls": cls,
                      "gauges": sorted(set(gs)), "dist": min([dist.get(x, 1e9) for x in (devs | {dev})] or [1e9])})
    groups = collections.defaultdict(list)
    for it in items:
        groups[it["dev"]].append(it)
    for g in groups.values():
        g.sort(key=lambda i: (i["role"], i["old"]))
    order = sorted(groups, key=lambda k: (min(i["dist"] for i in groups[k]), k))
    free16 = [[n for n in col if SIZE[n] == 16] for c, col in COLUMNS.items() if c not in (1, 12)]
    free16 = free16[::-1]               # fill from the low-numbered column (cavity 9) up; inside a column, low number first
    free16 = [sorted(col) for col in free16]
    ends = {1: sorted(COLUMNS[1]), 12: sorted(COLUMNS[12])}
    col_i, used_in_col = 0, 0
    new = {}
    for k in order:
        g16 = [i for i in groups[k] if i["cls"] == 16]
        g12 = [i for i in groups[k] if i["cls"] == 12]
        if g16:
            while col_i < len(free16) and len(free16[col_i]) - used_in_col < len(g16) and len(g16) <= len(free16[col_i]):
                col_i, used_in_col = col_i + 1, 0     # does not fit what is left of the column: next column
            col0 = col_i
            for it in g16:
                while used_in_col >= len(free16[col_i]):
                    col_i, used_in_col = col_i + 1, 0
                new[it["old"]] = free16[col_i][used_in_col]
                used_in_col += 1
            where = col0
        else:
            where = col_i
        for it in g12:                 # the size 12 feeds sit in the end column next to the device's own column
            end = 12 if where < 6 else 1
            new[it["old"]] = ends[end].pop(0)
    return pins, spare, items, new, order, groups


def check(items, new):
    bad = []
    if len(set(new.values())) != len(new):
        bad.append("two circuits share a cavity")
    for it in items:
        n = new[it["old"]]
        if SIZE[n] != it["cls"]:
            bad.append("%s: wire %s AWG needs a size %d cavity, cavity %d is size %d" % (it["desc"], it["gauges"], it["cls"], n, SIZE[n]))
        rng = {16: (16, 20), 12: (12, 14)}[SIZE[n]]
        for g in it["gauges"]:
            if not rng[0] <= g <= rng[1]:
                bad.append("%s: %d AWG is outside the size %d contact range %s" % (it["desc"], g, SIZE[n], rng))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    lists = read_all()
    pins, spare, items, new, order, groups = plan(lists)
    bad = check(items, new)
    owner = {new[i["old"]]: i["loom"] for i in items}
    print("%-14s %-30s %s" % ("device", "old cavities", "-> new cavities"))
    for k in order:
        g = groups[k]
        print("%-14s %-30s -> %s" % (k, ", ".join(str(i["old"]) for i in g), ", ".join(str(new[i["old"]]) for i in g)))
    for b in bad:
        print("LIMIT FAILED:", b)
    by_cls = collections.Counter(i["cls"] for i in items)
    print("wired cavities: %d (size 16: %d, size 12: %d); spare %d" % (len(items), by_cls[16], by_cls[12], 102 - len(items)))
    if bad:
        raise SystemExit(1)
    if not a.apply:
        return 0
    apply(lists, pins, items, new, owner)
    return 0


def old_section_map():
    """(letter, 'cN') -> old DRB number, from the map being replaced (for the text references)."""
    out = {}
    if os.path.exists(MAP_MD):
        for line in open(MAP_MD, encoding="utf-8"):
            m = re.match(r"\| (\d+) \| [^|]+\| (\d+) \| ([AB]) \| (c\d+) \|", line)
            if m:
                out[(m.group(3), m.group(4))] = int(m.group(1))
    return out


def remap_text(s, new, secmap):
    """Old pin / section-cavity references in a text -> the new cavity number."""
    def sec(m):
        old = secmap.get((m.group(1).upper(), m.group(2)))
        return "bulkhead pin %d" % new[old] if old in new else m.group(0)
    s = re.sub(r"bulkhead ([AB]) (c\d+)", sec, s)
    s = re.sub(r"(DRB102 pin |bulkhead [AB] pin |BH-[AB] pin )(\d+)", lambda m: m.group(1) + str(new.get(int(m.group(2)), int(m.group(2)))), s)
    return s


def apply(lists, pins, items, new, owner):
    secmap = old_section_map()
    desc_of = {new[i["old"]]: i["desc"] for i in items}
    # 1. wire lists: pins on every bulkhead end, spare rows regenerated
    names = {}
    for h, rs in lists.items():
        out = []
        for r in rs:
            hit = [s for s in ("from", "to") if r[s + "_type"] == "connector" and r[s + "_conn"] in BH]
            if hit and not r["wire_id"]:
                names.setdefault(r["from_conn"], r["from_conn_name"])
                continue                                    # a spare row: regenerated below
            for s in hit:
                r[s + "_pin"] = str(new[int(r[s + "_pin"])])
            out.append(r)
        lists[h] = out
    wired = set(new.values())
    for loom, (cab, eng) in LOOM_FILES.items():
        for h, conn in ((cab, CABIN[loom]), (eng, ENGINE[loom])):
            for n in sorted(range(1, 103)):
                if n in wired or spare_owner(n, owner) != loom:
                    continue
                row = {c: "" for c in WL.COLUMNS}
                row.update(harness=h, from_type="connector", from_conn=conn, from_conn_name=names.get(conn, conn),
                           from_pin=str(n), from_desc="spare, sealing plug")
                lists[h].append(row)
    for h, rs in lists.items():
        WL.write_rows(h, rs)
    # 2. drawings: the four bulkhead connectors, whole, in every file that draws one
    lib = json.load(open(os.path.join(HARNESS, "rebuild", "ST185.harnesslib"), encoding="utf-8"))
    for h, fn in model.harness_files().items():
        path = os.path.join(HARNESS, "rebuild", fn)
        d = json.load(open(path, encoding="utf-8"))
        touched = False
        for c in d.get("connectors", []):
            if c["id"] not in BH:
                continue
            loom, side = BH[c["id"]], ("fw" if c["id"].endswith("fw") else "eng")
            cavs = []
            for n in range(1, 103):
                sp = spare_owner(n, owner)
                if n in wired and owner[n] == loom:
                    cavs.append({"id": "c%d" % n, "designation": str(n), "signal": desc_of[n],
                                 "contactPartId": CONTACT[(side, SIZE[n])], "propagate": False})
                elif n not in wired and sp == loom:
                    cavs.append({"id": "c%d" % n, "designation": str(n), "cavityPlugPartId": "pl_sz%d" % SIZE[n], "notConnected": True})
                else:
                    cavs.append({"id": "nc%d" % n, "designation": str(n), "notConnected": True, "cavityPlugPartId": None})
            c["cavities"] = cavs
            touched = True
            for kind, ids in (("contactParts", {CONTACT[(side, k)] for k in (16, 12)}),
                              ("cavityPlugParts", {"pl_sz%d" % k for k in (16, 12, 8, 4)})):
                have = {p["id"] for p in d.get(kind, [])}
                libp = {p["id"]: p for p in lib.get(kind, [])}
                for i in sorted(ids - have):
                    if i in libp:
                        d.setdefault(kind, []).append(json.loads(json.dumps(libp[i])))
        if touched:
            # the cavities moved, so the old routing points (R202: none unless they square a diagonal) of the wires that end
            # on a bulkhead cavity mean nothing now: the app routes them
            bh_ids = {c["id"] for c in d["connectors"] if c["id"] in BH}
            for w, cable, scr in model.conductors(d):
                for k in ("source", "target"):
                    e = w.get(k)
                    if e and e.get("id") in bh_ids:
                        w.pop({"source": "sourceLayoutPoints", "target": "targetLayoutPoints"}[k], None) if cable else w.pop("layoutPoints", None)
            # parts the connector no longer uses go (R44)
            used = {cv.get(k) for c in d["connectors"] for cv in c["cavities"] for k in ("contactPartId", "cavityPlugPartId")}
            if "cavityPlugParts" in d:
                d["cavityPlugParts"] = [x for x in d["cavityPlugParts"] if x["id"] not in ("pl_sz16", "pl_sz12", "pl_sz8", "pl_sz4") or x["id"] in used]
            # a contact part another connector's configuration names stays defined (the library is the master, R39)
            raw_d = json.dumps(d)
            libc = {p["id"]: p for p in lib.get("contactParts", [])}
            have = {p["id"] for p in d.get("contactParts", [])}
            for i in ("ct_hdp16p", "ct_hdp16s", "ct_hdp12p", "ct_hdp12s"):
                if i not in have and ('"%s"' % i) in raw_d and i in libc:
                    d.setdefault("contactParts", []).append(json.loads(json.dumps(libc[i])))
        text = json.dumps(d, indent=2, ensure_ascii=False) + "\n"
        text = remap_text_in_json(text, new, secmap)
        eol = "\r\n" if b"\r\n" in open(path, "rb").read(4096) else "\n"
        open(path, "w", encoding="utf-8", newline="").write(text.replace("\n", eol))
    # 3. the other places that say a bulkhead pin: the long texts, the registry, the specs, the SoT notes
    ft = json.load(open(FULL_TEXT, encoding="utf-8"))
    for rec in ft.values():
        for cid in list(rec.get("connectors", {})):
            if cid in BH:
                rec["connectors"][cid] = {"cavities": {}}
    raw = json.dumps(ft, indent=1, ensure_ascii=False) + "\n"
    open(FULL_TEXT, "w", encoding="utf-8", newline="").write(remap_text(raw, new, secmap))
    for p in (os.path.join(HARNESS, "interfaces.json"), os.path.join(os.path.dirname(os.path.dirname(HARNESS)), "sot", "channels.csv")):
        s = open(p, encoding="utf-8", newline="").read()
        open(p, "w", encoding="utf-8", newline="").write(remap_text(s, new, secmap))
    for p in [os.path.join(HERE, "specs", f) for f in os.listdir(os.path.join(HERE, "specs"))]:
        s = open(p, encoding="utf-8", newline="").read()
        open(p, "w", encoding="utf-8", newline="").write(remap_text(s, new, secmap))
    write_map(lists, items, new, owner)
    print("applied: lists, 4 drawings, full_text.json, registry, specs, cavity map; now run build_harness.py on the files that touch a bulkhead")


def remap_text_in_json(text, new, secmap):
    return remap_text(text, new, secmap)


def spare_owner(n, owner):
    """A spare cavity belongs to the loom of the nearest lower wired cavity (the nearest higher for the first ones)."""
    lo = [m for m in owner if m < n]
    hi = [m for m in owner if m > n]
    return owner[max(lo)] if lo else owner[min(hi)]


def write_map(lists, items, new, owner):
    """DRB102-CAVITY-MAP.md: the physical facts (TE drawing) are fixed text, the allocation is read from the wire lists."""
    use = {}
    for h, rs in lists.items():
        for r in rs:
            for s in ("from", "to"):
                if r["wire_id"] and r[s + "_type"] == "connector" and r[s + "_conn"] in BH and BH[r[s + "_conn"]]:
                    o = "to" if s == "from" else "from"
                    far = r[o + "_conn"]
                    nm = r[o + "_conn_name"]
                    n = int(r[s + "_pin"])
                    if r[o + "_type"] == "connector" and far in ("ecu_a", "ecu_b"):
                        use[n] = ("ECU-%s %s" % (far[-1].upper(), r[o + "_pin"]), BH[r[s + "_conn"]])
                    else:
                        use.setdefault(n, (r[s + "_desc"], BH[r[s + "_conn"]]))
    head = open(MAP_MD, encoding="utf-8").read().split("\n## Allocation")[0] if os.path.exists(MAP_MD) else ""
    old_sentence = ('"A" and "B" are only our names for its two sections, set by\n'
                    'ECU connector letter (Rule 3); each drawing wires its own section and marks the other\n'
                    'section\'s cavities N/C ("see ST185-<other>"). This file says which section owns each cavity.')
    new_sentence = ('"A" and "B" in the connector ids are the ECU loom whose file draws and\n'
                    'wires the cavity (the ECU letter rule, R1); they are NOT cavity sections (R208): each drawing wires its own\n'
                    'loom\'s cavities, whichever they are, and marks the other loom\'s cavities N/C ("see ST185-<other>").\n'
                    'This file says which loom owns each cavity.')
    head = head.replace(old_sentence, new_sentence)
    out = [head.rstrip("\n"), "",
           "## Allocation (generated - do not edit)", "",
           "This table is GENERATED by `docs/harness/cleanroom/bulkhead_assign.py` from the wire lists, which are the wiring SoT "
           "(DECISIONS R206): re-run it whenever a circuit through the bulkhead changes. Method (R208, Dan): treat every engine / cabin "
           "circuit as one continuous wire, group the wires by device in route order (supply, signal, return, the device's own shield pin), "
           "then cut them at the bulkhead into a contiguous run of cavities per device. Both halves use the same cavity number. There are "
           "no A / B sections: the Loom column says which ECU loom's file owns the wire (the ECU letter rule, R1); the cavity placement "
           "ignores it. Contact sizes from the TE drawing: size 16 = 16-20 AWG, 13 A; size 12 = 12-14 AWG, 25 A; size 8 / 4 are spare.", "",
           "| DRB | Wedgelock | Size | Loom | Cavity id | Use |", "|---|---|---|---|---|---|"]
    for n in range(1, 103):
        if n in new.values():
            u, loom = use.get(n, ("", owner[n]))
            out.append("| %d | %s | %d | %s | c%d | %s |" % (n, WEDGE(n), SIZE[n], owner[n], n, u))
        else:
            out.append("| %d | %s | %d | %s | c%d | spare (size %d) |" % (n, WEDGE(n), SIZE[n], spare_owner(n, owner), n, SIZE[n]))
    spare = collections.Counter(SIZE[n] for n in range(1, 103) if n not in new.values())
    out += ["", "## Spare capacity", "", "| Size | Spare cavities |", "|---|---|"]
    for sz in (16, 12, 8, 4):
        out.append("| %d | %d (%s) |" % (sz, spare[sz], ", ".join(str(n) for n in range(1, 103) if SIZE[n] == sz and n not in new.values())))
    out += ["", "## Sealing plugs", "",
            "Size 16 `114017` (to buy), size 12 `0413-214-1205`, size 8 `114018-ZZ`, size 4 `114019-ZZ`, all Deutsch; the last three are owned "
            "(`docs/sourcing/te-on-hand-bom.csv`). Test-fit one plug of each size in the physical housing before buying more (`docs/OPEN-ITEMS.md`).", ""]
    open(MAP_MD, "w", encoding="utf-8", newline="").write("\n".join(out))


if __name__ == "__main__":
    sys.exit(main())
