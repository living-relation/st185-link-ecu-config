"""Master from-to wire list, A-cabin pilot (DECISIONS R201: Dan N39 = A, N40 = A).

One row per physical wire, FROM a real pin TO a real pin or a splice node, in a format that can
later hold every harness file. Today's SoT stays live (channels.csv, interfaces.json, the DRB102
cavity map, the fuse-box wiring plan): every row is checked AGAINST it, and `status` says OK,
MISMATCH (row disagrees with the SoT) or SOT GAP (the SoT itself is silent or inconsistent).

Rules in the format (Dispatch for Dan, 2026-10-19):
  - splice = its own node (ID, plain name, net); every wire into it is its own row; splice table
  - bussed DT plug (R169) = a normal connector: one row per pin, net = the bus net; the bussed
    cap is listed as the plug's mate ("all cavities bussed: one net") with no wire rows;
    unused cavities are "spare, sealing plug" rows with no wire
  - through a connector (bulkhead, inline DT): one row per harness, each ending at its pin,
    sharing `circuit_id` and the description; the mating table checks both sides agree (N40 1)
  - one wire running through two files with no connector: ONE row, owned by the file it is
    built with (the longer half), `passes_through` names the other file (N40 2)
  - factory ends are endpoints of type OEM with the factory wire colour, EWD page and method;
    only our new wire is a row (flying-lead rule, R11 / R117)

Outputs (pilot, untracked) in <main checkout>/_research/harness-cleanroom/:
  A-cabin-wirelist.csv, A-cabin-splices.csv, A-cabin-connectors.csv, A-cabin-mates.csv,
  A-cabin-pinouts.md

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

MAIN = REPO  # a worktree sits in <main>/.claude/worktrees/<name>; outputs go to the main checkout
while os.path.basename(os.path.dirname(MAIN)) == "worktrees":
    MAIN = os.path.dirname(os.path.dirname(os.path.dirname(MAIN)))
OUT = os.path.join(MAIN, "_research", "harness-cleanroom")
LOOM = "A-cabin"

COLUMNS = ["circuit_id", "wire_id", "harness", "passes_through",
           "from_type", "from_conn", "from_conn_name", "from_pin", "from_desc",
           "to_type", "to_conn", "to_conn_name", "to_pin", "to_desc",
           "net_id", "net_name", "splice", "cable", "gauge_awg", "colour", "stripe", "ident_bands",
           "oem_wire_colour", "oem_ewd_page", "oem_method",
           "route_branch", "est_length_mm", "sot_check", "status", "notes"]
SPLICE_COLUMNS = ["splice_id", "name", "net_id", "net_name", "harness", "location", "method", "wires",
                  "gauges_awg", "combined_cma", "equivalent_awg", "sot_check"]
CONN_COLUMNS = ["conn_id", "name", "harness", "part_number", "cavities", "mates_with", "note"]
MATE_COLUMNS = ["circuit_id", "net_name", "this_conn", "this_pin", "this_desc", "mate_harness", "mate_conn",
                "mate_pin", "mate_desc", "check"]

NETS = {"sp_5v": "Sensor +5 V (ECU A32)", "sp_5v_2": "Sensor +5 V (ECU A32)",
        "sp_8v": "Cam +8 V (ECU A6)", "sp_trig2": "Cam signal (ECU A9)",
        "sp_gndout": "Sensor ground A (ECU A24)", "sp_sw12": "Switched +12 V (SW12)",
        "sp_chassis": "ECU power ground", "sp_shield_a": "Shield drain A (ECU A7)",
        "sp_ac_psw": "A/C pressure-switched relay coil +",
        "bus_5v_bha_p": "Sensor +5 V (ECU A32)", "bus_gnd_bha_p": "Sensor ground A (ECU A24)"}
# Net sources (Dispatch net rule): the one pin each supply / ground / screen net comes from.
# key = endpoint key (node_key); value = (net_id, net_name, kind)
SOURCES = {
    ("pin", "ecu_a", "A32"): ("ECU-A.A32", "+5V sensor (ECU-A A32)", "supply"),
    ("pin", "ecu_a", "A6"): ("ECU-A.A6", "+8V cam sensor (ECU-A A6)", "supply"),
    ("pin", "ecu_a", "A24"): ("ECU-A.A24", "Sensor GND (ECU-A A24)", "ground"),
    ("pin", "ecu_a", "A7"): ("ECU-A.A7", "Screen A (ECU A7, SHIELD_A)", "screen"),
    ("splice", "sp_shield_b"): ("ECU-B.B17", "Screen B (ECU B17, SHIELD_B)", "screen"),
    ("term", "chassis_ring"): ("STUD.M6-ECU", "Chassis GND (cabin stud M6 at ECU)", "ground"),
    ("pin", "bus_sw12_p", "2"): ("LOGIC.SW12", "+12V switched (LOGIC SW12 bus)", "supply"),
    ("pin", "fb_logic", "BUS2-4"): ("LOGIC.BUS2-4", "+12V injectors (LOGIC INJ 15A)", "supply"),
    ("pin", "fb_logic", "BUS2-3"): ("LOGIC.BUS2-3", "+12V coils (LOGIC COP 15A)", "supply"),
    ("pin", "fb_logic", "BUS2-12"): ("LOGIC.BUS2-12", "+12V EHPS enable (LOGIC MRS 7.5A)", "supply"),
    ("pin", "A5 (factory)", "4"): ("A5.4", "A/C pressure-switched relay coil +", "supply"),
}
SCREEN_PINS = {("ecu_a", "A7"), ("ecu_b", "B17")}
BUS_CAP = {"bus_5v_bha_p": "bus_5v_bha_r", "bus_gnd_bha_p": "bus_gnd_bha_r"}
# connectors whose other half is in another drawing: (harness, connector)
MATES = {"bh_a_fw": ("A-engine", "bh_a_eng"), "ix_ws_front_p": ("WheelSpeed-Front", "ix_ws_front_r")}
CMA = {22: 642, 20: 1022, 18: 1624, 16: 2583, 14: 4107, 12: 6530, 10: 10380, 8: 16510, 6: 26240, 4: 41740}

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
    (("ecu_a", "cam_pullup") + tuple(SPLICES), "at ECU-A plug"),
]


def branch(nodes):
    names = []
    for n in nodes:
        for ids, name in BRANCH:
            if n in ids and name not in names:
                names.append(name)
    if len(names) > 1 and "at ECU-A plug" in names:
        names.remove("at ECU-A plug")
    return " / ".join(names)


def assign_nets(rows, sot_pin, drb):
    """Electrical nets from the wire list itself: the union of every row's two ends (a splice and a
    bussed plug are one node, a resistor splits). Each net gets net_id (its source pin) and a
    unique readable net_name. Returns the findings of checks (a)-(d) and the screen checks."""
    parent = {}

    def find(k):
        parent.setdefault(k, k)
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    for r in rows:
        ks = [k for k in r["_keys"] if k]
        for k in ks:
            find(k)
        if len(ks) == 2 and r["wire_id"]:
            parent[find(ks[0])] = find(ks[1])
    comp = {}
    for k in list(parent):
        comp.setdefault(find(k), set()).add(k)
    bad, naming = [], {}
    for root, keys in comp.items():
        src = [SOURCES[k] for k in keys if k in SOURCES]
        if len(src) > 1:  # (c) one source per supply / ground / screen net
            bad.append("(c) one net has %d sources: %s" % (len(src), ", ".join(x[0] for x in src)))
        pins = sorted(k for k in keys if k[0] == "pin")
        if src:
            nid, name, kind = src[0]
        else:  # a signal net: id = its ECU pin (or first pin), named by its wire
            rr = [r for r in rows if r["wire_id"] and set(r["_keys"]) & keys]
            ecu = [k for k in pins if k[1] in ("ecu_a", "ecu_b")]
            k0 = (ecu or pins or sorted(keys))[0]
            nid = ".".join(str(x) for x in k0[1:]).replace("ecu_a", "ECU-A").replace("ecu_b", "ECU-B")
            name = "%s (%s)" % (rr[0]["from_desc"], nid.replace(".", " ")) if rr else "spare (%s)" % nid.replace(".", " ")
            kind = "signal" if rr else "spare"
        # (b) one splice / bus never joins two SoT nets
        sot_nets = {sot_pin[(k[1], k[2].lower())]["net"] for k in pins
                    if (k[1], k[2].lower()) in sot_pin and sot_pin[(k[1], k[2].lower())]["net"]}
        if len(sot_nets) > 1:
            bad.append("(b) net %s joins SoT nets %s" % (name, sorted(sot_nets)))
        # screen nets: only screen / drain pins, never a supply or ground source
        if kind == "screen":
            for k in pins:
                ok = (k[1], k[2]) in SCREEN_PINS or (k[1] == "ix_ws_front_p" and k[2] == "5") or \
                    (k[1] == "bh_a_fw" and "screen" in drb.get(k[2], ("", "", ""))[2].lower())
                if not ok:
                    bad.append("screen: %s lands on non-screen pin %s %s" % (name, k[1], k[2]))
            if any(SOURCES[k][2] != "screen" for k in keys if k in SOURCES):
                bad.append("screen: %s touches a supply / ground net" % name)
        else:
            for k in pins:
                if (k[1], k[2]) in SCREEN_PINS:
                    bad.append("screen: %s (not a screen net) lands on %s %s" % (name, k[1], k[2]))
        if kind != "spare":
            naming.setdefault(name, set()).add(root)
        for r in rows:
            if set(r["_keys"]) & keys:
                r["net_id"], r["net_name"] = nid, name
    for name, roots in naming.items():  # (a) one name, one net
        if len(roots) > 1:
            bad.append("(a) net name %r is used by %d unconnected nets" % (name, len(roots)))
    sot_seen = {}
    for root, keys in comp.items():  # (d) one SoT supply / ground / screen net split in two here
        for k in keys:
            r = sot_pin.get((k[1], k[2].lower())) if k[0] == "pin" else None
            if r and r["net"] and r["class"] in ("rail", "ground", "power", "screen"):
                sot_seen.setdefault(r["net"], set()).add(root)
    for net, roots in sot_seen.items():
        if len(roots) > 1:
            bad.append("(d) SoT net %s is on %d unconnected nets in this loom" % (net, len(roots)))
    return bad


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main():
    reg = model.registry()
    docs = model.docs(reg)          # with the gates' long text (full_text.json)
    files = model.harness_files(reg)
    raw = {h: load_json(os.path.join(HARNESS, "rebuild", fn)) for h, fn in files.items()}  # as drawn
    cab = docs[LOOM]
    sot_pin = {(r["conn"], r["pin"]): r for r in model.sot_rows()}
    drb = {}
    with open(os.path.join(HARNESS, "DRB102-CAVITY-MAP.md"), encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\| (\d+) \| [^|]+\| (\d+) \| ([AB]) \| (c\d+) \| (.+) \|\s*$", line)
            if m:
                drb[m.group(1)] = (m.group(3), m.group(4), m.group(5).strip())
    fuse_cav = {w: (c["box"], c["cav"])
                for c in load_json(os.path.join(REPO, "cad", "fusebox", "rev7", "wiring_plan.json"))["cavities"]
                for w in c["wires"]}
    breaks = {e["terminal"]: br for br in reg["breaks"] for e in br["ends"] if e["harness"] == LOOM}
    fleads = {f["terminal"]: f for f in reg["flyingLeads"] if f["harness"] == LOOM}
    fleads_all = {(f["harness"], f["terminal"]): f for f in reg["flyingLeads"]}
    sot_text = "".join(open(p, encoding="utf-8").read() for p in (
        os.path.join(REPO, "sot", "channels.csv"), os.path.join(HARNESS, "DRB102-CAVITY-MAP.md"))) + json.dumps(reg)
    circuit_of = {w: name for name, c in reg["identBands"].get(LOOM, {}).items()
                  if isinstance(c, dict) for w in c.get("wires", [])}
    with open(os.path.join(HARNESS, "HARNESS-BUILD-LIST.csv"), encoding="utf-8") as f:
        est = {(r["File"], r["Wire"]): r["Est mm"] for r in csv.DictReader(f)}

    parts = model.parts(cab)
    cond = {c["id"]: c for c, _, _ in model.conductors(cab)}
    label = {c["id"]: c.get("label", c["id"]).split("  ")[0] for c in raw[LOOM]["connectors"]}
    core_gauge = {}
    for cb in cab.get("cables", []):
        cores = (parts.get(cb.get("partId")) or {}).get("cores") or []
        for i, core in enumerate(cb["cores"]):
            core_gauge[core["id"]] = ((cores[i] if i < len(cores) else {}).get("gauge") or {}).get("value", "")

    def far_end(term):
        """Break end on A-cabin -> the real pin the wire lands on in the other file."""
        br = breaks[term]
        other = next(e for e in br["ends"] if e["harness"] != LOOM)
        h, d = other["harness"], raw[other["harness"]]
        for c, _, _ in model.conductors(d):
            for a, b in (("source", "target"), ("target", "source")):
                if (c.get(a) or {}).get("id") == other["terminal"] and c.get(b):
                    o = c[b]
                    cn = next((x for x in d.get("connectors", []) if x["id"] == o["id"]), None)
                    if cn:
                        cav = next(x for x in cn["cavities"] if x["id"] == o["handle"])
                        return dict(type="connector", conn=cn["id"], name=cn.get("label", cn["id"]),
                                    pin=cav.get("designation", ""), harness=h), c["id"], br["id"]
                    fl = fleads_all.get((h, o["id"]))
                    if fl:  # the far end is a tap into factory wiring: an OEM end
                        ew = fl["ewd"]
                        return dict(type="OEM", conn="%s (factory)" % ew["connector"], name="OEM %s, factory %s lead" % (
                            ew["connector"], ew["color"].split(" ")[0]), pin=ew["pin"], harness=h, ewd=ew), c["id"], br["id"]
                    kind = "splice" if o.get("handle") == "Splice" else "resistor" if o.get("handle") in ("Left", "Right") else "terminal"
                    return dict(type=kind, conn=o["id"], name="%s %s on %s" % (kind, o["id"], h), pin="",
                                harness=h), c["id"], br["id"]
        return dict(type="?", conn="?", name="?", pin="", harness=h), "?", br["id"]

    rows, splice_wires = [], {}

    def endpoint(node, pin, gauge, wid, checks, bad, gap, extra):
        if node in CONNECTORS:
            return dict(type="connector", conn=node, name=label[node], pin=pin, harness=LOOM)
        if node in SPLICES:
            splice_wires.setdefault(node, []).append((wid, gauge))
            if node in sot_text:
                checks.append("splice %s named in SoT" % node)
            else:
                gap.append("splice %s is not named in the SoT (drawing only)" % node)
            return dict(type="splice", conn=node, name="splice %s (%s)" % (node, SPLICES[node].split(" - ")[1]),
                        pin="", harness=LOOM)
        if node in breaks:
            e, half, brid = far_end(node)
            extra["through"] = (e["harness"], half)
            if e.get("ewd"):
                extra.setdefault("oems", []).append(e["ewd"])
                checks.append("flying lead on %s: EWD %s pin %s %s" % (e["harness"], e["ewd"]["connector"], e["ewd"]["pin"], e["ewd"]["color"]))
            checks.append("break %s (other drawn half %s on %s)" % (brid, half, e["harness"]))
            if e["conn"] in ("k_efi", "k_str", "k_fan", "k_etb", "k_acc", "k_eps", "k_fp"):
                checks.append("relay pin from the %s drawing (no channels.csv row)" % e["harness"])
            if half in fuse_cav:
                box, cav = fuse_cav[half]
                checks.append("fuse-box plan %s %s" % (box, cav))
                if cav.split(" ")[-1] != e["pin"].split("-")[-1] and cav != e["pin"]:
                    bad.append("fuse-box plan says %s %s, drawing says %s" % (box, cav, e["pin"]))
                slot = cav.split(" ")[0]
                if " " in cav and slot not in re.findall(r"[A-Z]+\d+", e["name"]):
                    gap.append("relay slot: fuse-box plan %s %s, %s drawing says '%s'" % (box, slot, e["harness"], e["name"]))
            return e
        if node in fleads:
            ew = fleads[node]["ewd"]
            extra.setdefault("oems", []).append(ew)
            checks.append("flying lead %s: EWD %s pin %s %s" % (fleads[node]["id"], ew["connector"], ew["pin"], ew["color"]))
            return dict(type="OEM", conn="%s (factory)" % ew["connector"], name="OEM A/C amplifier",
                        pin=ew["pin"], harness=LOOM)
        if node == "cam_pullup":
            checks.append("channels.csv a9 pull-up ext-1k8-to-8v")
            return dict(type="resistor", conn="cam_pullup", name="Cam pull-up 1.8 k", pin="1" if pin == "Left" else "2", harness=LOOM)
        if node.startswith("screen:"):
            return dict(type="cable screen", conn=node[7:], name="cable screen (one end only)", pin="", harness=LOOM)
        return dict(type="terminal", conn=node, name="Ground ring M6, cabin chassis stud at ECU", pin="", harness=LOOM)

    def node_key(e):
        if e["type"] == "splice":
            return ("splice", e["conn"])
        if e["conn"] in BUS_CAP:  # a bussed plug is one node: every live pin is the bus
            return ("bus", e["conn"])
        if e["type"] == "resistor":
            return ("res", e["conn"], e["pin"])
        if e["type"] == "cable screen":
            return ("screen", e["conn"])
        if e["type"] == "terminal":
            return ("term", e["conn"])
        return ("pin", e["conn"], e["pin"])

    def add(wid, f, t, desc, cable=""):
        w = cond[wid]
        gauge = ((parts.get(w.get("partId")) or {}).get("gauge") or {}).get("value", "") or core_gauge.get(wid, "")
        checks, bad, gap, extra = [], [], [], {}
        ends = [endpoint(n, p, gauge, wid, checks, bad, gap, extra) for n, p in (f, t)]
        for e in ends:  # ECU pins against channels.csv
            if e["conn"] in ("ecu_a", "ecu_b"):
                r = sot_pin.get((e["conn"], e["pin"].lower()))
                if r:
                    checks.append("channels.csv %s %s %s (%s)" % (e["conn"], e["pin"], r["channel"], r["net"] or "-"))
                else:
                    bad.append("%s %s not in channels.csv" % (e["conn"], e["pin"]))
        ecu_pins = [e["pin"] for e in ends if e["conn"] == "ecu_a"]
        for e in ends:  # bulkhead cavities against the DRB102 map
            if e["conn"] in ("bh_a_fw", "bh_b_fw"):
                sec, cavid, use = drb.get(e["pin"], ("?", "?", "?"))
                checks.append("DRB102 %s = section %s %s '%s'" % (e["pin"], sec, cavid, use[:50]))
                if ecu_pins and use.startswith("ECU-A") and use != "ECU-A " + ecu_pins[0]:
                    bad.append("DRB102 %s is '%s' but the wire is from ECU-A %s" % (e["pin"], use, ecu_pins[0]))
                if use.startswith("spare"):
                    gap.append("DRB102 map table row %s says spare; its own note and R22 put the EPS relay coil there" % e["pin"])
        owner, through, notes = LOOM, "", []
        if "through" in extra:  # N40 2: one row, owned by the longer half's file
            h, half = extra["through"]
            mine, theirs = est.get((LOOM, wid), ""), est.get((h, half), "")
            if mine and theirs and float(theirs) > float(mine):
                owner, through = h, LOOM
            else:
                through = h
            notes.append(("owner proposed: longer half" if mine and theirs else "owner TBD: a half has no length estimate") +
                         " (drawn today as %s on %s, %s mm; %s on %s, %s mm)" % (wid, LOOM, mine or "?", half, h, theirs or "?"))
        oems = extra.get("oems") or []
        for e in ends:  # nothing floats: every end is a real pin, an OEM tap, a splice or a part
            if e["type"] in ("?", "terminal") and e["conn"] != "chassis_ring":
                bad.append("end %s (%s) floats: not a pin, OEM tap or splice" % (e["conn"], e["type"]))
        rows.append({
            "circuit_id": circuit_of.get(wid, ""), "wire_id": wid, "harness": owner, "passes_through": through,
            "from_type": ends[0]["type"], "from_conn": ends[0]["conn"], "from_conn_name": ends[0]["name"],
            "from_pin": ends[0]["pin"], "from_desc": desc,
            "to_type": ends[1]["type"], "to_conn": ends[1]["conn"], "to_conn_name": ends[1]["name"],
            "to_pin": ends[1]["pin"], "to_desc": desc,
            "net_id": "", "net_name": "", "_keys": [node_key(e) for e in ends],
            "splice": next((n for n in (f[0], t[0]) if n in SPLICES), ""), "cable": cable,
            "gauge_awg": gauge, "colour": w.get("color", ""), "stripe": w.get("stripeColor", ""),
            "ident_bands": "-".join(w.get("identColors", [])),
            "oem_wire_colour": " / ".join(o.get("color", "") for o in oems),
            "oem_ewd_page": " / ".join(o.get("page", "") for o in oems),
            "oem_method": " / ".join(o.get("method", "") for o in oems),
            "route_branch": branch((f[0], t[0])), "est_length_mm": est.get((LOOM, wid), ""),
            "sot_check": "; ".join(checks),
            "status": ("MISMATCH: " + "; ".join(bad)) if bad else ("SOT GAP: " + "; ".join(gap)) if gap else "OK",
            "notes": "; ".join(notes)})

    for wid, f, t, desc in WIRES:
        add(wid, f, t, desc)
    for cid, cores in CABLES.items():
        for core, (f, t, desc) in cores.items():
            add(core, f or ("screen:" + cid, None), t, desc, cable=cid)
            if f is None:
                rows[-1]["colour"] = "Shield"
                rows[-1]["notes"] = "; ".join(x for x in ("screen floats at the far end", rows[-1]["notes"]) if x)

    # unused cavities on this loom's own connectors: "spare, sealing plug" rows with no wire
    wired = {(r[s + "_conn"], r[s + "_pin"]) for r in rows for s in ("from", "to")}
    for c in raw[LOOM]["connectors"]:
        if c["id"] in BUS_CAP.values():
            continue
        for i, cav in enumerate(c["cavities"]):
            des = cav.get("designation", str(i + 1))
            if (c["id"], des) in wired:
                continue
            if c["id"] == "bh_a_fw" and drb.get(des, ("B",))[0] != "A":
                continue  # section B of the shared DRB102 is B-cabin's
            rows.append(dict({k: "" for k in COLUMNS}, harness=LOOM, from_type="connector", from_conn=c["id"],
                             from_conn_name=label[c["id"]], from_pin=des, from_desc="spare, sealing plug",
                             _keys=[("bus", c["id"]) if c["id"] in BUS_CAP else ("pin", c["id"], des)], status="OK",
                             sot_check=("DRB102 %s = '%s'" % (des, drb[des][2])) if c["id"] == "bh_a_fw" else ""))

    net_findings = assign_nets(rows, sot_pin, drb)

    os.makedirs(OUT, exist_ok=True)

    def write(name, cols, data):
        with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(data)

    write("A-cabin-wirelist.csv", COLUMNS, rows)

    # splices
    spl = {s["id"]: s for s in cab["splices"]}
    srows = []
    for sid, name in SPLICES.items():
        ws = splice_wires.get(sid, [])
        gauges = [int(g) for _, g in ws if g]
        cma = sum(CMA.get(g, 0) for g in gauges)
        loc = spl[sid].get("locationId", "")
        net = next((r for r in rows if ("splice", sid) in r["_keys"]), {})
        srows.append({"splice_id": sid, "name": name, "net_id": net.get("net_id", ""),
                      "net_name": net.get("net_name", ""), "harness": LOOM,
                      "location": name.split(" - ")[0] + (" (layout node %s)" % loc if loc else ""),
                      "method": (parts.get(spl[sid].get("partId")) or {}).get("description", "solder splice")[:60],
                      "wires": len(ws), "gauges_awg": "+".join(map(str, gauges)) + (" + shield" if len(gauges) < len(ws) else ""),
                      "combined_cma": cma,
                      "equivalent_awg": next((a for a in sorted(CMA, reverse=True) if CMA[a] >= cma), "") if cma else "",
                      "sot_check": "named in SoT" if sid in sot_text else "SOT GAP: not named in the SoT (drawing only)"})
    write("A-cabin-splices.csv", SPLICE_COLUMNS, srows)

    # connectors (this loom's own), with what each mates with
    cparts = model.parts(raw[LOOM])
    crows = []
    for c in raw[LOOM]["connectors"]:
        mate, note = "", ""
        if c["id"] in BUS_CAP:
            mate, note = BUS_CAP[c["id"]], "bussed DT plug (R169): every live pin is one net"
        elif c["id"] in BUS_CAP.values():
            mate = next(k for k, v in BUS_CAP.items() if v == c["id"])
            note = "bussed cap: all cavities bussed, one net; no wire rows"
        elif c["id"] in MATES:
            mate = "%s on %s" % (MATES[c["id"]][1], MATES[c["id"]][0])
            note = "shared DRB102 (section A here, section B on B-cabin)" if c["id"] == "bh_a_fw" else "inline DT pair"
        crows.append({"conn_id": c["id"], "name": label[c["id"]], "harness": LOOM,
                      "part_number": (cparts.get(c.get("partId")) or {}).get("partNumber", ""),
                      "cavities": len(c["cavities"]), "mates_with": mate, "note": note})
    write("A-cabin-connectors.csv", CONN_COLUMNS, crows)

    # mating table (N40 1): this half's pin vs the other drawing's pin, same circuit and description
    mrows = []
    for cid, (h, other) in MATES.items():
        oc = next(x for x in raw[h]["connectors"] if x["id"] == other)
        ocav = {x.get("designation"): x for x in oc["cavities"]}
        for r in rows:
            for s in ("from", "to"):
                if r[s + "_conn"] == cid and r["wire_id"]:
                    o = ocav.get(r[s + "_pin"]) or {}
                    ok = not o.get("notConnected") and o.get("signal") == r[s + "_desc"]
                    mrows.append({"circuit_id": r["circuit_id"], "net_name": r["net_name"], "this_conn": cid, "this_pin": r[s + "_pin"],
                                  "this_desc": r[s + "_desc"], "mate_harness": h, "mate_conn": other,
                                  "mate_pin": r[s + "_pin"], "mate_desc": o.get("signal", "(N/C)" if o.get("notConnected") else ""),
                                  "check": "OK" if ok else "DIFFERS"})
    for plug, cap in BUS_CAP.items():
        mrows.append({"circuit_id": "", "net_name": next(r["net_name"] for r in rows if ("bus", plug) in r["_keys"]),
                      "this_conn": plug, "this_pin": "all", "this_desc": "bus",
                      "mate_harness": LOOM, "mate_conn": cap, "mate_pin": "all", "mate_desc": "bussed: one net",
                      "check": "OK"})
    write("A-cabin-mates.csv", MATE_COLUMNS, mrows)

    # pinouts, derived from the wire list
    def pkey(p):
        m = re.match(r"([A-Za-z]*)(\d+)(.*)", p or "")
        return (m.group(1), int(m.group(2)), m.group(3)) if m else (p or "", 0, "")
    with open(os.path.join(OUT, "A-cabin-pinouts.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# A-cabin pinouts (derived from A-cabin-wirelist.csv)\n\n"
                "Generated by `docs/harness/cleanroom/wirelist.py`. Pin | wire | description | other end. "
                "Spare pins say \"spare, sealing plug\". The bulkhead lists section A only (section B is B-cabin's).\n")
        for c in crows:
            lst = []
            for r in rows:
                for s, o in (("from", "to"), ("to", "from")):
                    if r[s + "_conn"] == c["conn_id"]:
                        oth = (r[o + "_conn_name"] + (" pin " + r[o + "_pin"] if r[o + "_pin"] else "")) if r[o + "_conn"] else ""
                        lst.append((r[s + "_pin"], r["wire_id"], r[s + "_desc"], oth))
            f.write("\n## %s (`%s`)\n\n" % (c["name"], c["conn_id"]))
            if c["mates_with"]:
                f.write("Mates with `%s`%s.\n\n" % (c["mates_with"], (" - " + c["note"]) if c["note"] else ""))
            if not lst:
                f.write("No wire rows (%s).\n" % c["note"])
                continue
            f.write("| Pin | Wire | Description | Other end |\n|---|---|---|---|\n")
            for pin, wid, desc, oth in sorted(lst, key=lambda x: pkey(x[0])):
                f.write("| %s | %s | %s | %s |\n" % (pin, wid, desc, oth))

    print("net checks: %d finding(s)" % len(net_findings))
    for x in net_findings:
        print("  NET", x)
    n = lambda k: sum(r["status"].startswith(k) for r in rows)  # noqa: E731
    print("wire list: %d rows (%d wires, %d spare pins), %d splices, %d connectors, %d mate rows (%d differ); "
          "%d mismatch(es), %d SoT gap row(s) -> %s" % (
              len(rows), sum(bool(r["wire_id"]) for r in rows), sum(not r["wire_id"] for r in rows), len(srows),
              len(crows), len(mrows), sum(m["check"] != "OK" for m in mrows), n("MISMATCH"), n("SOT GAP"), OUT))
    for r in rows:
        if r["status"] != "OK":
            print("  ", r["wire_id"], r["status"][:150])


if __name__ == "__main__":
    main()
