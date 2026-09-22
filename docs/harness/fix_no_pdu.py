"""No PDU (plan 6.46-6.48).

The PMU-16 was dropped 2026-09-22. Loom C's `pmu` node becomes the glove-box body
block - a second fuse block plus micro ISO relays - carrying the same ex-J/B2
circuits plus the two CAN device feeds. Same cavities, same wires, new identity.

Run from docs/harness:  python fix_no_pdu.py
"""
import json, io, os

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
P = os.path.join(R, "ST185-EngineRoom-C.harness")

CAV = {
    "c1":  ("IN",  u"Feed from PDB stud, ANL 100 A"),
    "c2":  ("GND", u"Chassis / PDB ground"),
    "c3":  ("IGN", u"Ignition-switched relay coil feed (not yet wired)"),
    "c4":  ("HL",  u"HEAD LH - relay 87, 15 A fuse -> J/B2 2A-3 / 2D-2"),
    "c5":  ("HR",  u"HEAD RH - relay 87, 15 A fuse -> J/B2 2A-6 / 2D-6"),
    "c6":  ("HZ",  u"HAZ-HORN - 15 A fuse -> J/B2 2E-3"),
    "c7":  ("DM",  u"DOME - 20 A fuse, always-hot -> J/B2 2E-4"),
    "c8":  ("RT",  u"RTR - relay 87, 30 A fuse -> J/B2 2E-2"),
    "c9":  ("WP",  u"Wiper park - relay 87, 15 A fuse (optional, unused)"),
    "c10": ("CSB", u"CSB3 permanent feed, 5 A - stays live for the kill sequence (plan 6.48)"),
    "c11": ("DEV", u"Cluster + RealDash Pi - device relay 87, held by CSB3 low-side L1 (plan 6.48)"),
}

d = json.load(io.open(P, encoding="utf-8"))

for p in d.get("connectorParts", []):
    if p.get("id") == "cp_pmu":
        p["partNumber"] = u"(glove-box body block - 2nd fuse block + relays)"
        p["manufacturer"] = u"assembly"
        p["description"] = (
            u"Replaces the ECUMaster PMU-16, dropped 2026-09-22 (plan 6.46-6.48). "
            u"A 12-16 way fuse block plus micro ISO relays in the glove box, "
            u"carrying the ex-J/B2 body circuits and the CAN device feeds. "
            u"Not a single purchased part - see NEED-TO-BUY.")

for c in d.get("connectors", []):
    if c.get("id") != "pmu":
        continue
    c["label"] = u"Glove-box body block (fuses + relays, ex-J/B2)"
    for cav in c.get("cavities", []):
        hit = CAV.get(cav.get("id"))
        if hit:
            cav["designation"], cav["signal"] = hit

with io.open(P, "w", encoding="utf-8", newline="\n") as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("rewrote rebuild/ST185-EngineRoom-C.harness - pmu node is now the body block")
