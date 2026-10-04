"""Self-test for the bulkhead pin-sharing and contact-fit gates.

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
                    ignore=shutil.ignore_patterns("__pycache__", "min"))
    shutil.copytree(os.path.join(ROOT, "sot"), os.path.join(d, "sot"))
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


def add_wire(d, loom, wid, a, b, part="wp_20_blk"):
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
    return out


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
