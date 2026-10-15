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
  S6  the CSV must not carry a per-wire shield flag. Only a device or sensor
      gets a shield, in docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md.
  S7  a signal row may not name a screen pin as its net.

PASS 2 - do the drawings agree with the SoT?
  D1  ABSOLUTE: nothing but a shield drain lands on a7 or b17.
  D2  every ecu_a / ecu_b cavity a drawing wires is a pin the SoT says is
      usable - never a spare, an nc, or the empty B14 cavity.
  D3  a cavity the SoT marks nc is not wired anywhere.
  D4  a signal-class ECU pin has exactly one conductor on it across all the
      drawings. Two conductors on one signal pin is two sources shorted
      together. Rails, grounds and screens are shared by design and exempt.

PASS 4 - do the drawings agree with the SoT's NON-ECU endpoint rows (relays, the
MR-S EPS plug, the VRC plugs, the A/C amps)? Added 2026-10-14 for OPEN-ITEMS row 60
(the reconcile plan's "endpoint pin list"): the list already exists - the SoT rows
plus interfaces.json "endpoints" (role -> cavity for the VRC plugs) - so this pass
gates it instead of a second document.
  P1  a row's conn resolves: a connector drawn in some loom, or an interfaces.json
      endpoint; its pin is a cavity there (an endpoint's role name, or "c<pin>").
      A conn that is neither (an OEM device on factory wiring or a flying lead,
      gated by validate_oem_endpoints.py) is listed, not failed.
  P2  a resolved row with status=set is wired in some drawing.
  P3  signal-class rows with the same net reach each other (through splices,
      bulkheads, inline pairs, broken-off wires and enclosures).
  P4  a row whose net is also an ECU pin's net reaches that ECU pin.
  P5  a signal-class row never reaches an ECU signal pin with a different net
      (crossed or swapped pins).

Exit 1 on any finding. Read-only - it changes nothing.
"""
import csv, json, pathlib, sys, collections

import model

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOT = ROOT / "sot" / "channels.csv"
REB = ROOT / "docs" / "harness" / "rebuild"

CLASSES = {"signal", "rail", "screen", "power", "ground", "spare", "nc"}
DIRS = {"in", "out", "bidir", "na"}
STATUS = {"set", "proposed", "spare", "tbd", "nc"}

findings = []


def bad(code, msg):
    findings.append("%-4s %s" % (code, msg))


_sot = csv.DictReader(SOT.open(encoding="utf-8"))
fieldnames = _sot.fieldnames or []
rows = list(_sot)
print("SoT: %d rows from %s" % (len(rows), SOT.relative_to(ROOT)))
if "shield" in fieldnames:
    bad("S6", "channels.csv has a per-wire shield column; only a device or sensor gets a shield")

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
    if r.get("shield"):
        bad("S6", "line %d: per-wire shield flag %r - only a device or sensor gets a shield" % (i, r["shield"]))

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
    return model.is_drain(cond)


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
    d = model.full_text(json.loads(path.read_text(encoding="utf-8")), path.name)
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


# ---------------------------------------------------------------- pass 3
# H1 (added 2026-09-25 after B12 drifted): XTREMEX-IO-TABLE.html is the human
# view of this CSV. It may never call a pin "Available" / "spare" that the SoT
# has in use.
import html as _html, re as _re
IO = ROOT / "XTREMEX-IO-TABLE.html"
_ecu = {(r["conn"], r["pin"]): r for r in rows if r["conn"] in ("ecu_a", "ecu_b")}


def _pins(cell):
    out = []
    for a, lo, _b, hi in _re.findall(r"([AB])(\d+)(?:\s*[\u2013-]\s*([AB])?(\d+))?", cell):
        lo, hi = int(lo), int(hi or lo)
        for n in range(min(lo, hi), max(lo, hi) + 1):
            out.append(("ecu_" + a.lower(), a.lower() + str(n)))
    return out


for tr in _re.findall(r"<tr[^>]*>(.*?)</tr>", IO.read_text(encoding="utf-8"), _re.S):
    cells = [_html.unescape(_re.sub(r"<[^>]+>", "", c)).strip()
             for c in _re.findall(r"<td[^>]*>(.*?)</td>", tr, _re.S)]
    if len(cells) < 4 or not _re.fullmatch(r"[AB0-9\s\u2013\u00b7-]+", cells[1]):
        continue
    if not any(w in cells[3].lower() for w in ("available", "spare")):
        continue
    for key in _pins(cells[1]):
        r = _ecu.get(key)
        if r and r["status"] not in ("spare", "nc"):
            bad("H1", "IO table calls %s.%s free (%r) but the SoT has it %s as %s"
                % (key + (cells[3], r["status"], r["label"])))

# ---------------------------------------------------------------- pass 4
# Non-ECU endpoint rows vs the drawings (OPEN-ITEMS row 60, 2026-10-14).
_reg = model.registry()
_ds = model.docs(_reg)
_g = model.Graph(_reg, _ds)
_drawn = {}
for _loom, _d in _ds.items():
    for _c in _d.get("connectors", []):
        if not _c["id"].startswith("dm_") and not model.is_xref(_c):
            _drawn.setdefault(_c["id"], (_loom, _c))
_endpoints = {e["id"]: e for e in _reg.get("endpoints", []) if e.get("connector")}
_THROUGH = ("SP", "BH", "IX", "BRK", "ENC")
_ecu_net = collections.defaultdict(set)
for r in rows:
    if r["owner"] == "ECU" and r["net"] and r["status"] not in ("spare", "nc"):
        _ecu_net[r["net"]].add(("ECU", r["conn"], r["pin"]))
_ecu_sig = {("ECU", r["conn"], r["pin"]): r["net"] for r in rows
            if r["owner"] == "ECU" and r["class"] == "signal" and r["net"]}


def _resolve(r):
    """(connector id, cavity id) for an endpoint row, or None if the conn is not drawn."""
    if r["conn"] in _drawn:
        return r["conn"], r["pin"]
    ep = _endpoints.get(r["conn"])
    if ep:
        return ep["connector"], ep.get("pins", {}).get(r["pin"]) or "c" + r["pin"]
    return None


unresolved = []
_nets = collections.defaultdict(list)
for r in rows:
    if r["owner"] == "ECU" or r["status"] in ("spare", "nc"):
        continue
    hit = _resolve(r)
    if not hit:
        unresolved.append("%s %s.%s" % (r["owner"], r["conn"], r["pin"]))
        continue
    conn, cav = hit
    loom, c = _drawn.get(conn, (None, None))
    if not c or cav not in {x["id"] for x in c.get("cavities", [])}:
        bad("P1", "%s.%s (%s) -> %s.%s is not a drawn cavity" % (r["conn"], r["pin"], r["net"], conn, cav))
        continue
    node = _g.node(loom, {"id": conn, "handle": cav})
    if node not in _g.adj:
        bad("P2", "%s.%s (%s) is set in the SoT but %s.%s is wired in no drawing"
            % (r["conn"], r["pin"], r["net"], conn, cav))
        continue
    net = _g.reach(node, stop=lambda m: m[0] not in _THROUGH)
    want = _ecu_net.get(r["net"])
    if want and not (want & net):
        bad("P4", "%s.%s (%s) never reaches ECU %s" % (r["conn"], r["pin"], r["net"],
            "/".join(sorted(p[2].upper() for p in want))))
    if r["class"] == "signal":
        _nets[r["net"]].append((r, node, net))
        for m in net:
            other = _ecu_sig.get(m)
            if other and other != r["net"]:
                bad("P5", "%s.%s (%s) reaches ECU %s, which the SoT calls %s"
                    % (r["conn"], r["pin"], r["net"], m[2].upper(), other))
for _net, lst in _nets.items():
    for i, (a, na, ra) in enumerate(lst):
        for b, nb, rb in lst[i + 1:]:
            if nb not in ra:
                bad("P3", "%s.%s and %s.%s are both %s in the SoT but are not joined in the drawings"
                    % (a["conn"], a["pin"], b["conn"], b["pin"], _net))
if unresolved:
    print("P1 listed (conn not drawn - factory wiring or OEM flying leads): " + ", ".join(unresolved))

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
