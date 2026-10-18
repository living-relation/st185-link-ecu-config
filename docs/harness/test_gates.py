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



@case("R154: a copied starter lug on its own empty 1060 mm leg (T1, the old N11 shape)", "audit_bundle_topology.py", 1)
def _(d):
    p, doc = load(d, "HeavyDC")
    leg = next(b for b in doc["bundles"] if b["id"] == "bn_bp_hdc_str__t_starter_b_2")
    leg["length"] = {"value": 1060, "unit": "mm"}
    doc["bundles"].append({"id": "bn_copy_leg", "sourceId": "bp_hdc_join", "targetId": "t_copy",
                           "length": {"value": 1060, "unit": "mm"}})
    doc["terminals"].append({"id": "t_copy", "type": "Ring", "signal": "copied stud",
                             "layoutPosition": {"x": 0, "y": 0}})
    save(p, doc)


@case("R154: HeavyDC as drawn - H4 + H5 share the join -> starter bundle", "audit_bundle_topology.py", 0)
def _(d):
    p, doc = load(d, "HeavyDC")
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
    out += wall_class_cases()
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


def wall_class_cases():
    """R151 (Dan 2026-10-17: minimum wall for critical / structural features only; questionable or unclear = flagged): the pass / flag /
    fail split of cad/fusebox/src/check_printed_solid.py S4 / S5 (wall_findings) and wall_classes.py, on hand-made wall_check data."""
    sys.path.insert(0, os.path.join(ROOT, "cad", "fusebox", "src"))
    import check_printed_solid as cps
    import wall_classes as wcl
    rep = {"boxes_mm": {"LOGIC": {"z_d": 38.5}, "POWER": {"z_d": 32.0}},
           "terminal_holes": {"LOGIC": [{"x": 10.5, "y": 28.0, "sx": 5.2, "sy": 6.0}]}}

    def wc(part=None, walls=(), attach=(), flagged=None, outline=True):
        parts = {}
        for n in cps.WALL_BASELINE:
            e = dict(volume_cm3=1.0, walls=[], attach=[], exempt={}, attach_checked=True, flagged=0,
                     bounds=[-40.0, 130.0, -10.0, 190.0, 0.0, 90.0])
            if "_Base_" in n and outline:
                e["outline"] = [0.0, 86.0, 0.0, 182.0]
            parts[n] = e
        if part:
            parts[part]["walls"] = [dict(at=list(b), sections=4) for b in walls]
            parts[part]["attach"] = [dict(kind="thin piece held at one place (cantilever)", at=list(b), vol_mm3=5.0) for b in attach]
            parts[part]["flagged"] = flagged if flagged is not None else sum(
                c in wcl.FLAGGED for (_, _, c, _) in wcl.classify_part(part, parts[part], rep))
        return {"parts": parts}

    def run(d, md=None):
        md = md if md is not None else "".join("- %s\n" % l for l in wcl.flag_lines(d["parts"], rep))
        bad, notes, flags = cps.wall_findings(d, {}, rep, md)
        return bad, flags

    LB, PB, LC = "Logic_Base_PA12_printed", "Power_Base_PA12_printed", "Logic_Cover_PA12_printed"
    inner = (40.0, 41.0, 160.0, 161.0, 45.0, 46.0)        # LOGIC deck, away from the skin and the terminal hole
    out = []
    bad, flags = run(wc())
    out.append(("R151 S4/S5: no thin spots pass, nothing flagged", True, not bad and not flags))
    bad, flags = run(wc(LB, [inner]))
    out.append(("R151 S4: a base spot the map cannot place is FLAGGED (questionable), not failed", True, not bad and len(flags) == 1
                and flags[0].startswith(wcl.QUESTIONABLE)))
    bad, flags = run(wc(LB, [inner], flagged=0))
    out.append(("R151 S4: wall_check.json whose flag count disagrees fails (stale)", False, not bad))
    bad, flags = run(wc(LB, [inner]), md="- none\n")
    out.append(("R151 S4: WALL-FLAGS.md that leaves a flagged spot out fails (stale)", False, not bad))
    bad, flags = run(wc(LB, [inner], outline=False))
    out.append(("R151 S4: no deck outline recorded = questionable, flagged (never silently passed)", True, not bad and len(flags) == 1))
    bad, flags = run(wc(LB, [(2.0, 3.0, 90.0, 95.0, 45.0, 50.0)]))
    out.append(("R151 S4: outer skin behind the pockets (structural) fails", False, not bad))
    bad, flags = run(wc(LB, [(14.0, 15.0, 27.0, 29.0, 45.0, 50.0)]))
    out.append(("R151 S4: wall between terminals (structural) fails", False, not bad))
    bad, flags = run(wc(LB, [(40.0, 41.0, 100.0, 101.0, 10.0, 12.0)]))
    out.append(("R151 S4: leg / block under the deck (load-bearing) fails", False, not bad))
    bad, flags = run(wc(LB, [(-30.0, -28.0, 100.0, 101.0, 45.0, 46.0)]))
    out.append(("R151 S4: mount ear outside the deck outline fails", False, not bad))
    bad, flags = run(wc(LB, attach=[inner]))
    out.append(("R151 S5: attachment < 3 mm (retention) fails", False, not bad))
    bad, flags = run(wc(PB, [(200.0, 201.0, 40.0, 41.0, 30.0, 31.0)]))
    out.append(("R151 S4: a spot Dan marked (R127 M1) fails", False, not bad))
    bad, flags = run(wc(LC, [(40.0, 41.0, 90.0, 91.0, 88.0, 89.9)]))
    out.append(("R151 S4: cover top away from its side walls is flagged, not failed", True, not bad and len(flags) == 1))
    bad, flags = run(wc(LC, [(-39.0, -38.0, 90.0, 91.0, 60.0, 70.0)]))
    out.append(("R151 S4: cover side wall (structural) fails", False, not bad))
    feat = {LB: [(wcl.NON_STRUCTURAL, "test: approved cosmetic rib", (39.0, 42.0, 159.0, 162.0, 44.0, 47.0))]}
    c, _ = wcl.classify(LB, inner, "W", {"outline": [0.0, 86.0, 0.0, 182.0]}, rep, feat)
    out.append(("R151 map: a spot in a non-structural box is non-structural (flagged)", True, c == wcl.NON_STRUCTURAL))
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


def _cluster(d, fn):
    p, doc = load(d, "ClusterLED")
    fn(doc)
    save(p, doc)


def _term(doc, tid):
    return next(t for t in doc["terminals"] if t["id"] == tid)


@case("R156: relabelled drawings as committed", "audit_destinations.py", 0)
def _(d):
    pass


@case("R156 L1: a relabelled terminal with no label", "audit_destinations.py", 1)
def _(d):
    _cluster(d, lambda doc: _term(doc, "fl_cl_c11_c12").pop("label"))


@case("R156 L1: a relabelled terminal that also carries a signal", "audit_destinations.py", 1)
def _(d):
    _cluster(d, lambda doc: _term(doc, "fl_cl_c11_c12").update(signal="High beam LED"))


@case("R156 L2: a label that names no landing (no pin / stud / lug ...)", "audit_destinations.py", 1)
def _(d):
    _cluster(d, lambda doc: _term(doc, "fl_cl_c11_c12").update(label="High beam LED - indicator"))


@case("R156 L3: the old '-> X' tail", "audit_destinations.py", 1)
def _(d):
    _cluster(d, lambda doc: _term(doc, "fl_cl_c11_c12").update(label="OEM cluster plug pin 12 - high beam -> C11-12"))


@case("R156 L3: a bare pin code (IE1-14)", "audit_destinations.py", 1)
def _(d):
    _cluster(d, lambda doc: _term(doc, "fl_cl_c11_c12").update(label="Inline IE1-14 pin - motor +"))


@case("R156 L4: both ends of one wire print the same name", "audit_destinations.py", 1)
def _(d):
    def f(doc):     # the IG tap wire runs from the C12 pin 9 lead to the LED +12 V splice
        _term(doc, "fl_cl_c12_c9")["label"] = next(x for x in doc["splices"] if x["id"] == "sp_led_12v")["label"]
    _cluster(d, f)


@case("R156 L5: a long note left narrow", "audit_destinations.py", 1)
def _(d):
    _cluster(d, lambda doc: doc["schematicNotes"][0].update(width=150, text="x " * 150))


def _core_points_live(d, extra):
    """CSB3 taken off CORE_POINTS_PENDING in the sandbox, its core points stripped, then `extra`."""
    g = os.path.join(d, "docs", "harness", "audit_wire_spacing.py")
    txt = open(g, encoding="utf-8").read().replace('"WheelSpeed-Rear", "CSB3"}', '"WheelSpeed-Rear"}')
    open(g, "w", encoding="utf-8").write(txt)
    p, doc = load(d, "CSB3")
    for cb in doc["cables"]:
        for co in cb.get("cores", []) + ([cb["shield"]] if cb.get("shield") else []):
            co.pop("sourceLayoutPoints", None)
            co.pop("targetLayoutPoints", None)
    extra(doc)
    save(p, doc)


@case("R141 RP1: cable cores stripped, drawing off the pending list", "audit_wire_spacing.py", 0)
def _(d):
    _core_points_live(d, lambda doc: None)


@case("R141 RP1: a routing point on a cable core leg", "audit_wire_spacing.py", 1)
def _(d):
    _core_points_live(d, lambda doc: doc["cables"][0]["cores"][0].update(
        targetLayoutPoints=[{"id": "lp_t_core", "schematicPosition": {"x": 0, "y": 0}}]))


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
