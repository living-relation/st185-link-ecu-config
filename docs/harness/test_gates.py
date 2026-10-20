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
    add_copy(d, "ECU-engine", "w109_e", "bh_eng", "c21")   # INJ1's cavity (R208 map)


@case("injector signal + injector 12V feed in one pin", "audit_bh_collisions.py", 1)
def _(d):
    add_copy(d, "ECU-engine", "w_inj_pwr_e_ae", "bh_eng", "c21")


@case("two sensor grounds crimped into one ground pin (direct form)", "audit_bh_collisions.py", 0)
def _(d):
    add_copy(d, "ECU-engine", "w17", "bh_eng", "c65")   # the cam sensor ground cavity


@case("ground + switched 12V in one pin", "audit_bh_collisions.py", 1)
def _(d):
    add_copy(d, "ECU-engine", "w_vss_12v", "bh_eng", "c29")   # a B ground cavity


@case("pigtail + splice: +5V bus plug (bussed DT, R169) also fed from ECU +8V Out", "audit_bh_collisions.py", 1)
def _(d):
    add_wire(d, "ECU-cabin", "w_t_8v_into_5v", {"id": "bus_5v2_p", "handle": "c8"},
             {"id": "ecu_a", "handle": "a6"})


@case("pigtail + splice: extra 12V device on the switched-12V splice", "audit_bh_collisions.py", 0)
def _(d):
    add_wire(d, "ECU-engine", "w_t_12v_dev", {"id": "sp_sw12_eng", "handle": "Splice"},
             {"id": "inj1", "handle": "c1"})


@case("one ECU signal fanned out to 2 devices, cavity NOT labelled splice", "audit_bh_collisions.py", 1)
def _(d):
    add_copy(d, "ECU-engine", "w109_e", "bh_eng", "c22", extra_target=None)
    add_copy(d, "ECU-engine", "w108_e", "bh_eng", "c22")


@case("same fan-out, cavity labelled 'splice' on both halves", "audit_bh_collisions.py", 0)
def _(d):
    add_copy(d, "ECU-engine", "w108_e", "bh_eng", "c22")
    for loom, half in (("ECU-engine", "bh_eng"), ("ECU-cabin", "bh_fw")):
        label(d, loom, half, "c22", "INJ2 (splice)")


@case("4 x 18 AWG grounds direct in one size-16 pin: sharing OK ...", "audit_bh_collisions.py", 0)
def _(d):
    p, doc = load(d, "ECU-engine")
    doc["wireParts"].append({"id": "wp_18_t", "partNumber": "T18", "manufacturer": "t",
                             "description": "t", "color": "Black", "gauge": {"value": 18, "unit": "AWG"}})
    save(p, doc)
    for i in range(3):
        add_copy(d, "ECU-engine", "w17", "bh_eng", "c56", gauge_part="wp_18_t")
    p, doc = load(d, "ECU-engine")
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


@case("DRB102: a B spare moved onto the crank signal cavity 74, both halves (M8 collision)", "audit_mating.py", 1)
def _(d):
    for loom, half in (("ECU-cabin", "bh_fw"), ("ECU-engine", "bh_eng")):
        designate(d, loom, half, "c97", "74")


@case("DRB102: size-12 plug put in a size-16 cavity (M8 size)", "audit_mating.py", 1)
def _(d):
    for loom, half in (("ECU-cabin", "bh_fw"), ("ECU-engine", "bh_eng")):
        designate(d, loom, half, "c97", "82")      # the size-12 plug sits on a size-16 number ...
        designate(d, loom, half, "c82", "97")      # ... and the size-16 plug on a size-12 number


@case("R202: a wire given one routing point (RP1)", "audit_wire_spacing.py", 1)
def _(d):
    p, doc = load(d, "CabinPower")
    w = doc["wires"][0]
    w["layoutPoints"] = [{"id": "lp_t_rp1", "schematicPosition": {"x": 0, "y": 0}}]
    save(p, doc)


@case("R202: bundle layout points are not wire routing points (RP1 allows)", "audit_wire_spacing.py", 0)
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
        ("Gnd Out with ECU power ground", [E("ground", "GNDOUT_A"), E("ground", "GND_ECU")], False),
        ("+5V with +8V", [E("+5V", "P5V"), E("+8V", "P8V")], False),
        ("12V rail with a '12V/8V' supply pin", [E("+12V", "SW12"), D("12V/8V")], True),
        ("signal with its pull-up resistor only", [E("signal", "TRIG2_CAM")], True),
    ]
    for name, ends, ok in checks:
        got = bhc.judge(ends, "") is None
        out.append((name, ok, got))
    out += fusebox_mesh_cases()
    out += wall_class_cases()
    out += drawing_model_cases()
    out += drawing_rule_cases()
    return out


def drawing_rule_cases():
    """R184 - R196 gate cad/check_drawing_rules.py on a sandbox drawing and its engine check report: a clean report passes; a missing
    or stale report, an engine rule failure, a banned note and a stale PENDING entry fail; a pending drawing is reported only."""
    sys.path.insert(0, os.path.join(ROOT, "cad"))
    import importlib
    import check_drawing_rules as G
    importlib.reload(G)
    out = []

    def run(name, want, rep=None, pdf=b"%PDF fake", pending=False, man_sha=None, rows=(("A", "DG"), ("B", "DG")), text=None, rev=None, exempt=None):
        d = tempfile.mkdtemp(prefix="dwgr_")
        try:
            os.makedirs(os.path.join(d, "m"))
            open(os.path.join(d, "m", "ST185-T-101.pdf"), "wb").write(pdf)
            ps = G.sha(pdf)
            json.dump({"drawings": {"ST185-T-101": {"pdf": "m/ST185-T-101.pdf", "pdf_sha": man_sha or ps,
                                                    "revlog": "m/ST185-T-101.REVLOG.md",
                                                    **({"rev": rev} if rev else {})}}},
                      open(os.path.join(d, "drawing-models.json"), "w"))
            open(os.path.join(d, "m", "ST185-T-101.REVLOG.md"), "w").write(
                "| Rev | Description | By | Date |\n|---|---|---|---|\n" + "".join("| %s | x | %s | 19/10/26 |\n" % r for r in rows))
            if rep is not None:
                r = dict(pn="ST185-T-101", pdf_sha=ps, engine_rules="2026-10-18", tangent_edges_in_pictorial=True, ok=True,
                         notes=["TORQUE THE 4 LID SCREWS EVENLY, CRISS-CROSS."], tol_block="DIMENSIONS ARE IN MILLIMETERS",
                         balloon_views=[], not_ballooned=[])
                r.update(rep)
                json.dump(r, open(os.path.join(d, "m", "ST185-T-101.checks.json"), "w"))
            G.CAD, G.MANIFEST = d, os.path.join(d, "drawing-models.json")
            if exempt:
                json.dump({"exempt_through": exempt}, open(os.path.join(d, "rev-marks.json"), "w"))
            G.PENDING = {"ST185-T-101"} if pending else set()
            G.sheet1_text = lambda _pdf: text      # None = no pypdf / unreadable PDF: the title-block check is skipped
            got = G.check(quiet=True)          # True = the gate passes
        finally:
            shutil.rmtree(d, ignore_errors=True)
        out.append(("R184-R196 " + name, want, got))

    run("clean report passes", True, rep={})
    run("no report fails", False)
    run("report for another PDF fails", False, rep={}, man_sha="0000000000000000")
    run("old engine fails", False, rep={"engine_rules": "2026-10-17"})
    run("no tangent edges fails (R187)", False, rep={"tangent_edges_in_pictorial": False})
    run("hidden part never ballooned fails (R186)", False, rep={"ok": False, "not_ballooned": ["5"]})
    run("overlapping balloons fail (R188)", False,
        rep={"ok": False, "balloon_views": [dict(view="TRIMETRIC VIEW", placed=9, overlaps=1, crowded=0, hidden=[])]})
    run("envelope note fails (R184)", False, rep={"notes": ["CONNECTOR BODIES ARE ENVELOPE MODELS."]})
    run("pin / socket note fails (R185)", False, rep={"notes": ["PINS (7) ON BOX SIDE; SOCKETS (14) ON HARNESS SO LIVE 12V IS SHROUDED."]})
    run("edge-break line in the tolerance block fails (R191)", False, rep={"tol_block": "BREAK SHARP EDGES 0.2-0.4"})
    run("markup / rule-number note fails (R192)", False, rep={"notes": ["MARKUP 2026-10-17 (R157 - R160): HOOKS BEAR ON THE COPPER."]})
    run("a bend radius is not a rule number", True, rep={"notes": ["BEND 2X 90 DEG, R1.0 INSIDE (R1.0)."]})
    run("pending drawing with a failing report is reported only", True, rep={"notes": ["MARKUP 2026-10-17."]}, pending=True)
    run("pending drawing with no report is reported only", True, pending=True)
    run("stale PENDING entry fails", False, rep={}, pending=True)
    # R200: DRAWN = Rev A BY, every BY a person's initials, never an agent / tool name or blank
    for bad in ("Claude", "SteveCAD", "Grok", "Fairsolid", "unknown", "SC", "", "D"):
        run("agent / blank BY %r fails (R200)" % bad, False, rep={}, rows=(("A", "DG"), ("B", bad)))
    run("agent on Rev A fails (R200)", False, rep={}, rows=(("A", "Claude"), ("B", "DG")))
    run("no Rev A row fails (R200)", False, rep={}, rows=(("B", "DG"),))
    run("other person's initials pass (R200)", True, rep={}, rows=(("A", "DG"), ("B", "JD")))
    run("title block DRAWN = Rev A passes (R200)", True, rep={}, text="x\nDRAWN\nDG\nSOURCE\n")
    run("title block DRAWN other than Rev A fails (R200)", False, rep={}, text="x\nDRAWN\nSteveCAD\nSOURCE\n")
    run("no DRAWN in the PDF fails (R200)", False, rep={}, text="nothing here")
    # R200 revision triangles: a full letter made after 2026-10-19 has at least one; older letters, Rev A and clerical revs are exempt
    run("new full letter without a triangle fails (R200)", False, rep={}, rev="C")
    run("new full letter with a triangle passes (R200)", True, rep={"rev_marks": {"C": 1}}, rev="C")
    run("clerical rev of a new letter still needs that letter's triangle (R200)", False, rep={}, rev="C.01")
    run("clerical rev with the letter's triangle passes (R200)", True, rep={"rev_marks": {"C": 2}}, rev="C.01")
    run("only an older letter's triangle does not count (R200)", False, rep={"rev_marks": {"B": 3}}, rev="C")
    run("letter made before the rule is exempt (R200)", True, rep={}, rev="D.01", exempt={"ST185-T-101": "D"})
    run("next letter after the exempt one needs a triangle (R200)", False, rep={}, rev="E", exempt={"ST185-T-101": "D"})
    run("Rev A needs no triangle (R200)", True, rep={}, rev="A")
    run("a declared triangle that could not be placed fails (R200)", False,
        rep={"rev_marks": {"A": 0}, "rev_marks_unplaced": [{"rev": "A", "item": 5, "why": "no free spot"}]}, rev="A")
    return out


def drawing_model_cases():
    """R183 gate cad/check_drawings_current.py on a sandbox drawing: model changes without a regenerated drawing fail, a re-export of
    the same geometry, a clerical .NN and a non-geometry report field pass, letters and rev logs follow R147 - R152 / revs.py."""
    sys.path.insert(0, os.path.join(ROOT, "cad"))
    import importlib
    import check_drawings_current as G
    importlib.reload(G)
    out = []

    def build(rev="V", revlog=("A", "U", "V"), reg_rev=None, step_data=b"#1=CARTESIAN_POINT('',(0.,0.,0.));", vol=845.5,
              extra=None, pdf=b"%PDF fake", in_manifest=True):
        d = tempfile.mkdtemp(prefix="dwg_")
        cad = os.path.join(d, "cad")
        os.makedirs(os.path.join(cad, "m"))
        open(os.path.join(cad, "m", "T-101.REVLOG.md"), "w").write(
            "| Rev | Description | By | Date |\n|---|---|---|---|\n" + "".join("| %s | x | C | 18/10/26 |\n" % r for r in revlog))
        open(os.path.join(cad, "m", "part.step"), "wb").write(b"ISO-10303-21;\nHEADER;\nFILE_NAME('part','2026-10-18T10:00:00');\nENDSEC;\nDATA;\n"
                                                             + step_data + b"\nENDSEC;\n")
        e = {"size_mm": [1, 2, 3], "volume_cm3": vol}
        e.update(extra or {})
        json.dump({"printed_parts": {"P": e}}, open(os.path.join(cad, "m", "report.json"), "w"))
        open(os.path.join(cad, "m", "ST185-T-101.pdf"), "wb").write(pdf)
        open(os.path.join(cad, "DRAWING-REVS.md"), "w").write(
            "| Item | Part no. | Model | Rev | Date | Change | Evidence | Files |\n|---|---|---|---|---|---|---|---|\n"
            "| T | ST185-T-101 | m | %s | d | c | e | `cad/m/ST185-T-101.pdf` |\n" % (reg_rev or rev))
        return d, cad

    def gate_on(d, cad, man_fn=None):
        G.CAD, G.REPO = cad, d
        G.MANIFEST, G.REGISTER = os.path.join(cad, "drawing-models.json"), os.path.join(cad, "DRAWING-REVS.md")
        G.main_checkout = lambda: d
        G.pdf_text = lambda p: None
        return G

    def baseline(rev="V"):
        d, cad = build(rev=rev)
        g = gate_on(d, cad)
        man = {"drawings": {"ST185-T-101": {"pdf": "m/ST185-T-101.pdf", "revlog": "m/T-101.REVLOG.md", "rev": rev,
                                            "steps": {"m/part.step": g.step_fp(os.path.join(cad, "m", "part.step"))},
                                            "ci": {"report:m/report.json#printed_parts#P": g.ci_fp("report:m/report.json#printed_parts#P")},
                                            "pdf_sha": g.sha(open(os.path.join(cad, "m", "ST185-T-101.pdf"), "rb").read())}}}
        json.dump(man, open(g.MANIFEST, "w"))
        return d, cad, g

    def case_(name, want, change):
        d, cad, g = baseline()
        try:
            change(d, cad, g)
            got = not g.check(quiet=True)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        out.append(("R183 " + name, want, got))

    def rewrite(cad, rel, data, mode="w"):
        open(os.path.join(cad, rel), mode).write(data)

    def step(cad, data, header="2026-10-18T10:00:00"):
        rewrite(cad, "m/part.step", b"ISO-10303-21;\nHEADER;\nFILE_NAME('part','" + header.encode() + b"');\nENDSEC;\nDATA;\n" + data
                + b"\nENDSEC;\n", "wb")

    def report(cad, vol=845.5, extra=None):
        e = {"size_mm": [1, 2, 3], "volume_cm3": vol}
        e.update(extra or {})
        json.dump({"printed_parts": {"P": e}}, open(os.path.join(cad, "m", "report.json"), "w"))

    def set_rev(cad, g, reg, man=None, revlog=None):
        rewrite(cad, "DRAWING-REVS.md", open(g.REGISTER).read().replace("| V |", "| %s |" % reg))
        m = json.load(open(g.MANIFEST))
        m["drawings"]["ST185-T-101"]["rev"] = man or reg
        json.dump(m, open(g.MANIFEST, "w"))
        if revlog:
            rewrite(cad, "m/T-101.REVLOG.md", "| Rev | Description | By | Date |\n|---|---|---|---|\n"
                    + "".join("| %s | x | C | 18/10/26 |\n" % r for r in revlog))

    case_("drawing matches its model", True, lambda d, c, g: None)
    case_("model re-exported, same geometry (STEP header only)", True, lambda d, c, g: step(c, b"#1=CARTESIAN_POINT('',(0.,0.,0.));", "2026-10-19T09:00:00"))
    case_("model STEP geometry changed, drawing not regenerated", False, lambda d, c, g: step(c, b"#1=CARTESIAN_POINT('',(1.,0.,0.));"))
    case_("model STEP not on this disk (CI): tracked fingerprints only", True, lambda d, c, g: os.remove(os.path.join(c, "m", "part.step")))
    case_("build report: part volume changed, drawing not regenerated", False, lambda d, c, g: report(c, vol=846.0))
    case_("build report: a non-geometry field changed", True, lambda d, c, g: report(c, extra={"note": "re-run"}))
    case_("clerical drawing rev V.01 on model V", True, lambda d, c, g: set_rev(c, g, "V.01"))
    case_("drawing rev W but the model rev log ends at V", False, lambda d, c, g: set_rev(c, g, "W"))
    case_("a decimal in the model rev log (models never get decimals)", False,
          lambda d, c, g: set_rev(c, g, "V.01", revlog=("A", "U", "V", "V.01")))
    case_("letter I is not a rev letter", False, lambda d, c, g: set_rev(c, g, "I", revlog=("A", "I")))
    case_("register rev differs from the issued drawing", False, lambda d, c, g: set_rev(c, g, "V", man="V.01"))
    case_("drawing PDF edited without re-registering", False, lambda d, c, g: rewrite(c, "m/ST185-T-101.pdf", b"%PDF hand-edited", "wb"))
    case_("a registered drawing missing from the manifest", False,
          lambda d, c, g: rewrite(c, "DRAWING-REVS.md", open(g.REGISTER).read() + "| T2 | ST185-T-102 | m | A | d | c | e | `x.pdf` |\n"))

    def pending(g, entry=None):   # R196: a model-only PR leaves the drawing for the regeneration pass
        m = json.load(open(g.MANIFEST))
        m["regen_pending"] = {"ST185-T-101": entry if entry is not None else {"reason": "model-only PR, drawings regenerated after"}}
        json.dump(m, open(g.MANIFEST, "w"))

    case_("R196 model changed + new letter, drawing on regen_pending", True,
          lambda d, c, g: (report(c, vol=846.0), rewrite(c, "m/T-101.REVLOG.md", open(os.path.join(c, "m", "T-101.REVLOG.md")).read()
                                                          + "| W | x | C | 18/10/26 |\n"), pending(g)))
    case_("R196 STEP changed, drawing on regen_pending", True,
          lambda d, c, g: (step(c, b"#1=CARTESIAN_POINT('',(1.,0.,0.));"), pending(g)))
    case_("R196 regen_pending entry without a reason", False, lambda d, c, g: (report(c, vol=846.0), pending(g, {})))
    case_("R196 regen_pending but the model did not change (stale entry)", False, lambda d, c, g: pending(g))
    case_("R196 regen_pending does not excuse a hand-edited PDF", False,
          lambda d, c, g: (report(c, vol=846.0), pending(g), rewrite(c, "m/ST185-T-101.pdf", b"%PDF hand-edited", "wb")))

    def upd(name, want, change):
        d, cad, g = baseline()
        try:
            change(d, cad, g)
            got = g.update(["ST185-T-101"]) == 0
        finally:
            shutil.rmtree(d, ignore_errors=True)
        out.append(("R183 --update: " + name, want, got))

    upd("model changed, letter not bumped: refused", False, lambda d, c, g: report(c, vol=846.0))
    upd("model changed, letter bumped to W in the rev log + register: accepted", True,
        lambda d, c, g: (report(c, vol=846.0), set_rev(c, g, "W", man="V", revlog=("A", "U", "V", "W"))))
    upd("drawing changed, model and rev not: refused (clerical .NN needed)", False,
        lambda d, c, g: rewrite(c, "m/ST185-T-101.pdf", b"%PDF new notes", "wb"))
    upd("drawing changed with a clerical V.01: accepted", True,
        lambda d, c, g: (rewrite(c, "m/ST185-T-101.pdf", b"%PDF new notes", "wb"), set_rev(c, g, "V.01", man="V")))

    d, cad, g = baseline()            # R196: --update after the regeneration takes the drawing off regen_pending
    try:
        report(cad, vol=846.0); set_rev(cad, g, "W", man="V", revlog=("A", "U", "V", "W")); pending(g)
        ok = g.update(["ST185-T-101"]) == 0 and "regen_pending" not in json.load(open(g.MANIFEST)) and not g.check(quiet=True)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    out.append(("R196 --update clears regen_pending", True, ok))
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
    p, doc = load(d, "CabinPower")   # an app-drawn file (the ECU harness is drawn by our own generator, R220)
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
    p, doc = load(d, "CabinPower")
    conns = {c["id"] for c in doc["connectors"]}
    b = copy.deepcopy(next(x for x in doc["bundles"] if conns & {x["sourceId"], x["targetId"]}))
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
    """CSB3 (off CORE_POINTS_PENDING since R156 PR2) with its core points stripped, then `extra`."""
    p, doc = load(d, "CSB3")
    for cb in doc["cables"]:
        for co in cb.get("cores", []) + ([cb["shield"]] if cb.get("shield") else []):
            co.pop("sourceLayoutPoints", None)
            co.pop("targetLayoutPoints", None)
    extra(doc)
    save(p, doc)


@case("R202 RP1: cable cores stripped, drawing off the pending list", "audit_wire_spacing.py", 0)
def _(d):
    _core_points_live(d, lambda doc: None)


@case("R202 RP1: a routing point on a cable core leg", "audit_wire_spacing.py", 1)
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
