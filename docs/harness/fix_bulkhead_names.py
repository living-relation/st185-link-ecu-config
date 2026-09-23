"""One bulkhead cavity, one name, on both halves and in every file.

Daniel, 2026-09-23:
  "Always verify pin signal names against the signal source, and the ECU pin
   it's assigned to. Bh connector pins must be named exactly the same across a
   mating pair. A cabin = A engine bay, B cabin = B engine bay.
   No pins should get different names on any two mating connectors."

The name is derived, not typed, so it cannot drift:

    <what is on the engine side>  ->  <what ECU pin it lands on>

Both sides are traced out of the harness data itself.  Run with no arguments to
print the proposed table; add --write to apply it.
"""
import json, glob, os, sys, collections

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
PAIRS = [("bh_a_fw", "bh_a_eng"), ("bh_b_fw", "bh_b_eng")]
WRITE = "--write" in sys.argv

files = sorted(glob.glob(os.path.join(R, "*.harness")))
docs = {f: json.load(open(f, encoding="utf-8")) for f in files}


def conductors(d):
    for w in d.get("wires", []):
        tail = w["id"].rsplit("_", 1)[-1]
        yield w, (w.get("color") == "Shield" or tail in ("sh", "shield", "drain")
                  or w["id"].startswith("w_drain"))
    for cb in d.get("cables", []):
        for co in cb.get("cores", []):
            yield co, False
        if cb.get("shield"):
            yield cb["shield"], True


# node -> friendly description, and the net graph
desc, net = {}, collections.defaultdict(set)
screen_of = {}
for d in docs.values():
    for c in d.get("connectors", []):
        for cv in c.get("cavities", []):
            desc[(c["id"], cv["id"])] = (c.get("label") or c["id"],
                                         cv.get("designation") or cv["id"])
    for w, screen in conductors(d):
        s, t = w.get("source"), w.get("target")
        if s and t:
            a = (s["id"], s.get("handle"))
            b = (t["id"], t.get("handle"))
            net[a].add(b)
            net[b].add(a)
            if screen:
                screen_of[a] = screen_of[b] = True

BH = {b for p in PAIRS for b in p}


def walk(start, want):
    """Nearest node matching want(), not passing back through a bulkhead."""
    seen, queue = {start}, [start]
    while queue:
        nxt = []
        for n in queue:
            for m in net.get(n, ()):
                if m in seen:
                    continue
                seen.add(m)
                if want(m):
                    return m
                if m[0] not in BH:
                    nxt.append(m)
        queue = nxt
    return None


is_ecu = lambda n: n[0] in ("ecu_a", "ecu_b")
is_dev = lambda n: n[0] not in BH and not n[0].startswith(("sp_", "dm_"))

# A cavity that feeds a shared rail is named for the RAIL, not for whichever
# device the walk happened to reach first across it.  Without this, bulkhead A
# c2 came out "Coolant Pressure Sensor c1" when it is the +5V Out supply.
RAILS = {
    "sp_5v": "+5V Out sensor supply rail", "sp_5v_eng": "+5V Out sensor supply rail",
    "sp_gndout": "Gnd Out sensor ground rail",
    "sp_gndout_eng": "Gnd Out sensor ground rail",
    "sp_sw12": "Switched 12V sensor supply rail",
    "sp_sw12_eng": "Switched 12V sensor supply rail",
    "sp_shield_a": "shield ground A", "sp_shield_b": "shield ground B",
}


def rail_on(cav_node):
    """Name of a rail splice directly on this cavity's net, if any."""
    seen, queue = {cav_node}, [cav_node]
    while queue:
        nxt = []
        for n in queue:
            for m in net.get(n, ()):
                if m in seen:
                    continue
                seen.add(m)
                key = m[0][3:-7] if m[0].startswith("dm_") and m[0].endswith("_Splice") \
                    else m[0]
                if key in RAILS:
                    return RAILS[key]
                if m[0].startswith(("sp_", "dm_")) or m[0] in BH:
                    nxt.append(m)
        queue = nxt
    return None

names = {}
for fw, eng in PAIRS:
    cavs = sorted({cv["id"] for d in docs.values() for c in d.get("connectors", [])
                   if c["id"] in (fw, eng) for cv in c.get("cavities", [])},
                  key=lambda x: int(x[1:]))
    for cav in cavs:
        ecu = walk((fw, cav), is_ecu) or walk((eng, cav), is_ecu)
        dev = walk((eng, cav), is_dev) or walk((fw, cav), is_dev)
        scr = screen_of.get((fw, cav)) or screen_of.get((eng, cav))
        rail = rail_on((fw, cav)) or rail_on((eng, cav))
        if ecu is None and dev is None and rail is None:
            continue                      # unused - leave the spare text alone
        if ecu:
            pin = "ECU-%s %s" % (ecu[0][-1].upper(), desc[ecu][1])
        elif dev:
            # not an ECU pin - say where it actually goes instead of "no ECU pin"
            pin = "%s %s" % desc[dev]
        else:
            pin = "rail"
        if scr:
            src = desc[dev][0] if dev else "sensor"
            n = "%s screen - DRAIN ONLY, no current -> %s" % (src, pin)
        elif rail:
            n = "%s -> %s" % (rail, pin)
        else:
            src = "%s %s" % desc[dev] if dev else "cabin side only"
            n = "%s -> %s" % (src, pin)
        names[(fw, cav)] = names[(eng, cav)] = n

print("%-10s %-5s %s" % ("PAIR", "CAV", "NAME"))
seen = set()
for (conn, cav), n in sorted(names.items(), key=lambda kv: (kv[0][0], int(kv[0][1][1:]))):
    if not conn.endswith("_fw"):
        continue
    print("%-10s %-5s %s" % (conn[:-3], cav, n))

if WRITE:
    for f, d in docs.items():
        hit = False
        for c in d.get("connectors", []):
            if c["id"] not in BH:
                continue
            for cv in c.get("cavities", []):
                n = names.get((c["id"], cv["id"]))
                if n and cv.get("signal") != n:
                    cv["signal"] = n
                    hit = True
        if hit:
            json.dump(d, open(f, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
            print("wrote", os.path.basename(f))
else:
    print("\ndry run - add --write to apply")
