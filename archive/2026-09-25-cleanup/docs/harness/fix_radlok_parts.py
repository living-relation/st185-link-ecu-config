"""The firewall heavy-DC pass-through, sized and specified.

Supersedes the earlier version of this script, which only flagged the problem.

WHAT CROSSES
    positive   trunk battery -> cabin PDB -> firewall -> starter B+, and the
               160 A alternator lands on that same starter post, so the full
               charge current comes back through this pass-through
    negative   engine block -> firewall -> trunk battery negative

    continuous design case   160 A  (alternator at rating)
    peak design case         ~300 A for a few seconds (cranking a 2.2 L four)

WIRE SIZE, from the run length
    Positive is roughly 18 ft one way (12 ft trunk -> PDB, 6 ft PDB -> starter),
    and the negative is a dedicated return of about the same, so ~36 ft round
    trip.  Copper at 20 C:

        2 AWG  0.1563 ohm/1000ft -> 36 ft = 5.63 mohm -> 0.90 V at 160 A, 1.69 V cranking
        1/0    0.0983 ohm/1000ft -> 36 ft = 3.54 mohm -> 0.57 V at 160 A, 1.06 V cranking
        2/0    0.0779 ohm/1000ft -> 36 ft = 2.80 mohm -> 0.45 V at 160 A, 0.84 V cranking

    2 AWG cranking drop is 13 % of 12.6 V - past the 10 % a starter circuit is
    normally held to.  1/0 lands at 8.4 % cranking and 4 % charging.  2/0 buys
    little for a lot more money and bend radius.

    -> 1/0 AWG (50 mm2) for the trunk feed, the firewall crossing and the engine
       ground.  The short alternator-B+-to-starter-post jumper stays 2 AWG; it
       never crosses the firewall.

CONNECTOR
    1/0 is 50 mm2, which is exactly the RADLOK 8.0 cable size, so the family
    carries over from the old 5.7 mm spec.  Verified on Amphenol / RS 2026-09-22:

        RL9080-301-F1     8.0 mm RADLOK feed-through receptacle, panel mount,
                          pin both sides, 200 A @ 40 C, 1 kV, IP40 mated, black
                          (-F1RE is the red version; the -303 nickel variant is
                          discontinued and RS names -301 as its replacement)
        RL00801-50RE      8.0 mm female CABLE connector, 200 A, 50 mm2, red
        RL00801-50BK      same in black

    200 A continuous clears the 160 A alternator case with 25 % headroom, and a
    connector of this class shrugs off a few seconds of cranking.  The old
    RL00571-35 was doubly wrong: no such part number exists (the catalogue has
    -16 and -25, the number being mm2), and 5.7 mm is only 120 A.

    Each polarity is THREE pieces: one feed-through in the firewall plus one
    cable connector each side.  The feed-through is not a harness component, so
    it is carried in buylist.py's EXTRA list.
"""
import json, os

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
FILES = ("ST185-B-ECU.harness", "ST185-B-engine.harness", "ST185-EngineRoom-C.harness")

RED = ("RL00801-50RE", "RADLOK 8.0 female cable connector, 200A, 50 mm2 (1/0), RED. "
       "Mates the RL9080-301-F1RE firewall feed-through.")
BLK = ("RL00801-50BK", "RADLOK 8.0 female cable connector, 200A, 50 mm2 (1/0), BLACK. "
       "Mates the RL9080-301-F1 firewall feed-through.")

NEW = {
    "cp_rl_red_fw": dict(id="cp_rl_red_fw", partNumber=RED[0], manufacturer="Amphenol",
                         description="Battery positive, CABIN side. " + RED[1]),
    "cp_rl_red_eng": dict(id="cp_rl_red_eng", partNumber=RED[0], manufacturer="Amphenol",
                          description="Battery positive, ENGINE side. " + RED[1]),
    "cp_rl_blk_fw": dict(id="cp_rl_blk_fw", partNumber=BLK[0], manufacturer="Amphenol",
                         description="Battery negative, CABIN side. " + BLK[1]),
    "cp_rl_blk_eng": dict(id="cp_rl_blk_eng", partNumber=BLK[0], manufacturer="Amphenol",
                          description="Battery negative, ENGINE side. " + BLK[1]),
}
ASSIGN = {"rl_pos_fw": "cp_rl_red_fw", "rl_pos_eng": "cp_rl_red_eng",
          "rl_neg_fw": "cp_rl_blk_fw", "rl_neg_eng": "cp_rl_blk_eng"}

for fn in FILES:
    p = os.path.join(R, fn)
    d = json.load(open(p, encoding="utf-8"))
    lib = d.setdefault("connectorParts", [])
    by_id = {q["id"]: q for q in lib}
    for cid, pid in ASSIGN.items():
        c = next((x for x in d.get("connectors", []) if x["id"] == cid), None)
        if c is None:
            continue
        if c.get("partId") != pid:
            print("%-14s %-12s %s -> %s" % (fn[6:-8], cid, c.get("partId"), pid))
            c["partId"] = pid
        if pid in by_id:
            by_id[pid].update(NEW[pid])
        else:
            lib.append(dict(NEW[pid]))
            by_id[pid] = lib[-1]
    used = {x.get("partId") for x in d.get("connectors", [])}
    for q in list(lib):
        if q["id"] in ("cp_rl_red", "cp_rl_blk") and q["id"] not in used:
            lib.remove(q)
            print("%-14s dropped old %s" % (fn[6:-8], q["id"]))
    json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
