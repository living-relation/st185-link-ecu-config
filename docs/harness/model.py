"""Shared reader for the looms and the interface registry.

Every drawing in rebuild/ is plain harness.design JSON. What the app cannot hold -
which physical harness owns a thing, which two connectors form an inline pair,
which loose ends are OEM flying leads or device endpoints - lives in
interfaces.json next to this file. See redesign/INTERFACES.md.

The graph built here is electrical: one node per physical point, whichever
drawing names it. Mated bulkhead halves, the two halves of an inline interface,
connector pairs mated inside one drawing, the two ends of a broken-off wire,
cross-reference dummies and the inside of a VRC enclosure all collapse onto one
node, so a net can be walked across every loom at once.
"""
import collections
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REB = os.path.join(HERE, "rebuild")
REGISTRY = os.path.join(HERE, "interfaces.json")
SOT = os.path.join(HERE, "..", "..", "sot", "channels.csv")

BULKHEAD_MATE = {"bh_a_fw": "bh_a_eng", "bh_a_eng": "bh_a_fw",
                 "bh_b_fw": "bh_b_eng", "bh_b_eng": "bh_b_fw"}
SHIELD_PINS = {("ecu_a", "a7"): "A", ("ecu_b", "b17"): "B", ("ecu_com", "c1"): "CAN"}
XREF_PART = "cp_xref"
# Drains are found by their part, never by colour: M22759/16-20-06, black/blue,
# used for nothing else (docs/SHIELD-RULES.md).
DRAIN_PART = "m16_20_06"


def registry():
    with open(REGISTRY, encoding="utf-8") as f:
        return json.load(f)


def harness_files(reg=None):
    """loom name -> filename, in registry order. Every file in rebuild/ must be
    listed; validate_ownership.py fails otherwise."""
    reg = reg or registry()
    return collections.OrderedDict((k, v["file"]) for k, v in reg["harnesses"].items())


def load(fn):
    with open(os.path.join(REB, fn), encoding="utf-8") as f:
        return full_text(json.load(f), fn)


# The app shows connector labels and cavity / terminal signals as the wiring table's
# Destination and in layout "Show destinations", so the drawings carry short ones
# (gate audit_destinations.py). The long text they replaced lives in full_text.json as
# [short, long] pairs, and the gates read it back here so they see the long text as
# before. A pair is put back only while the drawing still holds its short text: if Dan
# renames something in the app, his name wins.
FULL_TEXT = os.path.join(HERE, "full_text.json")
_FULL = None


def full_text(d, fn):
    global _FULL
    if _FULL is None:
        with open(FULL_TEXT, encoding="utf-8") as f:
            _FULL = json.load(f)
    rec = _FULL.get(os.path.basename(fn))
    if not rec:
        return d

    def put(obj, key, pair):
        # R156: a relabelled terminal carries no signal (its label says where it lands); its
        # pair is ["", long] so the gates still read the long text.
        if pair and (obj.get(key) or "") == pair[0]:
            obj[key] = pair[1]

    for c in d.get("connectors", []):
        r = rec["connectors"].get(c["id"], {})
        put(c, "label", r.get("label"))
        for x in c.get("cavities", []):
            put(x, "signal", r.get("cavities", {}).get(x["id"]))
    for t in d.get("terminals", []):
        put(t, "signal", rec["terminals"].get(t["id"]))
    return d


def docs(reg=None):
    return collections.OrderedDict((k, load(fn)) for k, fn in harness_files(reg).items())


def sot_rows():
    with open(SOT, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parts(d):
    return {p["id"]: p for k in d if k.endswith("Parts") for p in d[k]}


# harness.design file format version of every file in rebuild/ (DECISIONS R111: the repo
# follows the desktop app's current schema, so the app never rewrites a file on open).
FORMAT_VERSION = 1.2
FORMAT_SCHEMA = "https://docs.harness.design/files/harness/schema/v1.2.json"

# Part configurations. The files are harness.design v1.2 (DECISIONS R111): a configuration's
# parts are an ordered `accessories` list of {id, type, partId, rule?}. v0.9 held them as
# single *PartId fields; those are still read so an old file does not silently lose its parts.
# https://docs.harness.design/files/harness/part-library.md "Configurations and accessories"
CFG_V09 = {"LockPart": "lockPartId", "DustCoverPart": "dustCoverPartId",
           "BackshellPart": "backshellPartId", "ContactPart": "contactPartId",
           "BootPart": "bootPartId", "MountPart": "mountPartId",
           "CavityPlugPart": "cavityPlugPartId"}
# Loaded per cavity by rule; every other accessory type counts once per component.
CAVITY_TYPES = ("ContactPart", "CavityPlugPart", "CavitySealPart")


def cfg_accessories(cfg):
    """[(type, partId, rule)] of a part configuration, in list order, filled slots only."""
    cfg = cfg or {}
    out = [(a.get("type"), a.get("partId"), a.get("rule"))
           for a in cfg.get("accessories") or [] if a.get("partId")]
    return out + [(t, cfg[k], None) for t, k in CFG_V09.items() if cfg.get(k)]


def cfg_default(cfg, typ):
    """The part a configuration loads into a cavity by default: its first `typ` accessory
    (ContactPart for a wired cavity, CavityPlugPart for an empty one), or None. The app's
    rule matching (gauge / cavity size / apply) is not modelled here, so a rule fails loudly
    instead of giving a wrong default."""
    for t, pid, rule in cfg_accessories(cfg):
        if t == typ:
            if rule:
                raise ValueError("configuration %s: %s %s has a rule - not modelled by model.py"
                                 % ((cfg or {}).get("id"), typ, pid))
            return pid
    return None


def conductors(d):
    """(conductor, cable id or None, is_screen) for every wire, core and screen."""
    for w in d.get("wires", []):
        yield w, None, is_drain(w)
    for cb in d.get("cables", []):
        for co in cb.get("cores", []):
            yield co, cb["id"], False
        if cb.get("shield"):
            yield cb["shield"], cb["id"], True


def is_drain(w):
    """A drain wire is the drain part; the id tails are a fallback for an unparted wire."""
    tail = w["id"].rsplit("_", 1)[-1]
    return (w.get("partId") == DRAIN_PART or tail in ("sh", "shield", "drain")
            or w["id"].startswith("w_drain"))


def is_xref(c):
    return c.get("partId") == XREF_PART


def interface_halves(reg):
    """(harness, connector id) -> (interface id, role) for every inline half."""
    out = {}
    for ix in reg.get("interfaces", []):
        for h in ix["halves"]:
            for loom in [h["harness"]] + h.get("alsoDrawnOn", []):
                out[(loom, h["connector"])] = (ix["id"], h["role"])
    return out


def break_ends(reg):
    """(harness, terminal id) -> break id for both ends of every broken-off pair: one
    physical wire drawn in two sections, each ending at a noted Loose terminal."""
    out = {}
    for br in reg.get("breaks", []):
        for e in br["ends"]:
            out[(e["harness"], e["terminal"])] = br["id"]
    return out


def mate_halves(reg, ds):
    """(harness, connector id) -> mate key for connector pairs mated inside one drawing
    (interfaces.json inFileMates); both halves collapse to one node per cavity."""
    out = {}
    for m in reg.get("inFileMates", []):
        d = ds.get(m["harness"]) or {}
        mate = next((x for x in d.get("mates", []) if x["id"] == m["mate"]), None)
        if mate:
            for cid in (mate["sourceId"], mate["targetId"]):
                out[(m["harness"], cid)] = "%s:%s" % (m["harness"], m["mate"])
    return out


def bussed_plugs(reg):
    """(harness, plug id) -> splice id for every splice built as a bussed DT pair
    (interfaces.json "bussedSplices", DECISIONS R169): the mated DT04 P021 receptacle
    buses every pin, so all of the plug's cavities are the one node the splice was."""
    return {(b["harness"], b["plug"]): b["splice"]
            for b in reg.get("bussedSplices", {}).get("buses", [])}


def endpoint_ends(ep):
    """role -> (id, handle) for a device endpoint. Two forms (interfaces.json "endpoints"):
    "terminals" {role: Loose terminal id}, or - where the harness-side mating plug is drawn
    (front VRC IN M8 cable plugs, Daniel 2026-10-12) - "connector" plus "pins" {role: cavity}."""
    if ep.get("connector"):
        return {r: (ep["connector"], c) for r, c in ep["pins"].items()}
    return {r: (t, "Terminal") for r, t in ep["terminals"].items()}


def enclosure_nodes(reg):
    """(harness, terminal id) -> enclosure id for every screen landing that a
    device enclosure joins internally (SHIELD-RULES 6.30). A "connector.cavity"
    entry is a screen pin on a drawn mating plug (keyed (harness, "conn.cav"))."""
    out = {}
    for enc in reg.get("enclosures", []):
        for t in enc["screen"]:
            out[(enc["harness"], t)] = enc["id"]
    return out


class Graph:
    """Electrical graph across every loom."""

    def __init__(self, reg=None, ds=None):
        self.reg = reg or registry()
        self.docs = ds or docs(self.reg)
        self.ix = interface_halves(self.reg)
        self.enc = enclosure_nodes(self.reg)
        self.brk = break_ends(self.reg)
        self.mates = mate_halves(self.reg, self.docs)
        self.bus = bussed_plugs(self.reg)
        self.components = set()
        for d in self.docs.values():
            for k in ("connectors", "terminals", "resistors", "diodes", "splices"):
                for c in d.get(k, []):
                    if not c["id"].startswith("dm_") and not is_xref(c):
                        self.components.add(c["id"])
        self.adj = collections.defaultdict(set)
        self.where = collections.defaultdict(list)
        for loom, d in self.docs.items():
            for cond, cable, screen in conductors(d):
                s, t = cond.get("source") or {}, cond.get("target") or {}
                ends = [self.node(loom, e) for e in (s, t) if e.get("id")]
                for n in ends:
                    self.where[n].append((loom, cond["id"]))
                if len(ends) == 2:
                    self.adj[ends[0]].add(ends[1])
                    self.adj[ends[1]].add(ends[0])

    def node(self, loom, e):
        nid, h = e.get("id", ""), e.get("handle")
        if nid in ("ecu_a", "ecu_b", "ecu_com"):
            return ("ECU", nid, h)
        if nid.startswith(("dm_ecu_a_", "dm_ecu_b_")):
            p = nid.split("_")
            return ("ECU", "ecu_" + p[2], p[3])
        if (loom, nid) in self.ix:
            return ("IX", self.ix[(loom, nid)][0], h)
        if (loom, nid) in self.mates:
            return ("IX", self.mates[(loom, nid)], h)
        if (loom, nid) in self.bus:
            return ("SP", self.bus[(loom, nid)])
        if (loom, nid) in self.brk:
            return ("BRK", self.brk[(loom, nid)])
        if (loom, nid) in self.enc:
            return ("ENC", self.enc[(loom, nid)])
        if h and (loom, "%s.%s" % (nid, h)) in self.enc:
            return ("ENC", self.enc[(loom, "%s.%s" % (nid, h))])
        if nid.startswith("dm_"):
            body = nid[3:]
            if body.endswith("_Splice"):
                return ("SP", body[:-7])
            if body.startswith("bh_"):
                bh, cav = body.rsplit("_", 1)
                return ("BH", min(bh, BULKHEAD_MATE.get(bh, bh)), cav)
            comp, _, cav = body.rpartition("_")
            if comp in self.components:
                return self.node(loom, {"id": comp, "handle": cav})
            return ("DM", nid)
        if nid in BULKHEAD_MATE:
            return ("BH", min(nid, BULKHEAD_MATE[nid]), h)
        if h == "Splice" or nid.startswith("sp_"):
            return ("SP", nid)
        if h == "Terminal":
            return ("T", loom, nid)
        return ("C", nid, h)

    def reach(self, start, stop=lambda n: False):
        seen, todo = {start}, [start]
        while todo:
            n = todo.pop()
            for m in self.adj.get(n, ()):
                if m in seen:
                    continue
                seen.add(m)
                if not stop(m):
                    todo.append(m)
        return seen

    def path(self, a, b):
        prev, todo = {a: None}, collections.deque([a])
        while todo:
            n = todo.popleft()
            if n == b:
                out = []
                while n is not None:
                    out.append(n)
                    n = prev[n]
                return out[::-1]
            for m in self.adj.get(n, ()):
                if m not in prev:
                    prev[m] = n
                    todo.append(m)
        return None


def fmt(n):
    return ":".join(str(x) for x in n)
