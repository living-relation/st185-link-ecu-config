#!/usr/bin/env python
"""Circuit tracer (OPEN-ITEMS row 117; DECISIONS "Parked rows (R102)" "Circuit tracer": Dan A53 a - A57 a and his
2026-11-15 scope). READ-ONLY: it reads the master wire list, sot/* and the fuse box wiring plan, and never edits them
(Dan A48 a). It traces the circuits WE created in the new harnesses and checks them against electrical principles. It
does not compare anything with the factory circuits: a factory part is only an end point our wire lands on (A57 a).

Step 1 (this file so far): the graph, the box join and the static chain of every load.

  graph   one node per connector pin, splice, bussed plug, stud or cable screen (check_wiring.Graph keys: the two
          bulkhead halves are one node); every wire is an edge. Body ground studs are one node (the body), the engine
          block lugs another.
  boxes   the insides of the POWER / LOGIC box and the trunk relay block come from cad/fusebox/rev8/wiring_plan.json
          (the box wires) and sot/fuse-relay-map.csv (which fuse and relay sits where): bars, fuses, relays.
  chain   for every load: source -> protection -> switching -> conductors -> load -> return, with every switch and
          relay contact taken as closed (the states come with the solver, step 2).

Checks in this step:
  B1  every master end at a box exists in the box plan, on the terminal the master names; every seated relay and
      assigned fuse of the seat map has its place in the plan
  C1  every master end is classified (hub, box, ECU pin, relay, switch, fuse, diode, resistor, ground, battery, load
      feed / return / signal, factory end); anything else is listed
  T1  closed loop: every load feed reaches a source and every load return reaches a ground (static)
  T2  no short: no rail reaches another rail or ground through conductors and switching alone
  F1  every load is fed by exactly one fuse (the nearest one; fuses further upstream are listed, A55 a); a fuse may
      feed several loads

    python docs/harness/tools/trace_circuits.py                 summary and findings (exit 0: SOFT, Dan A56 a)
    python docs/harness/tools/trace_circuits.py --chains        every static chain
    python docs/harness/tools/trace_circuits.py --chain K-FP    the chains of one device or harness
    python docs/harness/tools/trace_circuits.py --self-test     prove each check fires on a broken copy
"""
import collections
import copy
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_wiring as CW                                        # noqa: E402  read_csv, Graph, MATES, FB_IDS, BOX_RING
from build_drawings import is_removal, is_integral, RELAY_CODE, PIGTAIL_DEVICES  # noqa: E402  one definition each

SEATS = os.path.join(CW.REPO, "sot", "fuse-relay-map.csv")

# Facts the tracer needs before the rules file exists (step 2 moves them into trace_rules.json, each with its source).
BATTERY_POS = ("terminal", "BATT-POS")        # master: "Battery + post (trunk)"
BATTERY_NEG = ("terminal", "T-TRUNK-NEG")     # master: "Battery - post (trunk)"
BODY = re.compile(r"^GND-|^T-AT-GND$")        # body ground studs (check_wiring CHASSIS / BODY_GND; DECISIONS "Grounds (B10)")
BLOCK = re.compile(r"^T-ENG-BLOCK")           # the lugs on the engine block ground stud
HUBS = re.compile(r"^RADLOK-|^JUMP-POST$")    # pass-through plugs and the jump post: junctions, not loads
SWITCHES = {"KILL-SW": (("MAIN1", "MAIN2"), ("ALT1", "ALT2")),   # master pin names: battery kill switch, two poles
            "REV-SW": (("2", "1"),)}                             # master: "+12 V (COM)" / "Switched +12 V (NO)"
INLINE_FUSES = {"F-PI": ("IN", "OUT")}                           # master: "RealDash Pi inline fuse 5 A"
BLOCK_FUSE = ("BATT +", "FP 40A")             # trunk relay block: BATT + -> fuse FP -> K-FP 30 (DECISIONS S1 a)

RETURN_RE = re.compile(r"\bground\b|\bgnd\b|\(-\)|\breturn\b|\bsink\b|\bcommon\b|motor -|battery -|to ground", re.I)
FEED_RE = re.compile(r"\+\s?(12|5|8) ?V|\+B\b|B\+|battery \+|\bfeed\b|supply|LED \+|motor \+|siren \+|IG excite|"
                     r"battery sense|solenoid S|\+12 V", re.I)


class Points(CW.Graph):
    """check_wiring's node keys (mated halves are one node), but a wire stays an edge and a stud is one node."""

    def __init__(self):
        self.parent = {}
        for a, b in CW.INTERNAL:
            self.join(("pin",) + a, ("pin",) + b)

    def key(self, r, s):
        t, i = r[s + "_type"], r[s + "_id"]
        if not i:
            return None
        if t == "terminal":
            if BODY.match(i):
                return ("body",)
            if BLOCK.match(i):
                return ("block",)
            return ("terminal", i)
        return CW.Graph.key(self, r, s)


class Comp:
    def __init__(self, cid, kind, t, label, **attr):
        self.id, self.kind, self.t, self.label, self.attr = cid, kind, t, label, attr

    def __repr__(self):
        return "<%s %s>" % (self.kind, self.id)


class Model:
    def __init__(self):
        self.g = Points()
        self.wires = []                                  # (wire id, point a, point b, master row or None)
        self.comps = []
        self.ends = collections.defaultdict(list)        # point -> [(row, side)]
        self.cls = {}                                    # (wire id, side) -> class
        self.names = {}                                  # point -> plain name
        self.findings = []
        self.unproven = []
        self.loads = []                                  # dict(dev, name, harness, feeds, returns)
        self.sources, self.sinks, self.endpoints = {}, {}, {}   # point -> (volts, name) / name / name
        self.drivers, self.factory_feeds, self.hubs = {}, {}, {}   # ECU outputs; factory feed ends; named bars and bodies

    def p(self, k):
        return self.g.find(k)

    def name(self, k):
        k = self.p(k)
        if k in self.names:
            return self.names[k]
        if k in self.ends:
            r, s = self.ends[k][0]
            return (r[s + "_id"] + " " + r[s + "_pin"]).strip()
        return " ".join(str(x) for x in k[1:]) or k[0]

    def find(self, code, harness, dev, text):
        self.findings.append({"code": code, "harness": harness, "device": dev, "text": text})


def read_seats(path=SEATS):
    return CW.read_csv(path)[1]


def bkey(e):
    """a box plan end -> its node"""
    if e["id"] == "pdb":
        return ("box", "POWER", "NEG bar" if e["cav"].startswith("NEG") else "+ bar")
    return ("box", e["id"], e["des"] or e["cav"])


def relay_id(plan_id):
    return plan_id.upper().replace("_", "-")


def build(rows, plan, seats, channels):
    M = Model()
    g = M.g
    live = [r for r in rows if r["wire_id"] and not is_removal(r)]
    M.rows = live
    box_relays = {s["master_id"] for s in seats if s["kind"] == "relay" and s["master_id"] and s["bank"] in ("B1", "B2", "B3")}

    def is_box(r, s):
        i = r[s + "_id"]
        return i in CW.FB_IDS or bool(CW.BOX_RING.match(i)) or i in box_relays
    M.is_box = is_box
    for r in live:
        a, b = g.key(r, "from"), g.key(r, "to")
        if not (a and b):
            M.find("T1", r["harness"], r["wire_id"], "wire %s has only one end in the master" % r["wire_id"])
            continue
        if is_integral(r) and "fuse" in r["wire_label"].lower():      # the MRBF block (Dan N61 a): an INTEGRAL link that is a fuse
            M.comps.append(Comp(r["wire_id"], "fuse", {"a": a, "b": b}, r["wire_label"] or "fuse " + r["wire_id"], harness=r["harness"]))
        else:
            M.wires.append((r["wire_id"], a, b, r))
    # ---- box join: the master end at a box is the box plan's end of the same wire
    pw = {w["wire"]: w for w in (plan or {}).get("wires", [])}
    plan_pts = set()
    for w in pw.values():
        inside = [e for e in w["ends"] if e.get("box")]
        plan_pts.update(bkey(e) for e in inside)
        if w["kind"] != "external" and len(inside) == 2:
            M.wires.append((w["wire"], bkey(inside[0]), bkey(inside[1]), None))
    for r in live:
        for s in ("from", "to"):
            if not is_box(r, s):
                continue
            w = pw.get(r["wire_id"])
            cand = [e for e in (w["ends"] if w else []) if e.get("box")]
            if len(cand) > 1:
                cand = [e for e in cand if e.get("des") == r[s + "_pin"]] or cand[:1]
            if not cand:
                M.find("B1", r["harness"], r[s + "_id"], "%s %s (wire %s) is not in the fuse box wiring plan" % (
                    r[s + "_id"], r[s + "_pin"], r["wire_id"]))
                continue
            e = cand[0]
            if r[s + "_id"] in box_relays and e.get("des") != r[s + "_pin"]:
                M.find("B1", r["harness"], r[s + "_id"], "wire %s lands on %s terminal %s in the master, %s in the box plan" % (
                    r["wire_id"], r[s + "_id"], r[s + "_pin"], e.get("des")))
            g.join(g.key(r, s), bkey(e))
    # ---- box parts: relays, fuses, bars
    rel = collections.defaultdict(dict)
    for w in pw.values():
        for e in w["ends"]:
            if e.get("box") and e["id"].startswith("k_"):
                rel[e["id"]][e["des"]] = bkey(e)
                M.names.setdefault(bkey(e), "%s %s" % (relay_id(e["id"]), e["des"]))
    for pid, t in sorted(rel.items()):
        M.comps.append(Comp(relay_id(pid), "relay", t, relay_id(pid), box=True))
    for s in seats:
        if s["kind"] == "relay" and s["status"] == "seated" and s["bank"] in ("B1", "B2", "B3") and s["master_id"].lower().replace("-", "_") not in rel:
            M.find("B1", "", s["master_id"], "relay %s is seated in sot/fuse-relay-map.csv (%s %s) but the box plan wires no terminal of it" % (
                s["master_id"], s["bank"], s["position"]))
    own_in = {(c["box"], c["cav"]) for c in (plan or {}).get("cavities", [])
              if c["kind"] == "fuse in" and c["source"] == "harness"}
    for s in seats:
        if s["kind"] != "fuse" or s["status"] != "assigned":
            continue
        pos, label = s["position"], "%s %s (%s)" % (s["bank"], s["position"], s["circuit"])
        if s["bank"] == "B1":
            a, b = ("box", "POWER", "+ bar"), ("box", "fb_power", pos)
        elif s["bank"] == "B2":
            a = ("box", "fb_logic", pos + " IN") if ("LOGIC", pos + " IN") in own_in else ("box", "fb_logic", pos.split("-")[0])
            b = ("box", "fb_logic", pos)
        else:
            continue
        if b not in plan_pts:
            M.find("B1", "", pos, "fuse %s is assigned in sot/fuse-relay-map.csv but the box plan has no wire on its output" % label)
        M.comps.append(Comp(label, "fuse", {"a": a, "b": b}, label, box=True))
        M.names.setdefault(b, "%s fuse out" % pos)
    if ("box", "fb_batt", BLOCK_FUSE[0]) in plan_pts:
        M.comps.append(Comp("B3 FP 40 A (trunk block)", "fuse", {"a": ("box", "fb_batt", BLOCK_FUSE[0]), "b": ("box", "fb_batt", BLOCK_FUSE[1])},
                            "B3 FP 40 A (trunk block)", box=True))
    # ---- parts outside the boxes: relays, switches, inline fuses, diodes, resistors
    pins = collections.defaultdict(dict)                # device id -> pin -> (row, side)
    for r in live:
        for s in ("from", "to"):
            if r[s + "_id"]:
                M.ends[g.key(r, s)].append((r, s))
                pins[r[s + "_id"]].setdefault(r[s + "_pin"], (r, s))
    M.pins = pins
    for i, ps in sorted(pins.items()):
        r0, s0 = next(iter(ps.values()))
        t, nm, h = r0[s0 + "_type"], r0[s0 + "_name"], r0["harness"]
        pt = {p: g.key(r, s) for p, (r, s) in ps.items()}
        if i.startswith(RELAY_CODE) and i not in box_relays:
            M.comps.append(Comp(i, "relay", pt, i, harness=h))
        elif i in SWITCHES:
            for a, b in SWITCHES[i]:
                if a in pt and b in pt:
                    M.comps.append(Comp("%s %s-%s" % (i, a, b), "switch", {"a": pt[a], "b": pt[b]}, "%s (%s)" % (nm, a), harness=h, dev=i))
        elif i in INLINE_FUSES:
            a, b = INLINE_FUSES[i]
            M.comps.append(Comp(i, "fuse", {"a": pt[a], "b": pt[b]}, nm, harness=h))
        elif t == "resistor":
            M.comps.append(Comp(i, "res", pt, nm, harness=h))
        elif (t == "diode" or "diode" in nm.lower()) and "LED" not in nm:
            an = next((p for p, (r, s) in ps.items() if "anode" in r[s + "_desc"].lower()), "1")
            ka = next((p for p in ps if p != an), None)
            if an in pt and ka:
                M.comps.append(Comp(i, "diode", {"a": pt[an], "k": pt[ka]}, nm, harness=h))
    for k, n in ((("box", "POWER", "+ bar"), "POWER box + bar"), (("box", "POWER", "NEG bar"), "POWER box NEG bar"),
                 (("box", "fb_logic", "BUS1"), "LOGIC Bus 1"), (("box", "fb_logic", "BUS2"), "LOGIC Bus 2"),
                 (("body",), "body ground"), (("block",), "engine block"), (BATTERY_POS, "battery +"), (BATTERY_NEG, "battery -")):
        M.names[M.p(k)] = M.hubs[M.p(k)] = n
    classify(M, channels)
    return M


def ecu_pins(channels):
    out = {}
    back = {v: k for k, v in CW.ECU.items()}
    for c in channels:
        if c["conn"] in back and c["pin"][1:].isdigit():
            out[("pin", back[c["conn"]], c["pin"][1:])] = c
    return out


def text_role(d):
    return "return" if RETURN_RE.search(d) else "feed" if FEED_RE.search(d) else "signal"


def classify(M, channels):
    """C1: a class for every master end; fills the sources, grounds, end points and loads of the static chains."""
    g, ecu = M.g, ecu_pins(channels)
    part = {}
    for c in M.comps:
        for k in c.t.values():
            part[M.p(k)] = c
    M.sources[M.p(BATTERY_POS)] = ("12", "battery +")
    M.sinks[M.p(BATTERY_NEG)] = "battery -"
    dev = collections.defaultdict(lambda: {"feeds": [], "returns": []})
    for r in M.rows:
        for s in ("from", "to"):
            t, i, p, d = r[s + "_type"], r[s + "_id"], r[s + "_pin"], r[s + "_desc"]
            if not i:
                continue
            raw = g.key(r, s)
            k = M.p(raw)
            c = ""
            if t == "splice":
                c = "hub.splice"
            elif t == "cable screen":
                c = "hub.screen"
            elif t == "connector" and i.startswith("BUS-"):
                c = "hub.bus"
            elif i in CW.MATES:
                c = "hub.bulkhead"
            elif HUBS.match(i):
                c = "hub.pass-through"
            elif i in CW.ECU:
                ch = ecu.get(raw)
                if not ch:
                    c = ""
                elif ch["class"] == "rail" and ch["type"] != "gnd":
                    c, M.sources[k] = "ecu.rail", (ch["type"][-2:-1], "ECU %s (%s %s)" % (ch["channel"], i, p))
                elif ch["class"] == "rail":
                    c, M.sinks[k] = "ecu.gndout", "ECU Gnd Out (%s %s)" % (i, p)
                elif ch["class"] == "power":
                    c = "ecu.power"
                    dev["ECU"]["feeds"].append((i[-1] + p, raw))
                elif ch["class"] == "ground":
                    c = "ecu.ground"
                    dev["ECU"]["returns"].append((i[-1] + p, raw))
                elif ch["class"] == "screen":
                    c = "ecu.screen"
                elif ch["dir"] == "out":
                    c, M.drivers[k] = "ecu.out", "ECU %s (%s %s, switched by the ECU)" % (ch["channel"], i, p)
                else:
                    c, M.endpoints[k] = "ecu.in", "ECU %s (%s %s)" % (ch["channel"], i, p)
            elif raw in (("body",), ("block",)):
                c = "ground." + raw[0]
            elif raw in (BATTERY_POS, BATTERY_NEG):
                c = "battery"
            elif M.is_box(r, s):
                c = "box"
            elif k in part and (i.startswith(RELAY_CODE) or i in SWITCHES or i in INLINE_FUSES or part[k].id == i):
                c = part[k].kind
            elif d:
                role = text_role(d)
                if t == "OEM" and i not in PIGTAIL_DEVICES:
                    # a factory plug or box: each pin is its own end point (A57 a); which way a feed runs comes with the rules file
                    c = "factory." + {"return": "sink", "feed": "feed", "signal": "signal"}[role]
                    if role == "return":
                        M.sinks[k] = "%s %s (factory ground or switch to ground: %s)" % (i, p, d)
                    elif role == "feed":
                        M.factory_feeds[k] = "%s %s (factory feed end: %s)" % (i, p, d)
                    M.endpoints[k] = "%s %s (%s)" % (i, p, d)
                else:
                    c = "load." + role
                    if role != "signal":
                        dev[i][role + "s"].append((p, raw))
                    M.endpoints[k] = "%s %s (%s)" % (i, p, d)
            M.cls[(r["wire_id"], s)] = c
            if not c:
                M.find("C1", r["harness"], i, "end %s %s of wire %s is not classified (no pin text, or an ECU pin sot/channels.csv does not list)" % (
                    i, p, r["wire_id"]))
    for c in M.comps:
        if c.kind in ("relay", "res"):
            for tn, k in c.t.items():
                if c.kind == "res" or tn in ("85", "86"):
                    M.endpoints.setdefault(M.p(k), "%s %s (%s)" % (c.id, tn, "relay coil" if c.kind == "relay" else "resistor"))
        if c.kind == "relay":
            if "86" in c.t and "85" in c.t:
                dev[c.id + " coil"] = {"feeds": [("86", c.t["86"])], "returns": [("85", c.t["85"])]}
            else:
                M.find("T1", c.attr.get("harness", ""), c.id, "relay %s: coil terminals 85 / 86 are not both wired (wired: %s)" % (
                    c.id, ", ".join(sorted(c.t))))
    for i, ps in M.pins.items():
        r0, s0 = next(iter(ps.values()))
        if r0[s0 + "_type"] == "diode" and "LED" in r0[s0 + "_name"] and "1" in ps and "2" in ps:
            dev[i] = {"feeds": [("1", g.key(*ps["1"]))], "returns": [("2", g.key(*ps["2"]))]}
    for i, d in sorted(dev.items()):
        if not (d["feeds"] or d["returns"]):
            continue
        base = i[:-5] if i.endswith(" coil") else i
        row, side = next(iter(M.pins[base].values())) if base in M.pins else (None, None)
        if not row:      # a box relay or the ECU: named by the first wire on it
            row, side = next(((r, s) for r in M.rows for s in ("from", "to") if r[s + "_id"] == base or (i == "ECU" and r[s + "_id"] == "ECU-A")),
                             (None, None))
        nm = "ECU" if i == "ECU" else (row[side + "_name"] if row else base)
        M.loads.append({"dev": i, "name": nm + (" (coil)" if i.endswith(" coil") else ""), "harness": row["harness"] if row else "",
                        "feeds": d["feeds"], "returns": d["returns"]})


# ------------------------------------------------------------------------------------------------ static chains
def adjacency(M, skip=()):
    """conductors and switching, every contact taken as closed; a diode only in its forward direction (a -> k)"""
    adj = collections.defaultdict(list)
    for wid, a, b, _r in M.wires:
        a, b = M.p(a), M.p(b)
        adj[a].append((b, wid, 0))
        adj[b].append((a, wid, 0))
    for c in M.comps:
        if c in skip:
            continue
        if c.kind in ("fuse", "switch"):
            pairs = [("a", "b", 0)]
        elif c.kind == "relay":
            pairs = [("30", "87", 0), ("30", "87a", 0)]
        elif c.kind == "diode":
            pairs = [("a", "k", 1)]
        else:
            continue
        for x, y, d in pairs:
            if x in c.t and y in c.t:
                a, b = M.p(c.t[x]), M.p(c.t[y])
                lab = "[%s]" % (c.label if c.kind != "relay" else "%s %s-%s" % (c.label, x, y))
                adj[a].append((b, lab, d))
                adj[b].append((a, lab, -d))
    return adj


def search(M, adj, start, targets, down=True):
    """the nearest target from start, along the current (down: a -> k) or against it (up);
    -> (target, [(label, node reached), ...] from start outward) or None"""
    start = M.p(start)
    seen, q = {start: None}, collections.deque([start])
    while q:
        k = q.popleft()
        if k in targets and k != start:
            path = []
            while seen[k]:
                path.append((seen[k][1], k))
                k = seen[k][0]
            return path[0][1], path[::-1]
        for nb, lab, d in adj[k]:
            if d and (d > 0) != down:
                continue
            if nb not in seen:
                seen[nb] = (k, lab)
                q.append(nb)
    return None


def reach_set(M, adj, start, down=True):
    start = M.p(start)
    seen, q = {start}, collections.deque([start])
    while q:
        k = q.popleft()
        for nb, _lab, d in adj[k]:
            if d and (d > 0) != down:
                continue
            if nb not in seen:
                seen.add(nb)
                q.append(nb)
    return seen


def hops(M, path, rev=False):
    """the trace line of a search path: wire ids and [parts], with the bars and ground bodies named on the way"""
    out = []
    order = range(len(path) - 1, -1, -1) if rev else range(len(path))
    for n in order:
        out.append(path[n][0])
        via = path[n - 1][1] if rev and n else (path[n][1] if not rev and n < len(path) - 1 else None)
        if via in M.hubs:
            out.append(M.hubs[via])
    return out


def chain(M, adj, fuses, load):
    """the static chain of one load: each feed up to a source, each return down to a ground"""
    res = {"load": load, "feeds": [], "returns": []}
    bat = M.p(BATTERY_POS)
    rails = {k for k, v in M.sources.items()}
    for p, k in load["feeds"]:
        k = M.p(k)
        ent = {"pin": p, "ok": False, "fuses": [], "class": ""}
        hit = search(M, adj, k, {bat}, down=False) or search(M, adj, k, rails | set(M.drivers), down=False) \
            or search(M, adj, k, set(M.factory_feeds), down=False)
        if k in rails or k in M.drivers or k in M.factory_feeds:
            hit = (k, [])
        if hit:
            src, path = hit
            ent.update(ok=True, source=(M.sources.get(src) or ("", M.drivers.get(src) or M.factory_feeds.get(src)))[1])
            ent["path"] = [ent["source"]] + hops(M, path, rev=True)
            if src == bat:
                dom = [f for f in fuses if bat not in reach_set(M, adjacency(M, skip=(f,)), k, down=False)]
                dist = {}
                for f in dom:
                    d = search(M, adj, k, {M.p(f.t["a"]), M.p(f.t["b"])}, down=False)
                    dist[f] = len(d[1]) if d else 999
                dom.sort(key=lambda f: dist[f])
                ent["fuses"] = [f.label for f in dom]
                if not dom:
                    ent["class"] = "unfused" if bat in reach_set(M, adjacency(M, skip=tuple(fuses)), k, down=False) else "parallel"
        else:
            ent["ends"] = sorted(M.endpoints[e] for e in (reach_set(M, adj, k, down=False) - {k}) & set(M.endpoints))[:3]
        res["feeds"].append(ent)
    for p, k in load["returns"]:
        k = M.p(k)
        ent = {"pin": p, "ok": False}
        hit = (k, []) if k in M.sinks or k in M.drivers else (
            search(M, adj, k, {M.p(BATTERY_NEG)}, down=True) or search(M, adj, k, set(M.sinks) | set(M.drivers), down=True))
        if hit:
            snk = M.sinks.get(hit[0]) or M.drivers[hit[0]]
            ent.update(ok=True, sink=snk, path=hops(M, hit[1]) + [snk])
        else:
            ent["ends"] = sorted(M.endpoints[e] for e in (reach_set(M, adj, k, down=True) - {k}) & set(M.endpoints))[:3]
        res["returns"].append(ent)
    return res


def pin(e):
    return ("pin " + e["pin"]) if e["pin"] else "its lead"


def chain_lines(M, c):
    L = c["load"]
    r = next((r for r in c["returns"] if r["ok"]), c["returns"][0] if c["returns"] else None)
    right = "(no return pin in the master)" if not r else (
        "%s -> %s" % (pin(r), " -> ".join(r["path"])) if r["ok"] else "%s -> OPEN, reaches no ground%s" % (
            pin(r), (" (ends on " + "; ".join(r["ends"]) + ")") if r.get("ends") else ""))
    out = []
    for f in c["feeds"] or [None]:
        left = "(no feed pin in the master)" if not f else (
            " -> ".join(f["path"]) + " -> " + pin(f) if f["ok"] else "OPEN, no source reaches %s%s" % (
                pin(f), (" (ends on " + "; ".join(f["ends"]) + ")") if f.get("ends") else ""))
        out.append("%s -> | %s | -> %s" % (left, L["dev"], right))
    return out


def analyse(M):
    adj = adjacency(M)
    fuses = [c for c in M.comps if c.kind == "fuse"]
    M.chains = []
    for L in M.loads:
        c = chain(M, adj, fuses, L)
        M.chains.append(c)
        h, d, nm = L["harness"], L["dev"], "%s (%s)" % (L["name"], L["dev"])
        for f in c["feeds"]:
            if not f["ok"] and f.get("ends"):
                M.unproven.append((h, d, "%s: feed %s ends on %s, not on a source the tracer knows yet (needs the rules file)" % (
                    nm, pin(f), "; ".join(f["ends"]))))
            elif not f["ok"]:
                M.find("T1", h, d, "%s: no source reaches its feed %s (open on the supply side)" % (nm, pin(f)))
            elif f["class"] == "unfused":
                M.find("F1", h, d, "%s: %s is reached from the battery with no fuse on the way" % (nm, pin(f)))
            elif f["class"] == "parallel":
                M.find("F1", h, d, "%s: %s is fed through more than one fuse in parallel (pulling one fuse leaves it fed)" % (nm, pin(f)))
        if not c["feeds"]:
            M.unproven.append((h, d, "%s: no feed pin in the master (its feed is on another plug or inside the part; needs the rules file)" % nm))
        if not c["returns"]:
            M.unproven.append((h, d, "%s: no return pin in the master (case ground, another plug or a factory return; needs the rules file)" % nm))
        elif not any(r["ok"] for r in c["returns"]):
            r = c["returns"][0]
            if r.get("ends"):
                M.unproven.append((h, d, "%s: return %s ends on %s, not on a ground the tracer knows yet (needs the rules file)" % (
                    nm, pin(r), "; ".join(r["ends"]))))
            else:
                M.find("T1", h, d, "%s: return %s reaches no ground (open on the return side)" % (nm, pin(r)))
    # T2: no rail reaches a ground or a rail of another voltage through conductors and switching alone
    grounds = set(M.sinks)
    seen = set()
    for src, (volt, sname) in sorted(M.sources.items(), key=lambda x: x[1]):
        others = grounds | {k for k, (v, _n) in M.sources.items() if v != volt}
        hit = search(M, adj, src, others, down=True)
        if hit and frozenset((src, hit[0])) not in seen:
            seen.add(frozenset((src, hit[0])))
            other = M.sources[hit[0]][1] if hit[0] in M.sources else M.sinks[hit[0]]
            M.find("T2", "", sname, "SHORT: %s reaches %s through %s with no load on the way" % (sname, other, " -> ".join(hops(M, hit[1]))))
    return M


def load_all():
    _h, rows = CW.read_csv(CW.MASTER)
    _c, channels = CW.read_csv(CW.CHANNELS)
    import json
    with open(CW.PLAN, encoding="utf-8") as f:
        plan = json.load(f)
    return rows, plan, read_seats(), channels


def run(rows, plan, seats, channels):
    return analyse(build(rows, plan, seats, channels))


def report(M, argv):
    cl = collections.Counter(c.split(".")[0] or "UNCLASSIFIED" for c in M.cls.values())
    print("trace_circuits: %d wires (+%d box wires), %d master ends: %s" % (
        sum(1 for w in M.wires if w[3]), sum(1 for w in M.wires if not w[3]), len(M.cls),
        ", ".join("%s %d" % kv for kv in sorted(cl.items()))))
    print("parts: " + ", ".join("%s %d" % kv for kv in sorted(collections.Counter(c.kind for c in M.comps).items())))
    ok = sum(1 for c in M.chains if c["feeds"] and c["returns"] and all(f["ok"] for f in c["feeds"]) and any(r["ok"] for r in c["returns"]))
    print("loads: %d, static chain closed: %d" % (len(M.chains), ok))
    fz = collections.Counter(f["fuses"][0] for c in M.chains for f in c["feeds"] if f.get("fuses"))
    print("fuses feeding loads: %d (a fuse may feed several loads, A55 a)" % len(fz))
    want = None
    if "--chain" in argv:
        want = argv[argv.index("--chain") + 1].lower()
    if "--chains" in argv or want:
        for c in M.chains:
            L = c["load"]
            if want and want not in (L["dev"].lower(), L["harness"].lower()) and not L["dev"].lower().startswith(want):
                continue
            for line in chain_lines(M, c):
                print("  [%s] %s" % (L["harness"], line))
            fz = sorted({x for f in c["feeds"] for x in f.get("fuses", [])[:1]})
            up = sorted({x for f in c["feeds"] for x in f.get("fuses", [])[1:]})
            if fz:
                print("      fuse: %s%s" % ("; ".join(fz), ("   upstream: " + "; ".join(up)) if up else ""))
    for h, d, t in M.unproven:
        print("NOT PROVEN [%s] %s" % (h, t))
    for f in M.findings:
        print("FINDING %s [%s] %s" % (f["code"], f["harness"], f["text"]))
    print("trace_circuits: %d finding(s), %d not proven (SOFT: never fails the build, Dan A56 a)" % (len(M.findings), len(M.unproven)))


def self_test():
    rows, plan, seats, channels = load_all()
    base = {(f["code"], f["text"]) for f in run(rows, plan, seats, channels).findings}
    cases = []

    def case(name, code, word, rs=None, pl=None):
        got = run(rs or rows, pl or plan, seats, channels).findings
        new = [f for f in got if (f["code"], f["text"]) not in base]
        cases.append((name, any(f["code"] == code and word in f["text"] for f in new)))

    def without(wire):
        return [r for r in rows if r["wire_id"] != wire]
    rs = copy.deepcopy(rows)
    r = next(r for r in rs if r["wire_id"] == "w_fpg")
    sd = "from" if r["to_id"] == "FUEL-PUMP" else "to"
    r.update({sd + "_type": "splice", sd + "_id": "SP-NOWHERE", sd + "_pin": "", sd + "_name": "a splice with one leg"})
    case("open: the fuel pump ground wire ends on a one-leg splice", "T1", "FUEL-PUMP", rs)
    case("open: the trunk relay block feed wire removed", "T1", "FUEL-PUMP", without("w_fp_feed"))
    rs = copy.deepcopy(rows)
    r = next(r for r in rs if r["wire_id"] == "w_fpump_r")
    sd = "to" if r["to_id"] == "FUEL-PUMP" else "from"
    r.update({sd + "_type": "terminal", sd + "_id": "GND-BL", sd + "_pin": "", sd + "_name": "Ground point BL", sd + "_desc": "Ground"})
    case("short: the fuel pump relay output landed on ground BL", "T2", "SHORT", rs)
    pl = copy.deepcopy(plan)
    pl["wires"] = [w for w in pl["wires"] if w["wire"] != "w_fpump_r"]
    case("missing box cavity: K-FP 87 gone from the box plan", "B1", "K-FP", pl=pl)
    pl = copy.deepcopy(plan)
    pl["wires"] = [w for w in pl["wires"] if w["wire"] != "w_hr_cp"]
    case("missing box wire: the HR fuse output has no wire in the box plan", "B1", "BUS1-3", pl=pl)
    rs = copy.deepcopy(rows)
    r = next(r for r in rs if r["wire_id"] == "w_fpg")
    sd = "to" if r["to_id"] == "FUEL-PUMP" else "from"
    r.update({sd + "_desc": ""})
    case("an end with no pin text is listed", "C1", "FUEL-PUMP", rs)
    # the acceptance chain: battery -> FP fuse -> K-FP -> pump -> ground
    M = run(rows, plan, seats, channels)
    c = next(c for c in M.chains if c["load"]["dev"] == "FUEL-PUMP")
    line = " ".join(chain_lines(M, c))
    cases.append(("RearFuel: battery -> FP fuse -> K-FP -> pump -> ground", all(
        x in line for x in ("battery +", "FP 40 A", "K-FP 30-87", "FUEL-PUMP", "battery -"))
        and line.index("battery +") < line.index("FP 40 A") < line.index("K-FP 30-87") < line.index("FUEL-PUMP") < line.index("battery -")))
    bad = [n for n, ok in cases if not ok]
    for n, ok in cases:
        print("%-5s %s" % ("ok" if ok else "FAIL", n))
    print("%d self-test failure(s)." % len(bad))
    return 1 if bad else 0


def main(argv):
    if "--self-test" in argv:
        return self_test()
    M = run(*load_all())
    report(M, argv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
