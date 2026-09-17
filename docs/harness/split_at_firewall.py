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
OVERRIDE = {"k_eps": "engine", "mrs_pwr": "engine",
            "mrs_en": "engine", "mrs_ctrl": "engine"}

# Wires that must cross the firewall and do not yet have a bulkhead pin.
# Each becomes a _c / _e pair once a pin is allocated. Cut here so the flood
# fill does not smear one side into the other.
CUT = {"w_k_eps_86", "w_mrs_relay_req"}

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
            if a in CABIN_BH and b and b not in BH:
                side.setdefault(b, set()).add("cabin")
            elif a in ENGINE_BH and b and b not in BH:
                side.setdefault(b, set()).add("engine")

    changed = True
    while changed:
        changed = False
        for n in list(adj):
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
            print("  LEAKS - these reach both sides without crossing a bulkhead;")
            print("  add them to CUT and allocate a bulkhead pin:")
            for n in leaks:
                print("     ", n)
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
