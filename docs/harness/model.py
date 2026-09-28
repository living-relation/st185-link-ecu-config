"""Shared reader for the looms and the interface registry.

Every drawing in rebuild/ is plain harness.design JSON. What the app cannot hold -
which physical harness owns a thing, which two connectors form an inline pair,
which loose ends are OEM flying leads or device endpoints - lives in
interfaces.json next to this file. See redesign/INTERFACES.md.

The graph built here is electrical: one node per physical point, whichever
drawing names it. Mated bulkhead halves, the two halves of an inline interface,
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
SHIELD_PINS = {("ecu_a", "a7"): "A", ("ecu_b", "b17"): "B"}
XREF_PART = "cp_xref"


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
        return json.load(f)


def docs(reg=None):
    return collections.OrderedDict((k, load(fn)) for k, fn in harness_files(reg).items())


def sot_rows():
    with open(SOT, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parts(d):
    return {p["id"]: p for k in d if k.endswith("Parts") for p in d[k]}


def conductors(d):
    """(conductor, cable id or None, is_screen) for every wire, core and screen."""
    for w in d.get("wires", []):
        tail = w["id"].rsplit("_", 1)[-1]
        screen = (w.get("color") == "Shield" or tail in ("sh", "shield", "drain")
                  or w["id"].startswith("w_drain"))
        yield w, None, screen
    for cb in d.get("cables", []):
        for co in cb.get("cores", []):
            yield co, cb["id"], False
        if cb.get("shield"):
            yield cb["shield"], cb["id"], True


def is_xref(c):
    return c.get("partId") == XREF_PART


def interface_halves(reg):
    """(harness, connector id) -> (interface id, role) for every inline half."""
    out = {}
    for ix in reg.get("interfaces", []):
        for h in ix["halves"]:
            out[(h["harness"], h["connector"])] = (ix["id"], h["role"])
    return out


def enclosure_nodes(reg):
    """(harness, terminal id) -> enclosure id for every screen landing that a
    device enclosure joins internally (SHIELD-RULES 6.30)."""
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
        if (loom, nid) in self.enc:
            return ("ENC", self.enc[(loom, nid)])
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
