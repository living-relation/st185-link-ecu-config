"""Master from-to wire list, A-cabin pilot (DECISIONS R201, Dan N39 = A).

One row per physical wire, FROM a real pin TO a real pin (or a splice node), in a format that
can later hold every harness file. A wire that runs on through another loom is ONE row: its
far end is the real pin it lands on in that loom (found through the registered break pair),
and `harnesses` lists every file it runs in.

The list is checked AGAINST today's SoT, row by row. channels.csv, interfaces.json, the
DRB102 cavity map and the fuse-box wiring plan stay the live SoT until Dan approves the
switch. Each row's `sot_check` says what it was matched to, and `status` is OK or the mismatch.

Outputs (pilot, untracked):  _research/harness-cleanroom/A-cabin-wirelist.csv
                             _research/harness-cleanroom/A-cabin-splices.csv
                             _research/harness-cleanroom/A-cabin-pinouts.md

    python docs/harness/cleanroom/wirelist.py
"""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(HARNESS))
sys.path.insert(0, HERE)
sys.path.insert(0, HARNESS)
import model  # noqa: E402
from build_a_cabin import CABLES, CONNECTORS, SPLICES, WIRES  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(REPO)) if REPO.endswith("harness-cr") else REPO,
                   "_research", "harness-cleanroom")
# the worktree sits in <main checkout>/.claude/worktrees/<name>: write into the main checkout's _research
MAIN = REPO
while os.path.basename(os.path.dirname(MAIN)) == "worktrees":
    MAIN = os.path.dirname(os.path.dirname(os.path.dirname(MAIN)))
OUT = os.path.join(MAIN, "_research", "harness-cleanroom")

COLUMNS = ["wire_id", "harnesses", "from_conn", "from_conn_name", "from_pin", "from_desc",
           "to_conn", "to_conn_name", "to_pin", "to_desc", "net", "splice", "cable",
           "gauge_awg", "colour", "stripe", "ident_bands", "route_branch", "est_length_mm",
           "sot_check", "status", "notes"]
SPLICE_COLUMNS = ["splice_id", "name", "net", "harness", "location", "method", "wires",
                  "gauges_awg", "combined_cma", "equivalent_awg", "sot_check"]

# what a splice net is called (Dispatch splice rule: one net name per splice)
NETS = {"sp_5v": "Sensor +5 V (ECU A32)", "sp_5v_2": "Sensor +5 V (ECU A32)",
        "sp_8v": "Cam +8 V (ECU A6)", "sp_trig2": "Cam signal (ECU A9)",
        "sp_gndout": "Sensor ground A (ECU A24)", "sp_sw12": "Switched +12 V (SW12)",
        "sp_chassis": "ECU power ground", "sp_shield_a": "Shield drain A (ECU A7)",
        "sp_ac_psw": "A/C pressure switch out"}
CMA = {22: 642, 6: 26240, 4: 41740, 20: 1022, 18: 1624, 16: 2583, 14: 4107, 12: 6530, 10: 10380, 8: 16510}

# route branch of an A-cabin end (Route 5, approved 2026-10-14). Names, not bundle ids.
BRANCH = [
    (("bh_a_fw", "bus_5v_bha_p", "bus_gnd_bha_p"), "trunk ECU-A to bulkhead (RH firewall)"),
    (("aps",), "pedal branch (driver footwell)"),
    (("ix_ws_front_p", "br_cab_fspur_r", "br_cab_fspur_fr_sh"), "dash branch (front WS inline)"),
    (("fl_acamp_act", "fl_acamp_psw", "fl_acamp_mg", "br_ac_psw", "br_ac_mg", "br_w_acc86", "sp_ac_psw"),
     "A/C amp branch (behind dash)"),
    (("br_w76", "br_w81", "br_w_str85", "br_w_fan85", "br_w_eps_rly", "br_w_fb_sw12", "br_w_inj_pwr_c",
      "br_w_cop_pwr_c", "br_w_fb_mrs_en", "br_w_fp85"), "glove-box branch (POWER / LOGIC boxes)"),
    (("br_w_b25", "br_w_b34", "br_w_rail_5v_b_c", "br_w39", "br_w_lamg_b", "br_w_rail_sw12_b_c"),
     "to ECU-B plug (beside ECU-A)"),
    (("br_w_cru_5v", "br_w_csbg"), "CSB3 branch (centre console)"),
    (("chassis_ring",), "ground stud at ECU"),
    (("ecu_a", "sp_5v", "sp_5v_2", "sp_8v", "sp_trig2", "sp_gndout", "sp_sw12", "sp_chassis", "sp_shield_a"),
     "at ECU-A plug"),
]


def branch_of(node):
    for nodes, name in BRANCH:
        if node in nodes:
            return name
    return ""


def main():
    reg = model.registry()
    docs = model.docs(reg)
    files = {k: v for k, v in model.harness_files(reg).items()}
    cab = docs["A-cabin"]
    sot = model.sot_rows()
    sot_pin = {(r["conn"], r["pin"]): r for r in sot}
    with open(os.path.join(HARNESS, "DRB102-CAVITY-MAP.md"), encoding="utf-8") as f:
        drb = {}
        for line in f:
            m = re.match(r"\| (\d+) \| [^|]+\| (\d+) \| ([AB]) \| (c\d+) \| (.+) \|\s*$", line)
            if m:
                drb[m.group(1)] = (m.group(3), m.group(4), m.group(5).strip())
    with open(os.path.join(REPO, "cad", "fusebox", "rev7", "wiring_plan.json"), encoding="utf-8") as f:
        fuse_cav = {w: (c["box"], c["cav"]) for c in json.load(f)["cavities"] for w in c["wires"]}
    breaks = {e["terminal"]: br for br in reg["breaks"] for e in br["ends"] if e["harness"] == "A-cabin"}
    fleads = {f["terminal"]: f for f in reg["flyingLeads"] if f["harness"] == "A-cabin"}
    sot_text = open(os.path.join(REPO, "sot", "channels.csv"), encoding="utf-8").read() + \
        json.dumps(reg) + open(os.path.join(HARNESS, "DRB102-CAVITY-MAP.md"), encoding="utf-8").read()

    raw = {}
    for h, fn in files.items():
        with open(os.path.join(HARNESS, "rebuild", fn), encoding="utf-8") as f:
            raw[h] = {c["id"]: c.get("label", c["id"]) for c in json.load(f).get("connectors", [])}
    parts = model.parts(cab)
    cond = {c["id"]: c for c, _, _ in model.conductors(cab)}
    conn_label = {c["id"]: c.get("label", c["id"]) for c in cab["connectors"]}

    def far_end(term):
        """A break end on A-cabin -> (harness, conn id, conn name, pin, other half wire id)."""
        br = breaks[term]
        other = next(e for e in br["ends"] if e["harness"] != "A-cabin")
        d = docs[other["harness"]]
        for c, _, _ in model.conductors(d):
            for a, b in (("source", "target"), ("target", "source")):
                if (c.get(a) or {}).get("id") == other["terminal"] and c.get(b):
                    o = c[b]
                    for cn in d.get("connectors", []):
                        if cn["id"] == o["id"]:
                            cav = next(x for x in cn["cavities"] if x["id"] == o["handle"])
                            return (other["harness"], cn["id"], raw[other["harness"]].get(cn["id"], cn["id"]),
                                    cav.get("designation", ""), c["id"], br["id"])
                    return other["harness"], o["id"], o["id"], "", c["id"], br["id"]
        return other["harness"], "?", "?", "", "?", br["id"]

    rows, splice_wires = [], {}

    core_gauge = {}
    for cb in cab.get("cables", []):
        cp = parts.get(cb.get("partId")) or {}
        for i, core in enumerate(cb["cores"]):
            g = ((cp.get("cores") or [{}] * (i + 1))[i].get("gauge") or {}).get("value", "")
            core_gauge[core["id"]] = g

    def add(wid, f, t, desc, cable=""):
        w = cond[wid]
        p = parts.get(w.get("partId")) or {}
        gauge = (p.get("gauge") or {}).get("value", "") or core_gauge.get(wid, "")
        harn, notes, checks, bad, gap = ["A-cabin"], [], [], [], []
        ends = []
        for node, pin in (f, t):
            if node in CONNECTORS:
                ends.append([node, conn_label[node].split("  ")[0], pin])
            elif node in SPLICES:
                ends.append([node, SPLICES[node].split(" - ")[1], ""])
                splice_wires.setdefault(node, []).append((wid, gauge))
                checks.append("splice %s named in SoT" % node if node in sot_text else "")
                if node not in sot_text:
                    gap.append("splice %s is not named in the SoT (drawing only)" % node)
            elif node in breaks:
                h, cid, cname, cpin, half, brid = far_end(node)
                harn.append(h)
                ends.append([cid, cname, cpin])
                checks.append("break %s (other half %s on %s)" % (brid, half, h))
                if cid in ("k_efi", "k_str", "k_fan", "k_etb", "k_acc", "k_eps", "k_fp"):
                    checks.append("relay pin from %s drawing (no channels.csv row)" % h)
                if half in fuse_cav:
                    box, cav = fuse_cav[half]
                    checks.append("fuse-box plan %s %s" % (box, cav))
                    plan_pin = cav.split(" ")[-1]
                    if plan_pin != cpin.split("-")[-1] and cav != cpin:
                        bad.append("fuse-box plan says %s %s, drawing says %s" % (box, cav, cpin))
                    slot = cav.split(" ")[0]
                    if " " in cav and slot not in re.findall(r"[A-Z]+\d+", cname) and not re.search(r"%s" % re.escape(slot), cname):
                        gap.append("relay slot: fuse-box plan %s %s, %s drawing label '%s'" % (box, slot, h, cname))
            elif node in fleads:
                ew = fleads[node]["ewd"]
                ends.append(["A18 (factory)", "OEM A/C amplifier, tap on factory %s lead" % ew["color"], ew["pin"]])
                checks.append("flying lead %s: EWD %s pin %s %s" % (fleads[node]["id"], ew["connector"], ew["pin"], ew["color"]))
            elif node == "cam_pullup":
                ends.append(["R-CAM", "Cam pull-up resistor 1.8 k", "1" if pin == "Left" else "2"])
                checks.append("channels.csv a9 pull-up ext-1k8-to-8v")
            else:  # chassis ring
                ends.append([node, "Ground ring M6, cabin chassis stud at ECU", ""])
        # ECU-A / ECU-B pins against channels.csv
        for (cid, _, pin) in ends:
            if cid in ("ecu_a", "ecu_b"):
                r = sot_pin.get((cid, pin.lower()))
                if not r:
                    bad.append("%s %s not in channels.csv" % (cid, pin))
                else:
                    checks.append("channels.csv %s %s %s (%s)" % (cid, pin, r["channel"], r["net"] or "-"))
        # bulkhead cavities against the DRB102 map
        ecu_pins = [p for c, _, p in ends if c == "ecu_a"]
        for (cid, _, pin) in ends:
            if cid in ("bh_a_fw", "bh_b_fw"):
                sec, cavid, use = drb.get(pin, ("?", "?", "?"))
                checks.append("DRB102 %s = section %s %s '%s'" % (pin, sec, cavid, use[:50]))
                if ecu_pins and use.startswith("ECU-A") and use != "ECU-A " + ecu_pins[0]:
                    bad.append("DRB102 %s is '%s' but wire is from ECU-A %s" % (pin, use, ecu_pins[0]))
                if use.startswith("spare"):
                    gap.append("DRB102 map table row %s says spare; its own note and R22 put the EPS relay coil there" % pin)
        net = next((NETS[n] for n in (f[0], t[0]) if n in NETS), desc)
        rows.append({
            "wire_id": wid, "harnesses": " + ".join(dict.fromkeys(harn)),
            "from_conn": ends[0][0], "from_conn_name": ends[0][1], "from_pin": ends[0][2], "from_desc": desc,
            "to_conn": ends[1][0], "to_conn_name": ends[1][1], "to_pin": ends[1][2], "to_desc": desc,
            "net": net, "splice": next((n for n in (f[0], t[0]) if n in SPLICES), ""), "cable": cable,
            "gauge_awg": gauge, "colour": w.get("color", ""), "stripe": w.get("stripeColor", ""),
            "ident_bands": "-".join(w.get("identColors", [])),
            "route_branch": " / ".join(x for x in dict.fromkeys(branch_of(n) for n in (f[0], t[0])) if x and
                                       (x != "at ECU-A plug" or all(branch_of(n) == x for n in (f[0], t[0])))),
            "est_length_mm": "", "sot_check": "; ".join(c for c in checks if c),
            "status": ("MISMATCH: " + "; ".join(bad)) if bad else ("SOT GAP: " + "; ".join(gap)) if gap else "OK",
            "notes": "; ".join(notes)})

    for wid, f, t, desc in WIRES:
        add(wid, f, t, desc)
    for cid, cores in CABLES.items():
        for core, (f, t, desc) in cores.items():
            if f is None:  # one-end shield: from the cable's own screen
                f = ("cable screen " + cid, None)
                rows_before = len(rows)
                w = cond[core]
                rows.append({"wire_id": core, "harnesses": "A-cabin", "from_conn": cid, "from_conn_name": "cable screen (one end only)",
                             "from_pin": "", "from_desc": desc, "to_conn": t[0],
                             "to_conn_name": SPLICES.get(t[0], t[0]).split(" - ")[-1], "to_pin": "", "to_desc": desc,
                             "net": NETS.get(t[0], desc), "splice": t[0] if t[0] in SPLICES else "", "cable": cid,
                             "gauge_awg": "", "colour": "Shield", "stripe": "", "ident_bands": "-".join(w.get("identColors", [])),
                             "route_branch": branch_of(t[0]) or branch_of(cid), "est_length_mm": "",
                             "sot_check": "shield to its drain (R29 / R30)", "status": "OK", "notes": "screen floats at the far end"})
                if t[0] in breaks:
                    h, cid2, cname, cpin, half, brid = far_end(t[0])
                    rows[-1].update(to_conn=cid2, to_conn_name=cname, harnesses="A-cabin + " + h,
                                    sot_check="break %s (other half %s on %s)" % (brid, half, h))
                if t[0] in SPLICES:
                    splice_wires.setdefault(t[0], []).append((core, ""))
                continue
            add(core, f, t, desc, cable=cid)

    # est length from the build list (current drawing)
    with open(os.path.join(HARNESS, "HARNESS-BUILD-LIST.csv"), encoding="utf-8") as f:
        est = {r["Wire"]: r["Est mm"] for r in csv.DictReader(f) if r["File"] == "A-cabin"}
    for r in rows:
        r["est_length_mm"] = est.get(r["wire_id"], "")

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "A-cabin-wirelist.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLUMNS)
        w.writeheader()
        w.writerows(rows)

    # splice table
    spl = {s["id"]: s for s in cab["splices"]}
    sparts = model.parts(cab)
    srows = []
    for sid, name in SPLICES.items():
        ws = splice_wires.get(sid, [])
        gauges = [g for _, g in ws if g]
        cma = sum(CMA.get(int(g), 0) for g in gauges)
        eq = next((a for a in sorted(CMA, reverse=True) if CMA[a] >= cma), "") if cma else ""
        loc = spl[sid].get("locationId", "")
        srows.append({"splice_id": sid, "name": name, "net": NETS[sid], "harness": "A-cabin",
                      "location": name.split(" - ")[0] + (" (layout node %s)" % loc if loc else ""),
                      "method": (sparts.get(spl[sid].get("partId")) or {}).get("description", "solder splice")[:60],
                      "wires": len(ws), "gauges_awg": "+".join(str(g) for g in gauges) + (" + shield" if len(gauges) < len(ws) else ""),
                      "combined_cma": cma, "equivalent_awg": eq,
                      "sot_check": "named in SoT" if sid in sot_text else "SOT GAP: not named in the SoT (drawing only)"})
    with open(os.path.join(OUT, "A-cabin-splices.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, SPLICE_COLUMNS)
        w.writeheader()
        w.writerows(srows)

    # pinout tables, derived from the list
    pins = {}
    for r in rows:
        for side, other in (("from", "to"), ("to", "from")):
            if r[side + "_pin"] and r[side + "_conn"] in CONNECTORS or r[side + "_conn"] in ("ecu_b", "k_efi", "k_str", "k_fan", "k_etb", "k_acc", "k_eps", "k_fp", "fb_logic", "bus_sw12_p", "bh_b_fw"):
                oth = r[other + "_conn_name"] + (" pin " + r[other + "_pin"] if r[other + "_pin"] else "")
                pins.setdefault((r[side + "_conn"], r[side + "_conn_name"]), []).append(
                    (r[side + "_pin"], r["wire_id"], r[side + "_desc"], oth))

    def pkey(p):
        m = re.match(r"([A-Za-z]*)(\d+)(.*)", p)
        return (m.group(1), int(m.group(2)), m.group(3)) if m else (p, 0, "")
    with open(os.path.join(OUT, "A-cabin-pinouts.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# A-cabin pinouts (derived from A-cabin-wirelist.csv)\n\n")
        f.write("Generated by `docs/harness/cleanroom/wirelist.py`. One table per connector; "
                "only pins this loom wires are listed. Far-end connectors on other looms are listed "
                "with just the pins A-cabin wires reach.\n")
        for (cid, cname), lst in sorted(pins.items(), key=lambda kv: (kv[0][0] not in CONNECTORS, kv[0][0])):
            f.write("\n## %s (`%s`)\n\n| Pin | Wire | Description | Other end |\n|---|---|---|---|\n" % (cname, cid))
            for pin, wid, desc, oth in sorted(lst, key=lambda x: pkey(x[0])):
                f.write("| %s | %s | %s | %s |\n" % (pin, wid, desc, oth))
    bad = [r for r in rows if r["status"] != "OK"]
    print("wire list: %d rows, %d splices, %d mismatch(es), %d SoT gap row(s) -> %s" % (
        len(rows), len(srows), sum(r["status"].startswith("MISMATCH") for r in rows),
        sum(r["status"].startswith("SOT GAP") for r in rows), OUT))
    for r in bad:
        print("  ", r["wire_id"], r["status"])


if __name__ == "__main__":
    main()
