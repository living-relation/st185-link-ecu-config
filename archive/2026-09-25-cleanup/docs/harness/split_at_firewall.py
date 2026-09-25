"""Split ST185-Signal and ST185-Power at the firewall.

Why: harness.design caps a document at 100 connections. Signal (112) and Power
(114) are over it, so the app refuses every write. See plan doc 6.13.

The cut is already marked in the data - crossing wires are drawn as `_c` / `_e`
pairs. The cabin file takes the `_fw` bulkhead halves, the engine file takes the
`_eng` halves.

Run from anywhere:  python docs/harness/split_at_firewall.py [--write]
Without --write it only reports. Nothing is overwritten; new files are created.
"""
import json, io, os, sys, collections

R = os.path.dirname(os.path.abspath(__file__))
CABIN_BH = {"bh_a_fw", "bh_b_fw"}
ENGINE_BH = {"bh_a_eng", "bh_b_eng"}
BH = CABIN_BH | ENGINE_BH

# Settled by Daniel 2026-09-17: the EPS control module is bolted to the pump, so
# the relay and all three pump connectors are engine bay.
OVERRIDE = {
    # EPS pump and its relay - control module is bolted to the pump.
    "k_eps": "engine", "mrs_pwr": "engine",
    "mrs_en": "engine", "mrs_ctrl": "engine",
    # Heavy DC islands. These hang off RADLOK mates, not wires, so the flood
    # fill cannot reach them from a bulkhead - place them by hand.
    "t_batt_pos": "cabin", "t_batt_neg": "cabin",
    "rl_pos_fw": "cabin", "rl_neg_fw": "cabin",
    "rl_pos_eng": "engine", "rl_neg_eng": "engine",
    "t_starter_b": "engine", "t_alt_b": "engine", "t_eng_block": "engine",
    # Body-side devices: behind the dash or down the tunnel, not over the
    # firewall. They ride the ECU-side drawing.
    "fuelpump": "cabin", "fuellvl": "cabin", "starter_trigger": "engine",
    "batt_ring": "cabin", "chassis_ring": "cabin",
}

# Wires that must cross the firewall and do not yet have a bulkhead pin.
# Each becomes a _c / _e pair once a pin is allocated. Cut here so the flood
# fill does not smear one side into the other.
CUT = {
    "w_k_eps_86",        # relay coil feed from the cabin switched-12V splice
    "w_mrs_relay_req",   # deleted per 6.16 - pump does not switch its own relay
    "w_fb_k_eps_30",     # 60 A feed, cabin fuse block -> engine-bay relay: heavy DC
    "w_strl",            # start relay -> starter solenoid, crosses with no pin
}

# Bulkhead C is deleted (plan doc 6.1) but still drawn. Until it is actually
# removed it bridges cabin and engine and smears the whole classification, so
# treat it as gone here.
DELETED = {"bh_c_fw", "bh_c_eng"}

FILES = [("ST185-Signal", "ST185-Signal.harness"),
         ("ST185-Power", "ST185-Power.harness")]

# Collections whose elements carry an id and belong to one side.
NODE_KEYS = ["connectors", "splices", "terminals", "diodes", "resistors",
             "groups", "branchPoints"]
PART_KEYS = [k for k in ("connectorParts", "contactParts", "wireParts",
                         "cableParts", "bootParts", "coveringParts",
                         "spliceParts", "terminalParts", "otherParts")]


def endpoints(w):
    return (w.get("source", {}) or {}).get("id"), (w.get("target", {}) or {}).get("id")


def classify(doc):
    """Return {nodeId: 'cabin'|'engine'} plus the list of leaks found."""
    wires = doc.get("wires", [])
    adj = collections.defaultdict(set)
    for w in wires:
        if w.get("id") in CUT:
            continue
        s, t = endpoints(w)
        if s in BH or t in BH or s in DELETED or t in DELETED:
            continue
        if s and t:
            adj[s].add(t)
            adj[t].add(s)

    side = {}
    for n, v in OVERRIDE.items():
        side[n] = {v}
    for w in wires:
        if w.get("id") in CUT:
            continue
        s, t = endpoints(w)
        for a, b in ((s, t), (t, s)):
            if b in OVERRIDE:
                continue
            if a in CABIN_BH and b and b not in BH:
                side.setdefault(b, set()).add("cabin")
            elif a in ENGINE_BH and b and b not in BH:
                side.setdefault(b, set()).add("engine")

    changed = True
    while changed:
        changed = False
        for n in list(adj):
            if n in OVERRIDE:      # an override is final - never widened by a neighbour
                continue
            cur = side.get(n, set())
            new = set(cur)
            for m in adj[n]:
                new |= side.get(m, set())
            if new != cur:
                side[n] = new
                changed = True

    leaks = sorted(n for n, v in side.items() if len(v) > 1)
    final = {n: ("cabin" if "cabin" in v else "engine")
             for n, v in side.items() if len(v) == 1}
    for n in CABIN_BH:
        final[n] = "cabin"
    for n in ENGINE_BH:
        final[n] = "engine"
    return final, leaks


def find_bridges(doc, extra_cut, limit=12):
    """Name the wires that let one side reach the other with no bulkhead.

    Repeatedly shortest-paths from an engine-anchored node to a cabin-anchored
    one, cutting the path each round, so every crossing that still needs a
    bulkhead pin gets named instead of guessed at.
    """
    cut = set(CUT) | set(extra_cut)
    found = []
    for _ in range(limit):
        adj = collections.defaultdict(list)
        for w in doc["wires"]:
            if w.get("id") in cut:
                continue
            s, t = endpoints(w)
            if s in BH or t in BH or s in DELETED or t in DELETED:
                continue
            adj[s].append((t, w["id"]))
            adj[t].append((s, w["id"]))

        anchor = {}
        for w in doc["wires"]:
            if w.get("id") in cut:
                continue
            s, t = endpoints(w)
            for a, b in ((s, t), (t, s)):
                if b in BH or b in DELETED:
                    continue
                if a in ENGINE_BH:
                    anchor.setdefault(b, "engine")
                elif a in CABIN_BH:
                    anchor.setdefault(b, "cabin")
        for n, v in OVERRIDE.items():
            anchor[n] = v

        prev, q = {}, collections.deque()
        for n, v in anchor.items():
            if v == "engine":
                prev[n] = None
                q.append(n)
        hit = None
        while q:
            n = q.popleft()
            if anchor.get(n) == "cabin":
                hit = n
                break
            for m, wid in adj[n]:
                if m not in prev:
                    prev[m] = (n, wid)
                    q.append(m)
        if not hit:
            return found
        cur, chain = hit, []
        while prev.get(cur):
            p, wid = prev[cur]
            chain.append((wid, p, cur))
            cur = p
        chain.reverse()
        # cut where the path leaves the engine-anchored end - that is the wire
        # actually crossing, not wherever the search happened to finish
        wid, a, b = chain[0]
        found.append((wid, a, b))
        cut.add(wid)
    return found


def side_of_wire(w, side):
    s, t = endpoints(w)
    labs = {side.get(s), side.get(t)} - {None}
    if len(labs) == 1:
        return next(iter(labs))
    return None


def build(doc, side, want):
    out = {k: doc[k] for k in ("$schema", "$docs", "version", "lengthUnit") if k in doc}
    keep_nodes = set()
    for key in NODE_KEYS:
        kept = [e for e in doc.get(key, [])
                if e.get("id") not in DELETED and side.get(e.get("id")) == want]
        if kept:
            out[key] = kept
        keep_nodes |= {e.get("id") for e in kept}

    wires = [w for w in doc.get("wires", [])
             if w.get("id") not in CUT
             and not (set(endpoints(w)) & DELETED)
             and side_of_wire(w, side) == want]
    out["wires"] = wires

    for key in ("cables", "twistedWires"):
        got = [c for c in doc.get(key, []) if side_of_wire(c, side) == want]
        if got:
            out[key] = got

    bundles = [b for b in doc.get("bundles", [])
               if b.get("sourceId") in keep_nodes and b.get("targetId") in keep_nodes]
    if bundles:
        out["bundles"] = bundles

    for key in ("schematicNotes", "layoutNotes"):
        if doc.get(key):
            out[key] = doc[key]
    for key in PART_KEYS:
        if doc.get(key):
            out[key] = doc[key]
    return out


def main():
    write = "--write" in sys.argv
    for name, fn in FILES:
        doc = json.load(io.open(os.path.join(R, fn), encoding="utf-8"))
        side, leaks = classify(doc)
        print("=" * 66)
        print(name, " wires:", len(doc.get("wires", [])))
        if leaks:
            bridges = find_bridges(doc, ())
            print("  CROSSINGS with no bulkhead pin - add to CUT and allocate one:")
            for wid, a, b in bridges:
                print("      %-18s %-16s -> %s" % (wid, a, b))
            print("  (they smear %d nodes across both sides)" % len(leaks))
        unplaced = [w.get("id") for w in doc.get("wires", [])
                    if w.get("id") not in CUT
                    and not (set(endpoints(w)) & DELETED)
                    and side_of_wire(w, side) is None]
        if unplaced:
            print("  UNPLACED wires (%d):" % len(unplaced), unplaced[:12])
        for want in ("cabin", "engine"):
            sub = build(doc, side, want)
            print("  %-7s wires %3d  connectors %3d  splices %2d  bundles %3d"
                  % (want, len(sub.get("wires", [])), len(sub.get("connectors", [])),
                     len(sub.get("splices", [])), len(sub.get("bundles", []))))
            if write:
                op = os.path.join(R, "%s-%s.harness" % (name, want))
                with io.open(op, "w", encoding="utf-8", newline="\n") as f:
                    json.dump(sub, f, indent=2, ensure_ascii=False)
                print("      wrote", os.path.basename(op))
        if CUT:
            print("  CUT (need a bulkhead pin allocated):", ", ".join(sorted(CUT)))


if __name__ == "__main__":
    main()
