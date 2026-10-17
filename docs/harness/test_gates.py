"""Self-test for the bulkhead pin-sharing, contact-fit, mating and wire-spacing gates.

    python docs/harness/test_gates.py      exit 0 = every case behaved as expected

Each case copies docs/harness + sot/ to a temp folder, changes the drawings the way
the case describes, and runs the gates there. Nothing in the repo is modified.
Rule owner: Daniel (2026-10-03) - see audit_bh_collisions.py and audit_cavity_parts.py.
"""
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import audit_bh_collisions as bhc  # noqa: E402  (unit-level cases below)


def sandbox():
    d = tempfile.mkdtemp(prefix="gates_")
    shutil.copytree(HERE, os.path.join(d, "docs", "harness"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(os.path.join(ROOT, "sot"), os.path.join(d, "sot"))
    shutil.copy(os.path.join(ROOT, "XTREMEX-IO-TABLE.html"), d)   # validate_sot.py H1 reads it
    return d


def load(d, loom):
    p = os.path.join(d, "docs", "harness", "rebuild", "ST185-%s.harness" % loom)
    return p, json.load(open(p, encoding="utf-8"))


def save(p, doc):
    json.dump(doc, open(p, "w", encoding="utf-8"), indent=2)


def add_copy(d, loom, wire, half, cav, extra_target=None, gauge_part=None):
    """Add a copy of `wire` whose bulkhead end lands on half/cav (original untouched)."""
    p, doc = load(d, loom)
    pool = doc.get("wires", []) + [c for cb in doc.get("cables", []) for c in cb.get("cores", [])]
    w = copy.deepcopy(next(x for x in pool if x["id"] == wire))
    w.pop("_awg", None)
    w["id"] = wire + "_t%d" % len(doc["wires"])
    for k in ("source", "target"):
        if (w.get(k) or {}).get("id") in bhc.BH:
            w[k] = {"id": half, "handle": cav}
        elif extra_target:
            w[k] = extra_target
    if gauge_part:
        w["partId"] = gauge_part
    doc["wires"].append(w)
    save(p, doc)


def add_wire(d, loom, wid, a, b, part="m16_20_0"):
    p, doc = load(d, loom)
    doc["wires"].append({"id": wid, "source": a, "target": b, "color": "Black", "partId": part})
    save(p, doc)


def label(d, loom, conn, cav, text):
    p, doc = load(d, loom)
    for c in doc["connectors"]:
        if c["id"] == conn:
            for cv in c["cavities"]:
                if cv["id"] == cav:
                    cv["signal"] = text
    save(p, doc)


def run(d, script):
    r = subprocess.run([sys.executable, "-B", script], cwd=os.path.join(d, "docs", "harness"),
                       capture_output=True, text=True)
    return r.returncode, r.stdout


def swap_cavities(d, loom, conn, a, b):
    """Swap every conductor end on conn.a with conn.b (a crossed pair at a device plug)."""
    p, doc = load(d, loom)
    pool = doc.get("wires", []) + [c for cb in doc.get("cables", []) for c in cb.get("cores", [])]
    for w in pool:
        for k in ("source", "target"):
            e = w.get(k) or {}
            if e.get("id") == conn and e.get("handle") in (a, b):
                e["handle"] = b if e["handle"] == a else a
    save(p, doc)


CASES = []


def case(name, gate, expect):
    def wrap(fn):
        CASES.append((name, gate, expect, fn))
        return fn
    return wrap


@case("two injector signals crimped into one bulkhead pin", "audit_bh_collisions.py", 1)
def _(d):
    add_copy(d, "A-engine", "w109_e", "bh_a_eng", "c13")


@case("injector signal + injector 12V feed in one pin", "audit_bh_collisions.py", 1)
def _(d):
    add_copy(d, "A-engine", "w_inj_pwr_e_ae", "bh_a_eng", "c13")


@case("two sensor grounds crimped into one ground pin (direct form)", "audit_bh_collisions.py", 0)
def _(d):
    add_copy(d, "A-engine", "w17", "bh_a_eng", "c42")


@case("ground + switched 12V in one pin", "audit_bh_collisions.py", 1)
def _(d):
    add_copy(d, "B-engine", "w_vss_12v", "bh_b_eng", "c19")


@case("pigtail + splice: +5V splice also fed from ECU +8V Out", "audit_bh_collisions.py", 1)
def _(d):
    add_wire(d, "A-cabin", "w_t_8v_into_5v", {"id": "sp_5v_bha", "handle": "Splice"},
             {"id": "ecu_a", "handle": "a6"})


@case("pigtail + splice: extra 12V device on the switched-12V splice", "audit_bh_collisions.py", 0)
def _(d):
    add_wire(d, "A-engine", "w_t_12v_dev", {"id": "sp_sw12_eng", "handle": "Splice"},
             {"id": "inj1", "handle": "c1"})


@case("one ECU signal fanned out to 2 devices, cavity NOT labelled splice", "audit_bh_collisions.py", 1)
def _(d):
    add_copy(d, "A-engine", "w109_e", "bh_a_eng", "c14", extra_target=None)
    add_copy(d, "A-engine", "w108_e", "bh_a_eng", "c14")


@case("same fan-out, cavity labelled 'splice' on both halves", "audit_bh_collisions.py", 0)
def _(d):
    add_copy(d, "A-engine", "w108_e", "bh_a_eng", "c14")
    for loom, half in (("A-engine", "bh_a_eng"), ("A-cabin", "bh_a_fw")):
        label(d, loom, half, "c14", "INJ2 (splice)")


@case("4 x 18 AWG grounds direct in one size-16 pin: sharing OK ...", "audit_bh_collisions.py", 0)
def _(d):
    p, doc = load(d, "A-engine")
    doc["wireParts"].append({"id": "wp_18_t", "partNumber": "T18", "manufacturer": "t",
                             "description": "t", "color": "Black", "gauge": {"value": 18, "unit": "AWG"}})
    save(p, doc)
    for i in range(3):
        add_copy(d, "A-engine", "w17", "bh_a_eng", "c43", gauge_part="wp_18_t")
    p, doc = load(d, "A-engine")
    for w in doc["wires"]:
        if w["id"] == "w17":
            w["partId"] = "wp_18_t"
    save(p, doc)


CASES.append(("... but the combined 12 AWG does not fit the 16-20 AWG contact (K3)",
              "audit_cavity_parts.py", 1, CASES[-1][3]))


def designate(d, loom, conn, cav, num):
    p, doc = load(d, loom)
    for c in doc["connectors"]:
        if c["id"] == conn:
            for cv in c["cavities"]:
                if cv["id"] == cav:
                    cv["designation"] = num
    save(p, doc)


@case("DRB102: B spare moved onto A's crank cavity 9, both halves (M8 collision)", "audit_mating.py", 1)
def _(d):
    for loom, half in (("B-cabin", "bh_b_fw"), ("B-engine", "bh_b_eng")):
        designate(d, loom, half, "c25", "9")


@case("DRB102: size-12 plug put in a size-16 cavity (M8 size)", "audit_mating.py", 1)
def _(d):
    for loom, half in (("B-cabin", "bh_b_fw"), ("B-engine", "bh_b_eng")):
        designate(d, loom, half, "c1", "62")
        designate(d, loom, half, "c25", "97")


@case("R141: a wire given one routing point (RP1)", "audit_wire_spacing.py", 1)
def _(d):
    p, doc = load(d, "CabinPower")
    w = doc["wires"][0]
    w["layoutPoints"] = [{"id": "lp_t_rp1", "schematicPosition": {"x": 0, "y": 0}}]
    save(p, doc)


@case("R141: bundle layout points are not wire routing points (RP1 allows)", "audit_wire_spacing.py", 0)
def _(d):
    p, doc = load(d, "WheelSpeed-Rear")
    assert any(b.get("layoutPoints") for b in doc["bundles"])    # Dan kept these 13
    save(p, doc)


@case("R140: a terminal moved so its bundle runs along its own label (Y5)", "audit_layout.py", 1)
def _(d):
    p, doc = load(d, "RearFuel")
    pos = {x["id"]: x["layoutPosition"] for k in ("connectors", "terminals")
           for x in doc.get(k, []) if x.get("layoutPosition")}
    gnd = next(x for x in doc["terminals"] if x["id"] == "t_trunk_fp_gnd")
    pump = pos["fuelpump"]
    gnd["layoutPosition"] = {"x": pump["x"] - 600, "y": pump["y"]}   # level with the pump, to its left
    save(p, doc)


def unit_cases():
    """judge() on hand-made pin contents (classes that the drawings don't contain yet)."""
    out = []
    E = lambda kind, net: (kind, net, set(), "ecu:%s" % net)
    D = lambda text: (None, None, bhc.text_kinds(text), text)
    checks = [
        ("CAN H with CAN H", [E("CAN H", "CAN1H"), D("CAN H to node")], True),
        ("CAN H with CAN L", [E("CAN H", "CAN1H"), E("CAN L", "CAN1L")], False),
        ("shield drain with shield drain", [D("Screen drain"), D("shield braid")], True),
        ("shield drain with ground", [E("shield", "SHIELD_A"), D("GND")], False),
        ("SHIELD_A with SHIELD_B", [E("shield", "SHIELD_A"), E("shield", "SHIELD_B")], False),
        ("Gnd Out with ECU power ground", [E("ground", "GNDOUT"), E("ground", "GND_ECU")], False),
        ("+5V with +8V", [E("+5V", "P5V"), E("+8V", "P8V")], False),
        ("12V rail with a '12V/8V' supply pin", [E("+12V", "P14V"), D("12V/8V")], True),
        ("signal with its pull-up resistor only", [E("signal", "TRIG2_CAM")], True),
    ]
    for name, ends, ok in checks:
        got = bhc.judge(ends, "") is None
        out.append((name, ok, got))
    out += fusebox_mesh_cases()
    return out


def _box_tris(x0, y0, z0, x1, y1, z1):
    """Outward-facing triangles of an axis-aligned box (STL right-hand order)."""
    v = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    quads = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    return [t for q in quads for t in ((v[q[0]], v[q[1]], v[q[2]]), (v[q[0]], v[q[2]], v[q[3]]))]


def fusebox_mesh_cases():
    """cad/fusebox/src/check_printed_solid.py S6 (gaps under 0.5 mm, SteveCAD sweep C1) and S2 zero-thickness edges (C3)."""
    sys.path.insert(0, os.path.join(ROOT, "cad", "fusebox", "src"))
    import check_printed_solid as cps
    out = []
    for g, want_ok in ((0.375, False), (0.65, True)):        # two blocks with a slot between them, 10 x 10 face
        tris = _box_tris(0, 0, 0, 10, 5, 10) + _box_tris(0, 5 + g, 0, 10, 10 + g, 10)
        found = [x for x in cps.gaps(tris) if x[0] < cps.GAP_MIN]
        out.append(("S6 fuse box gap %.3f mm %s" % (g, "passes" if want_ok else "fails"), want_ok, not found))
    tris = _box_tris(0, 0, 0, 5, 5, 5) + _box_tris(5, 5, 0, 10, 10, 5)  # corners touching along one edge
    out.append(("S2 fuse box cavity corners touching edge to edge fail", False, not cps.nonmanifold(tris)))
    tris = _box_tris(0, 0, 0, 5, 5, 5) + _box_tris(7, 7, 0, 12, 12, 5)
    out.append(("S2 fuse box blocks 2 mm apart pass", True, not cps.nonmanifold(tris)))
    return out


@case("SoT endpoint rows: drawings as committed", "validate_sot.py", 0)
def _(d):
    pass


@case("SoT endpoint rows: k_eps_en coil- (B12) and coil+ (SW12) swapped", "validate_sot.py", 1)
def _(d):
    swap_cavities(d, "CabinPower", "k_eps_en", "c2", "c3")


@case("SoT endpoint rows: front VRC OUT FL / FR crossed at the plug", "validate_sot.py", 1)
def _(d):
    swap_cavities(d, "WheelSpeed-Front", "lp16_vrc_f_out", "c3", "c4")


@case("R107: a layout bundle drawn on top of another, no shared end (W2)", "audit_wire_spacing.py", 1)
def _(d):
    p, doc = load(d, "A-cabin")
    pos = {x["id"]: x["layoutPosition"] for k in ("connectors", "terminals", "branchPoints")
           for x in doc.get(k, []) if x.get("layoutPosition")}
    b = next(x for x in doc["bundles"] if x["sourceId"] in pos and x["targetId"] in pos
             and pos[x["sourceId"]]["y"] == pos[x["targetId"]]["y"]
             and abs(pos[x["sourceId"]]["x"] - pos[x["targetId"]]["x"]) >= 90)
    for k, end in (("bp_t_w2a", b["sourceId"]), ("bp_t_w2b", b["targetId"])):
        doc["branchPoints"].append({"id": k, "layoutPosition": dict(pos[end])})
    doc["bundles"].append({"id": "bn_t_w2", "sourceId": "bp_t_w2a", "targetId": "bp_t_w2b"})
    save(p, doc)


@case("R107: two layout bundles ending at the same connector run together (W2 allows)", "audit_wire_spacing.py", 0)
def _(d):
    p, doc = load(d, "A-cabin")
    b = copy.deepcopy(next(x for x in doc["bundles"] if "ecu_a" in (x["sourceId"], x["targetId"])))
    b["id"] += "_twin"
    doc["bundles"].append(b)
    save(p, doc)


def main():
    fails = 0
    for name, gate, expect, fn in CASES:
        d = sandbox()
        try:
            fn(d)
            code, txt = run(d, gate)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        ok = (code != 0) == bool(expect)
        fails += not ok
        print("%s  %-70s %s %s" % ("ok  " if ok else "FAIL", name, gate, "fails" if code else "passes"))
    for name, want, got in unit_cases():
        ok = want == got
        fails += not ok
        print("%s  %-70s judge() %s" % ("ok  " if ok else "FAIL", name, "allows" if got else "refuses"))
    print("\n%d self-test failure(s)." % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
