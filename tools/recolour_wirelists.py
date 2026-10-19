"""One-shot rule script for DECISIONS R209 (Dan N52): recolour the wire lists to 7 solid colours.
Red +12 V power / Black power+chassis ground / Orange sensor supply / Blue sensor ground /
White signals and ECU outputs / Green CAN / Yellow switch inputs. Rows with a cable part keep
their cable conductors. Colour and stripe columns only, by function (from_desc)."""
import csv, glob, re, sys

RULES = [
    ("Green", r"\bCAN [HL]\b"),
    ("Black", r"shield|drain|screen"),
    ("Yellow", r"^(Brake on|Brake to CSB3|Clutch pedal sw|Cruise MAIN on|Cruise ladder$|Door trigger|Hood trigger|Trunk trigger|"
               r"Ignition sw sense|IG2 wake|Start request|Start sw ST1|Reverse to |Reverse sw \+12 V out|A/C request|A/C btn divider mid|"
               r"A/C switch V-G|A/C press sw feed|A/C pressure sw out|Valet switch$|Wiper park sw|Park brake sw|Retract (open|close) limit)"),
    ("White", r"coil ?\(-\)|coil-$|relay \(-\)|drive \(-\)|trigger \(IGT\)|^Boost solenoid|^ETB motor [+-]$|^A/C cancel|^EHPS pump speed|"
              r"^Charge lamp drive|^Alt [LS] |^Park lamp flash|LED sink"),
    ("Orange", r"^\+5 V|^\+8 V|^Opto \+5"),
    ("Blue", r"^Gnd |^Sensor ground|thermistor gnd|^Fuel level ground|^Knock sensor \(-\)|^Cruise stalk ground|btn divider gnd"),
    ("Black", r"gnd|ground|^Battery - |strap"),
    ("Red", r"\+12 ?V|feed|coil\+|\+B$|B\+$|\(\+\)|return|motor|LED \+|excite|^Battery \+|^Alt IG|^Starter|^Wiper|^Washer|"
            r"box +$|relay out|enable out|^Siren +\+|^Back-up|^Alarm|lamp \+|^(LH|RH) clearance|^Licence light \+|^Stop (LH|RH)|^Tail (LH|RH)|marker (LH|RH) \+|"
            r"^Turn (LH|RH) rear|front turn|^Block|^High stop lamp \+|^Status LED \+"),
    ("White", r".*"),
]

def pick(desc):
    for col, rx in RULES:
        if re.search(rx, desc):
            return col

def main(write):
    seen = {}
    for f in sorted(glob.glob("docs/harness/wirelist/*-wirelist.csv")):
        rows = list(csv.DictReader(open(f, encoding="utf-8", newline="")))
        flds = list(rows[0].keys())
        for r in rows:
            if r["cable"] or not r["colour"]:
                continue
            c = pick(r["from_desc"])
            seen.setdefault((c, r["from_desc"]), 0)
            seen[(c, r["from_desc"])] += 1
            r["colour"], r["stripe"] = c, ""
        if write:
            with open(f, "w", encoding="utf-8", newline="") as o:
                w = csv.DictWriter(o, flds, lineterminator="\n"); w.writeheader(); w.writerows(rows)
    if not write:
        for (c, d), n in sorted(seen.items()):
            print(c, "|", d)

main("--write" in sys.argv)
