"""Finish the 6.32 migration: every screen on its own bulkhead pin, both halves.

SHIELD-RULES 6.27 rule 5 - "shields pass THROUGH the bulkhead on their own pin" -
and 6.32 - "first choice: every shield gets its own bulkhead passthrough pin,
allocate that way whenever the pins exist" - were half applied.

What was in the files before this ran:

  engine side   crank/cam/knock cable screens land on bh_a_eng c33/c34/c35   (6.32, correct)
                AND each also jumpers to sp_shield_eng, which goes out on c1  (the old shared drain)
  cabin side    only c1 is wired, to sp_shield_cab -> ECU-A A7 / ECU-B B17
                c33/c34/c35 are not wired at all

So the three dedicated pins dead-ended in the connector and every screen was
actually still travelling on the old shared c1 drain.  Bulkhead A has the
headroom 6.32 asks for, so this finishes the migration rather than falling back
to sharing:

  * wire bh_a_fw c33/c34/c35 through to sp_shield_cab in the cabin
  * delete the engine-bay collector splice sp_shield_eng and its three jumpers
  * retire the shared c1 drain on both halves - it is spare now

Each screen ends up with exactly one termination, at the ECU.  Written 2026-09-22.
"""
import json, os

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")

SCREENS = [("c33", "Crank VR screen", "w_shc_crank"),
           ("c34", "Cam Hall screen", "w_shc_cam"),
           ("c35", "Knock 1 screen", "w_shc_knock1")]


def load(n):
    p = os.path.join(R, "ST185-%s.harness" % n)
    return p, json.load(open(p, encoding="utf-8"))


def save(p, d):
    json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


# ---- cabin: wire the three dedicated pins through to the ECU shield splice ----
p, d = load("A-ECU")
have = {w["id"] for w in d["wires"]}
bh = next(c for c in d["connectors"] if c["id"] == "bh_a_fw")
cav = {c["id"]: c for c in bh["cavities"]}
for cid, name, wid in SCREENS:
    if wid not in have:
        d["wires"].append({"id": wid, "color": "Shield",
                           "source": {"id": "bh_a_fw", "handle": cid},
                           "target": {"id": "sp_shield_cab", "handle": "Splice"}})
        print("A-ECU    + %-14s bh_a_fw %s -> sp_shield_cab   (%s)" % (wid, cid, name))
    cav[cid]["signal"] = name + " - own pin per 6.32, terminates at the ECU"
# retire the old shared drain
d["wires"] = [w for w in d["wires"] if w["id"] != "w_drain_bh_c"]
cav["c1"]["signal"] = "spare (size 16) - was the shared shield drain, retired by 6.32"
print("A-ECU    - w_drain_bh_c    shared drain retired, bh_a_fw c1 is spare")
save(p, d)

# ---- engine: drop the collector splice, the screens already land on c33-c35 ----
p, d = load("A-engine")
drop = {"w_sh_crank", "w_sh_cam", "w_sh_knock1", "w_drain_bh_e"}
d["wires"] = [w for w in d["wires"] if w["id"] not in drop]
d["splices"] = [s for s in d.get("splices", []) if s["id"] != "sp_shield_eng"]
bh = next(c for c in d["connectors"] if c["id"] == "bh_a_eng")
cav = {c["id"]: c for c in bh["cavities"]}
for cid, name, _ in SCREENS:
    cav[cid]["signal"] = name + " - own pin per 6.32, floats at the sensor"
cav["c1"]["signal"] = "spare (size 16) - was the shared shield drain, retired by 6.32"
print("A-engine - %s" % ", ".join(sorted(drop)))
print("A-engine - sp_shield_eng   engine-bay collector removed, bh_a_eng c1 is spare")
save(p, d)
