"""Split the RADLOK firewall pass-through into two parts, and flag what is wrong.

Three looms drew the battery feed-through as a single part number used twice -
cp_rl_red on rl_pos_fw AND on rl_pos_eng - with the description "bulkhead pair",
as if one order line bought both halves.  Checked against Amphenol 2026-09-22:

  * The series is RADLOK.  The 5.7mm RADSOK contact is rated 120 A and is sold
    for 16 mm2 and 25 mm2 cable.  Nothing in the catalogue is "-35".
  * RL00571-25 (suffix RE red / BK black) is a CABLE-MOUNT RECEPTACLE, one
    piece.  It is not a pair, and it is not a panel mount.
  * 25 mm2 is about 3 AWG.  The 2 AWG cable this harness calls for is 33.6 mm2
    and will not fit it.

So this script does the mechanical half - two distinct parts instead of one
used twice, so the count is honest - and writes the open questions into the
descriptions.  It deliberately does NOT invent replacement part numbers.
"""
import json, os

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
FILES = ("ST185-B-ECU.harness", "ST185-B-engine.harness", "ST185-EngineRoom-C.harness")

NOTE = ("UNVERIFIED - Amphenol lists RL00571-16/-25 (16/25 mm2), no -35, and it is a "
        "cable-mount receptacle, not a bulkhead pair. 2 AWG = 33.6 mm2 will not fit "
        "25 mm2. Pick the real part before ordering.")

NEW = {
    "cp_rl_red_fw": {"id": "cp_rl_red_fw", "partNumber": "TBD RADLOK red, cabin side",
                     "manufacturer": "Amphenol",
                     "description": "RADLOK 5.7 battery positive, CABIN side of the firewall. " + NOTE},
    "cp_rl_red_eng": {"id": "cp_rl_red_eng", "partNumber": "TBD RADLOK red, engine side",
                      "manufacturer": "Amphenol",
                      "description": "RADLOK 5.7 battery positive, ENGINE side, mates the cabin half. " + NOTE},
    "cp_rl_blk_fw": {"id": "cp_rl_blk_fw", "partNumber": "TBD RADLOK black, cabin side",
                     "manufacturer": "Amphenol",
                     "description": "RADLOK 5.7 battery negative, CABIN side of the firewall. " + NOTE},
    "cp_rl_blk_eng": {"id": "cp_rl_blk_eng", "partNumber": "TBD RADLOK black, engine side",
                      "manufacturer": "Amphenol",
                      "description": "RADLOK 5.7 battery negative, ENGINE side, mates the cabin half. " + NOTE},
}
ASSIGN = {"rl_pos_fw": "cp_rl_red_fw", "rl_pos_eng": "cp_rl_red_eng",
          "rl_neg_fw": "cp_rl_blk_fw", "rl_neg_eng": "cp_rl_blk_eng"}

for fn in FILES:
    p = os.path.join(R, fn)
    d = json.load(open(p, encoding="utf-8"))
    lib = d.setdefault("connectorParts", [])
    by_id = {q["id"]: q for q in lib}
    touched = False
    for cid, pid in ASSIGN.items():
        c = next((x for x in d.get("connectors", []) if x["id"] == cid), None)
        if c is None:
            continue
        if c.get("partId") != pid:
            print("%-14s %-12s %s -> %s" % (fn[6:-8], cid, c.get("partId"), pid))
            c["partId"] = pid
            touched = True
        if pid not in by_id:
            lib.append(dict(NEW[pid]))
            by_id[pid] = lib[-1]
        else:
            by_id[pid].update(NEW[pid])
    used = {x.get("partId") for x in d.get("connectors", [])}
    for q in list(lib):
        if q["id"] in ("cp_rl_red", "cp_rl_blk") and q["id"] not in used:
            lib.remove(q)
            print("%-14s dropped old %s" % (fn[6:-8], q["id"]))
            touched = True
    if touched:
        json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
