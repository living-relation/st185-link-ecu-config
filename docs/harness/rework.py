"""Rework the ST185 harness files into the six-file structure of plan 6.14.

Reads the three current .harness files, applies every change settled 2026-09-17,
and writes a fresh set into docs/harness/rework/ for review. NOTHING in
docs/harness/ is modified - the originals stay put until Daniel OKs the new set.

    python docs/harness/rework.py

Changes applied, each logged as it runs:
  1  delete bulkhead C (6.1) and everything hanging off it
  2  delete w_mrs_relay_req - the pump does not switch its own relay (6.16)
  3  move all EPS wiring and both fans to loom C (6.17)
  4  move the wheel-speed sensors and conditioners to their own loom (6.14)
  5  rewire the cam resistor as a real pull-up on the ECU side
  6  mrs_ctrl becomes a 6-way, spare cavities marked unused
  7  add the ECU-driven EPS relay trigger on Ign 6 / B12 (6.16)
  8  split loom A and loom B at the firewall (6.14)
  9  replace every cross-file component with a dummy block (6.15)
"""
import json, io, os, collections, copy

R = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(R, "rework")

CABIN_BH = {"bh_a_fw", "bh_b_fw"}
ENGINE_BH = {"bh_a_eng", "bh_b_eng"}
BH = CABIN_BH | ENGINE_BH

# --- what moves where -------------------------------------------------
TO_LOOM_C = {"k_eps", "mrs_pwr", "mrs_en", "mrs_ctrl", "rad_fan", "fan2"}
TO_WHEELSPEED = {"wss_fl", "wss_fr", "wss_rl", "wss_rr",
                 "vr1_ch1n", "vr1_ch1p", "vr1_ch2n", "vr1_ch2p",
                 "vr2_ch1n", "vr2_ch1p", "vr2_ch2n", "vr2_ch2p",
                 "vr1_out1", "vr1_out2", "vr2_out1", "vr2_out2",
                 "vr1_gnd", "vr2_gnd", "vr1_pwr", "vr2_pwr",
                 "sp_shield_rear"}
DELETE_NODES = {"bh_c_fw", "bh_c_eng"}
DELETE_WIRES = {"w_mrs_relay_req", "w23", "w20_e"}

# nodes that sit on the engine side but cannot be reached from a bulkhead
HAND_PLACED = {
    "t_batt_pos": "ECU", "t_batt_neg": "ECU",
    "rl_pos_fw": "ECU", "rl_neg_fw": "ECU",
    "rl_pos_eng": "engine", "rl_neg_eng": "engine",
    "t_starter_b": "engine", "t_alt_b": "engine", "t_eng_block": "engine",
    "fuelpump": "ECU", "fuellvl": "ECU", "starter_trigger": "engine",
    "batt_ring": "ECU", "chassis_ring": "ECU",
}
# crossings with no bulkhead pin yet - cut so the classifier does not smear
CUT = {"w_strl"}

NODE_KEYS = ["connectors", "splices", "terminals", "diodes", "resistors",
             "branchPoints", "groups"]
PART_KEYS = ["connectorParts", "contactParts", "wireParts", "cableParts",
             "bootParts", "coveringParts", "spliceParts", "terminalParts"]
LOG = []


def log(msg):
    LOG.append(msg)
    print("  " + msg)


def load(fn):
    return json.load(io.open(os.path.join(R, fn), encoding="utf-8"))


def ends(w):
    return ((w.get("source") or {}).get("id"), (w.get("target") or {}).get("id"))


def drop_nodes(doc, ids, why):
    """Remove nodes and every wire that touched them."""
    n0 = len(doc.get("wires", []))
    for k in NODE_KEYS:
        if k in doc:
            doc[k] = [e for e in doc[k] if e.get("id") not in ids]
    doc["wires"] = [w for w in doc["wires"]
                    if not (set(ends(w)) & ids)]
    for k in ("mates", "bundles"):
        if k in doc:
            doc[k] = [b for b in doc[k]
                      if b.get("sourceId") not in ids and b.get("targetId") not in ids]
    gone = n0 - len(doc["wires"])
    if gone or ids:
        log("%s: dropped %d node(s), %d wire(s)" % (why, len(ids), gone))


def extract(doc, ids, why):
    """Pull nodes and their internal wires out of doc. Returns (nodes, wires)."""
    taken_nodes = collections.defaultdict(list)
    for k in NODE_KEYS:
        keep, take = [], []
        for e in doc.get(k, []):
            (take if e.get("id") in ids else keep).append(e)
        if take:
            taken_nodes[k] = take
            doc[k] = keep
    inner, rest = [], []
    for w in doc.get("wires", []):
        s, t = ends(w)
        if s in ids and t in ids:
            inner.append(w)
        else:
            rest.append(w)
    doc["wires"] = rest
    log("%s: took %d node(s), %d internal wire(s)" %
        (why, sum(len(v) for v in taken_nodes.values()), len(inner)))
    return taken_nodes, inner


def classify(doc):
    """Label every node ECU-side or engine-side, cutting at the bulkheads."""
    adj = collections.defaultdict(set)
    for w in doc.get("wires", []):
        if w.get("id") in CUT:
            continue
        s, t = ends(w)
        if s in BH or t in BH:
            continue
        if s and t:
            adj[s].add(t)
            adj[t].add(s)

    side = {n: {v} for n, v in HAND_PLACED.items()}
    for w in doc.get("wires", []):
        if w.get("id") in CUT:
            continue
        s, t = ends(w)
        for a, b in ((s, t), (t, s)):
            if not b or b in BH or b in HAND_PLACED:
                continue
            if a in CABIN_BH:
                side.setdefault(b, set()).add("ECU")
            elif a in ENGINE_BH:
                side.setdefault(b, set()).add("engine")

    changed = True
    while changed:
        changed = False
        for n in list(adj):
            if n in HAND_PLACED:
                continue
            cur = side.get(n, set())
            new = set(cur) | set().union(*(side.get(m, set()) for m in adj[n])) \
                if adj[n] else set(cur)
            if new != cur:
                side[n] = new
                changed = True

    out = {n: ("ECU" if "ECU" in v else "engine")
           for n, v in side.items() if len(v) == 1}
    smeared = sorted(n for n, v in side.items() if len(v) > 1)
    for n in CABIN_BH:
        out[n] = "ECU"
    for n in ENGINE_BH:
        out[n] = "engine"
    return out, smeared


def wire_side(w, side):
    s, t = ends(w)
    labs = {side.get(s), side.get(t)} - {None}
    return next(iter(labs)) if len(labs) == 1 else None


def dummy(node_id, pin, label):
    """A connection block standing in for a component owned by another file.

    Per 6.15 it carries no part number and no contacts, so it adds nothing to
    this drawing's BOM.
    """
    return {"id": "dm_%s_%s" % (node_id, pin),
            "label": "%s-%s" % (label, pin),
            "cavities": [{"id": "c1", "designation": "1"}],
            "schematicPosition": {"x": 0, "y": 0},
            "notes": "Dummy block. Real part lives on the owning drawing - see plan 6.15."}


def emit(doc, side, want, extra_nodes=None, extra_wires=None):
    out = {k: doc[k] for k in ("$schema", "$docs", "version", "lengthUnit") if k in doc}
    keep = set()
    for k in NODE_KEYS:
        got = [e for e in doc.get(k, []) if side.get(e.get("id")) == want]
        if extra_nodes:
            got += extra_nodes.get(k, [])
        if got:
            out[k] = got
        keep |= {e.get("id") for e in got}

    wires = [w for w in doc.get("wires", [])
             if w.get("id") not in CUT and wire_side(w, side) == want]
    if extra_wires:
        wires += extra_wires
    out["wires"] = wires

    bundles = [b for b in doc.get("bundles", [])
               if b.get("sourceId") in keep and b.get("targetId") in keep]
    if bundles:
        out["bundles"] = bundles
    for k in ("schematicNotes", "layoutNotes"):
        if doc.get(k):
            out[k] = doc[k]
    for k in PART_KEYS:
        if doc.get(k):
            out[k] = doc[k]
    return out


def save(name, doc):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name)
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    print("  wrote %-28s wires %3d  connectors %3d  splices %2d"
          % (name, len(doc.get("wires", [])),
             len(doc.get("connectors", [])), len(doc.get("splices", []))))
