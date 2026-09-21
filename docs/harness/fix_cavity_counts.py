"""Three fixes the stricter lint found. All three are real, none are cosmetic.

1. csb3io c4 was notConnected but wire wc_l_csb lands CAN Low on it. The CSB3
   has four screw terminals - 12V, GND, CANH, CANL - so c3 and c4 are CANH and
   CANL. Same bug as ecu_com C4: a live pin flagged dead.

2. acamp modelled 1 cavity while its part declares 7. The part invariant is
   cavities.length == numberOfCavities, so the drawing has to carry all seven
   even though this harness only lands the kill input.

3. mrs_ctrl modelled 3 cavities while its part declares 6. Worse, the two pins
   we actually know - pin 2 speed-pulse out, pin 6 relay-request out - were
   sitting in cavity slots 1 and 3, so the drawing disagreed with the pin
   numbers in its own signal text. Rebuilt as six cavities in pin order and the
   wire re-pointed at the right one.
"""
import json, os, glob

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")

changes = []

for path in sorted(glob.glob(os.path.join(SRC, "*.harness"))):
    name = os.path.basename(path)
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    dirty = False

    for c in doc.get("connectors", []):

        # ---- 1. CSB3 CAN pair -------------------------------------------
        if c.get("id") == "csb3io":
            for x in c.get("cavities", []):
                if x.get("id") == "c3":
                    x.pop("notConnected", None)
                    x["signal"] = "CANH screw term"
                    dirty = True
                if x.get("id") == "c4":
                    x.pop("notConnected", None)
                    x["signal"] = "CANL screw term"
                    dirty = True
                    changes.append("%s: csb3io c4 -> CANL (was notConnected)" % name)

        # ---- 2. A/C amplifier, 7-way -------------------------------------
        if c.get("id") == "acamp" and len(c.get("cavities", [])) == 1:
            kept = c["cavities"][0]
            kept["designation"] = "1"
            c["cavities"] = [kept] + [
                {"id": "c%d" % i, "designation": str(i), "notConnected": True}
                for i in range(2, 8)]
            dirty = True
            changes.append("%s: acamp expanded 1 -> 7 cavities" % name)

        # ---- 3. MRS control connector B, 6-way ---------------------------
        if c.get("id") == "mrs_ctrl" and len(c.get("cavities", [])) != 6:
            c["cavities"] = [
                {"id": "c1", "designation": "1", "notConnected": True},
                {"id": "c2", "designation": "2",
                 "signal": "SPD Out - speed-pulse output"},
                {"id": "c3", "designation": "3", "notConnected": True},
                {"id": "c4", "designation": "4", "notConnected": True},
                {"id": "c5", "designation": "5", "notConnected": True},
                {"id": "c6", "designation": "6",
                 "signal": "Relay request out. Not wired - 6.16 moved the EPS relay "
                           "trigger to the ECU (Ign 6 / B12). Kept for reference."},
            ]
            dirty = True
            changes.append("%s: mrs_ctrl rebuilt to 6 cavities in pin order" % name)

    # The speed-pulse wire pointed at the old slot 1. It belongs on pin 2.
    for w in doc.get("wires", []):
        for end in ("source", "target"):
            e = w.get(end)
            if e and e.get("id") == "mrs_ctrl" and e.get("handle") == "c1":
                e["handle"] = "c2"
                dirty = True
                changes.append("%s: wire %s re-pointed mrs_ctrl c1 -> c2 (pin 2)"
                               % (name, w.get("id")))

    if dirty:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2)

for c in changes:
    print("  " + c)
print("\n%d changes" % len(changes))
