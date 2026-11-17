#!/usr/bin/env python
"""Circuit tracer (OPEN-ITEMS row 117; DECISIONS "Parked rows (R102)" "Circuit tracer": Dan A53 a - A57 a and his
2026-11-15 scope). READ-ONLY: it reads the master wire list, sot/*, the fuse box wiring plan, circuit-plan.md and its
own rules file, and never edits them (Dan A48 a). It traces the circuits WE created in the new harnesses and checks
them against electrical principles. It does not compare anything with the factory circuits: a factory part is only an
end point our wire lands on - a source, a ground, a switch or a load (A57 a).

  graph   one node per connector pin, splice, bussed plug, stud or cable screen (check_wiring.Graph keys: the two
          bulkhead halves are one node); every wire is an edge. Body ground studs are one node (the body), the engine
          block lugs another.
  boxes   the insides of the POWER / LOGIC box and the trunk relay block come from cad/fusebox/rev8/wiring_plan.json
          (the box wires) and sot/fuse-relay-map.csv (which fuse and relay sits where): bars, fuses, relays.
  rules   docs/harness/tools/trace_rules.json (A54 a): what the master cannot say - what each part IS (switch, relay,
          diode, load, factory end point), when a switch is closed, when an ECU output is on. Every line cites its
          source; "TBD" = not in the repo, reported as "not proven".
  chain   for every load: source -> protection -> switching -> conductors -> load -> return (static: every contact
          taken as closed).
  solver  an on / off state model, no amps, no wire sizes, no voltage drop (Dan 2026-11-15): every node is 12 V, 5 V,
          8 V, ground or floating; switches, relays, diodes and ECU outputs open and close edges; a load is ON with a
          hard rail on one side and a hard ground on the other, WEAK when it only sees them through another load.
          Whole-car scenarios (key, lights, horn, charging, start ...), each also with every fuse pulled.

Checks:
  B1  every master end at a box exists in the box plan, on the terminal the master names; every seated relay and
      assigned fuse of the seat map has its place in the plan
  C1  every master end is classified; anything else is listed
  T1  closed loop: every load feed reaches a source and every load return reaches a ground (static)
  T2  no short: no rail reaches another rail or a ground with no load on the way (static, and in every scenario)
  F1  every load is fed by exactly one fuse (the nearest one; fuses further upstream are listed, A55 a)
  T6  relay logic: the coil is on exactly when its driver says so, and its suppression fits its driver
      (DECISIONS "Relays (B15)": an Ign / Inj output is not flywheeled, so its relay is a diode-coil part, the
      diode the right way round)
  T7  active state: the load is ON in every scenario its rule says it is on
  T8  inactive state: the load is OFF in every scenario its rule says it is off
  BF  no back-feed: no load weakly fed through another load, a coil, a lamp or a pull-up; pulling a load's own fuse
      turns it off, and pulling any fuse feeds nothing backwards
  T9  logic chain: switch -> opto -> CSB3 cavity -> SW_MASK bit -> CAN 0x642 -> ECU VDI, through bench/frames.py and
      switchboard_frames.json; watched inputs (ECU DI, A/C amp, cluster) read active exactly when they should and
      never float while their reader is powered
  TT  the headlamp / DRL / pop-up truth table of circuit-plan.md, row by row
  EX  overrides (Dan A75 a): each trace_rules.json "exceptions" entry names Dan's permission for that one violation
      (src "Dan <question ID> <date>", e.g. "Dan A70 a 2026-11-16") and matches exactly one current finding: one with
      no Dan ID and date, one that matches nothing (stale) or one that covers more than one finding is a finding
  T0  (--asbuilt, on demand) each harness.design file as built = the master: every master wire drawn once, in a file
      of its own harness, on the same two ends, with the same wire part and colour; nothing drawn that the master
      does not have. The documents are pulled read-only into _scratch/asbuilt/ (gitignored) with the harness_design
      MCP; the tracer and the pull never edit a file

    python docs/harness/tools/trace_circuits.py                 summary and findings (exit 0)
    python docs/harness/tools/trace_circuits.py --write         write docs/harness/CIRCUIT-TRACE.html: one card per device
                                                                (flowchart, scenario table, trace line, pass / fail / not proven)
    python docs/harness/tools/trace_circuits.py --check         exit 1 if that page is stale or a finding is open: a HARD gate
                                                                of tools/check_all.py (Dan A75 a; an override is one "exceptions" entry, EX)
    python docs/harness/tools/trace_circuits.py --chains        every static chain
    python docs/harness/tools/trace_circuits.py --chain K-FP    the chains of one device or harness
    python docs/harness/tools/trace_circuits.py --table H1      the scenario table of one device
    python docs/harness/tools/trace_circuits.py --t9 --pclink   the CSB3 / CAN legs; the PCLink settings this wiring depends on
    python docs/harness/tools/trace_circuits.py --asbuilt [dir] T0: compare the pulled harness.design documents with the master
    python docs/harness/tools/trace_circuits.py --self-test     prove each check fires on a broken copy
"""
import collections
import copy
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_wiring as CW                                        # noqa: E402  read_csv, Graph, MATES, FB_IDS, BOX_RING
from build_drawings import is_removal, is_integral, RELAY_CODE, PIGTAIL_DEVICES  # noqa: E402  one definition each

SEATS = os.path.join(CW.REPO, "sot", "fuse-relay-map.csv")
RULES = os.path.join(HERE, "trace_rules.json")
CIRCUIT_PLAN = os.path.join(CW.HARNESS, "circuit-plan.md")

RETURN_RE = re.compile(r"\bground\b|\bgnd\b|\(-\)|\breturn\b|\bsink\b|\bcommon\b|motor -|battery -|to ground", re.I)
FEED_RE = re.compile(r"\+\s?(12|5|8) ?V|\+B\b|B\+|battery \+|\bfeed\b|supply|LED \+|motor \+|siren \+|IG excite|"
                     r"battery sense|solenoid S|\+12 V", re.I)
HIGH = ("12", "5", "8")
SIG_KINDS = ("res", "pullup", "sense")     # weak elements that are signal parts, not loads


class Points(CW.Graph):
    """check_wiring's node keys (mated halves are one node), but a wire stays an edge and a stud is one node."""

    def __init__(self, grounds):
        self.parent = {}
        self.grounds = [(re.compile(g["match"]), g["node"]) for g in grounds]
        for a, b in CW.INTERNAL:
            self.join(("pin",) + a, ("pin",) + b)

    def key(self, r, s):
        t, i = r[s + "_type"], r[s + "_id"]
        if not i:
            return None
        if t == "terminal":
            for rx, node in self.grounds:
                if rx.search(i):
                    return (node,)
            return ("terminal", i)
        return CW.Graph.key(self, r, s)


class Comp:
    def __init__(self, cid, kind, t, label, **attr):
        self.id, self.kind, self.t, self.label, self.attr = cid, kind, t, label, attr

    def __repr__(self):
        return "<%s %s>" % (self.kind, self.id)


class Model:
    def __init__(self, rules):
        self.R = rules
        self.g = Points(rules["grounds"])
        self.wires = []                                  # (wire id, point a, point b, master row or None)
        self.comps = []                                  # fuses, relays, switches, diodes
        self.elems = []                                  # weak elements: loads, coils, LEDs, resistors, pull-ups
        self.rails = []                                  # (point, level, when or None, name)
        self.ends = collections.defaultdict(list)        # point -> [(row, side)]
        self.cls = {}                                    # (wire id, side) -> class
        self.names, self.hubs = {}, {}                   # point -> plain name; named bars and bodies
        self.findings, self.unproven, self.accepted = [], [], []
        self.sources, self.sinks, self.endpoints = {}, {}, {}   # point -> (volts, name) / name / name
        self.drivers, self.factory_feeds = {}, {}        # ECU outputs; factory feed ends no rule names yet
        self.devices = collections.OrderedDict()         # device id -> {name, harness}
        self.pclink = []                                 # PCLink settings this wiring depends on
        self.BP = ("terminal", rules["battery"]["pos"])
        self.BN = ("terminal", rules["battery"]["neg"])

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

    def find(self, code, harness, dev, text, devices=None):
        f = {"code": code, "harness": harness, "device": dev, "text": text, "devices": devices or [dev]}
        n, x = next(((n, x) for n, x in enumerate(self.R.get("exceptions", [])) if ex_matches(x, code, dev, text)), (None, None))
        if x:      # a named exception Dan accepted (rules "exceptions"): listed, never a finding
            a = dict(f, why=x["why"], src=x["src"], ex=n)
            if a not in self.accepted:
                self.accepted.append(a)
            return
        if f not in self.findings:
            self.findings.append(f)

    def unp(self, harness, dev, text):
        if (harness, dev, text) not in self.unproven:
            self.unproven.append((harness, dev, text))

    def ref(self, dev, pin):
        """a rules pin reference ('pin' of this device, or 'ID:pin') -> its point, or None"""
        if ":" in pin:
            dev, pin = pin.split(":", 1)
        if dev in self.pins and pin in self.pins[dev]:
            return self.g.key(*self.pins[dev][pin])
        for c in self.comps:
            if c.id == dev and pin in c.t:
                return c.t[pin]
        return None

    def dev(self, i, name=None, harness=None):
        d = self.devices.setdefault(i, {"name": name or i, "harness": harness or ""})
        if name and d["name"] == i:
            d["name"] = name
        if harness and not d["harness"]:
            d["harness"] = harness
        return d


DAN_OK = re.compile(r"\bDan [A-Z]+\d+ [a-z] \d{4}-\d{2}-\d{2}\b")   # "Dan A70 a 2026-11-16": his answer to one question, dated


def ex_matches(x, code, dev, text):
    """an exception matches by check + device, or check + text_has (one piece, or a list of pieces that must all be there)"""
    if x["check"] != code:
        return False
    if "device" in x:
        return x["device"] == dev
    th = x.get("text_has", "\0")
    return all(t in text for t in (th if isinstance(th, list) else [th]))


def exception_checks(M, pulls=True):
    """EX (Dan A75 a): an override is one entry in "exceptions" with Dan's permission for that one violation: its src names
    his question ID and the date, and it matches exactly one current finding. A stale one (matches nothing) or a wide one
    (matches more than one) is a finding. The stale test needs the pulled-fuse scenarios, so it runs only with them."""
    hits = collections.Counter(a["ex"] for a in M.accepted)
    for n, x in enumerate(M.R.get("exceptions", [])):
        who = "exception %d (%s %s)" % (n + 1, x["check"], x.get("device") or x.get("text_has"))
        if not DAN_OK.search(x.get("src", "")):
            M.findings.append({"code": "EX", "harness": "", "device": "", "devices": [], "text": who +
                               ": its src names no Dan question ID and date (e.g. 'Dan A70 a 2026-11-16'); an override needs Dan's permission for that one violation (A75 a)"})
        if hits[n] > 1:
            M.findings.append({"code": "EX", "harness": "", "device": "", "devices": [], "text": who +
                               ": covers %d findings; one exception covers exactly one violation (A75 a)" % hits[n]})
        elif pulls and not hits[n]:
            M.findings.append({"code": "EX", "harness": "", "device": "", "devices": [], "text": who +
                               ": matches no current finding (stale override): remove it (A75 a)"})


def read_seats(path=SEATS):
    return CW.read_csv(path)[1]


def read_rules(path=RULES):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def bkey(e):
    """a box plan end -> its node"""
    if e["id"] == "pdb":
        return ("box", "POWER", "NEG bar" if e["cav"].startswith("NEG") else "+ bar")
    return ("box", e["id"], e["des"] or e["cav"])


def relay_id(plan_id):
    return plan_id.upper().replace("_", "-")


def ecu_pins(channels):
    out = {}
    back = {v: k for k, v in CW.ECU.items()}
    for c in channels:
        if c["conn"] in back and c["pin"][1:].isdigit():
            out[("pin", back[c["conn"]], c["pin"][1:])] = c
    return out


def text_role(d):
    return "return" if RETURN_RE.search(d) else "feed" if FEED_RE.search(d) else "signal"


def elem(M, dev, name, a, b, kind="load", on_when=None, polar=False, when=None, src="", assumed=False):
    e = {"id": "%s.%s" % (dev, name), "dev": dev, "name": name, "a": a, "b": b, "kind": kind, "on_when": on_when,
         "polar": polar, "when": when, "src": src, "assumed": assumed}
    M.elems.append(e)
    return e


def build(rows, plan, seats, channels, rules):
    M = Model(rules)
    g, P = M.g, rules.get("parts", {})
    live = [r for r in rows if r["wire_id"] and not is_removal(r)]
    M.rows = live
    box_relays = {s["master_id"] for s in seats if s["kind"] == "relay" and s["master_id"] and s["bank"] in ("B1", "B2", "B3")}
    hubs = [re.compile(h["match"]) for h in rules.get("hubs", [])]

    def is_box(r, s):
        i = r[s + "_id"]
        return i in CW.FB_IDS or bool(CW.BOX_RING.match(i)) or i in box_relays
    M.is_box = is_box
    M.is_hub = lambda i: any(h.search(i) for h in hubs)
    for r in live:
        a, b = g.key(r, "from"), g.key(r, "to")
        if not (a and b):
            M.find("T1", r["harness"], r["wire_id"], "wire %s has only one end in the master" % r["wire_id"])
            continue
        if is_integral(r) and "fuse" in r["wire_label"].lower():      # the MRBF block (Dan N61 a): an INTEGRAL link that is a fuse
            M.comps.append(Comp(r["wire_id"], "fuse", {"a": a, "b": b}, r["wire_label"] or "fuse " + r["wire_id"], harness=r["harness"]))
        else:
            if a == b:
                M.unp(r["harness"], r[("from_id")], "wire %s has the same end ID and pin on both sides (%s %s): the tracer cannot tell its two ends apart" % (
                    r["wire_id"], r["from_id"], r["from_pin"]))
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
    seat_name = {s["master_id"]: s["circuit"] for s in seats if s["master_id"]}
    for pid, t in sorted(rel.items()):
        M.comps.append(Comp(relay_id(pid), "relay", t, relay_id(pid), box=True, name=seat_name.get(relay_id(pid), "") + " relay"))
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
    bf = rules["box"]["trunk_block_fuse"]
    if ("box", "fb_batt", bf["in"]) in plan_pts:
        M.comps.append(Comp(bf["label"], "fuse", {"a": ("box", "fb_batt", bf["in"]), "b": ("box", "fb_batt", bf["out"])}, bf["label"], box=True))
    # ---- parts outside the boxes, from the rules file (or, with no rule, from the master's own types and names)
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
        rule = P.get(i, {})
        kind = rule.get("kind")
        if i.startswith(RELAY_CODE) and i not in box_relays:
            M.comps.append(Comp(i, "relay", pt, i, harness=h, name=nm))
        elif kind == "fuse":
            a, b = rule["pins"]
            M.comps.append(Comp(i, "fuse", {"a": pt[a], "b": pt[b]}, rule.get("label", nm), harness=h))
        elif kind == "diode" or (not kind and (t == "diode" or "diode" in nm.lower()) and "LED" not in nm):
            an = rule.get("a") or next((p for p, (r, s) in ps.items() if "anode" in r[s + "_desc"].lower()), "1")
            ka = rule.get("k") or next((p for p in ps if p != an), None)
            if an in pt and ka in pt:
                M.comps.append(Comp(i, "diode", {"a": pt[an], "k": pt[ka]}, nm, harness=h))
                M.dev(i, nm, h)
    for k, n in ((("box", "POWER", "+ bar"), "POWER box + bar"), (("box", "POWER", "NEG bar"), "POWER box NEG bar"),
                 (("box", "fb_logic", "BUS1"), "LOGIC Bus 1"), (("box", "fb_logic", "BUS2"), "LOGIC Bus 2"),
                 (("body",), "body ground"), (("block",), "engine block"), (M.BP, "battery +"), (M.BN, "battery -")):
        M.names[M.p(k)] = M.hubs[M.p(k)] = n
    for ln in rules.get("links", []):                   # two factory ends that are one factory wire (each with its source)
        a, b = M.ref("", ln["a"]), M.ref("", ln["b"])
        if a and b:
            M.wires.append(("(factory: %s)" % ln["name"], a, b, None))
        else:
            M.unp("", ln["a"].split(":")[0], "rules link %s - %s: an end is not in the master" % (ln["a"], ln["b"]))
    classify(M, channels)
    return M


def classify(M, channels):
    """C1: a class for every master end; builds the sources, grounds, end points, switches and load elements."""
    g, ecu, P, R = M.g, ecu_pins(channels), M.R.get("parts", {}), M.R
    part = {}
    for c in M.comps:
        for k in c.t.values():
            part[M.p(k)] = c
    M.sources[M.p(M.BP)] = ("12", "battery +")
    M.sinks[M.p(M.BN)] = "battery -"
    M.rails.append((M.BP, "12", None, "battery +"))
    M.rails.append((M.BN, "0", None, "battery -"))
    gen = collections.defaultdict(lambda: {"feeds": [], "returns": [], "signals": []})
    E = R["ecu"]
    alive = E["alive"]
    for r in M.rows:
        for s in ("from", "to"):
            t, i, p, d = r[s + "_type"], r[s + "_id"], r[s + "_pin"], r[s + "_desc"]
            if not i:
                continue
            raw = g.key(r, s)
            k = M.p(raw)
            rule = P.get(i, {})
            prule = rule.get("pins", {}).get(p) if rule.get("kind") == "endpoint" else None
            c = ""
            if t == "splice":
                c = "hub.splice"
            elif t == "cable screen":
                c = "hub.screen"
            elif t == "connector" and i.startswith("BUS-"):
                c = "hub.bus"
            elif i in CW.MATES:
                c = "hub.bulkhead"
            elif M.is_hub(i):
                c = "hub.pass-through"
            elif i in CW.ECU:
                ch = ecu.get(raw)
                if not ch:
                    c = ""
                elif ch["class"] == "rail" and ch["type"] != "gnd":
                    c = "ecu.rail"
                    if k not in M.sources:
                        M.sources[k] = (ch["type"][-2:-1], "ECU %s (%s %s)" % (ch["channel"], i, p))
                        M.rails.append((raw, ch["type"][-2:-1], alive, "ECU %s" % ch["channel"]))
                elif ch["class"] == "rail":
                    c = "ecu.gndout"
                    if k not in M.sinks:
                        M.sinks[k] = "ECU Gnd Out (%s %s)" % (i, p)
                        M.rails.append((raw, "0", E["gnd_ok"], "ECU Gnd Out %s %s" % (i, p)))
                elif ch["class"] == "power":
                    c = "ecu.power"
                elif ch["class"] == "ground":
                    c = "ecu.ground"
                elif ch["class"] == "screen":
                    c = "ecu.screen"
                elif ch["dir"] == "out":
                    c = "ecu.out"
                    M.drivers[k] = "ECU %s (%s %s, switched by the ECU)" % (ch["channel"], i, p)
                else:
                    c, M.endpoints[k] = "ecu.in", "ECU %s (%s %s)" % (ch["channel"], i, p)
            elif raw in M.hubs and raw[0] in ("body", "block"):
                c = "ground." + raw[0]
            elif raw in (M.BP, M.BN):
                c = "battery"
            elif M.is_box(r, s):
                c = "box"
            elif k in part and (i.startswith(RELAY_CODE) or part[k].id == i):
                c = part[k].kind
            elif rule.get("kind") in ("switch", "load", "led", "part-of", "module"):
                c = "part." + rule["kind"]
            elif prule:
                c = "factory." + prule["role"] if t == "OEM" else "end." + prule["role"]
            elif t == "resistor":
                c = "res"
            elif t == "diode" and "LED" in r[s + "_name"]:
                c = "part.led"
            elif d:
                role = text_role(d)
                if t == "OEM" and i not in PIGTAIL_DEVICES:
                    # a factory plug or box with no rule yet: each pin is its own end point (A57 a)
                    c = "factory." + {"return": "sink", "feed": "feed", "signal": "signal"}[role]
                    if role == "return":
                        M.sinks[k] = "%s %s (factory ground or switch to ground: %s)" % (i, p, d)
                    elif role == "feed":
                        M.factory_feeds[k] = "%s %s (factory feed end: %s)" % (i, p, d)
                    M.endpoints[k] = "%s %s (%s)" % (i, p, d)
                    M.unp(r["harness"], i, "%s pin %s (%s): no rule says what this factory end is (source, ground, switch or load)" % (i, p, d))
                else:
                    c = "load." + role
                    gen[i][role + "s"].append((p, raw))
                    M.endpoints[k] = "%s %s (%s)" % (i, p, d)
            M.cls[(r["wire_id"], s)] = c
            if not c:
                M.find("C1", r["harness"], i, "end %s %s of wire %s is not classified (no pin text, or an ECU pin sot/channels.csv does not list)" % (
                    i, p, r["wire_id"]))
    # ---- relays: coil element, contacts, suppression (DECISIONS "Relays (B15)")
    for c in M.comps:
        if c.kind != "relay":
            continue
        rule = P.get(c.id, {})
        h = c.attr.get("harness") or next((r["harness"] for r in M.rows for s in ("from", "to") if r[s + "_id"] == c.id), "")
        M.dev(c.id, c.attr.get("name") or c.id, h)
        c.attr.update(rule=rule, harness=h)
        if "86" in c.t and "85" in c.t:
            elem(M, c.id, "coil", c.t["86"], c.t["85"], kind="coil", on_when=rule.get("on_when"), src=rule.get("src", ""))
            for tn in ("85", "86"):
                M.endpoints.setdefault(M.p(c.t[tn]), "%s %s (relay coil)" % (c.id, tn))
            if rule.get("suppression") == "diode" and rule.get("cathode") in ("85", "86"):
                ka = rule["cathode"]
                an = "85" if ka == "86" else "86"
                M.comps.append(Comp(c.id + " coil diode", "diode", {"a": c.t[an], "k": c.t[ka]}, c.id + " coil diode", supp=c.id))
        else:
            M.find("T1", h, c.id, "relay %s: coil terminals 85 / 86 are not both wired (wired: %s)" % (c.id, ", ".join(sorted(c.t))))
    # ---- parts with a rule
    for i, rule in P.items():
        kind = rule.get("kind")
        if i not in M.pins and kind not in ("relay",):
            if kind:
                M.unp("", i, "rules part %s is not in the master (a stale rule)" % i)
            continue
        if kind == "relay" or i not in M.pins:
            continue
        r0, s0 = next(iter(M.pins[i].values()))
        nm, h = r0[s0 + "_name"], r0["harness"]
        src = rule.get("src", "")
        if kind not in ("part-of",):
            M.dev(i, nm, h)
        if rule.get("tbd"):
            M.unp(h, i, "%s (%s): %s" % (nm, i, rule["tbd"]))
        for a, b, when in rule.get("contacts", []):
            pa, pb = M.ref(i, a), M.ref(i, b)
            if pa and pb:
                M.comps.append(Comp("%s %s-%s" % (i, a, b), "switch", {"a": pa, "b": pb}, "%s %s-%s" % (nm, a, b.split(":")[-1]), harness=h, dev=i, when=when))
            else:
                M.unp(h, i, "%s (%s): contact %s - %s is not wired in the master" % (nm, i, a, b))
        for el in rule.get("elements", []):
            if isinstance(el, list):
                el = dict(zip(("a", "b", "name", "on_when", "when"), el))
            a, b, name, on_when = el["a"], el["b"], el["name"], el.get("on_when")
            pa, pb = M.ref(i, a), (M.ref(i, b) if b != "@inside" else ("in", i, a))
            if pa and pb:
                elem(M, i, name, pa, pb, on_when=on_when, src=src, kind=el.get("kind", "load"), when=el.get("when"))
                if b == "@inside":
                    M.rails.append((pb, "0", None, "inside %s" % i))
            else:
                M.unp(h, i, "%s (%s): %s (%s - %s) is not wired in the master" % (nm, i, name, a, b))
        for p, lvl, when, name in rule.get("rails", []):
            pp = M.ref(i, p)
            if pp:
                M.rails.append((pp, lvl, when, "%s %s" % (i, name)))
                if lvl == "0":
                    M.sinks.setdefault(M.p(pp), "%s %s (%s)" % (i, p, name))
                else:
                    M.sources.setdefault(M.p(pp), (lvl, "%s %s (%s)" % (i, p, name)))
        for p, pr in (rule.get("pins", {}) if kind == "endpoint" else {}).items():
            pp = M.ref(i, p)
            if not pp:
                M.unp(h, i, "%s (%s): rules pin %s is not wired in the master" % (nm, i, p))
                continue
            role, k, label = pr["role"], M.p(pp), "%s %s (%s)" % (i, p, pr.get("name", pr["role"]))
            M.endpoints[k] = label
            if pr.get("tbd"):
                M.unp(h, i, "%s pin %s: %s" % (i, p, pr["tbd"]))
            if role == "source":
                if pr.get("when") == "TBD":
                    M.factory_feeds[k] = label
                    M.unp(h, i, "%s pin %s (%s): when it is live is not in the repo (TBD)" % (i, p, pr.get("name", "")))
                else:
                    M.sources[k] = ("12", label)
                    M.rails.append((pp, "12", pr.get("when"), label))
            elif role in ("sink", "ground"):
                M.sinks[k] = label
                M.rails.append((pp, "0", pr.get("when"), label))
            elif role == "load":
                inside = ("in", i, p)
                elem(M, i, pr.get("name", "pin " + p), pp, inside, on_when=pr.get("on_when"), src=pr.get("src", src))
                M.rails.append((inside, "0", None, "inside %s" % i))
            elif role == "input" and pr.get("pull"):
                pu = M.ref(i, pr["pull"])
                if pu:
                    elem(M, i, pr.get("name", "pin " + p) + " (pull-up inside)", pu, pp, kind="pullup", src=pr.get("src", src), assumed=True)
    # ---- LEDs and resistors
    for i, ps in M.pins.items():
        r0, s0 = next(iter(ps.values()))
        t, nm, h = r0[s0 + "_type"], r0[s0 + "_name"], r0["harness"]
        if i in P and P[i].get("elements"):
            continue
        if t == "diode" and "LED" in nm and "1" in ps and "2" in ps:
            M.dev(i, nm, h)
            elem(M, i, "LED", g.key(*ps["1"]), g.key(*ps["2"]), kind="led", polar=True, on_when=P.get(i, {}).get("on_when"), src=P.get(i, {}).get("src", ""))
        elif t == "resistor" and "1" in ps and "2" in ps:
            elem(M, i, "resistor", g.key(*ps["1"]), g.key(*ps["2"]), kind="res")
            for p in ("1", "2"):
                M.endpoints.setdefault(M.p(g.key(*ps[p])), "%s %s (resistor)" % (i, p))
    # ---- devices no rule names: a load between its feed and return pins, by the master's pin text
    for i, d in sorted(gen.items()):
        r0, s0 = next(iter(M.pins[i].values()))
        nm, h = r0[s0 + "_name"], r0["harness"]
        M.dev(i, nm, h)
        if d["feeds"] and d["returns"]:
            pairs = zip(d["feeds"], d["returns"]) if len(d["feeds"]) == len(d["returns"]) else [(f, d["returns"][0]) for f in d["feeds"]]
            for (fp, fk), (rp, rk) in pairs:
                elem(M, i, "pin %s to %s" % (fp or "lead", rp or "lead"), fk, rk, src="master pin text", on_when="@rail")
        elif d["feeds"]:
            M.unp(h, i, "%s (%s): no return pin in the master and no rule (case ground, another plug or a factory return)" % (nm, i))
        elif d["signals"] and d["returns"]:      # a passive two-wire sensor: signal to an ECU input, return to the sensor ground
            for (sp, sk), (rp, rk) in zip(d["signals"], d["returns"]):
                elem(M, i, "sensor (pin %s to %s)" % (sp, rp), sk, rk, kind="sense", src="master pin text")
        elif d["returns"]:
            M.unp(h, i, "%s (%s): no feed pin in the master and no rule (its feed is on another plug)" % (nm, i))
    # ---- the ECU: its supply as a load, its outputs as switches, its pull-ups (sot/channels.csv)
    M.dev("ECU", "Link G4X ECU", "AB-cabin")
    gk = [M.ref("", x) for x in E["grounds"]]
    for a, b in zip(gk, gk[1:]):
        if a and b:
            M.wires.append(("(inside the ECU)", a, b, None))
    for ref, name, on_when in E["supply"]:
        pa = M.ref("", ref)
        if pa and gk[0]:
            elem(M, "ECU", name, pa, gk[0], on_when=on_when, src=E["src"])
    back = {v: k for k, v in CW.ECU.items()}
    for ch in channels:
        if ch["conn"] not in back or ch["status"] != "set":
            continue
        raw = ("pin", back[ch["conn"]], ch["pin"][1:])
        o = E["outputs"].get(ch["channel"])
        wired = M.p(raw) in M.drivers
        if ch["dir"] == "in" and ch["class"] == "signal" and raw in M.ends:
            i = E.get("inputs", {}).get(ch["channel"], {})
            if ch["pullup"] not in ("none", "") or i:
                M.pclink.append("%s (%s %s) %s: input type %s, pull-up %s%s [%s]" % (
                    ch["channel"], back[ch["conn"]], ch["pin"][1:], ch["label"], ch["type"], ch["pullup"],
                    ("; " + i["pclink"]) if i.get("pclink") else "", i.get("src", "sot/channels.csv")))
            if i.get("pull") and E.get("pullup_ref"):
                elem(M, "ECU", "%s pull-up (inside the ECU, PCLink setting)" % ch["channel"], M.ref("", E["pullup_ref"]), raw, kind="pullup",
                     src=i.get("src", E["pullup_src"]), assumed=True)
        if ch["dir"] == "out" and ch["class"] == "signal":
            if o and wired:
                if o["drive"] in ("low", "high"):
                    M.rails.append((raw, "0" if o["drive"] == "low" else "12", "(%s) and (%s)" % (alive, o["when"]), "ECU %s on" % ch["channel"]))
                M.pclink.append("%s (%s %s): %s [%s]" % (ch["channel"], back[ch["conn"]], ch["pin"][1:], o["pclink"], o["src"]))
            elif wired:
                M.unp("AB-cabin", "ECU", "ECU output %s (%s): no rule says when it is on" % (ch["channel"], ch["label"]))
            if ch["pullup"] == "int-1k5" and wired and E.get("pullup_ref"):   # noqa: E129
                elem(M, "ECU", "%s pull-up 1.5 k (inside the ECU)" % ch["channel"], M.ref("", E["pullup_ref"]), raw, kind="pullup",
                     src=E["pullup_src"], assumed=True)


def relay_checks(M):
    """T6, the part: a relay on an ECU output with no flywheel diode (Ign / Inj) is a diode-coil part, the diode the
    right way round (DECISIONS "Relays (B15)"); Aux outputs are flywheeled and a switch needs none."""
    for c in M.comps:
        if c.kind != "relay" or "85" not in c.t or "86" not in c.t:
            continue
        rule, h = c.attr.get("rule") or {}, c.attr.get("harness", "")
        drv = M.drivers.get(M.p(c.t["85"])) or M.drivers.get(M.p(c.t["86"]))
        c.attr["driver"] = drv or "a switch or a factory part (no ECU output)"
        if not rule:
            M.unp(h, c.id, "%s: no relay rule (its part, its suppression, when it is on)" % c.id)
            continue
        sup = rule.get("suppression", "TBD")
        if drv and re.match(r"ECU (Ign|Inj) ", drv):
            if sup != "diode":
                M.find("T6", h, c.id, "%s is driven by %s, an output with no flywheel diode, but its relay %s is not a diode-coil part "
                       "(suppression: %s; DECISIONS 'Relays (B15)')" % (c.id, drv, rule.get("part", "?"), sup))
            elif rule.get("cathode") not in ("85", "86"):
                M.unp(h, c.id, "%s: which coil terminal is the diode's cathode is not in the rules, so its polarity is not proven" % c.id)
        if M.drivers.get(M.p(c.t["86"])) and not M.drivers.get(M.p(c.t["85"])):
            M.find("T6", h, c.id, "%s: the ECU output lands on coil 86, not on 85 (DECISIONS R219: an ECU output driving a relay lands on coil pin 85)" % c.id)


# ------------------------------------------------------------------------------------------------ static chains
def adjacency(M):
    """conductors and switching, every contact taken as closed; a diode only in its forward direction (a -> k)"""
    adj = collections.defaultdict(list)
    for wid, a, b, _r in M.wires:
        a, b = M.p(a), M.p(b)
        adj[a].append((b, wid, 0, None))
        adj[b].append((a, wid, 0, None))
    for c in M.comps:
        if c.kind in ("fuse", "switch"):
            pairs = [("a", "b", 0)]
        elif c.kind == "relay":
            pairs = [("30", "87", 0), ("30", "87a", 0)]
        elif c.kind == "diode" and not c.attr.get("supp"):
            pairs = [("a", "k", 1)]
        else:
            continue
        for x, y, d in pairs:
            if x in c.t and y in c.t:
                a, b = M.p(c.t[x]), M.p(c.t[y])
                lab = "[%s]" % (c.label if c.kind != "relay" else "%s %s-%s" % (c.label, x, y))
                adj[a].append((b, lab, d, c))
                adj[b].append((a, lab, -d, c))
    return adj


def search(M, adj, start, targets, down=True, skip=()):
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
        for nb, lab, d, c in adj[k]:
            if (d and (d > 0) != down) or c in skip:
                continue
            if nb not in seen:
                seen[nb] = (k, lab)
                q.append(nb)
    return None


def reach_set(M, adj, start, down=True, skip=()):
    start = M.p(start)
    seen, q = {start}, collections.deque([start])
    while q:
        k = q.popleft()
        for nb, _lab, d, c in adj[k]:
            if (d and (d > 0) != down) or c in skip:
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


def chain(M, adj, fuses, e):
    """the static chain of one element: its feed up to a source, its return down to a ground"""
    bat = M.p(M.BP)
    rails = set(M.sources)
    k = M.p(e["a"])
    f = {"ok": False, "fuses": [], "class": ""}
    hit = (k, []) if (k in rails or k in M.drivers or k in M.factory_feeds) else (
        search(M, adj, k, {bat}, down=False) or search(M, adj, k, rails | set(M.drivers), down=False)
        or search(M, adj, k, set(M.factory_feeds), down=False))
    if hit:
        src, path = hit
        f.update(ok=True, source=(M.sources.get(src) or ("", M.drivers.get(src) or M.factory_feeds.get(src)))[1])
        f["path"] = [f["source"]] + hops(M, path, rev=True)
        # F1: walking up from the load without crossing a fuse, exactly one feeder may be met: one fuse, or one source
        # that brings its own protection (an ECU rail or output, a factory feed). The battery itself = no fuse at all.
        region = reach_set(M, adj, k, down=False, skip=tuple(fuses))
        first = [] if bat in region else [c for c in fuses if M.p(c.t["a"]) in region or M.p(c.t["b"]) in region]
        other = sorted((M.sources.get(x) or ("", M.drivers.get(x) or M.factory_feeds.get(x)))[1]
                       for x in region & (rails | set(M.drivers) | set(M.factory_feeds)) if x != bat)
        dom = [c for c in fuses if c not in first and src == bat and bat not in reach_set(M, adj, k, down=False, skip=(c,))]
        f["fuses"] = [c.label for c in first] + [c.label for c in dom]
        f["first"] = [c.label for c in first]
        f["feeders"] = [c.label for c in first] + other
        if bat in region:
            f["class"] = "unfused"
        elif len(f["feeders"]) > 1:
            f["class"] = "multi"
    else:
        f["ends"] = sorted(M.endpoints[x] for x in (reach_set(M, adj, k, down=False) - {k}) & set(M.endpoints))[:3]
    k = M.p(e["b"])
    r = {"ok": False}
    if e["b"][0] == "in":
        r.update(ok=True, path=["inside the part (a factory or case return, A57 a)"])
    else:
        hit = (k, []) if k in M.sinks or k in M.drivers else (
            search(M, adj, k, {M.p(M.BN)}, down=True) or search(M, adj, k, set(M.sinks) | set(M.drivers), down=True))
        if hit:
            snk = M.sinks.get(hit[0]) or M.drivers[hit[0]]
            r.update(ok=True, path=hops(M, hit[1]) + [snk])
        else:
            r["ends"] = sorted(M.endpoints[x] for x in (reach_set(M, adj, k, down=True) - {k}) & set(M.endpoints))[:3]
    return {"feed": f, "ret": r}


def chain_line(M, e):
    c = e["chain"]
    f, r = c["feed"], c["ret"]
    left = " -> ".join(f["path"]) if f["ok"] else "OPEN, no source reaches it%s" % (
        (" (ends on " + "; ".join(f["ends"]) + ")") if f.get("ends") else "")
    right = " -> ".join(r["path"]) if r["ok"] else "OPEN, reaches no ground%s" % (
        (" (ends on " + "; ".join(r["ends"]) + ")") if r.get("ends") else "")
    return "%s -> | %s | -> %s" % (left, e["id"], right)


def static_checks(M):
    adj = M.adj = adjacency(M)
    fuses = [c for c in M.comps if c.kind == "fuse"]
    multi = collections.OrderedDict()
    ecu_in = {k for k, n in M.endpoints.items() if n.startswith("ECU ")}
    deg = collections.Counter()
    for _w, a, b, _r in M.wires:
        deg[M.p(a)] += 1
        deg[M.p(b)] += 1
    for c in M.comps:
        for k in c.t.values():
            deg[M.p(k)] += 1
    for i, ps in sorted(M.pins.items()):
        r0, s0 = next(iter(ps.values()))
        if r0[s0 + "_type"] == "splice" and deg[M.p(M.g.key(r0, s0))] < 2:
            M.find("T1", r0["harness"], i, "splice %s (%s) has only one wire on it: a dead end" % (i, r0[s0 + "_name"]))
    for e in M.elems:
        if e["kind"] in ("pullup", "res"):
            continue
        d = M.devices.get(e["dev"], {"name": e["dev"], "harness": ""})
        h, nm = d["harness"], "%s (%s), %s" % (d["name"], e["dev"], e["name"])
        if e["kind"] == "sense":
            hit = search(M, adj, e["a"], ecu_in, down=True) or search(M, adj, e["a"], ecu_in, down=False)
            k = M.p(e["b"])
            rt = (k, []) if k in M.sinks else search(M, adj, k, set(M.sinks), down=True)
            e["chain"] = {"feed": {"ok": bool(hit), "fuses": [], "first": [], "class": "",
                                   "path": ([M.endpoints[hit[0]]] + hops(M, hit[1], rev=True)) if hit else []},
                          "ret": {"ok": bool(rt), "path": (hops(M, rt[1]) + [M.sinks[rt[0]]]) if rt else []}}
            if not hit:
                M.find("T1", h, e["dev"], "%s: its signal pin reaches no ECU input" % nm)
            if not rt:
                M.find("T1", h, e["dev"], "%s: its return pin reaches no sensor ground" % nm)
            continue
        c = e["chain"] = chain(M, adj, fuses, e)
        if c["feed"].get("class") == "multi":
            multi.setdefault(tuple(c["feed"]["feeders"]), [])
        f, r = c["feed"], c["ret"]
        if not f["ok"] and f.get("ends"):
            M.unp(h, e["dev"], "%s: the feed side ends on %s, not on a source the rules name" % (nm, "; ".join(f["ends"])))
        elif not f["ok"]:
            M.find("T1", h, e["dev"], "%s: no source reaches its feed side (open on the supply side)" % nm)
        elif f["class"] == "unfused":
            M.find("F1", h, e["dev"], "%s: reached from the battery with no fuse on the way" % nm)
        elif f["class"] == "multi":
            multi[tuple(f["feeders"])].append(e)
        if not r["ok"] and r.get("ends"):
            M.unp(h, e["dev"], "%s: the return side ends on %s, not on a ground the rules name" % (nm, "; ".join(r["ends"])))
        elif not r["ok"]:
            M.find("T1", h, e["dev"], "%s: its return side reaches no ground (open on the return side)" % nm)
    for feeders, es in multi.items():
        M.find("F1", M.devices.get(es[0]["dev"], {}).get("harness", ""), es[0]["dev"],
               "%d load(s) are fed from %d places at once, not through one fuse: %s. Feeders: %s" % (
                   len(es), len(feeders), ", ".join(e["id"] for e in es), " + ".join(feeders)), devices=sorted({e["dev"] for e in es}))
    # T2 (static): no rail reaches a ground or a rail of another voltage through conductors and switching alone
    grounds = set(M.sinks)
    seen = set()
    for src, (volt, sname) in sorted(M.sources.items(), key=lambda x: x[1]):
        others = grounds | {k for k, (v, _n) in M.sources.items() if v != volt}
        hit = search(M, adj, src, others, down=True)
        if hit and frozenset((src, hit[0])) not in seen:
            seen.add(frozenset((src, hit[0])))
            other = M.sources[hit[0]][1] if hit[0] in M.sources else M.sinks[hit[0]]
            M.find("T2", "", sname, "SHORT: %s reaches %s through %s with no load on the way" % (sname, other, " -> ".join(hops(M, hit[1]))))


# ------------------------------------------------------------------------------------------------ the solver
class State:
    pass


class Sim:
    """On / off state model. Hard edges: wires, fuses, closed switches, relay contacts, conducting diodes. Weak
    elements: loads, coils, LEDs, resistors, pull-ups. A node is hard 12 / 5 / 8 V, hard ground, or it floats and is
    then pulled weakly high, weakly low, both (a divider) or neither."""

    def __init__(self, M):
        self.M = M
        par = {}

        def find(x):
            par.setdefault(x, x)
            while par[x] != x:
                par[x] = par[par[x]]
                x = par[x]
            return x
        for _w, a, b, _r in M.wires:
            par[find(M.p(a))] = find(M.p(b))
        self._find, self.ids = find, {}
        self.fuses = [(self.n(c.t["a"]), self.n(c.t["b"]), c) for c in M.comps if c.kind == "fuse"]
        self.switches = [(self.n(c.t["a"]), self.n(c.t["b"]), c) for c in M.comps if c.kind == "switch"]
        self.relays = [(c, {t: self.n(k) for t, k in c.t.items()}) for c in M.comps if c.kind == "relay"]
        self.diodes = [(self.n(c.t["a"]), self.n(c.t["k"]), c) for c in M.comps if c.kind == "diode"]
        self.elems = [(self.n(e["a"]), self.n(e["b"]), e) for e in M.elems]
        self.rails = [(self.n(k), lvl, when, name) for k, lvl, when, name in M.rails]
        for k in list(M.ends):
            self.n(k)
        self.N = len(self.ids)
        self.code = {}
        self.inputs = {k: v["default"] for k, v in M.R["inputs"].items()}
        self.derived = list(M.R["derived"].items())
        self.bad_rules = set()

    def n(self, k):
        return self.ids.setdefault(self._find(self.M.p(k)), len(self.ids))

    def nref(self, ref):
        k = self.M.ref("", ref)
        return self.ids.get(self._find(self.M.p(k))) if k else None

    def ev(self, expr, ns):
        if expr is None:
            return True
        if expr == "TBD":
            return False
        try:
            if expr not in self.code:
                self.code[expr] = compile(expr, "<rules>", "eval")
            return bool(eval(self.code[expr], {"__builtins__": {}}, ns))
        except Exception as x:      # a rule that does not evaluate is reported once, and counts as false
            self.bad_rules.add("%s (%s)" % (expr, x))
            return False

    def static(self, expr, v):
        """a rule over the scenario inputs alone (what SHOULD be), with no look at the solved state"""
        ns = dict(v)
        ns.update(hot=lambda r: False, low=lambda r: False, on=lambda r: False, lit=lambda r: False)
        return self.ev(expr, ns)

    def vars(self, env):
        v = dict(self.inputs)
        v.update(env)
        ns = dict(v)
        ns.update(hot=lambda r: False, low=lambda r: False, on=lambda r: False, lit=lambda r: False)
        for k, expr in self.derived:
            v[k] = ns[k] = self.ev(expr, ns)
        return v

    def solve(self, env, pulled=()):
        v = self.vars(env)
        relay = {c.id: False for c, _t in self.relays}
        prev, seen, st = None, [], None
        for _it in range(60):
            st = self.step(v, pulled, relay, prev)
            relay = st.relay
            if prev is not None and st.sig == prev.sig:
                break
            if st.sig in seen:
                st.unstable = True
                break
            seen.append(st.sig)
            prev = st
        st.vars = v
        return st

    def step(self, v, pulled, relay, prev):
        N = self.N
        par = list(range(N))

        def f(x):
            while par[x] != x:
                par[x] = par[par[x]]
                x = par[x]
            return x

        def u(a, b):
            ra, rb = f(a), f(b)
            if ra != rb:
                par[ra] = rb
        ns = dict(v)
        if prev is None:
            ns.update(hot=lambda r: False, low=lambda r: False, on=lambda r: False, lit=lambda r: False)
        else:
            ns.update(hot=lambda r: prev.level(self.nref(r)) == "H", low=lambda r: prev.level(self.nref(r)) == "L",
                      on=lambda r: prev.relay.get(r, False), lit=lambda r: prev.elem.get(r) == "ON")
        for a, b, c in self.fuses:
            if c not in pulled:
                u(a, b)
        closed = []
        for a, b, c in self.switches:
            if self.ev(c.attr.get("when"), ns):
                u(a, b)
                closed.append(c.id)
        for c, t in self.relays:
            if relay[c.id] and "30" in t and "87" in t:
                u(t["30"], t["87"])
            elif not relay[c.id] and "30" in t and "87a" in t:
                u(t["30"], t["87a"])
        active = [(n, lvl, name) for n, lvl, when, name in self.rails if self.ev(when, ns)]
        elems = [(a, b, e) for a, b, e in self.elems if not e["when"] or self.ev(e["when"], ns)]
        conducting, reversed_supp = set(), set()
        while True:
            lab = collections.defaultdict(set)
            for n, lvl, name in active:
                lab[f(n)].add((lvl, name))
            hard = {}
            for r, s in lab.items():
                lv = {x for x, _n in s}
                hard[r] = "X" if ("0" in lv and len(lv) > 1) or len(lv - {"0"}) > 1 else ("L" if lv == {"0"} else "H")
            hi, lo = collections.defaultdict(list), collections.defaultdict(list)
            for a, b, e in elems:
                ra, rb = f(a), f(b)
                if ra == rb:
                    continue
                hi[ra].append(rb)
                lo[rb].append(ra)
                if not e["polar"]:
                    hi[rb].append(ra)
                    lo[ra].append(rb)

            def spread(start, edges):
                seen, q = set(), collections.deque(start)
                while q:
                    k = q.popleft()
                    for nb in edges[k]:
                        if nb not in seen and nb not in hard:
                            seen.add(nb)
                            q.append(nb)
                return seen
            rh = spread([r for r, h in hard.items() if h in "HX"], hi)
            rl = spread([r for r, h in hard.items() if h in "LX"], lo)

            def rank(r):
                h = hard.get(r)
                if h:
                    return 0 if h == "L" else 4
                return 3 if (r in rh and r not in rl) else 1 if (r in rl and r not in rh) else 2
            changed = False
            for a, k, c in self.diodes:
                if c.id not in conducting and rank(f(a)) > rank(f(k)):
                    if c.attr.get("supp") and hard.get(f(a)) in ("H", "X"):
                        reversed_supp.add(c.attr["supp"])
                    conducting.add(c.id)
                    u(a, k)
                    changed = True
            if not changed:
                break
        st = State()
        st.unstable = False
        st.hard, st.rh, st.rl, st.f, st.lab = hard, rh, rl, f, lab
        st.conducting, st.reversed_supp = conducting, reversed_supp
        st.elem = {}
        for a, b, e in self.elems:
            ra, rb = f(a), f(b)
            ha, hb = hard.get(ra), hard.get(rb)
            s = "OFF"
            if (e["when"] and not self.ev(e["when"], ns)) or ra == rb:
                s = "OFF"
            elif (ha == "H" and hb == "L") or (not e["polar"] and ha == "L" and hb == "H"):
                s = "ON"
            else:
                ah, al = ha in ("H", "X") or ra in rh, ha in ("L", "X") or ra in rl
                bh, bl = hb in ("H", "X") or rb in rh, hb in ("L", "X") or rb in rl
                if (ah and bl) or (not e["polar"] and bh and al):
                    s = "WEAK"
            st.elem[e["id"]] = s
        st.relay = {c.id: st.elem.get(c.id + ".coil") == "ON" for c, _t in self.relays}
        st.shorts = [sorted(n for _l, n in lab[r]) for r, h in hard.items() if h == "X"]
        st.sig = (tuple(sorted(st.relay.items())), tuple(sorted(st.elem.items())), tuple(n for n, _l, _n in active),
                  tuple(closed), tuple(sorted(conducting)))
        return st


def _level(self, n):
    """H hard rail, L hard ground, X short, h weakly high, l weakly low, m divider, - floating"""
    if n is None:
        return "-"
    r = self.f(n)
    if r in self.hard:
        return self.hard[r]
    return "m" if (r in self.rh and r in self.rl) else "h" if r in self.rh else "l" if r in self.rl else "-"


State.level = _level


def expected(M, sim, e, v):
    """what the rules say an element should be in these scenario inputs: True / False, or None when no rule says"""
    ow = e["on_when"]
    if ow == "@rail":
        src = e.get("chain", {}).get("feed", {}).get("source", "")
        ow = M.R["defaults"]["rail_fed_on_when"] if src.startswith("ECU ") else None
    if ow in (None, "TBD"):
        return None
    ns = dict(v)
    ns.update(hot=lambda r: False, low=lambda r: False, on=lambda r: False, lit=lambda r: False)
    return sim.ev(ow, ns)


def weak_clusters(sim, st):
    """connected groups of weakly fed elements -> [(entries, members)]; an entry has one side on a hard supply"""
    par = {}

    def find(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    weak = []
    for a, b, e in sim.elems:
        if st.elem[e["id"]] != "WEAK":
            continue
        ra, rb = st.f(a), st.f(b)
        soft = [r for r in (ra, rb) if r not in st.hard]
        for r in soft[1:]:
            par[find(soft[0])] = find(r)
        weak.append((ra, rb, soft[0] if soft else None, e))
    groups = collections.defaultdict(lambda: ([], []))
    for ra, rb, s, e in weak:
        if s is None:
            continue
        ent, mem = groups[find(s)]
        mem.append(e)
        if st.hard.get(ra) in ("H", "X") or st.hard.get(rb) in ("H", "X"):
            ent.append(e)
    return [(ent, mem) for ent, mem in groups.values() if any(m["kind"] in ("load", "coil", "led") for m in mem)]


def cluster_key(ent, mem):
    return tuple(sorted(e["id"] for e in ent)) or tuple(sorted(m["id"] for m in mem))[:3]


def cluster_text(ent, mem):
    rest = [m["id"] for m in mem if m not in ent and m["kind"] in ("load", "coil", "led")]
    return "12 V leaks in through %s and on to ground through %d other load(s)%s" % (
        ", ".join(e["id"] for e in ent) or "a load", len(rest), (": " + ", ".join(rest[:8]) + (" ..." if len(rest) > 8 else "")) if rest else "")


def run_scenarios(M, pulls=True):
    sim = M.sim = Sim(M)
    M.table = collections.OrderedDict()            # scenario id -> {element id: state}
    M.states, M.notes = {}, []
    fuses = [c for _a, _b, c in sim.fuses]
    t7, t8 = collections.defaultdict(list), collections.defaultdict(list)
    weak = collections.OrderedDict()               # (pulled fuse label, cluster key) -> [ent, mem, [scenario names]]
    bf_own = collections.defaultdict(lambda: collections.defaultdict(list))
    bf_on = collections.defaultdict(lambda: collections.defaultdict(list))
    byid = {e["id"]: e for e in M.elems}

    def dh(dev):
        return M.devices.get(dev, {}).get("harness", "")
    base_keys = {}
    for sc in M.R["scenarios"]:
        st = sim.solve(sc["set"])
        M.states[sc["id"]] = st
        M.table[sc["id"]] = dict(st.elem)
        for names in st.shorts:
            M.find("T2", "", names[0], "SHORT in scenario '%s': %s are joined with no load between them" % (sc["name"], " and ".join(names)))
        if st.unstable:
            M.find("T6", "", "", "scenario '%s' never settles: a relay or diode loop keeps switching" % sc["name"])
        for rid in sorted(st.reversed_supp):
            M.find("T6", dh(rid), rid,
                   "%s: its coil suppression diode is forward-biased from the supply (coil + and - are the wrong way round for a diode-coil relay)" % rid)
        for _a, _b, e in sim.elems:
            if e["kind"] in SIG_KINDS:
                continue
            act, exp = st.elem[e["id"]], expected(M, sim, e, st.vars)
            if exp is True and act != "ON":
                t7[e["id"]].append(sc["name"] + (" (only weakly fed)" if act == "WEAK" else ""))
            elif exp is False and act == "ON":
                t8[e["id"]].append(sc["name"])
        base_keys[sc["id"]] = set()
        for ent, mem in weak_clusters(sim, st):
            k = cluster_key(ent, mem)
            base_keys[sc["id"]].add(k)
            weak.setdefault(("", k), [ent, mem, []])[2].append(sc["name"])
    for i, names in t7.items():
        e = byid[i]
        M.find("T6" if e["kind"] == "coil" else "T7", dh(e["dev"]), e["dev"], "%s: should be ON (rule: %s) but is not, in: %s" % (i, e["on_when"], "; ".join(names)))
    for i, names in t8.items():
        e = byid[i]
        M.find("T6" if e["kind"] == "coil" else "T8", dh(e["dev"]), e["dev"], "%s: should be OFF (rule: %s) but is ON, in: %s" % (i, e["on_when"], "; ".join(names)))
    for e in M.elems:
        if e["kind"] in SIG_KINDS:
            continue
        if e["on_when"] is None or e["on_when"] == "TBD" or (e["on_when"] == "@rail" and expected(M, sim, e, sim.vars({})) is None):
            M.unp(dh(e["dev"]), e["dev"], "%s: no rule says when it should be on (active / inactive state not proven)" % e["id"])
        elif not any(st.elem[e["id"]] == "ON" for st in M.states.values()):
            M.unp(dh(e["dev"]), e["dev"], "%s: no scenario turns it on yet (active state not proven)" % e["id"])
    for b in sorted(sim.bad_rules):
        M.find("C1", "", "rules", "a rule in trace_rules.json does not evaluate: %s" % b)
    if pulls:
        for sc in M.R["scenarios"]:
            if sc.get("pull") is False:
                continue
            base = M.states[sc["id"]]
            for fz in fuses:
                st = sim.solve(sc["set"], pulled=(fz,))
                for _a, _b, e in sim.elems:
                    if e["kind"] in SIG_KINDS:
                        continue
                    s2, s1 = st.elem[e["id"]], base.elem[e["id"]]
                    if s2 == "ON" and fz.label in e.get("chain", {}).get("feed", {}).get("fuses", []):
                        bf_own[fz][e["id"]].append(sc["name"])
                    elif s2 == "ON" and s1 != "ON":
                        bf_on[fz][e["id"]].append(sc["name"])
                for ent, mem in weak_clusters(sim, st):
                    k = cluster_key(ent, mem)
                    if k not in base_keys[sc["id"]] and ("", k) not in weak:
                        weak.setdefault((fz.label, k), [ent, mem, []])[2].append(sc["name"])
    for fz, items in bf_own.items():
        ids = sorted(items)
        e = byid[ids[0]]
        alt = search(M, M.adj, e["a"], set(M.sources), down=False, skip=(fz,))
        via = (" They are then fed from %s through %s." % (M.sources[alt[0]][1], " -> ".join(hops(M, alt[1], rev=True)))) if alt else ""
        M.find("BF", dh(e["dev"]), e["dev"], "back-feed: with fuse %s pulled, %d load(s) it protects stay ON: %s.%s Seen in: %s" % (
            fz.label, len(ids), ", ".join(ids), via, "; ".join(sorted({n for v in items.values() for n in v}))),
            devices=sorted({byid[i]["dev"] for i in ids}))
    for fz, items in bf_on.items():
        M.notes.append("with fuse %s pulled, these turn ON (a relay contact falls back, not a back-feed): %s; in: %s" % (
            fz.label, ", ".join(sorted(items)), "; ".join(sorted({n for v in items.values() for n in v}))))
    merged = collections.OrderedDict()            # the same leak seen with several fuses pulled is one item
    for (fl, k), (ent, mem, names) in weak.items():
        m = merged.setdefault(k, [ent, mem, [], set()])
        m[2].append(fl)
        m[3].update(names)
    for k, (ent, mem, fls, names) in merged.items():
        first = (ent or mem)[0]
        fl = [x for x in fls if x]
        text = "%s%s; in: %s" % (("with fuse %s pulled, " % " / ".join(fl)) if "" not in fls else "", cluster_text(ent, mem), "; ".join(sorted(names)))
        devs = sorted({e["dev"] for e in (ent or mem[:1])})
        if any(m["assumed"] for m in mem):
            why = "; ".join(sorted({m["src"] for m in mem if m["assumed"]}))[:400]
            M.unp(dh(first["dev"]), first["dev"], "possible back-feed, not proven because it runs through the inside of a part the repo does not describe (%s): %s" % (why, text))
        else:
            M.find("BF", dh(first["dev"]), first["dev"], "back-feed: " + text, devices=devs)


LEVEL = {"H": "a hard supply", "L": "a hard ground", "X": "a short", "h": "pulled high", "l": "pulled low", "m": "a divider (between high and low)",
         "-": "floating"}


def logic_checks(M):
    """T7 / T8 for inputs: every watched input pin reads its active level exactly when its rule says so, and never floats
    while its reader is powered (rules "watch"; ECU pins from sot/channels.csv)."""
    sim = M.sim
    M.watch = []
    for w in M.R.get("watch", []):
        dev = w.get("dev") or w["pin"].split(":")[0]
        h = M.devices.get(dev, {}).get("harness", "")
        n = sim.nref(w["pin"])
        if n is None:
            M.unp(h, dev, "%s (%s): not wired in the master" % (w["name"], w["pin"]))
            continue
        rows, on, off, fl = collections.OrderedDict(), [], [], []
        for sc in M.R["scenarios"]:
            st = M.states[sc["id"]]
            lvl = rows[sc["id"]] = st.level(n)
            if w["when"] == "TBD":
                exp = None
            else:
                exp = sim.static(w["when"], st.vars)
            if exp is True and lvl != w["level"]:
                on.append("%s (reads %s)" % (sc["name"], LEVEL[lvl]))
            elif exp is False and lvl == w["level"]:
                off.append(sc["name"])
            if exp is not True and lvl == "-" and sim.static(w.get("alive", "True"), st.vars):
                fl.append(sc["name"])
        M.watch.append((w, dev, rows))
        if w["when"] == "TBD":
            M.unp(h, dev, "%s: %s" % (w["name"], w.get("tbd", "no rule says when it is active (TBD)")))
        if on:
            M.find("T7", h, dev, "%s (%s): should read %s (rule: %s) but does not, in: %s" % (w["name"], w["pin"], LEVEL[w["level"]], w["when"], "; ".join(on)))
        if off:
            M.find("T8", h, dev, "%s (%s): reads active (%s) when it should not, in: %s" % (w["name"], w["pin"], LEVEL[w["level"]], "; ".join(off)))
        if fl and w.get("float") == "tbd":
            M.unp(h, dev, "%s (%s) floats while inactive (%s), in: %s" % (w["name"], w["pin"], w.get("float_note", "its pull is TBD"), "; ".join(fl)))
        elif fl and w.get("float") != "ok":
            M.find("T8", h, dev, "%s (%s): floating input - nothing holds it at a level while inactive, in: %s" % (w["name"], w["pin"], "; ".join(fl)))


def csb3_checks(M):
    """T9: switch -> (opto) -> CSB3 cavity -> SW_MASK bit -> CAN 0x642 -> ECU VDI, for every scenario. The cavity comes
    from docs/enclosures/csb3-hd34-pinmap.csv, the bit and the VDI from switchboard_frames.json, the frame bytes from
    bench/frames.py (the same encoder the bench uses); nothing is copied into the rules."""
    C = M.R.get("csb3")
    M.t9 = []
    if not C:
        return
    sim = M.sim
    sys.path.insert(0, os.path.join(CW.REPO, "bench"))
    try:
        import frames
    finally:
        sys.path.remove(os.path.join(CW.REPO, "bench"))
    with open(os.path.join(CW.REPO, "switchboard_frames.json"), encoding="utf-8") as f:
        sw = json.load(f)
    cav = {r["board_signal"]: r["cavity"] for r in CW.read_csv(os.path.join(CW.REPO, "docs", "enclosures", "csb3-hd34-pinmap.csv"))[1]}
    f642 = next(x for x in sw["frames"] if x["id"] == "0x642")
    bits = next(c for c in f642["channels"] if c["name"] == "SW_MASK")["bits"]
    rx = {c["bit"]: c for c in sw["ecu_receive"]["channels"] if c["frame"] == "0x642" and "bit" in c}
    h = M.devices.get("CSB3", {}).get("harness", "")
    if C.get("tbd"):
        M.unp(h, "CSB3", "CSB3 switch inputs (their cavities float in the model while a switch is open): " + C["tbd"])
    items = []
    for sig, rule in C["switches"].items():
        bit, c = int(sig[1:]) - 1, cav.get(sig)
        frm = rule["from"]
        fh = M.devices.get(frm, {}).get("harness", h)
        n = sim.nref("CSB3:%s" % c) if c else None
        r = rx.get(bit)
        if not c or n is None:
            M.find("T9", fh, frm, "%s: CSB3 board input %s (cavity %s) is not wired in the master" % (rule["name"], sig, c))
            continue
        if not bits.get(str(bit), "").startswith("Switch %d" % (bit + 1)) or "unassigned" in bits.get(str(bit), ""):
            M.find("T9", fh, frm, "%s: switchboard_frames.json does not assign SW_MASK bit %d to board input %s" % (rule["name"], bit, sig))
        if not r:
            M.find("T9", fh, frm, "%s: no ECU receive channel (VDI) for 0x642 byte 4 bit %d in switchboard_frames.json" % (rule["name"], bit))
            continue
        items.append((sig, rule, bit, c, n, r, frm, fh))
    rows = {i[0]: collections.OrderedDict() for i in items}
    bad = collections.defaultdict(list)
    for sc in M.R["scenarios"]:
        st = M.states[sc["id"]]
        alive = st.elem.get(C["alive"]) == "ON"
        mask = 0
        for sig, rule, bit, c, n, r, frm, fh in items:
            if alive and st.level(n) == C["active_level"]:
                mask |= 1 << bit
        payload = frames.encode_sb_rotary_sw(sw_mask=mask)
        ok = frames.decode_sb_rotary_sw(payload)["sw_mask"] == mask
        for sig, rule, bit, c, n, r, frm, fh in items:
            vdi = (payload[r["byte"]] >> r["bit"]) & 1
            exp = sim.static(rule["when"], st.vars)
            lvl = st.level(n)
            rows[sig][sc["id"]] = (lvl, vdi)
            if not ok or bool(vdi) != exp:
                bad[sig].append("%s (cavity reads %s, %s = %d)" % (sc["name"], LEVEL[lvl], r["pclink_target"], vdi))
    for sig, rule, bit, c, n, r, frm, fh in items:
        line = "%s -> CSB3 cavity %s (board %s) -> 0x642 byte %d bit %d -> ECU %s (%s)" % (
            M.devices.get(frm, {}).get("name", frm), c, sig, r["byte"], r["bit"], r["pclink_target"], r["name"])
        M.t9.append({"sig": sig, "name": rule["name"], "from": frm, "line": line, "rows": rows[sig], "ok": sig not in bad})
        M.pclink.append("CAN receive 0x642 byte %d bit %d -> %s (%s): %s [switchboard_frames.json ecu_receive]" % (r["byte"], r["bit"], r["pclink_target"], r["name"], r.get("use", "")))
        if sig in bad:
            M.find("T9", fh, frm, "%s: %s does not follow the switch (rule: %s), in: %s" % (rule["name"], line, rule["when"], "; ".join(bad[sig])), devices=[frm, "CSB3"])
    for sig, rule in C.get("analog", {}).items():
        c = cav.get(sig)
        n = sim.nref("CSB3:%s" % c) if c else None
        frm = rule["from"]
        fh = M.devices.get(frm, {}).get("harness", h)
        if n is None:
            M.find("T9", fh, frm, "%s: CSB3 analog input %s (cavity %s) is not wired in the master" % (rule["name"], sig, c))
            continue
        wrong = []
        for sc in M.R["scenarios"]:
            st = M.states[sc["id"]]
            if st.elem.get(C["alive"]) != "ON":
                continue
            want = "m" if sim.static(rule["when"], st.vars) else "h"
            if st.level(n) != want:
                wrong.append("%s (reads %s)" % (sc["name"], LEVEL[st.level(n)]))
        rxa = next((x for x in sw["ecu_receive"]["channels"] if x["frame"] == "0x640"), None)
        if rxa:
            M.pclink.append("CAN receive 0x640 bytes %d-%d -> %s: %s [switchboard_frames.json ecu_receive]" % (
                rxa["byte"], rxa["byte"] + rxa["length"] - 1, rxa["name"], rxa["pclink_target"]))
        M.t9.append({"sig": sig, "name": rule["name"], "from": frm, "ok": not wrong, "rows": {},
                     "line": "%s -> pull-up to the switch board +5 V -> CSB3 cavity %s (board %s) -> 0x640 -> ECU" % (M.devices.get(frm, {}).get("name", frm), c, sig)})
        if wrong:
            M.find("T9", fh, frm, "%s: CSB3 cavity %s should sit pulled high with no button and on a divider with a button held, but: %s" % (
                rule["name"], c, "; ".join(wrong)), devices=[frm, "CSB3"])
    for sig, rule in C.get("outputs", {}).items():
        c = cav.get(sig)
        f643 = next(x for x in sw["frames"] if x["id"] == "0x643")
        byte = int(sig[1:]) - 1
        ch = next((x for x in f643["channels"] if x["byte"] == byte), {})
        ok = frames.decode_ls_control(frames.encode_ls_control(**{sig.lower(): 1}))[sig.lower()] == 1 and ch.get("name", "").startswith(sig)
        M.pclink.append("CAN transmit 0x643 byte %d = %s ctrl: %s [switchboard_frames.json 0x643]" % (byte, sig, ch.get("assignment", "")))
        M.t9.append({"sig": sig, "name": rule["name"], "from": rule["to"], "ok": ok and sim.nref("CSB3:%s" % c) is not None, "rows": {},
                     "line": "ECU -> 0x643 byte %d -> CSB3 low-side output %s (cavity %s) -> %s" % (byte, sig, c, M.devices.get(rule["to"], {}).get("name", rule["to"]))})
        if not ok or sim.nref("CSB3:%s" % c) is None:
            M.find("T9", h, rule["to"], "%s: 0x643 byte %d / CSB3 output %s (cavity %s) does not line up across switchboard_frames.json, bench/frames.py and the master" % (
                rule["name"], byte, sig, c))


# ------------------------------------------------------------------------------------------------ the truth table
def tt_rows(text):
    """the rows of circuit-plan.md's headlamp / DRL / pop-up truth table -> [(cells, [scenario settings])]"""
    lines = text.replace("\r\n", "\n").split("\n")
    try:
        n = next(i for i, l in enumerate(lines) if l.startswith("| Stalk | DRL switch |"))
    except StopIteration:
        return None
    rows = []
    for l in lines[n + 2:]:
        if not l.startswith("|"):
            break
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if len(c) < 7 or "released" in c[0]:
            continue
        both = [{"stalk": s, "dimmer": d} for s in "0123" for d in ("low", "high")]
        if c[0].startswith("flash"):
            stalks = [dict(x, flash=True) for x in both]
        elif c[0].startswith("any"):
            stalks = both
        elif c[0].startswith("3"):
            stalks = [{"stalk": "3", "dimmer": "high" if "high" in c[0] else "low"}]
        else:
            stalks = [{"stalk": c[0][0], "dimmer": "low"}]
        if c[1] == "off":
            drls = [{"drl_sw": False, "key": k} for k in ("OFF", "ON")]
        elif c[1].startswith("on") and "key off" in c[1]:
            drls = [{"drl_sw": True, "key": "OFF"}]
        elif c[1].startswith("on"):
            drls = [{"drl_sw": True, "key": "ON"}]
        else:
            drls = [{"drl_sw": d, "key": k} for d in (False, True) for k in ("OFF", "ON")]
        rows.append((c[:7], [dict(s, **d) for s in stalks for d in drls]))
    return rows


def truth_table(M, text):
    T = M.R["truth_table"]
    rows = tt_rows(text)
    if not rows:
        M.find("TT", "CabinPower", "truth table", "the headlamp / DRL / pop-up truth table was not found in circuit-plan.md")
        return
    sim = M.sim

    def observe(env):
        st = sim.solve(env)
        out = {}
        for col, spec in T["columns"].items():
            if "low" in spec:
                out[col] = (st.level(sim.nref(spec["low"])) == "L", "")
            else:
                vals = [st.elem.get(i) == "ON" for i in spec["all"]]
                out[col] = (all(vals), "" if len(set(vals)) == 1 else " (only %s)" % ", ".join(i for i, x in zip(spec["all"], vals) if x))
        return out
    M.tt = []
    for cells, envs in rows:
        bad = []
        for env in envs:
            got = observe(env)
            ref = observe(dict(env, drl_sw=False)) if any(x.startswith("per stalk") for x in cells[2:]) else None
            for col, want in zip(T["order"], cells[2:]):
                if want.startswith("per stalk"):
                    w = ref[col][0]
                elif want in ("up", "on"):
                    w = True
                else:
                    w = False
                if got[col][0] != w:
                    bad.append("%s is %s%s, the table says %s (stalk %s, dimmer %s%s, DRL switch %s, key %s)" % (
                        col, "on / up" if got[col][0] else "off / not commanded", got[col][1], want, env["stalk"], env["dimmer"],
                        ", flash" if env.get("flash") else "", "on" if env["drl_sw"] else "off", env["key"]))
        M.tt.append((cells, len(envs), bad))
        for b in bad[:6]:
            M.find("TT", "CabinPower", "truth table", "truth table row '%s | %s': %s" % (cells[0], cells[1], b))


# ------------------------------------------------------------------------------------------------ run and report
def load_all():
    _h, rows = CW.read_csv(CW.MASTER)
    _c, channels = CW.read_csv(CW.CHANNELS)
    with open(CW.PLAN, encoding="utf-8") as f:
        plan = json.load(f)
    with open(CIRCUIT_PLAN, encoding="utf-8") as f:
        cp = f.read()
    return rows, plan, read_seats(), channels, read_rules(), cp


def run(rows, plan, seats, channels, rules, cp, pulls=True):
    M = build(rows, plan, seats, channels, rules)
    relay_checks(M)
    static_checks(M)
    run_scenarios(M, pulls)
    logic_checks(M)
    csb3_checks(M)
    truth_table(M, cp)
    exception_checks(M, pulls)
    return M


def verdicts(M):
    """device id -> pass / fail / not proven"""
    out = collections.OrderedDict()
    bad = {d for f in M.findings for d in f["devices"]}
    unp = {d for _h, d, _t in M.unproven}
    for i in M.devices:
        out[i] = "fail" if i in bad else "not proven" if i in unp else "pass"
    return out


def report(M, argv):
    cl = collections.Counter(c.split(".")[0] or "UNCLASSIFIED" for c in M.cls.values())
    print("trace_circuits: %d wires (+%d box / factory links), %d master ends: %s" % (
        sum(1 for w in M.wires if w[3]), sum(1 for w in M.wires if not w[3]), len(M.cls),
        ", ".join("%s %d" % kv for kv in sorted(cl.items()))))
    print("parts: " + ", ".join("%s %d" % kv for kv in sorted(collections.Counter(c.kind for c in M.comps).items()))
          + "; elements: " + ", ".join("%s %d" % kv for kv in sorted(collections.Counter(e["kind"] for e in M.elems).items())))
    print("scenarios: %d, each also with each of %d fuses pulled" % (len(M.table), len(M.sim.fuses)))
    if getattr(M, "tt", None):
        print("truth table (circuit-plan.md): %d rows, %d cases, %d rows differ" % (
            len(M.tt), sum(n for _c, n, _b in M.tt), sum(1 for _c, _n, b in M.tt if b)))
    print("inputs watched: %d; CSB3 / CAN legs (T9): %d, %d ok" % (len(M.watch), len(M.t9), sum(1 for t in M.t9 if t["ok"])))
    if "--t9" in argv:
        for t in M.t9:
            print("  %-4s %s" % ("ok" if t["ok"] else "FAIL", t["line"]))
    v = verdicts(M)
    cnt = collections.Counter(v.values())
    print("devices: %d - pass %d, fail %d, not proven %d" % (len(v), cnt["pass"], cnt["fail"], cnt["not proven"]))
    want = argv[argv.index("--chain") + 1].lower() if "--chain" in argv else None
    if "--chains" in argv or want:
        for e in M.elems:
            if "chain" not in e:
                continue
            h = M.devices.get(e["dev"], {}).get("harness", "")
            if want and want not in (e["dev"].lower(), h.lower()) and not e["dev"].lower().startswith(want):
                continue
            print("  [%s] %s" % (h, chain_line(M, e)))
            fd = e["chain"]["feed"]
            if fd.get("fuses"):
                up = [x for x in fd["fuses"] if x not in fd["first"]]
                print("      fuse: %s%s" % (" + ".join(fd["first"]) or "-", ("   upstream: " + "; ".join(up)) if up else ""))
    if "--table" in argv:
        want = argv[argv.index("--table") + 1].lower()
        ids = [e["id"] for e in M.elems if e["dev"].lower() == want]
        for sc in M.R["scenarios"]:
            print("  %-34s %s" % (sc["name"], "  ".join("%s=%s" % (i.split(".", 1)[1], M.table[sc["id"]][i]) for i in ids)))
    if "--pclink" in argv:
        for p in M.pclink:
            print("PCLINK " + p)
    if "--devices" in argv:
        for i, x in v.items():
            print("  %-10s %-22s %s" % (x, i, M.devices[i]["name"]))
    for n in M.notes:
        print("NOTE " + n)
    for h, d, t in M.unproven:
        print("NOT PROVEN [%s] %s" % (h, t))
    for a in M.accepted:
        print("ACCEPTED %s [%s] %s (exception: %s; %s)" % (a["code"], a["harness"], a["text"], a["why"], a["src"]))
    for f in M.findings:
        print("FINDING %s [%s] %s" % (f["code"], f["harness"], f["text"]))
    print("trace_circuits: %d finding(s), %d not proven (HARD: an open finding fails tools/check_all.py, Dan A75 a)" % (len(M.findings), len(M.unproven)))


# ------------------------------------------------------------------------------------------------ the report page
PAGE = os.path.join(CW.HARNESS, "CIRCUIT-TRACE.html")
ORDER = ["HeavyDC", "CabinPower", "AB-cabin", "AB-engine", "EngineRoom-C", "Dash", "AntiTheft", "RearFuel", "WheelSpeed-Front", "WheelSpeed-Rear"]
CHECKS = [("B1", "box ends exist in the fuse box plan"), ("C1", "every master end is classified"), ("T1", "closed loop, source to ground"),
          ("T2", "no short"), ("F1", "one fuse per load"), ("T6", "relay logic and suppression"), ("T7", "active state"),
          ("T8", "inactive state, no floating input"), ("T9", "switch to CSB3 to CAN bit to ECU input"), ("BF", "no back-feed"),
          ("TT", "headlamp / DRL / pop-up truth table"), ("EX", "each override names Dan's permission and covers exactly one finding")]
CSS = """
body{font:14px/1.45 system-ui,Segoe UI,Arial,sans-serif;margin:0;background:#f4f5f7;color:#1c2330}
header{background:#1c2330;color:#fff;padding:14px 22px}header h1{margin:0 0 4px;font-size:20px}header p{margin:2px 0;color:#c9d1dc}
main{padding:14px 22px;max-width:1500px;margin:auto}h2{font-size:17px;margin:22px 0 8px;border-bottom:2px solid #c9d1dc;padding-bottom:3px}
.sum{display:flex;gap:10px;flex-wrap:wrap}.sum div{background:#fff;border-radius:8px;padding:8px 14px;box-shadow:0 1px 2px #0002}
.sum b{font-size:22px;display:block}.bar{position:sticky;top:0;background:#f4f5f7;padding:8px 0;z-index:2;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.bar input{padding:6px 10px;border:1px solid #9aa5b4;border-radius:6px;min-width:240px}.bar button{padding:6px 12px;border:1px solid #9aa5b4;border-radius:6px;background:#fff;cursor:pointer}
.bar button.on{background:#1c2330;color:#fff}.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(560px,1fr));gap:12px}
.card{background:#fff;border-radius:8px;padding:10px 14px;box-shadow:0 1px 2px #0002;border-left:6px solid #9aa5b4;overflow-x:auto}
.card.pass{border-left-color:#2e7d32}.card.fail{border-left-color:#c62828}.card.np{border-left-color:#ef8f00}
.card h3{margin:0;font-size:15px}.card h3 code{font-size:12px;background:#eef1f5;padding:1px 5px;border-radius:4px}
.badge{float:right;font-size:11px;font-weight:700;padding:2px 8px;border-radius:10px;color:#fff;background:#9aa5b4}
.pass .badge{background:#2e7d32}.fail .badge{background:#c62828}.np .badge{background:#ef8f00}
.meta{color:#5b6676;font-size:12px;margin:2px 0 6px}.flow{display:flex;flex-wrap:wrap;align-items:center;gap:3px;margin:6px 0 2px}
.flow span{border:1px solid #9aa5b4;border-radius:5px;padding:2px 6px;font-size:12px;background:#f8f9fb}.flow i{color:#5b6676;font-style:normal}
.flow .src{background:#fde8e8;border-color:#c62828}.flow .fz{background:#fff3d6;border-color:#ef8f00}.flow .sw{background:#e3ecfb;border-color:#3566b8}
.flow .ld{background:#1c2330;color:#fff;border-color:#1c2330}.flow .gd{background:#e3f1e4;border-color:#2e7d32}.flow .open{background:#c62828;color:#fff}
.trace{font:11px/1.4 Consolas,monospace;color:#3b4554;margin:2px 0 6px;word-break:break-word}
table{border-collapse:collapse;font-size:12px;margin:6px 0}td,th{border:1px solid #d5dbe3;padding:2px 7px;text-align:left}th{background:#eef1f5}
td.ON{background:#d9f0da;font-weight:700}td.WEAK{background:#ffe2b8;font-weight:700}td.OFF{color:#8b95a3}
ul{margin:4px 0;padding-left:18px}li{margin:2px 0}li.f{color:#a31515}li.n{color:#8a5a00}.small{font-size:12px;color:#5b6676}
"""
JS = """
const q=document.getElementById('q'),bs=[...document.querySelectorAll('.bar button')];let v='';
function go(){const t=q.value.toLowerCase();document.querySelectorAll('.card').forEach(c=>{
c.style.display=((!v||c.classList.contains(v))&&(!t||c.textContent.toLowerCase().includes(t)))?'':'none'})}
q.oninput=go;bs.forEach(b=>b.onclick=()=>{v=b.dataset.v;bs.forEach(x=>x.classList.toggle('on',x===b));go()});
"""


def esc(x):
    return html.escape(str(x), quote=True)


def flow_html(M, e):
    """source -> protection -> switching -> load -> return, as a row of boxes"""
    c = e["chain"]
    out = []

    def box(t):
        cls = "fz" if ("fuse" in t.lower() or t.startswith("[B")) and t.startswith("[") else "sw" if t.startswith("[") else ""
        return '<span class="%s">%s</span>' % (cls, esc(t.strip("[]")))
    f, r = c["feed"], c["ret"]
    if f["ok"] and f.get("path"):
        out.append('<span class="src">%s</span>' % esc(f["path"][0]))
        out += [box(t) for t in f["path"][1:] if t.startswith("[") or t in M.hubs.values()]
    else:
        out.append('<span class="open">OPEN: no source</span>')
    out.append('<span class="ld">%s</span>' % esc(e["id"]))
    if r["ok"] and r.get("path"):
        out += [box(t) for t in r["path"][:-1] if t.startswith("[") or t in M.hubs.values()]
        out.append('<span class="gd">%s</span>' % esc(r["path"][-1]))
    else:
        out.append('<span class="open">OPEN: no ground</span>')
    return '<div class="flow">%s</div>' % "<i>&rarr;</i>".join(out)


def card_html(M, i, verdict):
    d = M.devices[i]
    es = [e for e in M.elems if e["dev"] == i]
    rule = M.R.get("parts", {}).get(i, {})
    comp = next((c for c in M.comps if c.id == i and c.kind == "relay"), None)
    cls = {"pass": "pass", "fail": "fail", "not proven": "np"}[verdict]
    o = ['<article class="card %s" id="dev-%s"><span class="badge">%s</span><h3>%s <code>%s</code></h3>' % (cls, esc(i), verdict.upper(), esc(d["name"]), esc(i)),
         '<p class="meta">%s%s</p>' % (esc(d["harness"] or "no harness"), (" &middot; source: " + esc(rule["src"])) if rule.get("src") else "")]
    if comp:
        o.append('<p class="small">Relay part %s; coil suppression: %s%s; coil driven by: %s</p>' % (
            esc(rule.get("part", "TBD")), esc(rule.get("suppression", "TBD")),
            (" (cathode on %s)" % esc(rule["cathode"])) if rule.get("cathode") else "", esc(comp.attr.get("driver", "?"))))
    for e in es:
        if "chain" not in e:
            continue
        o.append(flow_html(M, e))
        fd = e["chain"]["feed"]
        fz = ""
        if fd.get("fuses"):
            up = [x for x in fd["fuses"] if x not in fd["first"]]
            fz = " &nbsp; <b>fuse:</b> %s%s" % (esc(" + ".join(fd["first"]) or "-"), (" (upstream: %s)" % esc("; ".join(up))) if up else "")
        o.append('<p class="trace">%s%s</p>' % (esc(chain_line(M, e)), fz))
    for t in M.t9:
        if t["from"] == i:
            o.append('<p class="trace"><b>%s CAN leg (T9):</b> %s</p>' % ("OK" if t["ok"] else "FAIL", esc(t["line"])))
    cols = [e for e in es if e["kind"] not in SIG_KINDS]
    ws = [(w, rows) for w, dev, rows in M.watch if dev == i]
    t9 = [t for t in M.t9 if t["from"] == i and t["rows"]]
    if cols or ws or t9:
        head = ["Scenario"] + [e["name"] for e in cols] + [w["name"] for w, _r in ws] + [t["name"] + " (cavity / VDI)" for t in t9]
        body, quiet = [], 0
        for sc in M.R["scenarios"]:
            st = [M.table[sc["id"]][e["id"]] for e in cols]
            wl = [rows[sc["id"]] for _w, rows in ws]
            tl = [t["rows"][sc["id"]] for t in t9]
            if all(x == "OFF" for x in st) and all(x != w["level"] for x, (w, _r) in zip(wl, ws)) and all(v == 0 for _l, v in tl):
                quiet += 1
                continue
            body.append("<tr><td>%s</td>%s%s%s</tr>" % (
                esc(sc["name"]), "".join('<td class="%s">%s</td>' % (x, x) for x in st),
                "".join("<td>%s</td>" % esc(LEVEL[x]) for x in wl), "".join("<td>%s / %d</td>" % (esc(LEVEL[lv]), v) for lv, v in tl)))
        o.append("<table><tr>%s</tr>%s</table>" % ("".join("<th>%s</th>" % esc(x) for x in head), "".join(body)))
        if quiet:
            o.append('<p class="small">Off / inactive in the other %d scenario(s).</p>' % quiet)
    fs = [f for f in M.findings if i in f["devices"]]
    ns = [t for _h, dv, t in M.unproven if dv == i]
    acc = [a for a in M.accepted if i in a["devices"]]
    if fs or ns or acc:
        o.append("<ul>%s%s%s</ul>" % ("".join('<li class="f"><b>%s</b> %s</li>' % (f["code"], esc(f["text"])) for f in fs),
                                      "".join('<li><b>accepted %s</b> %s <i>(%s; %s)</i></li>' % (a["code"], esc(a["text"]), esc(a["why"]), esc(a["src"])) for a in acc),
                                      "".join('<li class="n"><b>not proven</b> %s</li>' % esc(t) for t in ns)))
    o.append("</article>")
    return "\n".join(o)


def page(M):
    v = verdicts(M)
    cnt = collections.Counter(v.values())
    o = ['<!DOCTYPE html>', '<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
         '<title>ST185 circuit trace</title><style>%s</style></head><body>' % CSS,
         '<header><h1>ST185 circuit trace</h1><p>Generated by <code>docs/harness/tools/trace_circuits.py --write</code> from the master wire list, '
         '<code>sot/</code>, the fuse box wiring plan and <code>docs/harness/tools/trace_rules.json</code>. Never edit this page: rerun the tool.</p>'
         '<p>It traces the circuits of the new harnesses against electrical principles only (closed loop, no short, no back-feed, relay logic, '
         'no floating input, one fuse per load). No amps, wire sizes or voltage drop. A factory part is only an end point.</p></header><main>',
         '<div class="sum"><div><b>%d</b>devices</div><div><b style="color:#2e7d32">%d</b>pass</div><div><b style="color:#c62828">%d</b>fail</div>'
         '<div><b style="color:#ef8f00">%d</b>not proven</div><div><b>%d</b>findings</div><div><b>%d</b>scenarios x %d fuses pulled</div>'
         '<div><b>%d / %d</b>truth table rows match</div><div><b>%d / %d</b>CAN legs ok</div></div>' % (
             len(v), cnt["pass"], cnt["fail"], cnt["not proven"], len(M.findings), len(M.table), len(M.sim.fuses),
             sum(1 for _c, _n, b in M.tt if not b), len(M.tt), sum(1 for t in M.t9 if t["ok"]), len(M.t9)),
         '<h2>Checks</h2><table><tr><th>Check</th><th>What it proves</th><th>Findings</th></tr>%s</table>' % "".join(
             "<tr><td>%s</td><td>%s</td><td>%d</td></tr>" % (c, esc(t), sum(1 for f in M.findings if f["code"] == c)) for c, t in CHECKS),
         '<h2>Findings (%d)</h2>' % len(M.findings)]
    if M.findings:
        o.append("<ul>%s</ul>" % "".join('<li class="f"><b>%s</b> [%s] %s</li>' % (f["code"], esc(f["harness"] or "-"), esc(f["text"])) for f in M.findings))
    else:
        o.append("<p>None.</p>")
    if M.accepted:
        o.append('<h2>Accepted exceptions (%d)</h2><p class="small">What a check would flag, accepted by Dan as a named exception '
                 '(trace_rules.json "exceptions"); not a finding.</p><ul>%s</ul>' % (len(M.accepted), "".join(
                     '<li><b>%s</b> [%s] %s <i>Accepted: %s (%s)</i></li>' % (a["code"], esc(a["harness"] or "-"), esc(a["text"]), esc(a["why"]), esc(a["src"]))
                     for a in M.accepted)))
    o.append('<h2>Truth table: headlamps, DRL, pop-ups (from circuit-plan.md)</h2><table><tr><th>Stalk</th><th>DRL switch</th><th>Pods</th><th>Low</th>'
             '<th>High</th><th>DRL</th><th>LED</th><th>Cases run</th><th>Result</th></tr>%s</table>' % "".join(
                 "<tr>%s<td>%d</td><td>%s</td></tr>" % ("".join("<td>%s</td>" % esc(x) for x in c), n, "match" if not b else esc("; ".join(b[:3])))
                 for c, n, b in M.tt))
    o.append('<h2>CAN legs (T9)</h2><ul>%s</ul>' % "".join("<li><b>%s</b> %s</li>" % ("ok" if t["ok"] else "FAIL", esc(t["line"])) for t in M.t9))
    o.append('<h2>PCLink settings this wiring depends on (%d)</h2><p class="small">The repo holds no PCLink file for these: each line is what the ECU must be '
             'set to for the wiring to work as traced.</p><ul>%s</ul>' % (len(M.pclink), "".join("<li>%s</li>" % esc(p) for p in M.pclink)))
    if M.notes:
        o.append('<h2>Fuse side effects (not findings)</h2><ul>%s</ul>' % "".join("<li>%s</li>" % esc(n) for n in M.notes))
    o.append('<h2>Not proven (%d)</h2><ul>%s</ul>' % (len(M.unproven), "".join(
        '<li class="n">[%s] %s</li>' % (esc(h or "-"), esc(t)) for h, _d, t in M.unproven)))
    o.append('<h2>Devices</h2><div class="bar"><input id="q" placeholder="search a device, wire or fuse"><button data-v="" class="on">all</button>'
             '<button data-v="fail">fail</button><button data-v="np">not proven</button><button data-v="pass">pass</button></div>')
    rank = {h: n for n, h in enumerate(ORDER)}
    last = None
    for i in sorted(M.devices, key=lambda x: (rank.get(M.devices[x]["harness"], 99), x)):
        h = M.devices[i]["harness"] or "no harness"
        if h != last:
            if last is not None:
                o.append("</div>")
            o.append('<h2>%s</h2><div class="cards">' % esc(h))
            last = h
        o.append(card_html(M, i, v[i]))
    o.append("</div></main><script>%s</script></body></html>" % JS)
    return "\n".join(o) + "\n"


# ------------------------------------------------------------------------------------------------ T0: as built = the master
ASBUILT = os.path.join(CW.REPO, "_scratch", "asbuilt")       # gitignored: the pulled harness.design documents (never edited)
TITLE = re.compile(r"^ST185-([A-Za-z]+(?:-[A-Za-z]+)*?)(?: \d+ - .*?)? Rev ([A-Z]+)$")


def norm(x):
    return re.sub(r"[^A-Za-z0-9]", "_", x or "")


def end_fits(r, s, e):
    """does a drawn wire end (a harness.design {id, handle}) sit on this master end? -> '' or what differs"""
    t, i, p = r[s + "_type"], r[s + "_id"], r[s + "_pin"]
    if e is None:
        return "" if t == "cable screen" else "no end drawn"
    node = e["id"].split("_", 1)[1] if "_" in e["id"] else e["id"]
    if node.startswith("scr_"):
        node = node[4:]
        if t != "cable screen":
            return "drawn on a cable screen end"
        return "" if node.startswith(norm(i)) else "screen of %s" % node
    N, P, h = norm(i), norm(p), e.get("handle", "")
    if "." in h:
        return "" if (node == N and norm(h.split(".", 1)[1]) == P) else "%s %s" % (node, h.split(".", 1)[1])
    if node in (N, N + "_" + P, N + "__" + P):
        return ""
    if node.startswith(N + "_" + P + "_") or (not P and node.startswith(N + "_")):
        return ""            # one drawn end per signal of a flying lead, or the cowl / device end of a lead with one master ID
    return node


def asbuilt_compare(rows, docs):
    """T0: every wire of the master is drawn once, in a file of its own harness, on the same two ends, with the same wire
    part and colour; nothing is drawn that the master does not have. -> (per-document lines, findings)"""
    master = collections.OrderedDict((r["wire_id"], r) for r in rows if r["wire_id"] and not is_removal(r))
    seen = collections.defaultdict(list)
    out, lines = [], []
    for d in docs:
        title, doc = d.get("title", d["documentId"]), d["document"]
        m = TITLE.match(title)
        harness = m.group(1) if m else ""
        tag = "%s (%s)" % (title, d["documentId"])
        wp = {p["id"]: p["partNumber"] for p in doc.get("wireParts", [])}
        cp = {p["id"]: p["partNumber"] for p in doc.get("cableParts", [])}
        anode_right = {x["id"]: x.get("anodeOnRight") for x in doc.get("diodes", [])}
        items = [(w["id"][2:], w, wp.get(w.get("partId", ""), ""), "wire") for w in doc.get("wires", [])]
        for c in doc.get("cables", []):
            items += [(k["id"][3:], k, cp.get(c.get("partId", ""), ""), "core") for k in c.get("cores", [])]
            if c.get("shield"):
                items.append((c["shield"]["id"][3:], c["shield"], "", "screen"))
        for mt in doc.get("mates", []):
            if mt["id"][2:] in master:
                items.append((mt["id"][2:], {"source": {"id": mt["sourceId"], "handle": mt["sourceId"][2:] + "." + master[mt["id"][2:]]["from_pin"]},
                                             "target": {"id": mt["targetId"], "handle": mt["targetId"][2:] + "." + master[mt["id"][2:]]["to_pin"]}}, "", "mate"))
        n = bad = ghosts = 0
        for wid, it, part, kind in items:
            if wid.startswith("gh_"):          # a ghost: another harness's wire shown where it rides this bundle (Dan T4 a)
                g = master.get(wid[3:])
                ghosts += 1
                if g is None:
                    out.append((harness, "%s: ghost wire %s names no wire of the master" % (tag, wid[3:])))
                elif g["harness"] == harness:
                    out.append((harness, "%s: %s is drawn as a ghost in a file of its own harness" % (tag, wid[3:])))
                continue
            r = master.get(wid)
            if r is None:
                if "_nc_" in it["id"] or (it.get("source") is None and it.get("target") is None):
                    continue                                   # a spare core of a cable, drawn unconnected
                out.append((harness, "%s: %s %s is drawn but is not a wire of the master" % (tag, kind, wid)))
                bad += 1
                continue
            n += 1
            seen[wid].append(tag)
            a, b = it.get("source"), it.get("target")
            fits = [x for x in ((end_fits(r, "from", a), end_fits(r, "to", b)), (end_fits(r, "from", b), end_fits(r, "to", a)))]
            best = min(fits, key=lambda f: sum(1 for x in f if x))
            errs = []
            if any(best):
                errs.append("ends drawn %s, master has %s %s -> %s %s" % (
                    " / ".join(x for x in best if x), r["from_id"], r["from_pin"], r["to_id"], r["to_pin"]))
            if harness and r["harness"] != harness:
                errs.append("drawn in a %s file, the master puts it in %s" % (harness, r["harness"]))
            if kind == "wire" and r["wire_pn"] and not is_integral(r) and part != r["wire_pn"]:
                errs.append("wire part %s, master %s" % (part or "none", r["wire_pn"]))
            if kind == "core" and r["cable_pn"] and part != r["cable_pn"]:
                errs.append("cable part %s, master %s" % (part or "none", r["cable_pn"]))
            if kind in ("wire", "core") and r["colour"] and it.get("color") and it["color"].lower() != r["colour"].lower():
                errs.append("colour %s, master %s" % (it["color"], r["colour"]))
            for sd, e in (("from", a), ("to", b)) if not any(fits[0]) else ():
                if e and e["id"] in anode_right and r[sd + "_pin"] in ("1", "2"):
                    anode = "Right" if anode_right[e["id"]] else "Left"
                    if (e.get("handle") == anode) != (r[sd + "_pin"] == "1"):
                        errs.append("%s is drawn on the wrong side of diode %s (master pin %s; pin 1 is the anode)" % (wid, r[sd + "_id"], r[sd + "_pin"]))
            if errs:
                bad += 1
                out.append((r["harness"], "%s: %s %s - %s" % (tag, kind, wid, "; ".join(errs))))
        lines.append("%-64s %3d drawn, %3d differ, %2d ghost wires" % (tag, n, bad, ghosts))
    for wid, r in master.items():
        if wid not in seen:
            out.append((r["harness"], "wire %s (%s, %s %s -> %s %s) is in the master but drawn in no harness.design file" % (
                wid, r["harness"], r["from_id"], r["from_pin"], r["to_id"], r["to_pin"])))
        elif len(seen[wid]) > 1:
            out.append((r["harness"], "wire %s is drawn %d times: %s" % (wid, len(seen[wid]), "; ".join(seen[wid]))))
    return lines, out


def doc_from_master(rows, harness, doc_id="TEST", rev="A"):
    """a harness.design document the way the generators draw one (self-test only)"""
    wires, parts = [], {}

    def end(r, s):
        t, i, p = r[s + "_type"], r[s + "_id"], r[s + "_pin"]
        if t == "connector":
            return {"id": "c_" + norm(i), "handle": norm(i) + "." + p}
        if t == "splice":
            return {"id": "s_" + norm(i), "handle": "Splice"}
        return {"id": "t_" + norm(i) + ("_" + norm(p) if p else ""), "handle": "Terminal"}
    for r in rows:
        if r["wire_id"] and r["harness"] == harness and not is_removal(r) and r["from_type"] != "cable screen" and not r["cable"]:
            pid = norm(r["wire_pn"])
            parts[pid] = r["wire_pn"]
            wires.append({"id": "w_" + r["wire_id"], "color": r["colour"], "partId": pid, "source": end(r, "from"), "target": end(r, "to")})
    return {"documentId": doc_id, "title": "ST185-%s Rev %s" % (harness, rev),
            "document": {"wires": wires, "wireParts": [{"id": k, "partNumber": v} for k, v in parts.items()]}}


def asbuilt_run(folder):
    _h, rows = CW.read_csv(CW.MASTER)
    files = sorted(f for f in os.listdir(folder) if f.endswith(".json")) if os.path.isdir(folder) else []
    if not files:
        print("trace_circuits --asbuilt: no documents in %s. Pull each current harness.design file there first (harness_design MCP: "
              "list_harnesses \"ST185\", get_document_json), one <documentId>.json each; nothing is ever edited." % os.path.relpath(folder, CW.REPO))
        return 1
    docs = []
    for f in files:
        with open(os.path.join(folder, f), encoding="utf-8") as fh:
            d = json.load(fh)
        d.setdefault("documentId", f[:-5])
        d.setdefault("title", d.get("document", {}).get("title", d["documentId"]))
        docs.append(d)
    lines, out = asbuilt_compare(rows, docs)
    print("T0 - each harness.design file as built = the master (%d documents, pulled into %s)" % (len(docs), os.path.relpath(folder, CW.REPO)))
    for ln in lines:
        print("  " + ln)
    for h, t in out:
        print("FINDING T0 [%s] %s" % (h, t))
    print("trace_circuits --asbuilt: %d finding(s)" % len(out))
    return 1 if out else 0


def self_test():
    rows, plan, seats, channels, rules, cp = load_all()
    M0 = run(rows, plan, seats, channels, rules, cp)
    base = {(f["code"], f["text"]) for f in M0.findings}
    cases = []

    def case(name, code, word, rs=None, pl=None, ru=None, pulls=False):
        got = run(rs or rows, pl or plan, seats, channels, ru or rules, cp, pulls=pulls).findings
        new = [f for f in got if (f["code"], f["text"]) not in base]
        cases.append((name, any(f["code"] == code and word in f["text"] for f in new)))

    def reland(wire, at, **upd):
        rs = copy.deepcopy(rows)
        r = next(r for r in rs if r["wire_id"] == wire)
        sd = "from" if r["from_id"] == at else "to"
        r.update({sd + "_" + k: v for k, v in upd.items()})
        return rs
    nowhere = dict(type="splice", id="SP-NOWHERE", pin="", name="a splice with one leg")
    case("open: the fuel pump ground wire ends on a one-leg splice", "T1", "FUEL-PUMP", reland("w_fpg", "GND-BL", **nowhere))
    case("open: the trunk relay block feed wire removed", "T1", "FUEL-PUMP", [r for r in rows if r["wire_id"] != "w_fp_feed"])
    case("short: the fuel pump relay output landed on ground BL", "T2", "SHORT",
         reland("w_fpump_r", "FUEL-PUMP", type="terminal", id="GND-BL", pin="", name="Ground point BL", desc="Ground"))
    pl = copy.deepcopy(plan)
    pl["wires"] = [w for w in pl["wires"] if w["wire"] != "w_fpump_r"]
    case("missing box cavity: K-FP 87 gone from the box plan", "B1", "K-FP", pl=pl)
    pl = copy.deepcopy(plan)
    pl["wires"] = [w for w in pl["wires"] if w["wire"] != "w_hr_cp"]
    case("missing box wire: the HR fuse output has no wire in the box plan", "B1", "BUS1-3", pl=pl)
    case("an end with no pin text is listed", "C1", "MAP", reland("w206", "MAP", desc=""))
    c = next(e for e in M0.elems if e["dev"] == "FUEL-PUMP")
    line = chain_line(M0, c)
    cases.append(("RearFuel: battery -> FP fuse -> K-FP -> pump -> ground", all(
        x in line for x in ("battery +", "FP 40 A", "K-FP 30-87", "FUEL-PUMP", "battery -"))
        and line.index("battery +") < line.index("FP 40 A") < line.index("K-FP 30-87") < line.index("FUEL-PUMP") < line.index("battery -")))
    # ---- the solver
    sim = M0.sim
    low = {"stalk": "3"}
    hl = next(c for _a, _b, c in sim.fuses if "BUS1-2" in c.label)
    cases.append(("solver: low beams on at HEAD, off with the kill switch open",
                  sim.solve(low).elem["H1.low beam"] == "ON" and sim.solve(dict(low, kill=False)).elem["H1.low beam"] == "OFF"))
    cases.append(("pulled fuse: the HL fuse out turns both low beams off",
                  [sim.solve(low, pulled=(hl,)).elem[i] for i in ("H1.low beam", "H2.low beam")] == ["OFF", "OFF"]))
    rs = copy.deepcopy(rows)
    r = dict(next(r for r in rs if r["wire_id"] == "w_hl_30_cp"))
    sd, ot = ("from", "to") if r["from_id"] == "SP-HL" else ("to", "from")
    r.update({"wire_id": "w_test_backfeed", ot + "_type": "splice", ot + "_id": "SP-HZ", ot + "_pin": "", ot + "_name": "Hazard and horn fuse splice",
              "net": "SP-HL"})
    rs.append(r)
    case("pulled fuse: a second feed from the HZ fuse onto the low-beam splice is a back-feed", "BF", "H1.low beam", rs, pulls=True)
    case("one fuse per load: the same second feed is listed as fed from 2 places", "F1", "H1.low beam", rs)
    case("open ground: the LH headlamp ground on a one-leg splice", "T7", "H1.low beam", reland("w_h1_gnd", "GND-EB", **nowhere))
    rs = copy.deepcopy(rows)
    for r in rs:
        for sd in ("from", "to"):
            if r[sd + "_id"] == "D-R8-1":
                r[sd + "_pin"] = {"1": "2", "2": "1"}[r[sd + "_pin"]]
    ru = copy.deepcopy(rules)
    case("reversed diode: pop-up diode D1 fitted backwards (the stalk no longer raises the pods)", "TT", "Pods", rs)
    ru["parts"]["K-FAN2"]["cathode"] = "85"
    case("reversed diode: a diode-coil relay with coil + on the anode side", "T6", "K-FAN2", ru=ru)
    ru = copy.deepcopy(rules)
    ru["parts"]["KILL-SW"]["contacts"][0][2] = "no_such_input"
    case("a rule that does not evaluate is listed", "C1", "no_such_input", ru=ru)
    case("floating input: the A/C amp coolant-OK ground wire goes nowhere", "T7", "floating", reland("w_ac_cool_gnd", "GND-IG", **nowhere))
    case("open input: the ignition sense wire to ECU DI 9 goes nowhere", "T7", "DI 9", reland("w_ign", "JB1", type="splice", id="SP-NOWHERE", pin="", name="x"))
    case("CAN leg: the opto input return removed (brake never reaches VDI7)", "T9", "brake", [r for r in rows if r["wire_id"] != "w_opto_inc"])
    ru = copy.deepcopy(rules)
    ru["csb3"]["switches"]["S5"] = ru["csb3"]["switches"].pop("S6")
    case("CAN leg: the clutch on a board input the CAN map does not assign", "T9", "clutch", ru=ru)
    case("a one-leg splice is a dead end", "T1", "SP-NOWHERE", reland("w_fpg", "GND-BL", **nowhere))
    ru = copy.deepcopy(rules)
    ru["exceptions"] = [x for x in ru.get("exceptions", []) if not (x["check"] == "F1" and x.get("device") == "T-STARTER-B")]
    case("named exception removed: the unfused starter B+ cable is a finding again", "F1", "T-STARTER-B", ru=ru)
    cases.append(("named exception: the starter B+ cable is listed as accepted, not a finding (Dan A68 a)",
                  any(a["device"] == "T-STARTER-B" for a in M0.accepted) and not any(f["device"] == "T-STARTER-B" for f in M0.findings)))
    ru = copy.deepcopy(rules)
    ru["exceptions"] = [x for x in ru.get("exceptions", []) if "Dan A70 a" not in x["src"]]
    case("named exception removed: the ECU wake diode back-feed on the SW12 bus is a finding again (Dan A70 a)", "BF", "ECU wake diode", ru=ru, pulls=True)
    case("named exception removed: the SW12 bus loads fed from 2 places are a finding again (Dan A70 a)", "F1", "SW12 5 A", ru=ru)
    ru = copy.deepcopy(rules)
    next(w for w in ru["watch"] if w["pin"] == "ECU-B:30").pop("float")
    case("rule removed: ECU DI 7 (pull-up OFF) floating is a finding again (Dan A73 a)", "T8", "DI 7", ru=ru)
    # ---- overrides (Dan A75 a): one exception = Dan's permission (question ID + date) for exactly one finding
    cases.append(("overrides: every current exception names Dan's ID + date and covers exactly one finding (A68 a, A70 a)",
                  not any(f["code"] == "EX" for f in M0.findings)
                  and sorted(collections.Counter(a["ex"] for a in M0.accepted).values()) == [1] * len(rules["exceptions"])))
    ru = copy.deepcopy(rules)
    next(x for x in ru["exceptions"] if x.get("device") == "T-STARTER-B")["src"] = "Dan said so; starting system 1993 TIS EWD p.66"
    case("override: an exception whose src has no Dan question ID + date fails", "EX", "no Dan question ID", ru=ru)
    ru = copy.deepcopy(rules)
    ru["exceptions"].append({"check": "F1", "text_has": "no finding has this text", "why": "test", "src": "Dan A99 a 2026-11-16"})
    case("override: a stale exception (matches no current finding) fails", "EX", "stale override", ru=ru, pulls=True)
    ru = copy.deepcopy(rules)
    ru["exceptions"] = [x for x in ru["exceptions"] if x["check"] != "BF"] + [
        {"check": "BF", "text_has": "[ECU wake diode (ignition feed)]", "why": "test", "src": "Dan A70 a 2026-11-16"}]
    case("override: one exception covering 2 findings (both wake-diode back-feeds) fails", "EX", "covers 2 findings", ru=ru, pulls=True)
    good = [doc_from_master(rows, "RearFuel"), doc_from_master(rows, "CabinPower"), doc_from_master(rows, "HeavyDC")]
    mine = [r for r in rows if r["harness"] in ("RearFuel", "CabinPower", "HeavyDC")]
    cases.append(("as built: files drawn from the master give no finding", asbuilt_compare(mine, good)[1] == []))
    d = copy.deepcopy(good)
    d[0]["document"]["wires"][0]["target"] = {"id": "c_FUEL_PUMP", "handle": "FUEL_PUMP.9"}
    cases.append(("as built: a wire drawn on another cavity is caught", any("ends drawn" in t for _h, t in asbuilt_compare(mine, d)[1])))
    d = copy.deepcopy(good)
    gone = d[0]["document"]["wires"].pop()["id"][2:]
    cases.append(("as built: a master wire drawn in no file is caught", any(gone in t and "drawn in no" in t for _h, t in asbuilt_compare(mine, d)[1])))
    d = copy.deepcopy(good)
    d[0]["document"]["wires"].append(dict(d[0]["document"]["wires"][0], id="w_w_not_in_master"))
    cases.append(("as built: a drawn wire the master does not have is caught", any("not a wire of the master" in t for _h, t in asbuilt_compare(mine, d)[1])))
    d = copy.deepcopy(good)
    d[0]["document"]["wireParts"][0]["partNumber"] = "WRONG-PART"
    cases.append(("as built: a different wire part is caught", any("wire part WRONG-PART" in t for _h, t in asbuilt_compare(mine, d)[1])))
    text = page(M0)
    cases.append(("report page: one card per device, the same text on a second build",
                  text.count('<article class="card') == len(M0.devices) and 'id="dev-FUEL-PUMP"' in text
                  and text == page(run(rows, plan, seats, channels, rules, cp))))
    bad = [n for n, ok in cases if not ok]
    for n, ok in cases:
        print("%-5s %s" % ("ok" if ok else "FAIL", n))
    print("%d self-test failure(s)." % len(bad))
    return 1 if bad else 0


def main(argv):
    if "--self-test" in argv:
        return self_test()
    if "--asbuilt" in argv:
        n = argv.index("--asbuilt")
        return asbuilt_run(argv[n + 1] if len(argv) > n + 1 and not argv[n + 1].startswith("--") else ASBUILT)
    M = run(*load_all())
    text = page(M)
    if "--write" in argv:
        with open(PAGE, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        v = collections.Counter(verdicts(M).values())
        print("wrote %s: %d devices (pass %d, fail %d, not proven %d), %d finding(s)" % (
            os.path.relpath(PAGE, CW.REPO), len(M.devices), v["pass"], v["fail"], v["not proven"], len(M.findings)))
        return 0
    if "--check" in argv:
        cur = open(PAGE, encoding="utf-8").read().replace("\r\n", "\n") if os.path.exists(PAGE) else ""
        stale = cur != text
        if stale:
            print("trace_circuits --check: docs/harness/CIRCUIT-TRACE.html is stale; run trace_circuits.py --write")
        for f in M.findings:
            print("FINDING %s [%s] %s" % (f["code"], f["harness"], f["text"][:300]))
        print("trace_circuits --check: page %s, %d finding(s), %d not proven" % ("STALE" if stale else "current", len(M.findings), len(M.unproven)))
        return 1 if stale or M.findings else 0
    report(M, argv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
