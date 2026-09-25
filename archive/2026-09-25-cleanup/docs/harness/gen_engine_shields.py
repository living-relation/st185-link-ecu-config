"""Turn the three shielded engine sensors into real cables, per 6.27/6.32.

The problem this fixes: 6.27 deleted every device-end drain, which was correct,
but nothing replaced them. The engine harnesses have no `cables` at all, so the
crank, cam and knock screens do not exist in the model - and sp_shield_eng was
left with a single connection, feeding nothing.

6.32, in order of preference:
  - every shield gets its own bulkhead passthrough pin, whenever the pins exist
  - if they do not: crank and cam keep dedicated pins (trigger inputs, and a
    corrupted trigger is a dead engine), knock next, everything else shares
  - all terminate together at the ECU shield grounds regardless

Headroom is 16 free pairs on bulkhead A, so the first choice applies: three
shields, three dedicated pins. No sharing.

Pins taken on bulkhead A, both halves, from the spare block at 33+:

    c33  crank screen
    c34  cam screen
    c35  knock screen

c1 keeps its existing role as the engine-bay shield collector that runs to the
cabin splice - the three new screens land on sp_shield_eng, which is what that
splice was always for and why it was left dangling.

Shield path, unchanged from 6.27:

    device end FLOATS -> cable screen -> bulkhead pin -> sp_shield_eng ->
    bh_a c1 -> sp_shield_cab -> ECU A7 / B17

Each screen core therefore has a `source` at the bulkhead (engine side) and NO
`target`, because it floats at the sensor.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "rebuild")

# sensor id -> (signal wire ids on A-engine, bulkhead A pin for its screen)
SHIELDED = {
    "crank":  {"pin": "c33", "label": "Crank VR screen",
               "wires": ["w200_e"], "cores": [("c1", "Blue")]},
    "cam":    {"pin": "c34", "label": "Cam Hall screen",
               "wires": ["w_cam_sig_e"], "cores": [("c2", "Blue")]},
    "knock1": {"pin": "c35", "label": "Knock 1 screen",
               "wires": ["w205_e", "w12_e"],
               "cores": [("c1", "Gray"), ("c2", "Green")]},
}


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def save(p, d):
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2)


def main():
    p = os.path.join(SRC, "ST185-A-engine.harness")
    d = load(p)

    bh = next(c for c in d["connectors"] if c["id"] == "bh_a_eng")
    by_id = {c["id"]: c for c in d["connectors"]}
    wires = {w["id"]: w for w in d["wires"]}

    d.setdefault("cables", [])
    d.setdefault("cableParts", [])
    if not any(cp["id"] == "cab_sh_gen" for cp in d["cableParts"]):
        d["cableParts"].append({
            "id": "cab_sh_gen", "partNumber": "(generic)", "manufacturer": "generic",
            "description": "Shielded sensor cable, overall foil + braid screen, 20 AWG. "
                           "Core count per run. Cable is generic in BOMs per 6.24.",
            "cores": [{"id": "k1", "color": "Blue"}, {"id": "k2", "color": "Gray"}],
        })

    made = []
    for sid, spec in SHIELDED.items():
        sensor = by_id[sid]
        pin = spec["pin"]

        # Claim the bulkhead pin away from the spare pool.
        cav = next(c for c in bh["cavities"] if c["id"] == pin)
        cav["signal"] = spec["label"] + " (6.32 dedicated shield pin)"
        cav.pop("cavityPlugPartId", None)

        # Move the existing signal wires into the cable as cores.
        cores = []
        for wid, (cav_id, colour) in zip(spec["wires"], spec["cores"]):
            w = wires.get(wid)
            if w is None:
                print("  ! %s: signal wire %s not found, skipped" % (sid, wid))
                continue
            cores.append({"id": "cab_%s_%s" % (sid, cav_id), "color": colour,
                          "source": dict(w["source"]), "target": dict(w["target"])})
            d["wires"] = [x for x in d["wires"] if x["id"] != wid]

        if len(cores) == 2:
            cores[0]["twistedWithNext"] = True

        d["cables"].append({
            "id": "cab_%s" % sid,
            "partId": "cab_sh_gen",
            "schematicPosition": {"x": 0, "y": 0},
            "cores": cores,
            # Floats at the sensor, so no target. 6.27 rule 1.
            "shield": {"id": "cab_%s_sh" % sid, "color": "Shield",
                       "source": {"id": "bh_a_eng", "handle": pin}},
        })

        # The screen's cabin-side continuation: bulkhead pin to the engine-bay
        # shield collector, which already runs on to the ECU.
        d["wires"].append({
            "id": "w_sh_%s" % sid, "color": "Shield",
            "source": {"id": "bh_a_eng", "handle": pin},
            "target": {"id": "sp_shield_eng", "handle": "Splice"},
        })
        made.append("%-8s -> bulkhead A %s" % (sid, pin))

    save(p, d)

    # The firewall half of bulkhead A has to claim the same three pins, or the
    # two halves of one connector disagree with each other.
    for fn in ("ST185-A-ECU.harness", "ST185-B-ECU.harness",
               "ST185-CAN.harness", "ST185-B-engine.harness"):
        fp = os.path.join(SRC, fn)
        if not os.path.exists(fp):
            continue
        doc = load(fp)
        touched = False
        for c in doc.get("connectors", []):
            if c["id"] not in ("bh_a_fw", "bh_a_eng"):
                continue
            for sid, spec in SHIELDED.items():
                cav = next((x for x in c["cavities"] if x["id"] == spec["pin"]), None)
                if cav is None:
                    continue
                cav["signal"] = spec["label"] + " (6.32 dedicated shield pin)"
                cav.pop("cavityPlugPartId", None)
                touched = True
        if touched:
            save(fp, doc)
            print("  claimed the same pins in %s" % fn)

    print("\n3 shielded runs, 3 dedicated bulkhead pins (6.32 first choice):")
    for m in made:
        print("   " + m)


if __name__ == "__main__":
    main()
