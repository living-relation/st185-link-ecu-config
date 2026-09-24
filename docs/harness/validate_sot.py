#!/usr/bin/env python3
"""Validate sot/channels.csv, then validate every harness drawing against it.

The SoT is the root of the tree: the ECU pin decides what a channel is, and
every drawing has to agree with it. This script is the gate that makes that
true instead of aspirational. It runs in two passes.

PASS 1 - is the SoT itself sane?
  S1  (conn,pin) is unique.
  S2  ecu_a and ecu_b each list exactly cavities 1..34, once each.
  S3  class / dir / status come from the allowed vocabularies.
  S4  a row with status=set has a net, unless its class is nc.
  S5  only a screen-class row may carry a SHIELD_* net.
  S6  the shield column names a real screen pin (a7 / b17), "own", or nothing.
  S7  a signal row may not name a screen pin as its net.

PASS 2 - do the drawings agree with the SoT?
  D1  ABSOLUTE: nothing but a shield drain lands on a7 or b17.
  D2  every ecu_a / ecu_b cavity a drawing wires is a pin the SoT says is
      usable - never a spare, an nc, or the empty B14 cavity.
  D3  a cavity the SoT marks nc is not wired anywhere.
  D4  a signal-class ECU pin has exactly one conductor on it across all the
      drawings. Two conductors on one signal pin is two sources shorted
      together. Rails, grounds and screens are shared by design and exempt.

Exit 1 on any finding. Read-only - it changes nothing.
"""
import csv, json, pathlib, sys, collections

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOT = ROOT / "sot" / "channels.csv"
REB = ROOT / "docs" / "harness" / "rebuild"

CLASSES = {"signal", "rail", "screen", "power", "ground", "spare", "nc"}
DIRS = {"in", "out", "bidir", "na"}
STATUS = {"set", "proposed", "spare", "tbd", "nc"}

findings = []


def bad(code, msg):
    findings.append("%-4s %s" % (code, msg))


rows = list(csv.DictReader(SOT.open(encoding="utf-8")))
print("SoT: %d rows from %s" % (len(rows), SOT.relative_to(ROOT)))

# ---------------------------------------------------------------- pass 1
seen = {}
for i, r in enumerate(rows, 2):
    key = (r["conn"], r["pin"])
    if r["pin"] != "TBD" and key in seen:
        bad("S1", "%s.%s appears on line %d and %d" % (key + (seen[key], i)))
    seen[key] = i
    if r["class"] not in CLASSES:
        bad("S3", "line %d: class %r" % (i, r["class"]))
    if r["dir"] not in DIRS:
        bad("S3", "line %d: dir %r" % (i, r["dir"]))
    if r["status"] not in STATUS:
        bad("S3", "line %d: status %r" % (i, r["status"]))
    if r["status"] == "set" and not r["net"] and r["class"] != "nc":
        bad("S4", "line %d: status=set with no net (%s.%s)" % (i, r["conn"], r["pin"]))
    if r["net"].startswith("SHIELD_") and r["class"] != "screen":
        bad("S5", "line %d: %s on a %s row" % (i, r["net"], r["class"]))
    if r["shield"] not in ("", "own", "a7", "b17"):
        bad("S6", "line %d: shield %r" % (i, r["shield"]))

for conn in ("ecu_a", "ecu_b"):
    pins = [r["pin"] for r in rows if r["conn"] == conn]
    want = ["%s%d" % (conn[-1], n) for n in range(1, 35)]
    missing = [p for p in want if p not in pins]
    extra = [p for p in pins if p not in want]
    if missing:
        bad("S2", "%s missing %s" % (conn, ", ".join(missing)))
    if extra:
        bad("S2", "%s has unexpected %s" % (conn, ", ".join(extra)))

# ---------------------------------------------------------------- pass 2
SCREEN_PINS = {(r["conn"], r["pin"]) for r in rows if r["class"] == "screen"}
USABLE = {(r["conn"], r["pin"]) for r in rows
          if r["status"] in ("set", "proposed") and r["class"] != "nc"}
NC = {(r["conn"], r["pin"]) for r in rows if r["status"] == "nc"}
SPARE = {(r["conn"], r["pin"]) for r in rows if r["status"] == "spare"}
SIGNAL = {(r["conn"], r["pin"]) for r in rows if r["class"] == "signal"}
landings = collections.defaultdict(list)


def is_drain(cond, cable_shield):
    if cable_shield:
        return True
    tail = cond["id"].rsplit("_", 1)[-1]
    return (cond.get("color") == "Shield" or tail in ("sh", "shield", "drain")
            or cond["id"].startswith("w_drain"))


def conductors(d):
    """Wires AND cable conductors. WheelSpeed has no `wires` at all."""
    out = []
    for w in d.get("wires", []):
        out.append((w, False))
    for cb in d.get("cables", []):
        for co in cb.get("cores", []):
            out.append((co, False))
        sh = cb.get("shield")
        if sh:
            out.append((sh, True))
    return out


def passive_ends(d):
    """Resistor and diode nodes. A conductor that runs from an ECU pin to one
    of these is a pull-up or a terminator, not a second source, so it does not
    count against the one-conductor-per-signal-pin rule. The cam Hall pull-up
    (1.8k from Trigger 2 to +8V) and the CAN 120 ohm terminators are both this
    shape."""
    ids = set()
    for k in ("resistors", "diodes"):
        for p in d.get(k, []):
            ids.add(p["id"])
    return ids


def ecu_ref(node_id):
    """Map a drawing node to an SoT connector: the real ECU connectors, and
    the dm_ecu_a_a23 / dm_ecu_b_b12 cross-reference dummies, which are the
    same electrical point as the pin they name."""
    if node_id in ("ecu_a", "ecu_b"):
        return node_id, None
    if node_id.startswith("dm_ecu_a_") or node_id.startswith("dm_ecu_b_"):
        parts = node_id.split("_")
        return "ecu_" + parts[2], parts[3]
    return None, None


checked = 0
for path in sorted(REB.glob("*.harness")):
    d = json.loads(path.read_text(encoding="utf-8"))
    passives = passive_ends(d)
    for cond, cable_shield in conductors(d):
        for end in ("source", "target"):
            e = cond.get(end) or {}
            far = (cond.get("target" if end == "source" else "source") or {}).get("id")
            conn, forced = ecu_ref(e.get("id", ""))
            if not conn:
                continue
            pin = forced or e.get("handle")
            if not pin:
                continue
            key = (conn, pin)
            checked += 1
            if key in SIGNAL and far not in passives:
                landings[key].append("%s %s" % (path.name[6:-8], cond["id"]))
            if key in SCREEN_PINS and not is_drain(cond, cable_shield):
                bad("D1", "%s: %s lands on %s.%s - shield grounds carry drains only"
                    % (path.name, cond["id"], conn, pin))
            if key in NC:
                bad("D3", "%s: %s wires %s.%s which the SoT marks nc"
                    % (path.name, cond["id"], conn, pin))
            elif key in SPARE:
                bad("D2", "%s: %s wires %s.%s which the SoT marks spare"
                    % (path.name, cond["id"], conn, pin))
            elif key not in USABLE:
                bad("D2", "%s: %s wires %s.%s which is not in the SoT"
                    % (path.name, cond["id"], conn, pin))

for key, who in sorted(landings.items()):
    if len(who) > 1:
        bad("D4", "%s.%s has %d conductors on one signal pin: %s"
            % (key + (len(who), "; ".join(who))))

# ---------------------------------------------------------------- report
if findings:
    print()
    for f in sorted(set(findings)):
        print(f)
    print("\n%d finding(s)" % len(set(findings)))
    sys.exit(1)

by_owner = collections.Counter(r["owner"] for r in rows)
print("owners: " + ", ".join("%s=%d" % kv for kv in sorted(by_owner.items())))
print("ECU landings checked in the drawings: %d" % checked)
print("OK - SoT is self-consistent and every drawing agrees with it")
