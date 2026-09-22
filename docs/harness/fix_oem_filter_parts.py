"""Carry the OEM's own diodes / filters into our drawings where we reuse the circuit.

Daniel: "make sure that any circuits in the OEM wiring diagrams that contain
filtering diodes or capacitors specify those in our diagrams so I can replace
them where necessary only where external filtering stuff was used on the OEM."

Read of the EWD snips in docs/electrical/ewd-snips, 2026-09-22:

  page 19  J/B No.1 inner circuit     ONE 3-terminal diode block, pins 1/2/3,
                                      two diodes with a common cathode on 2.
                                      Inside a block we KEEP - nothing to build,
                                      but do not inject power around it.
  page 21  J/B No.2 inner circuit     no diodes, no capacitors. Relays and fuses.
  page 22  J/B No.3 inner circuit     pure junction block. Nothing.
  page 46  Power source               no diodes, no capacitors.
  page 48  Starting and ignition      diode inside S2 start injector time switch,
                                      between the STJ and STA coils. DELETED with
                                      the cold-start injector.
  page 52  Charging                   C12 combination meter, charge warning lamp
                                      between pin 9 (IG, B-O) and pin 8 (alt L, Y),
                                      drawn with a diode. THIS ONE MATTERS.

The charge lamp is not an indicator, it is the alternator's pre-excitation path:
IG -> bulb -> L terminal -> field.  A 3.4 W bulb passes roughly 250 mA at 13.8 V.
We are replacing it with an LED at about 20 mA, an order of magnitude less, and
many IC regulators will not start charging on that until the engine is revved.

So the LED gets a resistor in parallel to carry the excitation current the bulb
used to.  56 ohm is the bulb-equivalent starting point; it only dissipates while
the lamp condition is true, because once charging both ends sit at ~14 V.

This script adds that resistor.  The value is marked for confirmation against
the actual alternator - it is the one number here that depends on a part we have
not bench-tested.
"""
import json, os

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
p = os.path.join(R, "ST185-ClusterLED.harness")
d = json.load(open(p, encoding="utf-8"))

PART = {
    "id": "rp_chg_excite",
    "partNumber": "56R 5W",
    "manufacturer": "generic",
    "description": "Alternator pre-excitation, in parallel with the charge LED. "
                   "Replaces the current the OEM 3.4W charge bulb used to pass "
                   "(~250 mA at 13.8 V) - an LED alone passes ~20 mA and many IC "
                   "regulators will not self-excite on that. Value CONFIRM against "
                   "the fitted alternator; wirewound, mount it where it can shed heat.",
}
RES = {
    "id": "r_chg_excite",
    "partId": "rp_chg_excite",
    "locationId": "cl_c12",
    "schematicPosition": {"x": 450, "y": 660},
    "layoutPosition": {"x": 450, "y": 660},
}
WIRES = [
    {"id": "w_chg_ex_a", "color": "Black",
     "source": {"id": "cl_c12", "handle": "c9"},
     "target": {"id": "r_chg_excite", "handle": "Left"}},
    {"id": "w_chg_ex_k", "color": "Yellow",
     "source": {"id": "r_chg_excite", "handle": "Right"},
     "target": {"id": "cl_c12", "handle": "c8"}},
]

lib = d.setdefault("resistorParts", [])
if not any(q["id"] == PART["id"] for q in lib):
    lib.append(PART)
res = d.setdefault("resistors", [])
if not any(x["id"] == RES["id"] for x in res):
    res.append(RES)
    print("+ r_chg_excite   56R 5W across the charge LED (alternator pre-excitation)")
have = {w["id"] for w in d["wires"]}
for w in WIRES:
    if w["id"] not in have:
        d["wires"].append(w)
        print("+ %-14s %s.%s -> %s.%s" % (w["id"], w["source"]["id"], w["source"]["handle"],
                                          w["target"]["id"], w["target"]["handle"]))

# say so on the drawing, not just in a commit message
note = ("OEM FILTER PARTS CARRIED OVER (EWD 1990 ST185)\n"
        "- Charging p.52: the C12 charge lamp sits between pin 9 (IG, B-O) and\n"
        "  pin 8 (alt L, Y) and is the alternator's pre-excitation path, not just\n"
        "  an indicator. r_chg_excite replaces the bulb's ~250 mA. Do not delete it.\n"
        "- J/B No.1 p.19 holds a 3-terminal diode (common cathode on pin 2). It stays\n"
        "  inside the block we keep - do not inject power in a way that bypasses it.\n"
        "- J/B No.2 p.21, J/B No.3 p.22, Power source p.46: no diodes, no capacitors.\n"
        "- Starting p.48: the diode in the S2 start injector time switch is deleted\n"
        "  with the cold-start injector.")
notes = d.setdefault("schematicNotes", [])
if not any("OEM FILTER PARTS" in (n.get("text") or "") for n in notes):
    notes.append({"id": "note_oem_filters", "text": note,
                  "schematicPosition": {"x": 0, "y": 840}})
    print("+ schematic note: OEM filter parts carried over")

json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
