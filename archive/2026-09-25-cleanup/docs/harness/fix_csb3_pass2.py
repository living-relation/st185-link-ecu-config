"""Pass 2 - bring the local .harness files in line with the harness.design edits.

CSB3 rebuilt to the real HD30 spec (6.37 cavity map + 6.40 connector family),
one shared connector part instead of three local copies, cruise-ladder splice
fix, and real text on the cross-reference (dummy) nodes.

Run from docs/harness:  python fix_csb3_pass2.py
"""
import json, io, os

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
log = []


def load(name):
    with io.open(os.path.join(R, name), "r", encoding="utf-8") as f:
        return json.load(f)


def save(name, doc):
    with io.open(os.path.join(R, name), "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write("\n")
    log.append("wrote rebuild/" + name)


def find(coll, eid):
    for e in coll:
        if e.get("id") == eid:
            return e
    return None


def drop(doc, key, eid):
    if key in doc:
        doc[key] = [e for e in doc[key] if e.get("id") != eid]


EM = u"—"
ARR = u"→"

# 6.37 cavity map, 6.40 connector family. 26 real terminals, 27-33 structural spare.
SIG = {
    1: u"+12V (ignition switched) " + EM + u" wired on ST185-B-ECU",
    2: u"GND " + EM + u" wired on ST185-B-ECU",
    3: u"+5V sensor supply (brought out, spare)",
    4: u"SGND sensor ground (brought out, spare)",
    5: u"CAN H " + EM + u" wired on ST185-CAN",
    6: u"CAN L " + EM + u" wired on ST185-CAN",
    7: u"A1 - Cabin Temp (source not yet wired - open item)",
    8: u"A2 - Cruise Ladder",
    15: u"S1 - Evap Core (source not yet wired - open item)",
    16: u"S2 - AC Request (source not yet wired - open item)",
    17: u"S3 - Cruise Main On",
    18: u"S4 - Cruise Set/Accel",
    19: u"S5 - Cruise Resume/Decel",
    20: u"S6 - Clutch Switch",
    21: u"S7 - Brake Switch",
    22: u"S8 - Reverse (via Bulkhead B c12)",
}
for n in range(9, 15):
    SIG[n] = u"A%d (brought out, spare)" % (n - 6)
for n in range(23, 27):
    SIG[n] = u"L%d low-side (spare %s oil lamp channel TBD, see open items)" % (n - 22, EM)


def csb3_cavities():
    out = []
    for n in range(1, 34):
        cav = {"id": "c%d" % n}
        if n <= 26:
            cav["signal"] = SIG[n]
            cav["contactPartId"] = "ct_hdp20s"
        else:
            cav["signal"] = u"spare (size 20)"
            cav["cavityPlugPartId"] = "pl_sz20"
        out.append(cav)
    return out


# ---------------------------------------------------------------- A-ECU
d = load("ST185-A-ECU.harness")

if not find(d.setdefault("contactParts", []), "ct_hdp20s"):
    d["contactParts"].append({
        "id": "ct_hdp20s", "type": "Crimp", "gender": "Socket",
        "minGauge": {"unit": "AWG", "value": 20},
        "maxGauge": {"unit": "AWG", "value": 20},
        "partNumber": "0462-201-2031",
        "description": "Size 20 solid SOCKET, 20 AWG - harness side (matches HDP20 size 20 pin family)",
        "manufacturer": "TE DEUTSCH"})

drop(d, "connectorParts", "cp_csb3io")
if not find(d.setdefault("connectorParts", []), "cp_csb3_plug"):
    d["connectorParts"].append({
        "id": "cp_csb3_plug", "gender": "Female", "hasShell": False,
        "numberOfCavities": 33, "partNumber": "HD36-24-33SE",
        "description": ("Deutsch HD30 shell 24, 33-way harness plug, sockets, E-seal - CSB3 "
                        "enclosure mating plug (harness side). Box-side receptacle is "
                        "HD34-24-33PE (device, not modeled). Cavity map per "
                        "HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md 6.37/6.40."),
        "manufacturer": "TE DEUTSCH",
        "configurations": [{"id": "cfg", "contactPartId": "ct_hdp20s",
                            "cavityPlugPartId": "pl_sz20"}]})

c = find(d["connectors"], "csb3io")
c["partId"] = "cp_csb3_plug"
c["cavities"] = csb3_cavities()

if not find(d.setdefault("splices", []), "sp_cruise_ladder"):
    d["splices"].append({"id": "sp_cruise_ladder",
                         "layoutPosition": {"x": 820, "y": 1050},
                         "schematicPosition": {"x": 820, "y": 1050}})

for wid in ("w_an2", "w_cru_sig"):
    find(d["wires"], wid)["target"] = {"id": "sp_cruise_ladder", "handle": "Splice"}
if not find(d["wires"], "w_cru_ladder_out"):
    d["wires"].append({"id": "w_cru_ladder_out", "color": "White",
                       "source": {"id": "sp_cruise_ladder", "handle": "Splice"},
                       "target": {"id": "csb3io", "handle": "c8"}})
for wid, cav in (("w_sw2", "c17"), ("w_sw3", "c18"), ("w_sw4", "c19"),
                 ("w_sw5", "c20"), ("w_sw6", "c21")):
    find(d["wires"], wid)["target"] = {"id": "csb3io", "handle": cav}
find(d["wires"], "w_sw7_c")["source"] = {"id": "csb3io", "handle": "c22"}
save("ST185-A-ECU.harness", d)


# ---------------------------------------------------------------- B-ECU (power feed only)
d = load("ST185-B-ECU.harness")
c = find(d["connectors"], "csb3io")
c["label"] = u"ECUMaster CSB3 (power feed " + EM + u" full I/O on ST185-A-ECU)"
c.pop("partId", None)
c["cavities"] = [
    {"id": "c1", "designation": "1", "signal": u"+12V (ignition switched)"},
    {"id": "c2", "designation": "2", "signal": u"GND"}]
drop(d, "connectorParts", "cp_csb3io")
save("ST185-B-ECU.harness", d)

# ---------------------------------------------------------------- CAN (CAN pair only)
d = load("ST185-CAN.harness")
c = find(d["connectors"], "csb3io")
c["label"] = u"ECUMaster CSB3 (CAN feed " + EM + u" full I/O on ST185-A-ECU)"
c.pop("partId", None)
c["cavities"] = [
    {"id": "c5", "designation": "5", "signal": u"CAN H"},
    {"id": "c6", "designation": "6", "signal": u"CAN L"}]
drop(d, "connectorParts", "cp_csb3io")
find(d["wires"], "wc_h_csb")["target"] = {"id": "csb3io", "handle": "c5"}
find(d["wires"], "wc_l_csb")["target"] = {"id": "csb3io", "handle": "c6"}
save("ST185-CAN.harness", d)

# ------------------------------------------------- EngineRoom-C cross-reference nodes
d = load("ST185-EngineRoom-C.harness")
XREF = {
    "dm_bh_b_eng_c13": u"Bulkhead B cavity 13 " + ARR + u" ECU-A A27 (Aux 7, MRS SPD) " + EM + u" wired on ST185-A-ECU",
    "dm_bh_b_eng_c14": u"Bulkhead B cavity 14 " + ARR + u" MRS EPS pump logic enable (F13, 7.5A, ignition-switched) " + EM + u" wired on ST185-B-ECU",
    "dm_fusebox_c7": u"Fusebox F7, 60A " + EM + u" EPS pump relay 30, wired on ST185-B-ECU",
    "dm_sp_sw12_Splice": u"Ignition-switched +12V splice (sp_sw12) " + EM + u" feeds EFI/ETB/fuel/fan relay coils, wired on ST185-B-ECU",
    "dm_sp_chassis_eng_Splice": u"Chassis ground splice (sp_chassis) " + EM + u" wired on ST185-B-ECU",
    "dm_ecu_b_b12": u"ECU-B pin B12 (Ign 6) " + EM + u" EPS relay trigger per 6.16, branches off at the ECU into loom C. NOTE: B12 still reads notConnected on ST185-A-ECU - fix there.",
}
for cid, text in XREF.items():
    conn = find(d["connectors"], cid)
    if conn:
        conn["cavities"][0]["signal"] = text
save("ST185-EngineRoom-C.harness", d)

# ---------------------------------------------------------------- ClusterLED
d = load("ST185-ClusterLED.harness")
conn = find(d["connectors"], "dm_csb_ls")
conn["cavities"][0]["signal"] = (
    u"ECUMaster CSB3 low-side output, L1-L4 " + EM +
    u" channel TBD (see ST185-A-ECU C10 cavities 23-26, and CAN 0x643), wired on ST185-A-ECU")
save("ST185-ClusterLED.harness", d)

print("\n".join(log))
print("done")
