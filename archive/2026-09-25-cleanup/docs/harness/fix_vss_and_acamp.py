"""Wire the VSS, and correct the A/C circuits from the EWD pages just pulled.

--------------------------------------------------------------------------
1. VSS - it was never wired at all
--------------------------------------------------------------------------
Daniel: "Vss is used for actual vehicle speed. Don't delete." The problem was
the opposite of deleting - ecu_b b29 was `notConnected: true` with no signal
name, so the VSS existed only in the IO table. Audit finding E10.

From XTREMEX-IO-TABLE.html, the ECU pin SoT, DI 8 / B29:
    "Daniel lock 2026-09-18: gearbox 3-wire 12V Toyota VSS (not 4-wire).
     Harness mate = generic oval 3-pin plug with socket contacts, PN TBD."

Three wires. B29 is on connector B, so it crosses bulkhead B - the letter rule.
Signal gets its own bulkhead pin; supply and ground join the engine-side rails
that already cross, exactly like every other engine sensor.

    vss c1  +12V switched  <- sp_sw12_eng          (no new bulkhead pin)
    vss c2  ground         <- sp_gndout_eng        (no new bulkhead pin)
    vss c3  signal         -> bh_b c15 -> ecu_b b29 (DI 8)

DI 8 takes the 12 V output directly - Link G4Install.pdf: DI max +/-50 V, low
< 1 V, high > 2 V, selectable 4k7 pull-up to 12 V. No divider, no series
resistor. Confirm the sensor's output type (open collector vs push-pull) before
choosing the pull-up setting; that is a PCLink setting, not a wiring change.

NOT the same thing as the wheel-speed inputs. Daniel: "Vrc is used only for link
ECU traction control." VSS = actual road speed. They coexist.

--------------------------------------------------------------------------
2. A/C - two different amplifiers, and the pressure switch is 2-wire
--------------------------------------------------------------------------
Read off the factory EWD pages pulled 2026-09-24 and saved to
docs/electrical/ewd-snips/ (automatic air conditioner section):

  p150  AUTO A/C AMPLIFIER  A32 = conn A, A33 = conn B, A34 = conn C
        A1 A/C Ambient Temp Sensor: pin 1 on Y, pin 2 on Y-B
        -> junction EA1 pin 4 -> IQ1 pin 1 -> terminal TAM = conn C pin 6
        (A27 A/C Water Temp Sensor -> terminal TW = conn C pin 20, for reference)

  p152  A/C AMPLIFIER  A18 - a SEPARATE module from the auto amp above
        A5 A/C Pressure SW: pin 1 <- V-R, pin 4 -> Y-R
        -> EB2 pin 2 -> E10 -> IJ1 pin 15 -> A18 pin 13
        The same Y-R also feeds A3 A/C Idle-Up VSV. TWO WIRES, not three.

So the guess of a single "acamp" was wrong in two ways: there are two
amplifiers, and the pressure switch is a 2-wire dual switch.
"""
import json, os

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")


def load(n):
    p = os.path.join(R, "ST185-%s.harness" % n)
    return p, json.load(open(p, encoding="utf-8"))


def save(p, d):
    json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


VSS_SIG = ("Gearbox VSS signal -> bulkhead B c15 -> ECU-B B29 (DI 8). "
           "Actual road speed. 12V direct, no divider - Link DI is +/-50V "
           "tolerant with a selectable 4k7 pull-up to 12V.")

# ---- engine / transmission side -------------------------------------------
p, d = load("B-engine")
if not any(c["id"] == "vss" for c in d["connectors"]):
    d["connectors"].append({
        "id": "vss", "label": "Gearbox VSS (3-wire, Toyota) - actual road speed",
        "width": 270, "partId": "cp_vss3",
        "schematicPosition": {"x": 180, "y": 2100},
        "layoutPosition": {"x": 180, "y": 2100},
        "cavities": [
            {"id": "c1", "designation": "1", "signal": "+12V switched"},
            {"id": "c2", "designation": "2", "signal": "Ground"},
            {"id": "c3", "designation": "3", "signal": VSS_SIG}]})
    d.setdefault("connectorParts", []).append({
        "id": "cp_vss3", "partNumber": "TBD - generic oval 3-pin, socket contacts",
        "manufacturer": "Toyota", "gender": "Female", "hasShell": False,
        "numberOfCavities": 3,
        "description": "Gearbox 3-wire 12V Toyota VSS, NOT the 4-wire type "
                       "(Daniel lock 2026-09-18, XTREMEX-IO-TABLE.html DI 8). "
                       "Harness mate is a generic oval 3-pin plug with socket "
                       "contacts - PN still TBD, measure the plug on the box."})
    d["wires"] += [
        {"id": "w_vss_12v", "color": "Red",
         "source": {"id": "sp_sw12_eng", "handle": "Splice"},
         "target": {"id": "vss", "handle": "c1"}},
        {"id": "w_vss_gnd", "color": "Black",
         "source": {"id": "vss", "handle": "c2"},
         "target": {"id": "sp_gndout_eng", "handle": "Splice"}},
        {"id": "w_vss_sig_e", "color": "Green",
         "source": {"id": "vss", "handle": "c3"},
         "target": {"id": "bh_b_eng", "handle": "c15"}}]
    print("+ B-engine  vss 3-way, 12V and gnd off the engine rails, sig -> bh_b c15")
save(p, d)

# ---- cabin side ------------------------------------------------------------
# This SHOULD live in the B file. It does not, because the A/B split never
# happened the way it was meant to: A-ECU holds BOTH full 34-cavity ECU
# connectors (ecu_a and ecu_b, with parts), and B-ECU holds only 6-cavity
# stubs of each with no part. B-ECU is a power/rail file wearing the wrong
# name. Landing the wire where the real b29 cavity actually is, and it moves
# to the B file with everything else in the re-split.
p, d = load("A-ECU")
if not any(w["id"] == "w_vss_sig_c" for w in d["wires"]):
    d["wires"].append({"id": "w_vss_sig_c", "color": "Green",
                       "source": {"id": "bh_b_fw", "handle": "c15"},
                       "target": {"id": "ecu_b", "handle": "b29"}})
    print("+ B-ECU     w_vss_sig_c  bh_b_fw c15 -> ecu_b b29")
save(p, d)

# b29 stops being notConnected, in every copy
for fn in os.listdir(R):
    if not fn.endswith(".harness"):
        continue
    p = os.path.join(R, fn)
    d = json.load(open(p, encoding="utf-8"))
    hit = False
    for c in d.get("connectors", []):
        if c["id"] != "ecu_b":
            continue
        for cv in c["cavities"]:
            if cv["id"] == "b29":
                cv.pop("notConnected", None)
                cv["signal"] = "DI 8 (VSS - actual road speed)"
                hit = True
    if hit:
        save(p, d)
        print("  b29 un-notConnected in %s" % fn[6:-8])

# ---- A/C: split the two amplifiers, pressure switch down to 2-wire ---------
p, d = load("EngineRoom-C")
conns = {c["id"]: c for c in d["connectors"]}

conns["dm_acamp"].update({
    "label": "AUTO A/C AMPLIFIER A34 = conn C (dash module)",
    "cavities": [
        {"id": "c1", "designation": "C-6",
         "signal": "TAM - ambient temp in. EWD p150: A1 pin 2 -> EA1 4 -> IQ1 1 "
                   "-> TAM, conn C pin 6, wire Y-B."},
        {"id": "c2", "designation": "Y bus",
         "signal": "Ambient temp sensor return, wire Y. EWD p150."}]})

if "dm_acamp18" not in conns:
    d["connectors"].append({
        "id": "dm_acamp18", "label": "A/C AMPLIFIER A18 (separate module, dash)",
        "width": 270,
        "schematicPosition": {"x": 900, "y": 2580},
        "layoutPosition": {"x": 900, "y": 2580},
        "cavities": [
            {"id": "c1", "designation": "13",
             "signal": "A/C pressure switch in. EWD p152: A5 pin 4 -> EB2 2 -> "
                       "E10 -> IJ1 15 -> A18 pin 13, wire Y-R. Shares this net "
                       "with the A3 A/C idle-up VSV."}]})
    print("+ EngineRoom-C  dm_acamp18 - the pressure switch goes to a DIFFERENT amp")

conns["ac_press"].update({
    "label": "A/C Pressure Switch (EWD A5) - 2-wire dual switch",
    "partId": "cp_ac_press",
    "cavities": [
        {"id": "c1", "designation": "1", "signal": "+12V in, wire V-R. EWD p152."},
        {"id": "c2", "designation": "4",
         "signal": "Switched out -> A/C AMPLIFIER A18 pin 13, wire Y-R. EWD p152."}]})

for q in d["connectorParts"]:
    if q["id"] == "cp_ac_press":
        q.update({"numberOfCavities": 2,
                  "partNumber": "TBD - A/C pressure switch connector, 2-way",
                  "description": "A/C pressure switch, EWD A5, engine compartment. "
                                 "CONFIRMED 2-WIRE from EWD p152 (pin 1 in on V-R, "
                                 "pin 4 out on Y-R) - it is a dual pressure switch, "
                                 "not a trinary. Connector PN still TBD."})
    if q["id"] == "cp_amb_temp":
        q["description"] = ("2-way for the A/C ambient temp thermistor, EWD A1, behind "
                            "the front bumper. Lands on the AUTO A/C amplifier terminal "
                            "TAM, connector C (A34) pin 6, wire Y-B (EWD p150). "
                            "Connector PN still TBD.")

# re-point the pressure-switch wires at A18 and drop the third pole
d["wires"] = [w for w in d["wires"] if w["id"] != "w_acp_3"]
for w in d["wires"]:
    if w["id"] == "w_acp_1":
        w.update({"color": "Violet",
                  "source": {"id": "ac_press", "handle": "c1"},
                  "target": {"id": "dm_fusebox_c7", "handle": "c1"}})
    if w["id"] == "w_acp_2":
        w.update({"color": "Yellow",
                  "source": {"id": "ac_press", "handle": "c2"},
                  "target": {"id": "dm_acamp18", "handle": "c1"}})
print("- w_acp_3 (no third pole), w_acp_1/2 re-pointed")

for n in d.get("schematicNotes", []):
    if n.get("id") == "note_acamp":
        n["text"] = (
            "A/C IS THE AMPLIFIERS' BUSINESS, NOT THE ECU'S - and there are TWO\n"
            "Read off the factory EWD automatic-A/C pages, saved in ewd-snips:\n"
            "  p150  AUTO A/C AMPLIFIER  A32=conn A, A33=conn B, A34=conn C\n"
            "        A1 Ambient Temp -> TAM, conn C pin 6, Y-B (via EA1 4, IQ1 1)\n"
            "        A27 Water Temp  -> TW,  conn C pin 20, R-G\n"
            "  p152  A/C AMPLIFIER A18 - a SEPARATE module\n"
            "        A5 Pressure SW  -> A18 pin 13, Y-R (via EB2 2, E10, IJ1 15)\n"
            "        TWO WIRES: pin 1 in on V-R, pin 4 out on Y-R. Dual switch,\n"
            "        not a trinary. Same Y-R net also feeds the A3 idle-up VSV.\n"
            "Engine-bay parts are loom C's: A1 ambient, A5 pressure switch.\n"
            "Cabin: A23 room temp, A24 solar, A26 evaporator thermistor, A27 water.\n"
            "The ECU sees NONE of them. Its only A/C tie is Aux 4 / A18 kill.\n"
            "STILL OPEN: both connector part numbers, and the A/C amp pin for the\n"
            "ambient sensor's Y return leg.")
save(p, d)
