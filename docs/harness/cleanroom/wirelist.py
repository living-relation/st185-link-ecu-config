"""Master from-to wire list, every harness file (DECISIONS R201: Dan N39 = A, N40 = A).

One row per physical wire, FROM a real pin TO a real pin or a splice node. Since the switch
(DECISIONS R206) the CSVs in docs/harness/wirelist/ (`<file>-wirelist.csv`) ARE the wiring SoT: this
script reads them, checks every row against the ECU channel settings (channels.csv, both ways), the
registry (interfaces.json), the DRB102 cavity map and the fuse-box wiring plan, and writes what follows from them: the `net_id`, `net_name`, `sot_check`
and `status` columns, the splice, connector and mating tables, the pinouts and the styled
workbooks, and one combined gap list (GAPS.md). `status` says OK, MISMATCH (the row disagrees
with the SoT) or SOT GAP (the SoT itself is silent or inconsistent).

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

Nets are electrical, so they are worked out across all the lists at once: a mated bulkhead or
inline pin, a bussed plug and a device enclosure's screen join are one node. A file's list is
gated (fails --check on a net finding on its rows or a mate that differs) once Dan has approved it
(GATED); a MISMATCH against channels.csv fails for every list; the others are reported in GAPS.md. Every ECU-pin
wire is also followed to its far ends and checked against the pin's Quick Start Guide class (DECISIONS R212);
those findings (`ecu_rules.py`: R212 QSG classes, R213 ground classes, R216 ECU ground,
R219 relay drive) fail --check unless listed in ecu_rules.PENDING, the known violations waiting for the wiring fix.

    python docs/harness/cleanroom/wirelist.py            # write
    python docs/harness/cleanroom/wirelist.py --check    # check_all.py gate
"""
import csv
import io
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
import wirelist_xlsx as X  # noqa: E402
import ecu_rules  # noqa: E402

OUT = os.path.join(HARNESS, "wirelist")   # tracked: the CSVs are the git source (R201, Dan N44 = A)
# Lists Dan has approved: a MISMATCH, mate or coverage finding on them fails --check, and so does a
# net finding whose files are all approved (R201 pilot). The others are reported in GAPS.md.
GATED = {"ECU-cabin"}

COLUMNS = ["circuit_id", "wire_id", "harness", "passes_through",
           "from_type", "from_conn", "from_conn_name", "from_pin", "from_desc", "from_note",
           "to_type", "to_conn", "to_conn_name", "to_pin", "to_desc", "to_note",
           "net_id", "net_name", "splice", "cable", "gauge_awg", "colour", "stripe", "ident_bands",
           "oem_location", "oem_wire_colour", "oem_ewd_page", "oem_method",
           "route_branch", "est_length_mm", "sot_check", "status", "notes"]
COMPUTED = ("net_id", "net_name", "sot_check", "status")   # written by this script, never by hand
SPLICE_COLUMNS = ["splice_id", "name", "net_id", "net_name", "harness", "location", "method", "wires",
                  "gauges_awg", "combined_cma", "equivalent_awg", "sot_check"]
CONN_COLUMNS = ["conn_id", "name", "harness", "part_number", "cavities", "mates_with", "note"]
MATE_COLUMNS = ["circuit_id", "net_name", "this_conn", "this_pin", "this_desc", "mate_harness", "mate_conn",
                "mate_pin", "mate_desc", "check"]
GAP_COLUMNS = ["file", "wire / pin", "what is wrong", "recommended answer"]
CMA = {22: 642, 20: 1022, 18: 1624, 16: 2583, 14: 4107, 12: 6530, 10: 10380, 8: 16510, 6: 26240, 4: 41740,
       2: 66360, 0: 105600}

# The DRB102 bulkhead is ONE connector (DRB102-CAVITY-MAP.md): the receptacle on ECU-cabin, the plug on ECU-engine.
DRB102 = {"bh_fw": "cabin", "bh_eng": "engine"}
DRB_RECEPT, DRB_PLUG = ("bh_fw",), ("bh_eng",)
ECU = {"ecu_a": "ECU-A", "ecu_b": "ECU-B", "ecu_com": "ECU-COMMS"}
SCREEN_PINS = {("ecu_a", "A7"): "A", ("ecu_b", "B17"): "B", ("ecu_com", "C1"): "CAN"}

# Readable names of the nets whose source is a fixed pin (R201: the name names the source).
# Any other source gets a generic name from its pin (see Ctx.source).
NET_NAMES = {
    "ECU-A.A32": "+5V sensor (ECU-A A32)", "ECU-A.A6": "+8V cam sensor (ECU-A A6)",
    "ECU-A.A24": "Sensor GND (ECU-A A24)", "ECU-B.B22": "Sensor GND B (ECU-B B22)",
    "ECU-A.A7": "Screen A (ECU A7, SHIELD_A)", "ECU-B.B17": "Screen B (ECU B17, SHIELD_B)",
    "ECU-COMMS.C1": "Screen CAN (ECU C1, CAN_SCREEN)",
    "LOGIC.BUS2-2": "+12V switched (LOGIC SW12 bus)", "LOGIC.BUS2-4": "+12V injectors (LOGIC INJ 15A)",
    "LOGIC.BUS2-3": "+12V coils (LOGIC COP 15A)", "LOGIC.BUS2-12": "+12V EHPS enable (LOGIC MRS 7.5A)",
}
# Drawn device connector -> its heading in docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md, whose
# pin table (pin | name) is the device pin SoT. Devices whose pin numbers the reference does not
# give are not listed (their pins cannot be checked yet).
DEVICE_REF = {"map": "MAP", "fuelp": "Fuel pressure", "oilp": "Oil pressure", "clntp": "Coolant pressure",
              "flex": "Flex fuel", "vss": "Gearbox VSS"}
# Sources the SoT tables cannot show: a factory switch output, a battery post.
FIXED_SOURCES = {
    ("oem", "A5 (factory)", "4"): ("A5.4", "A/C pressure-switched relay coil +", "supply"),
    ("term", "Ground ring M6, cabin chassis stud at ECU"): ("STUD.M6-ECU", "Chassis GND (cabin stud M6 at ECU)", "stud"),
}


def csv_path(h):
    return os.path.join(OUT, "%s-wirelist.csv" % h)


def read_rows(h):
    with open(csv_path(h), encoding="utf-8", newline="") as f:
        return [dict({k: "" for k in COLUMNS}, **r) for r in csv.DictReader(f)]


def write_rows(h, rows):
    with open(csv_path(h), "w", encoding="utf-8", newline="\n") as f:
        f.write(csv_text(rows, COLUMNS))


def csv_text(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, cols, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def pin_key(p):
    m = re.match(r"([A-Za-z +/-]*?)(\d+)(.*)", p or "")
    return (m.group(1), int(m.group(2)), m.group(3)) if m else (p or "", 0, "")


def drb_map():
    """DRB102 cavity number -> (cavity id, use), from the generated map (bulkhead_assign.py, R208)."""
    drb = {}
    with open(os.path.join(HARNESS, "DRB102-CAVITY-MAP.md"), encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\| (\d+) \| [^|]+\| (\d+) \| (c\d+) \| (.+) \|\s*$", line)
            if m:
                drb[m.group(1)] = (m.group(3), m.group(4).strip())
    return drb


def device_pins():
    """heading -> {pin: name} from the device reference's pin tables (rows with a pin number)."""
    out, head = {}, None
    with open(os.path.join(REPO, "docs", "devices", "SENSOR-AND-ACTUATOR-REFERENCE.md"), encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\*\*(.+?)\*\*", line)
            if m:
                head = m.group(1)
                continue
            m = re.match(r"\| ([0-9A-Z]{1,2}) \| (.+?) \|\s*$", line)
            if m and head:
                out.setdefault(head, {})[m.group(1)] = m.group(2)
    return out


def role(text):
    t = (text or "").lower()
    if re.search(r"5v|5 v|supply|vcc|12v|12 v|\+8v|ig \+", t):
        return "supply"
    if re.search(r"gnd|ground|low reference|return", t):
        return "ground"
    return "signal"


def pin_names(connector):
    """The wire-list pin of each cavity: its designation, or its position when it has none; a
    designation used twice on one connector (opto board in / out 01-08) gives way to the cavity id."""
    des = [cav.get("designation") or str(i + 1) for i, cav in enumerate(connector["cavities"])]
    return [cav["id"] if des.count(d) > 1 else d for cav, d in zip(connector["cavities"], des)]


# Parts whose cavity is a stud, post or single heavy contact: several lugs on one is normal.
STUD_PART = re.compile(r"STUD|POST|BUS ZONE|SWITCH, BATTERY|RADLOK|BLOCK, RELAY AND FUSE", re.I)


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def short(text):
    return re.split(r"  | - ", text or "")[0].strip()


class Ctx:
    """Everything the checks read: the live SoT, plus the drawings for labels / part numbers."""

    def __init__(self):
        self.reg = model.registry()
        self.files = model.harness_files(self.reg)
        self.order = list(self.files)
        self.raw = {h: load_json(os.path.join(HARNESS, "rebuild", fn)) for h, fn in self.files.items()}
        self.sot = model.sot_rows()
        self.sot_pin = {(r["conn"], r["pin"].lower()): r for r in self.sot}
        self.sot_conn = {}
        for r in self.sot:
            self.sot_conn.setdefault(r["conn"], []).append(r)
        self.drb = drb_map()
        plan = load_json(os.path.join(REPO, "cad", "fusebox", "rev7", "wiring_plan.json"))
        self.plan_end = {}
        for w in plan["wires"]:
            for e in w["ends"]:
                self.plan_end.setdefault((e["id"], e["des"]), []).append(w)
        # parts seated in a box (an end with a box): the box design decides their connections (R204)
        self.plan_conns = {e["id"] for w in plan["wires"] for e in w["ends"] if e.get("box")}
        self.plan_kind = {(c["box"], c["cav"]): c["kind"] for c in plan["cavities"]}
        self.fl = {(f["ewd"]["connector"], f["ewd"]["pin"]): f for f in self.reg["flyingLeads"]}
        # every drawn node: id -> (harness, kind, object)
        self.node = {}
        for h, d in self.raw.items():
            for k in ("connectors", "splices", "resistors", "diodes", "terminals"):
                for x in d.get(k, []):
                    self.node.setdefault(x["id"], (h, k, x))
        self.parts = {h: model.parts(d) for h, d in self.raw.items()}
        self.cav = {}   # (conn, designation) -> cavity, (conn, cavity id) -> designation
        self.des = {}
        for h, d in self.raw.items():
            for c in d.get("connectors", []):
                for x, des in zip(c["cavities"], pin_names(c)):
                    self.cav[(c["id"], des)] = x
                    self.des[(c["id"], x["id"])] = des
        self.studs = {c["id"] for h, d in self.raw.items() for c in d.get("connectors", [])
                      if STUD_PART.search((self.parts[h].get(c.get("partId")) or {}).get("description", ""))}
        self.dup_des = {c["id"]: sorted({x for x in [cv.get("designation") for cv in c["cavities"]] if x and
                                         [cv.get("designation") for cv in c["cavities"]].count(x) > 1})
                        for d in self.raw.values() for c in d.get("connectors", [])}
        self.bus = {b["plug"]: b for b in self.reg["bussedSplices"]["buses"]}
        self.cap = {b["receptacle"]: b for b in self.reg["bussedSplices"]["buses"]}
        # mated pairs: conn -> (mate conn, mate harness, kind)
        self.mate = {}
        for ix in self.reg["interfaces"]:
            a, b = ix["halves"]
            self.mate[a["connector"]] = (b["connector"], b["harness"], "inline DT pair (%s)" % ix["id"])
            self.mate[b["connector"]] = (a["connector"], a["harness"], "inline DT pair (%s)" % ix["id"])
        self.ix_pins = {}
        for ix in self.reg["interfaces"]:
            for h in ix["halves"]:
                for cid, text in ix["pins"].items():
                    self.ix_pins[(h["connector"], self.des.get((h["connector"], cid), cid))] = (ix["id"], text)
        for h, d in self.raw.items():
            for m in d.get("mates", []):
                s, t = m["sourceId"], m["targetId"]
                if s in self.bus or t in self.bus:
                    continue
                self.mate[s] = (t, h, "mated pair in this file (%s)" % m["id"])
                self.mate[t] = (s, h, "mated pair in this file (%s)" % m["id"])
        self.canon = {}  # conn -> the one electrical node name its pins share with the mate
        for c, (m, _, _) in self.mate.items():
            self.canon[c] = min(c, m)
        for c in DRB102:
            self.canon[c] = "DRB102"
        self.enc = []    # pairs of pin keys a device enclosure joins inside
        for e in self.reg["enclosures"]:
            ks = []
            for s in e["screen"]:
                conn, cav = s.split(".")
                ks.append(self.pin_node(conn, self.des.get((conn, cav), cav)))
            self.enc.append(ks)
        self.endpoint = {}  # (conn, designation) -> [(endpoint id, role)]; a shared screen pin has two
        for ep in self.reg["endpoints"]:
            if ep.get("connector"):
                for role, cav in ep["pins"].items():
                    self.endpoint.setdefault((ep["connector"], self.des.get((ep["connector"], cav), cav)), []).append((ep["id"], role))
        self.device_pins = device_pins()
        self.relay_out = {}  # (relay conn, pin) whose channels.csv row says "out": a supply source
        for r in self.sot:
            if r["conn"].startswith("k_") and r["dir"] == "out":
                self.relay_out[(r["conn"], r["channel"].split()[-1])] = r

    def pin_node(self, conn, pin):
        if conn in self.bus:
            return ("bus", conn)
        return ("pin", self.canon.get(conn, conn), pin)

    def key(self, r, s):
        """The electrical node of one row end."""
        t, conn, pin = r[s + "_type"], r[s + "_conn"], r[s + "_pin"]
        if not conn:
            return None
        if t == "connector":
            return self.pin_node(conn, pin)
        if t == "splice":
            return ("splice", conn)
        if t in ("resistor", "diode"):
            return ("res", conn, pin)
        if t == "OEM":
            return ("oem", conn, pin)
        if t == "cable screen":
            return ("screen", conn)
        # lugs on one stud share it (the stud is the node); a pinned end (a device header) is per pin
        return ("term", r[s + "_conn_name"], pin) if pin else ("term", r[s + "_conn_name"])

    def sot_row(self, conn, pin):
        """channels.csv row of a connector pin: by pin, by the channel's pin number (relays,
        'Coil 85'), or through a device endpoint (VRC plugs)."""
        r = self.sot_pin.get((conn, pin.lower())) or self.sot_pin.get((conn, pin.lower().replace("-", "")))
        if r:
            return r
        for x in self.sot_conn.get(conn, []):
            if x["channel"].split()[-1] == pin:
                return x
        for eid, role in self.endpoint.get((conn, pin), []):
            for x in self.sot_conn.get(eid, []):
                if x["pin"] == role or (role == "screen" and x["class"] == "screen"):
                    return x
        return None

    def sot_rows_at(self, conn, pin):
        """Every channels.csv row a connector pin carries (a shared screen pin carries two)."""
        out = [self.sot_row(conn, pin)] if conn in self.sot_conn or conn in ECU else []
        for eid, role in self.endpoint.get((conn, pin), []):
            out += [x for x in self.sot_conn.get(eid, []) if x["pin"] == role or (role == "screen" and x["class"] == "screen")]
        return [x for x in out if x]

    def source(self, k, r, s):
        """(net_id, net_name, kind) when this end is where a supply / ground / screen net comes from."""
        if k in FIXED_SOURCES:
            return FIXED_SOURCES[k]
        t, conn, pin = r[s + "_type"], r[s + "_conn"], r[s + "_pin"]
        if t == "connector" and conn in ECU:
            row = self.sot_pin.get((conn, pin.lower()))
            if row and row["class"] in ("rail", "screen") and row["dir"] in ("out", "na"):
                nid = "%s.%s" % (ECU[conn], pin)
                kind = "screen" if row["class"] == "screen" else "ground" if row["type"] == "gnd" else "supply"
                return nid, NET_NAMES.get(nid, "%s (%s %s)" % (row["label"], ECU[conn], pin)), kind
        if t == "connector" and conn in ("fb_logic", "fb_power", "fb_batt"):
            box = {"fb_logic": "LOGIC", "fb_power": "POWER", "fb_batt": "BATT"}[conn]
            if self.plan_kind.get((box, pin)) in ("fuse out", "acps out") or re.match(r"AMI (IN|OUT)-\d|FP ", pin):
                nid = "%s.%s" % (box, pin)
                fuse = (self.cav.get((conn, pin)) or {}).get("signal") or pin
                return nid, NET_NAMES.get(nid, "+12V %s (%s %s)" % (fuse, box, pin)), "supply"
        if t == "connector" and (conn, pin) in self.relay_out:
            nid = "%s.%s" % (conn, pin)
            return nid, NET_NAMES.get(nid, "%s (%s %s)" % (self.relay_out[(conn, pin)]["label"], conn, pin)), "supply"
        if t == "terminal":
            name = r[s + "_conn_name"]
            low = name.lower()
            if "battery positive" in low:
                return "BATT+", "Battery + (%s)" % name, "supply"
            if re.search(r"ground|negative|neg bar|\bgnd\b", low) and "signal" not in low:
                return "GND." + conn, "Chassis GND (%s)" % name, "stud"
        return None


def check_row(ctx, r):
    """Row-level checks against the SoT: (checks, mismatches, gaps)."""
    ok, bad, gap = [], [], []
    for s in ("from", "to"):
        t, conn, pin = r[s + "_type"], r[s + "_conn"], r[s + "_pin"]
        if t == "connector" and conn in ECU:
            row = ctx.sot_pin.get((conn, pin.lower()))
            if not row:
                bad.append("%s %s not in channels.csv" % (conn, pin))
            elif row["class"] in ("nc", "spare"):
                bad.append("%s %s is '%s' in channels.csv (%s)" % (conn, pin, row["class"], row["label"]))
            else:
                ok.append("channels.csv %s %s %s (%s)" % (conn, pin, row["channel"], row["net"] or "-"))
        elif t == "connector" and (conn in ctx.sot_conn or (conn, pin) in ctx.endpoint):
            row = ctx.sot_row(conn, pin)
            if row:
                ok.append("channels.csv %s %s %s (%s)" % (row["conn"], row["pin"], row["channel"], row["net"] or "-"))
            elif conn in ctx.sot_conn:
                bad.append("%s pin %s is not in channels.csv (it lists %s)" % (
                    conn, pin, ", ".join(x["channel"] for x in ctx.sot_conn[conn])))
        if t == "connector" and conn in DEVICE_REF:
            head = next((k for k in ctx.device_pins if k.startswith(DEVICE_REF[conn])), None)
            table = ctx.device_pins.get(head, {})
            want = table.get(pin)
            if want is None and table and pin.isdigit() and all(k.isalpha() for k in table):
                want = table.get("ABCDEFGH"[int(pin) - 1])
                if want:
                    gap.append("%s pins are drawn without the device's pin letters (reference: %s)" % (
                        conn, ", ".join(sorted(table))))
            if want is None:
                bad.append("%s pin %s is not in the device reference (%s)" % (conn, pin, head))
            else:
                ok.append("device ref %s pin %s '%s'" % (head, pin, want))
                kind = r.get("_kind")
                if kind in ("supply", "ground", "signal") and role(want) != kind:
                    bad.append("%s pin %s is '%s' in the device reference but the wire is on a %s net (%s)" % (
                        conn, pin, want, kind, r["net_name"]))
        if t == "connector" and conn in DRB102:
            cavid, use = ctx.drb.get(pin, ("?", "?"))
            ok.append("DRB102 %s = %s '%s'" % (pin, cavid, use[:50]))
            if cavid == "?":
                bad.append("DRB102 has no cavity %s" % pin)
            if use.lower().startswith("spare"):
                gap.append("DRB102 map says cavity %s is '%s' but a wire lands on it" % (pin, use))
        if t == "connector" and conn in ctx.plan_conns:
            ws = ctx.plan_end.get((conn, pin))
            if not ws:
                bad.append("fuse-box plan (rev7 wiring_plan.json) has no wire at %s %s" % (conn, pin))
            else:
                g = {str(w.get("gauge")) for w in ws}
                ok.append("fuse-box plan %s %s (%s AWG)" % (conn, pin, "/".join(sorted(g))))
                bands = {"-".join(w.get("bands") or []) for w in ws}
                if r["ident_bands"] and r["ident_bands"] not in bands:
                    bad.append("fuse-box plan wire at %s %s is %s (bands %s), not this wire (bands %s)" % (
                        conn, pin, "/".join(w["wire"] for w in ws), "/".join(sorted(bands)), r["ident_bands"]))
                if r["gauge_awg"] and r["gauge_awg"] not in g:
                    bad.append("fuse-box plan wires %s %s in %s AWG, the row says %s AWG" % (
                        conn, pin, "/".join(sorted(g)), r["gauge_awg"]))
        if t in ("resistor", "diode") and pin not in ("1", "2"):
            bad.append("%s %s end has no pin (1 or 2)" % (t, conn))
        if t == "splice":   # a splice is a node of the wire list: the list is its SoT (R206)
            ok.append("splice %s: node of the wire list (SoT)" % conn)
        if t == "OEM":
            f = ctx.fl.get((conn.replace(" (factory)", ""), pin))
            if not f:
                gap.append("factory end %s pin %s is not an interfaces.json flying lead (no EWD record)" % (conn, pin))
            else:
                ew = f["ewd"]
                ok.append("flying lead %s: EWD %s pin %s %s" % (f["id"], ew["connector"], ew["pin"], ew["color"]))
                if ew["color"] not in r["oem_wire_colour"].split(" / "):
                    bad.append("factory colour: interfaces.json says %s, the row says %s" % (ew["color"], r["oem_wire_colour"]))
        if t == "terminal":   # a ground point, post or device lead is an end row of the list: the list is its SoT (R206)
            ok.append("end %s: end row of the wire list (SoT)" % conn)
        if t == "?":
            bad.append("end %s floats: not a pin, OEM tap or splice" % conn)
    return ok, bad, gap


def assign_nets(ctx, rows):
    """Electrical nets over every list: the union of every wire row's two ends (a splice, a bussed
    plug, a mated pin and an enclosure screen join are one node; a resistor splits). Sets net_id /
    net_name on every row; returns [(finding, [row ids])] for checks (a)-(d) and the screens, and
    the per-row net mismatches (bulkhead / inline pin uses that name an ECU pin)."""
    parent = {}

    def find(k):
        parent.setdefault(k, k)
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    def join(a, b):
        parent[find(a)] = find(b)

    for r in rows:
        r["_keys"] = [ctx.key(r, s) for s in ("from", "to")]
        ks = [k for k in r["_keys"] if k]
        for k in ks:
            find(k)
        if len(ks) == 2 and r["wire_id"]:
            join(*ks)
    for a, b in ctx.enc:
        if a in parent or b in parent:
            join(a, b)
    comp = {}
    for k in list(parent):
        comp.setdefault(find(k), set()).add(k)
    members = {}
    for r in rows:
        ks = [k for k in r["_keys"] if k]
        if ks:
            members.setdefault(find(ks[0]), []).append(r)
    findings, row_bad = [], {}

    def ids(rs):
        return [r["_id"] for r in rs]

    naming = {}
    for root, keys in comp.items():
        rs = members.get(root, [])
        wired = [r for r in rs if r["wire_id"]]
        src = {}
        for r in rs:
            for s, k in zip(("from", "to"), r["_keys"]):
                x = k and ctx.source(k, r, s)
                if x:
                    src[x[0]] = x
        real = [x for x in src.values() if x[2] != "stud"]
        studs = sorted(x for x in src.values() if x[2] == "stud")
        if len(real) > 1:  # (c) one source per supply / ground / screen net
            findings.append(("(c) one net has %d sources: %s" % (len(real), ", ".join(sorted(x[0] for x in real))), ids(wired)))
        pins = sorted(k for k in keys if k[0] == "pin")
        ecu = [k for k in pins if k[1] in ECU]
        if real:
            nid, name, kind = sorted(real)[0]
        elif studs:
            nid, name, kind = studs[0][0], studs[0][1], "ground"
        else:
            k0 = (ecu or pins or sorted(keys, key=str))[0]
            nid = ".".join(str(x) for x in k0[1:])
            for c, n in ECU.items():
                nid = nid.replace(c + ".", n + ".")
            name = "%s (%s)" % (wired[0]["from_desc"], nid.replace(".", " ")) if wired else "spare (%s)" % nid.replace(".", " ")
            kind = "signal" if wired else "spare"
        # (b) one splice / bus never joins two SoT nets
        sot_nets = {}
        for k in pins:
            conn = next((r[s + "_conn"] for r in rs for s, kk in zip(("from", "to"), r["_keys"]) if kk == k), None)
            row = conn and ctx.sot_row(conn, k[2])
            if row and row["net"]:
                sot_nets.setdefault(row["net"], set()).add("%s %s" % (conn, k[2]))
        if len(sot_nets) > 1:
            findings.append(("(b) net %s joins SoT nets %s" % (name, "; ".join(
                "%s at %s" % (n, ", ".join(sorted(p))) for n, p in sorted(sot_nets.items()))), ids(wired)))
        # screens: only screen / drain pins, never a supply or ground source
        screen_pins = [k for k in pins if (k[1], k[2]) in SCREEN_PINS]
        if kind == "screen":
            for k in pins:
                conn = next((r[s + "_conn"] for r in rs for s, kk in zip(("from", "to"), r["_keys"]) if kk == k), k[1])
                row = ctx.sot_row(conn, k[2])
                use = ctx.drb.get(k[2], ("", ""))[1].lower() if k[1] == "DRB102" else ""
                ixt = (ctx.ix_pins.get((conn, k[2])) or ("", ""))[1].lower()
                if not ((k[1], k[2]) in SCREEN_PINS or (row and row["class"] == "screen") or "screen" in use
                        or "shield" in use or "drain" in ixt or "screen" in ixt):
                    findings.append(("screen: %s lands on non-screen pin %s %s" % (name, conn, k[2]), ids(wired)))
            if any(x[2] not in ("screen",) for x in src.values()):
                findings.append(("screen: %s touches a supply / ground net" % name, ids(wired)))
            if len({SCREEN_PINS[(k[1], k[2])] for k in screen_pins}) > 1:
                findings.append(("screen: two screen nets meet (A, B and CAN never touch)", ids(wired)))
        else:
            for k in screen_pins:
                findings.append(("screen: %s (not a screen net) lands on %s %s" % (name, k[1], k[2]), ids(wired)))
        # a bulkhead / inline pin whose SoT use names an ECU pin must be on that pin's net
        ecu_on = {"%s %s" % (ECU[k[1]][-1], k[2]) for k in ecu}
        for r in wired:
            for s in ("from", "to"):
                conn, pin = r[s + "_conn"], r[s + "_pin"]
                named = []
                if conn in DRB102:
                    m = re.match(r"ECU-([AB]) ([AB]\d+)", ctx.drb.get(pin, ("", ""))[1])
                    if m:
                        named.append(("DRB102 %s" % pin, m.group(1), m.group(2)))
                if (conn, pin) in ctx.ix_pins:
                    ixid, text = ctx.ix_pins[(conn, pin)]
                    for m in re.finditer(r"->\s*(?:SHIELD_[AB]\s*)?([AB])(\d{1,2})\b", text):
                        named.append(("%s pin %s" % (ixid, pin), m.group(1), m.group(1) + m.group(2)))
                for where, letter, p in named:
                    if "%s %s" % (letter, p) not in ecu_on:
                        row_bad.setdefault(r["_id"], []).append(
                            "%s is for ECU-%s %s but this net reaches %s" % (where, letter, p, ", ".join(sorted(ecu_on)) or "no ECU pin"))
        if kind != "spare":
            naming.setdefault(name, set()).add(root)
        for r in rs:
            r["net_id"], r["net_name"] = nid, name
        if kind != "spare":
            for r in rs:
                r["_kind"] = kind
    for name, roots in naming.items():  # (a) one name, one net
        if len(roots) > 1:
            findings.append(("(a) net name %r is used by %d unconnected nets" % (name, len(roots)),
                             [r["_id"] for root in roots for r in members.get(root, []) if r["wire_id"]]))
    sot_seen = {}
    for root, keys in comp.items():  # (d) one SoT supply / ground / screen net split in two
        for r in members.get(root, []):
            for s, k in zip(("from", "to"), r["_keys"]):
                if k and k[0] == "pin":
                    row = ctx.sot_row(r[s + "_conn"], r[s + "_pin"])
                    if row and row["net"] and row["class"] in ("rail", "ground", "power", "screen"):
                        sot_seen.setdefault(row["net"], {}).setdefault(root, set()).add("%s %s" % (r[s + "_conn"], r[s + "_pin"]))
    for net, roots in sot_seen.items():
        if len(roots) > 1:
            parts = ["{%s}" % ", ".join(sorted(p)) for p in roots.values()]
            findings.append(("(d) SoT net %s is on %d unconnected nets: %s" % (net, len(roots), " / ".join(sorted(parts))),
                             [r["_id"] for root in roots for r in members.get(root, []) if r["wire_id"]]))
    return findings, row_bad


def recommend(what):
    """The plain recommended answer for each kind of gap (GAPS.md)."""
    rules = [
        (r"is not named in the SoT \(drawing only\)", "clerical: name the splice in sot/channels.csv notes or interfaces.json when its file is rebuilt (R203)"),
        (r"end \S+ \(OEM", "add the factory tap to interfaces.json flyingLeads (EWD page, connector, pin, colour, method; TBD where the EWD is not read yet)"),
        (r"is drawing-only", "clerical: name this end in interfaces.json (endpoints / a ground-point list) or ENGINE-ROOM-POWER-REDISTRIBUTION.md"),
        (r"not an interfaces.json flying lead", "add the tap to interfaces.json flyingLeads with its EWD page, pin, colour and method (TBD where the EWD is not read yet)"),
        (r"DRB102 map says cavity", "fix the DRB102-CAVITY-MAP.md table row to name what the wire is"),
        (r"fuse-box plan .* has no wire", "fuse-box design decides (R204): move the wire to the cavity the rev7 plan gives, or add it to the plan"),
        (r"has \d+ wires", "one wire per cavity: move one wire to its own pin (or splice them first if the SoT says they share a net)"),
        (r"fuse-box plan wire at", "fuse-box design decides (R204): this cavity belongs to another wire in the rev7 plan"),
        (r"fuse-box plan wires", "fuse-box design decides (R204): use the plan's gauge"),
        (r"is '(nc|spare)' in channels.csv", "the SoT says the pin is unused: drop the wire, or set the pin in channels.csv (design question)"),
        (r"not in channels.csv", "add the pin to sot/channels.csv or move the wire to the pin the SoT gives"),
        (r"^\(a\)", "give one of the nets a distinct name"),
        (r"^\(b\)", "design question: two SoT nets are joined by a wire or splice; split them or merge the SoT nets"),
        (r"^\(c\)", "design question: a supply / screen net has two sources; one must go"),
        (r"^\(d\) SoT net (CHASSIS|GND)", "none: these are separate leads to chassis ground points; the body joins them"),
        (r"^\(d\)", "check the two parts of this SoT net: either wire them together or give them different SoT net names"),
        (r"^screen", "design question: screens land only on A7 / B17 / C1 drain pins (R29 / R30 / R207)"),
        (r"is for ECU-", "the pin's SoT use and the wire disagree: re-check the bulkhead / inline pin"),
        (r"halves drawn with different gauges", "clerical: one gauge for the whole wire (the larger), set in the rebuild"),
        (r"halves drawn in different colours", "clerical: one colour for the whole wire, set in the rebuild"),
        (r"mate", "wire the other half of the pin, or mark this one spare"),
        (r"cavity in the map", "re-run bulkhead_assign.py --apply: the map is generated from the lists (R208)"),
        (r"drawn without the device's pin letters", "clerical: give the drawn cavities the device's pin letters in the rebuild"),
        (r"in the device reference but the wire", "the drawn pin and the device's datasheet pin disagree: re-pin to the reference"),
        (r"not in the device reference", "add the device's pin table to SENSOR-AND-ACTUATOR-REFERENCE.md (from its datasheet)"),
        (r"factory colour", "re-check the EWD colour; fix interfaces.json or the row"),
        (r"channels.csv \(it lists", "fix the pin to one channels.csv lists for this part"),
    ]
    for pat, ans in rules:
        if re.search(pat, what):
            return ans
    return "check against the SoT"


def main(check=False):
    ctx = Ctx()
    lists = {h: read_rows(h) for h in ctx.order if os.path.exists(csv_path(h))}
    rows = []
    for h, rs in lists.items():
        for i, r in enumerate(rs):
            r["_file"], r["_id"] = h, "%s:%d" % (h, i)
            rows.append(r)
    findings, row_bad = assign_nets(ctx, rows)
    # one wire per cavity: two wire rows on the same pin of the same connector is a collision
    at = {}
    for r in rows:
        if r["wire_id"]:
            for s in ("from", "to"):
                if r[s + "_type"] == "connector" and r[s + "_conn"] not in ctx.bus and r[s + "_conn"] not in ctx.studs:
                    at.setdefault((r[s + "_conn"], r[s + "_pin"]), []).append(r)
    for (conn, pin), rs in at.items():
        if len(rs) > 1:
            for r in rs:
                row_bad.setdefault(r["_id"], []).append("%s pin %s has %d wires: %s" % (
                    conn, pin, len(rs), ", ".join(x["wire_id"] for x in rs)))
    for r in rows:
        if not r["wire_id"]:
            r["status"] = r["status"] or "OK"
            if r["from_conn"] in DRB102:
                r["sot_check"] = "DRB102 %s = '%s'" % (r["from_pin"], ctx.drb.get(r["from_pin"], ("", "?"))[1])
            continue
        ok, bad, gap = check_row(ctx, r)
        bad += row_bad.get(r["_id"], [])
        r["sot_check"] = "; ".join(ok)
        r["status"] = ("MISMATCH: " + "; ".join(bad)) if bad else ("SOT GAP: " + "; ".join(gap)) if gap else "OK"
    by_id = {r["_id"]: r for r in rows}

    files, books, gaps = {}, {}, []
    for h in ctx.order:
        if h not in lists:
            continue
        mine = lists[h]
        here = {c["id"] for k in ("connectors", "splices") for c in ctx.raw[h].get(k, [])}
        touching = [r for r in rows if r["from_conn"] in here or r["to_conn"] in here]
        sheets = []

        def add(name, cols, data):
            files[name] = csv_text(data, cols)
            sheets.append((name.split("-")[-1].split(".")[0].capitalize(), cols, data,
                           "WL" + name.split("-")[-1].split(".")[0].capitalize()))

        add("%s-wirelist.csv" % h, COLUMNS, mine)
        # splices drawn on this file; every row into one, from any list
        srows = []
        for s in ctx.raw[h].get("splices", []):
            sid = s["id"]
            ws = [r for r in rows if r["wire_id"] and sid in (r["from_conn"], r["to_conn"])]
            gauges = [int(r["gauge_awg"]) for r in ws if r["gauge_awg"].isdigit()]
            cma = sum(CMA.get(g, 0) for g in gauges)
            loc = s.get("locationId", "")
            name = s.get("label") or ""
            srows.append({"splice_id": sid, "name": name, "net_id": ws[0]["net_id"] if ws else "",
                          "net_name": ws[0]["net_name"] if ws else "", "harness": h,
                          "location": name.split(" - ")[0] + (" (layout node %s)" % loc if loc else ""),
                          "method": (ctx.parts[h].get(s.get("partId")) or {}).get("description", "solder splice")[:60],
                          "wires": len(ws), "gauges_awg": "+".join(map(str, gauges)) + (" + shield" if len(gauges) < len(ws) else ""),
                          "combined_cma": cma,
                          "equivalent_awg": next((a for a in sorted(CMA, reverse=True) if CMA[a] >= cma), "") if cma else "",
                          "sot_check": "node of the wire list (SoT)"})
            if not name:
                gaps.append((h, sid, "splice has no name (R203)", "clerical: name it in the rebuild"))
        add("%s-splices.csv" % h, SPLICE_COLUMNS, srows)
        # this file's connectors, with what each mates with
        crows = []
        for c in ctx.raw[h].get("connectors", []):
            mate, note = "", ""
            if c["id"] in ctx.bus:
                mate, note = ctx.bus[c["id"]]["receptacle"], "bussed DT plug (R169): every live pin is one net"
            elif c["id"] in ctx.cap:
                mate, note = ctx.cap[c["id"]]["plug"], "bussed cap: all cavities bussed, one net; no wire rows"
            elif c["id"] in DRB102:
                other = (DRB_PLUG if c["id"] in DRB_RECEPT else DRB_RECEPT)[0]
                mate = "%s on %s" % (other, ctx.node[other][0])
                note = "DRB102 bulkhead, %s half" % DRB102[c["id"]]
            elif c["id"] in ctx.mate:
                m, mh, kind = ctx.mate[c["id"]]
                mate, note = "%s on %s" % (m, mh), kind.split(" (")[0]
            crows.append({"conn_id": c["id"], "name": short(c.get("label", c["id"])), "harness": h,
                          "part_number": (ctx.parts[h].get(c.get("partId")) or {}).get("partNumber", ""),
                          "cavities": len(c["cavities"]), "mates_with": mate, "note": note})
        add("%s-connectors.csv" % h, CONN_COLUMNS, crows)
        for c in ctx.raw[h].get("connectors", []):
            if ctx.dup_des.get(c["id"]):
                gaps.append((h, c["id"], "cavity designations repeat on one connector (%s): the list uses the cavity ids" %
                             ", ".join(ctx.dup_des[c["id"]]), "clerical: give every cavity its own designation in the rebuild "
                             "(e.g. IN1-IN8 / OUT1-OUT8)"))
        # mating table (N40 1): this half's pin vs the other half's pin, same circuit and description
        mrows = []
        for c in ctx.raw[h].get("connectors", []):
            cid = c["id"]
            if cid in DRB102:
                others = DRB_PLUG if cid in DRB_RECEPT else DRB_RECEPT
            elif cid in ctx.mate:
                others = (ctx.mate[cid][0],)
            else:
                others = ()
            if not others:
                continue
            for r in rows:
                for s in ("from", "to"):
                    if r[s + "_conn"] != cid or not r["wire_id"]:
                        continue
                    pin = r[s + "_pin"]
                    o = [(x, oo) for x in rows if x["wire_id"] for oo in ("from", "to")
                         if x[oo + "_conn"] in others and x[oo + "_pin"] == pin]
                    oc = o[0][0][o[0][1] + "_conn"] if o else others[0]
                    odesc = o[0][0][o[0][1] + "_desc"] if o else "(not wired)"
                    good = bool(o) and odesc == r[s + "_desc"]
                    mrows.append({"circuit_id": r["circuit_id"], "net_name": r["net_name"], "this_conn": cid, "this_pin": pin,
                                  "this_desc": r[s + "_desc"], "mate_harness": ctx.node[oc][0], "mate_conn": oc,
                                  "mate_pin": pin, "mate_desc": odesc, "check": "OK" if good else "DIFFERS"})
                    if not good:
                        gaps.append((h, "%s %s (%s)" % (cid, pin, r["wire_id"]),
                                     "mate %s pin %s: %s" % (oc, pin, "not wired" if not o else "description differs: %r vs %r" % (r[s + "_desc"], odesc)),
                                     recommend("mate")))
        for plug in [c["id"] for c in ctx.raw[h].get("connectors", []) if c["id"] in ctx.bus]:
            net = next((r["net_name"] for r in rows if ("bus", plug) in r["_keys"]), "")
            mrows.append({"circuit_id": "", "net_name": net, "this_conn": plug, "this_pin": "all", "this_desc": "bus",
                          "mate_harness": h, "mate_conn": ctx.bus[plug]["receptacle"], "mate_pin": "all",
                          "mate_desc": "bussed: one net", "check": "OK"})
        add("%s-mates.csv" % h, MATE_COLUMNS, mrows)
        # pinouts, derived from the wire lists
        f = io.StringIO()
        pin_sheets = []
        f.write("# %s pinouts (derived from the master wire list)\n\n"
                "Generated by `docs/harness/cleanroom/wirelist.py`. Pin | wire | description | other end. "
                "Spare pins say \"spare\".\n" % h)
        for c in crows:
            lst = []
            for r in touching + [x for x in mine if not x["wire_id"]]:
                for s, o in (("from", "to"), ("to", "from")):
                    if r[s + "_conn"] == c["conn_id"] and (r["wire_id"] or s == "from") and \
                            (r["_file"] == h or r["wire_id"]):
                        oth = (r[o + "_conn_name"] + (" pin " + r[o + "_pin"] if r[o + "_pin"] else "")) if r[o + "_conn"] else ""
                        lst.append((r[s + "_pin"], r["wire_id"], r[s + "_desc"], oth))
            lst = sorted(dict.fromkeys(lst), key=lambda x: (pin_key(x[0]), x[1]))
            f.write("\n## %s (`%s`)\n\n" % (c["name"], c["conn_id"]))
            if c["mates_with"]:
                f.write("Mates with `%s`%s.\n\n" % (c["mates_with"], (" - " + c["note"]) if c["note"] else ""))
            if not lst:
                f.write("No wire rows (%s).\n" % (c["note"] or "nothing wired"))
                continue
            f.write("| Pin | Wire | Description | Other end |\n|---|---|---|---|\n")
            for pin, wid, desc, oth in lst:
                f.write("| %s | %s | %s | %s |\n" % (pin, wid, desc, oth))
            pin_sheets.append(("%s (%s)" % (c["name"], c["conn_id"]),
                               [{"Pin": a, "Wire": b, "Description": cc, "Other end": d} for a, b, cc, d in lst]))
        files["%s-pinouts.md" % h] = f.getvalue()
        books["%s-wirelist.xlsx" % h] = X.wirelist_workbook(sheets)
        if pin_sheets:  # a file with no connectors (all splices / flying leads) has no pinout sheets
            books["%s-pinouts.xlsx" % h] = X.pinout_workbook(pin_sheets)

    # the ONE combined gap list across every file
    per_item = {}  # a gap about one end (a splice, a terminal) is one line, however many wires reach it
    for r in rows:
        if r["status"] != "OK":
            what = r["status"].split(": ", 1)[1]
            for part in what.split("; "):
                m = re.match(r"()(\S+) pins are drawn without", part)
                if m and r["status"].startswith("SOT GAP") and m.group(2) in ctx.node:
                    per_item.setdefault((ctx.node[m.group(2)][0], m.group(2), part), []).append(r["wire_id"])
                    continue
                pin = "%s %s %s" % (r["from_conn"], r["from_pin"], "-> %s %s" % (r["to_conn"], r["to_pin"]))
                gaps.append((r["harness"], "%s (%s)" % (r["wire_id"], pin.strip()),
                             ("MISMATCH: " if r["status"].startswith("MISMATCH") else "SOT GAP: ") + part, recommend(part)))
    for (h, item, part), wids in per_item.items():
        gaps.append((h, "%s (wires %s)" % (item, ", ".join(sorted(set(wids)))), "SOT GAP: " + part, recommend(part)))
    for what, rids in findings:
        hs = sorted({by_id[i]["harness"] for i in rids}, key=ctx.order.index) or ["-"]
        gaps.append((" / ".join(hs), ", ".join(sorted({by_id[i]["wire_id"] for i in rids}))[:300], "NET " + what, recommend(what)))
    # coverage: every channels.csv pin in use on a drawn part has a wire in some list
    used = {(r[s + "_conn"], r[s + "_pin"]) for r in rows if r["wire_id"] for s in ("from", "to")}
    for x in ctx.sot:
        if x["class"] in ("nc", "spare") or x["status"] != "set" or x["conn"] not in ctx.node and                 x["conn"] not in {e[0] for v in ctx.endpoint.values() for e in v}:
            continue
        hit = [k for k in used if any(y is x for y in ctx.sot_rows_at(*k))]
        if not hit:
            owner = ctx.node.get(x["conn"], (next((ctx.node[c][0] for (c, _), v in ctx.endpoint.items()
                                                   if any(e[0] == x["conn"] for e in v)), "?"),))[0]
            gaps.append((owner, "%s %s" % (x["conn"], x["pin"]),
                         "MISMATCH: channels.csv %s %s '%s' (%s) is in use but no list has a wire on it" % (
                             x["conn"], x["pin"], x["label"], x["channel"]),
                         "add the wire the SoT gives, or set the pin nc in channels.csv (design question)"))
    # ECU-pin / ground-class / relay rules (R212-R219): ecu_rules.py; --check fails on any finding
    # that is not in ecu_rules.PENDING (the known violations waiting for the wiring fix)
    rule_findings = ecu_rules.findings(ctx, rows, ECU)
    for f in rule_findings:
        gaps.append((f["harness"], f["item"], "RULE %s: %s%s" % (f["rule"], f["text"], " [pending fix]" if f["id"] in ecu_rules.PENDING else ""),
                     "wiring fix session (OPEN-ITEMS N55 / N56); see DECISIONS %s" % f["rule"]))
    seen, glines = set(), []
    for g in gaps:
        if g not in seen:
            seen.add(g)
            glines.append(g)
    glines.sort(key=lambda g: (ctx.order.index(g[0].split(" / ")[0]) if g[0].split(" / ")[0] in ctx.order else 99, g[2], g[1]))
    gm = io.StringIO()
    gm.write("# Master wire list - gap list (all files)\n\n"
             "Generated by `docs/harness/cleanroom/wirelist.py` from `*-wirelist.csv`. One line per gap: "
             "the file, the wire / pin, what is wrong against the live SoT, and the recommended answer. "
             "Real design questions go to Dan through Dispatch (`docs/OPEN-ITEMS.md` Needs Dan); this list "
             "is regenerated, never hand-edited.\n\n%d gap(s).\n\n| File | Wire / pin | What is wrong | Recommended answer |\n"
             "|---|---|---|---|\n" % len(glines))
    for g in glines:
        gm.write("| %s |\n" % " | ".join(x.replace("|", "/") for x in g))
    files["GAPS.md"] = gm.getvalue()

    import drb102_outputs as D   # the DRB102 pin table (csv + xlsx) and the insert-face map (png), R208
    d_rows = D.table(lists)
    d_text = D.csv_text(d_rows)
    files["DRB102-pin-table.csv"] = d_text
    books["DRB102-pin-table.xlsx"] = D.workbook(d_text)
    stale = sync(files, books, check)
    png = os.path.join(OUT, "DRB102-bulkhead-map.png")
    want = D.digest(d_text)
    if D.png_digest(png) != want:
        stale.append("DRB102-bulkhead-map.png")
        if not check:
            D.render(d_rows, png, want)
            print("updated: DRB102-bulkhead-map.png")
    n = lambda rs, k: sum(r["status"].startswith(k) for r in rs)  # noqa: E731
    for h, rs in lists.items():
        print("%-17s %4d rows (%3d wires, %3d spare), %3d mismatch(es), %3d SoT gap row(s)%s" % (
            h, len(rs), sum(bool(r["wire_id"]) for r in rs), sum(not r["wire_id"] for r in rs),
            n(rs, "MISMATCH"), n(rs, "SOT GAP"), "  [gated]" if h in GATED else ""))
    print("net findings: %d; gap list: %d line(s) -> %s" % (len(findings), len(glines), os.path.join(OUT, "GAPS.md")))
    if check:
        bad = list(stale)
        # the switch (R206): a list row that disagrees with channels.csv, and a channels.csv pin in use
        # with no wire, fail for EVERY list. A mate or net finding still fails only when every file it
        # touches is approved (a file still being rebuilt is reported, not gated)
        bad += ["%s %s: %s" % (g[0], g[1], g[2]) for g in glines
                if g[2].startswith("MISMATCH") or (g[2].startswith(("mate", "NET")) and all(h in GATED for h in g[0].split(" / ")))]
        ids = {f["id"] for f in rule_findings}
        bad += ["RULE %s %s: %s" % (f["rule"], f["item"], f["text"]) for f in rule_findings if f["id"] not in ecu_rules.PENDING]
        bad += ["PENDING entry %s no longer violates: delete it from ecu_rules.PENDING" % i for i in sorted(ecu_rules.PENDING - ids)]
        for x in bad:
            print("FAIL", x)
        print("wirelist --check: %s" % ("FAIL" if bad else "OK"))
        return 1 if bad else 0
    return 0


def sync(files, books, check):
    """Write (or, with check, compare) the text files and the styled workbooks; return what is stale."""
    stale = []
    os.makedirs(OUT, exist_ok=True)
    for name, text in files.items():
        path = os.path.join(OUT, name)
        old = open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n") if os.path.exists(path) else None
        if old != text:
            stale.append(name)
            if not check:
                with open(path, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
    for name, wb in books.items():
        path = os.path.join(OUT, name)
        tmp = io.BytesIO()
        wb.save(tmp)
        tmp.seek(0)
        want = X.values(X.load_workbook(tmp))
        if not os.path.exists(path) or X.values(path) != want:
            stale.append(name)
            if not check:
                with open(path, "wb") as fh:
                    fh.write(tmp.getvalue())
    if stale and not check:
        print("updated:", ", ".join(stale))
    return stale


if __name__ == "__main__":
    sys.exit(main(check="--check" in sys.argv))
