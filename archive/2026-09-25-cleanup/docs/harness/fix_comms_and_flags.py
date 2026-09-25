"""Two fixes the harness.design upload warnings surfaced.

1. ecu_com cavity C4 carries CAN 1 Low (wire w_can_bh1_c runs it to bulkhead A
   pin 31) but was still flagged notConnected, and C3/C4 were labelled vaguely.
   Pinout is from XTREMEX-IO-TABLE.html, the source of truth:
       1 Brown  Ground
       2 Blue   Unused
       3 White  CAN 1 High
       4 Green  CAN 1 Low
       5 Yellow RS232 TX
       6 Grey   RS232 RX

2. A cavity carrying BOTH notConnected and a signal is contradictory and the app
   warns on every one. The signal text is the documentation - a line like
   "DO NOT REFEED, fan moved to k_fan2" is the whole point of the cavity being
   in the drawing - so the flag is what goes, not the text.
"""
import json, os, glob

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")

COMMS = {
    "c1": ("C1", "Ground (Brown)"),
    "c2": ("C2", "Unused (Blue)"),
    "c3": ("C3", "CAN 1 High (White)"),
    "c4": ("C4", "CAN 1 Low (Green)"),
    "c5": ("C5", "RS232 TX (Yellow) - not used on this build"),
    "c6": ("C6", "RS232 RX (Grey) - not used on this build"),
}

fixed_comms = 0
cleared = 0

for path in sorted(glob.glob(os.path.join(SRC, "*.harness"))):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    changed = False

    for c in doc.get("connectors", []):
        if c.get("id") == "ecu_com":
            for cav in c.get("cavities", []):
                spec = COMMS.get(cav.get("id"))
                if spec:
                    cav["designation"], cav["signal"] = spec
                    cav.pop("notConnected", None)
                    fixed_comms += 1
                    changed = True
        # A signal and notConnected cannot both be true. Keep the text.
        for cav in c.get("cavities", []):
            if cav.get("notConnected") and cav.get("signal"):
                cav.pop("notConnected")
                cleared += 1
                changed = True

    if changed:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2)
        print("updated %s" % os.path.basename(path))

print("\ncomms cavities relabelled: %d" % fixed_comms)
print("contradictory notConnected flags cleared: %d" % cleared)
