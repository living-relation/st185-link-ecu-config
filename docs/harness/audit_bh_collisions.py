"""Bulkhead pin sharing - Daniel's rule (2026-10-03, refined).

Daniel: "several wires won't necessarily connect to a single pin directly - that's a
matter of the combined awg fitting in the particular pin. Unless the pin size
accommodates the equivalent combined wires awg, a splice can be applied before the pin:
one short wire crimped to the PIN, with splices from the wire for the circuits sharing
it. Combined circuits must be for the same signal: power, ground, drain (for cable
shield/screen/braid), CAN L, CAN H."

Both forms are accepted and checked the same way, per HALF of a bulkhead cavity:
  direct   several conductors crimped into the one cavity - the combined gauge must fit
           the contact; that is audit_cavity_parts.py K3 (Wire Barn combined gauge)
  pigtail  one short conductor in the cavity running to a splice; the circuits are the
           branches behind that splice (walked through splices on this side only)

  B1  everything behind the pin is ONE class, and the same rail/net where the net is known:
        +5V, +8V or +12V rail (same rail only - +5V with +5V, never +5V with +8V)
        ground (Gnd Out sensor return and ECU/chassis ground are different nets)
        shield / screen drain (SHIELD_A and SHIELD_B are different nets)
        CAN H  /  CAN L
  B2  a SIGNAL pin carries one ECU signal only. Pull-up/series resistors and diodes on it
      are part of that circuit. One signal fanned out to two or more devices through one
      pin is allowed only when the bulkhead cavity label says "splice" (case by case).
  Anything else - two signals, a signal with any rail/ground, two different classes, two
  different rails or grounds - fails.

Class of each thing behind the pin:
  ECU pin       from sot/channels.csv (net CAN1H/CAN1L -> CAN H/L, class screen -> shield,
                class ground or net GNDOUT -> ground, P5V/P8V -> +5V/+8V, class power ->
                +12V, class signal -> signal)
  device pin    from its label text; a label naming two supplies ("12V/8V") accepts either
  continues     another bulkhead hole, an inline interface pin or a broken-off end is the
                same circuit carrying on - it is checked at its own hole
History: 2026-09-23 bulkhead B c7/c8 each carried an analog signal AND a switched 12V.
"""
import collections
import re
import sys

import model

BH = {"bh_a_fw", "bh_a_eng", "bh_b_fw", "bh_b_eng"}
KIND_TEXT = (("shield", re.compile(r"shield|screen|drain|braid", re.I)),
             ("CAN H", re.compile(r"\bCAN\s?-?\s?H(igh)?\b|\bCAN\d?H\b", re.I)),
             ("CAN L", re.compile(r"\bCAN\s?-?\s?L(ow)?\b|\bCAN\d?L\b", re.I)),
             ("ground", re.compile(r"\bGND\b|\bGnd\b|ground|chassis|earth", re.I)),
             ("+5V", re.compile(r"(?<![0-9.])\+?5\s?V(?![0-9])", re.I)),
             ("+8V", re.compile(r"(?<![0-9.])\+?8\s?V(?![0-9])", re.I)),
             ("+12V", re.compile(r"(?<![0-9.])\+?(12|14)\s?V(?![0-9])|\+B\b|\bbatt", re.I)))
SHAREABLE = {"+5V", "+8V", "+12V", "ground", "shield", "CAN H", "CAN L"}


def text_kinds(t):
    """Every class a label names (a supply pin labelled "12V/8V" accepts both)."""
    return {k for k, rx in KIND_TEXT if rx.search(t or "")}


def ecu_kind(r):
    if r["net"] == "CAN1H":
        return "CAN H"
    if r["net"] == "CAN1L":
        return "CAN L"
    if r["class"] == "screen":
        return "shield"
    if r["class"] == "ground" or r["net"] == "GNDOUT":
        return "ground"
    if r["net"] == "P5V":
        return "+5V"
    if r["net"] == "P8V":
        return "+8V"
    if r["class"] == "power":
        return "+12V"
    return "signal"


def judge(ends, cav_label, through=()):
    """ends: list of (kind or None, net or None, accepted kinds, what) for everything behind
    one half of one pin. through: (kind, net) of the ECU pins the circuit reaches on the
    OTHER side of the hole - used only when nothing behind this half is an ECU pin.
    Returns None if allowed, else the reason."""
    if not any(e[0] is not None for e in ends) and through:
        tk = {k for k, n in through}
        if tk == {"signal"} and not any(e[2] & SHAREABLE for e in ends):
            ends = list(ends) + [("signal", n, set(), "via hole: ecu %s" % n) for k, n in sorted(set(through))]
    ecu = [e for e in ends if e[0] is not None]
    dev = [e for e in ends if e[0] is None]
    if len(ends) < 2:
        return None
    kinds = {e[0] for e in ecu}
    if "signal" in kinds:
        nets = {e[1] for e in ecu if e[0] == "signal"}
        if len(nets) > 1:
            return "two ECU signals share it (%s)" % ", ".join(sorted(nets))
        if kinds != {"signal"}:
            return "an ECU signal shares it with %s" % ", ".join(sorted(kinds - {"signal"}))
        powered = [e for e in dev if e[2] & SHAREABLE]
        if powered:
            return "an ECU signal shares it with %s (%s)" % (
                "/".join(sorted(powered[0][2])), powered[0][3])
        if len(dev) >= 2 and not re.search(r"splice", cav_label or "", re.I):
            # fan-out of one signal: case by case, marked in the cavity label
            return ("one ECU signal fans out to %d device pins - allowed only when the cavity "
                    "label says 'splice'" % len(dev))
        return None
    if len(kinds) > 1:
        return "different classes share it (%s)" % ", ".join(sorted(kinds))
    for kind in kinds:
        nets = {e[1] for e in ecu}
        if len(nets) > 1:
            return "different %s nets share it (%s)" % (kind, ", ".join(sorted(nets)))
    want = next(iter(kinds)) if kinds else None
    if want is None:                          # no ECU pin behind it: classes come from labels
        sets = [e[2] for e in dev]
        common = set.intersection(*sets) & SHAREABLE if sets else set()
        if not common:
            return "the device pins behind it are not one shareable class: %s" % "; ".join(
                "%s=%s" % (e[3], "/".join(sorted(e[2])) or "signal") for e in dev)
        return None
    bad_dev = [e for e in dev if want not in e[2]]
    if bad_dev:
        return "%s pin shares with %s" % (want, "; ".join(
            "%s (%s)" % (e[3], "/".join(sorted(e[2])) or "no class in label") for e in bad_dev))
    return None


def main():
    reg = model.registry()
    ds = model.docs(reg)
    g = model.Graph(reg, ds)
    sot = {(r["conn"], r["pin"]): r for r in model.sot_rows()}
    label, cav_label, passive = {}, {}, set()
    for loom, d in ds.items():
        for c in d.get("connectors", []):
            for cv in c.get("cavities", []):
                label[("C", c["id"], cv["id"])] = cv.get("signal") or ""
                if c["id"] in BH:
                    cav_label[(c["id"], cv["id"])] = cv.get("signal") or ""
        for t in d.get("terminals", []):
            label[("T", loom, t["id"])] = t.get("signal") or t.get("label") or ""
        for r in d.get("resistors", []) + d.get("diodes", []):
            passive.add(r["id"])

    halves = collections.defaultdict(list)   # (loom, half, cav) -> [(far node, conductor id)]
    for loom, d in ds.items():
        for cond, cable, screen in model.conductors(d):
            s, t = cond.get("source") or {}, cond.get("target") or {}
            for e, o in ((s, t), (t, s)):
                nid = e.get("id", "")
                if nid in BH:
                    half, cav = nid, e.get("handle")
                elif nid.startswith("dm_bh_"):
                    half, cav = nid[3:].rsplit("_", 1)
                else:
                    continue
                if o.get("id"):
                    halves[(loom, half, cav)].append((g.node(loom, o), cond["id"], screen,
                                                     g.node(loom, {"id": half, "handle": cav})))

    bad, shared = [], 0
    for (loom, half, cav), conds in sorted(halves.items(), key=lambda kv: (kv[0][1], int(kv[0][2][1:]), kv[0][0])):
        hole = conds[0][3]
        seen, todo, ends = {hole}, [c[0] for c in conds], []
        screen_conds = {c[0] for c in conds if c[2]}
        while todo:
            n = todo.pop()
            if n in seen:
                continue
            seen.add(n)
            if n[0] == "SP":
                todo += [m for m in g.adj.get(n, ()) if m not in seen]
                continue
            if n[0] in ("BH", "IX", "BRK"):
                continue                                   # same circuit, checked at its own hole
            if n[0] == "C" and n[1] in passive:
                continue                                   # resistor / diode in the circuit
            if n[0] == "ECU" and (n[1], n[2]) in sot:
                r = sot[(n[1], n[2])]
                ends.append((ecu_kind(r), r["net"], set(), model.fmt(n)))
            elif n in screen_conds:
                ends.append((None, None, {"shield"}, model.fmt(n)))
            else:
                ends.append((None, None, text_kinds(label.get(n, "")), model.fmt(n)))
        if len(conds) < 2 and len(ends) < 2:
            continue
        through = []
        if not any(e[0] is not None for e in ends) and len(ends) >= 2:
            net = g.reach(hole, stop=lambda m: m[0] not in ("SP", "BH", "IX", "BRK"))
            through = [(ecu_kind(sot[(m[1], m[2])]), sot[(m[1], m[2])]["net"])
                       for m in net if m[0] == "ECU" and (m[1], m[2]) in sot]
        why = judge(ends, cav_label.get((half, cav), ""), through)
        if why is None:
            if len(ends) >= 2:
                shared += 1
            continue
        bad.append("%s %s (%s, %s): %s" % (half, cav, loom,
                                           "direct, %d conductors" % len(conds) if len(conds) > 1 else "pigtail + splice",
                                           why))
        for kind, net, acc, what in ends:
            bad.append("      %-28s %s" % (what, kind or ("/".join(sorted(acc)) or "no class in label")))

    for line in bad:
        print(line)
    print()
    print("bulkhead pins legitimately shared (one class / one signal): %d" % shared)
    print("Direct form: the combined gauge must fit the contact - audit_cavity_parts.py K3.")
    n = sum(1 for l in bad if not l.startswith(" "))
    print("%d bulkhead pins shared by circuits that may not share." % n)
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
