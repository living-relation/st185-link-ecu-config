"""Bulkhead cavity sharing - Daniel's rule (2026-10-03).

One bulkhead hole carries ONE circuit, with two exceptions:

  B1  SPLICE in the hole: several conductors of the SAME circuit may land on one half of
      a cavity (crimped together / spliced into the pin - Daniel's case-by-case choice).
  B2  SHARED power hole: two or more DIFFERENT circuits may share a hole only when they
      are ALL the same kind - all +5V, all ground, all +12V, or all shields / screen
      drains (used when bulkhead pins run out). Mixing kinds (ground with +12V would be a
      dead short), +8V, signals and everything else may not share.
  Anything else on one half of one cavity is a short between two circuits and fails.

How a conductor's circuit is decided: walk the electrical graph (model.py) from the
conductor's far end, AWAY from this bulkhead hole.
  - If it reaches ECU pins: the circuit is the sot/channels.csv net of those pins; its kind
    is +5V (P5V), ground (Gnd Out / ECU ground), +12V (a 12-14 V feed, class power) or
    shield (SHIELD_A/B). +8V Out and signals have no kind.
  - A screen conductor (cable shield, drain wire) is always kind "shield".
  - Otherwise it is the device pins it reaches (two injectors are two circuits even when
    both cavities read "INJ"); its kind comes from the far-end labels when they all say
    the same one of +5V, +12V/14V/+B, ground/GND/chassis or shield/screen/drain.
  - One ECU signal fanned out to several devices through the same hole counts as ONE circuit
    (B1) only when the bulkhead cavity label says "splice" - Daniel decides those case by
    case, and the drawing alone cannot tell a planned split from a mis-landed wire.

Grouped by half (cabin side vs engine side), so the mated pair of one circuit through
the bulkhead never trips it. History: found 2026-09-23 - bulkhead B c7/c8 each had an
analog sensor signal (A files) and a switched 12V feed (B files) on one pin.
"""
import collections
import re
import sys

import model

BH = {"bh_a_fw", "bh_a_eng", "bh_b_fw", "bh_b_eng"}
THROUGH = ("SP", "BH", "IX", "BRK")
CATS = (("shield", re.compile(r"shield|screen|drain", re.I)),
        ("ground", re.compile(r"\bGND\b|\bGnd\b|ground|chassis|earth", re.I)),
        ("+5V", re.compile(r"(?<![0-9.])\+?5\s?V(?![0-9])", re.I)),
        ("+12V", re.compile(r"(?<![0-9.])\+?(12|14)\s?V(?![0-9])|\+B\b|batt", re.I)))
EIGHT_V = re.compile(r"(?<![0-9.])\+?8\s?V(?![0-9])", re.I)


def text_cat(t):
    """Power category a label names, or None (signals, +8V, or two categories at once)."""
    if EIGHT_V.search(t):
        return None
    hit = [name for name, rx in CATS if rx.search(t)]
    return hit[0] if len(hit) == 1 else None

reg = model.registry()
ds = model.docs(reg)
g = model.Graph(reg, ds)
sot = {(r["conn"], r["pin"]): r for r in model.sot_rows()}


def ecu_cat(row):
    """Power category of an ECU pin row, or None for signals / +8V."""
    if row["class"] == "screen":
        return "shield"
    if row["class"] == "ground" or row["net"] == "GNDOUT":
        return "ground"
    if row["net"] == "P5V":
        return "+5V"
    if row["class"] == "power":
        return "+12V"
    return None


labels, cav_label = {}, {}
for loom, d in ds.items():
    for c in d.get("connectors", []):
        if c["id"] in BH:
            for cv in c.get("cavities", []):
                cav_label[(c["id"], cv["id"])] = cv.get("signal") or ""
    for c in d.get("connectors", []):
        for cv in c.get("cavities", []):
            if cv.get("signal"):
                labels[("C", c["id"], cv["id"])] = cv["signal"]
    for t in d.get("terminals", []):
        if t.get("signal") or t.get("label"):
            labels[("T", loom, t["id"])] = t.get("signal") or t.get("label")


def circuit(loom, far, hole):
    """(identity, power_type) of the circuit a conductor brings to `hole`."""
    if not far.get("id"):
        return ("unconnected",), False
    start = g.node(loom, far)
    if start == hole:
        return ("loop",), False
    net = g.reach(start, stop=lambda m: m == hole or m[0] not in THROUGH)
    net.discard(hole)
    ecu = sorted(m for m in net | {start} if m[0] == "ECU")
    rows = [sot.get((m[1], m[2])) for m in ecu]
    rows = [r for r in rows if r]
    if rows:
        cats = {ecu_cat(r) for r in rows}
        return tuple(sorted({r["net"] for r in rows})), (cats.pop() if len(cats) == 1 else None)
    ends = sorted(m for m in net | {start} if m[0] not in THROUGH)
    texts = sorted({labels[m] for m in ends if m in labels})
    cats = {text_cat(t) for t in texts}
    power = cats.pop() if len(cats) == 1 else None
    # identity = the device pins it reaches (two injectors are two circuits even if both
    # cavities are labelled "INJ")
    return tuple(model.fmt(m) for m in ends) or (model.fmt(start),), power


hits = collections.defaultdict(list)   # (half, cavity) -> [(loom, conductor id, far end, screen)]
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
            hits[(half, cav)].append((loom, cond["id"], o, screen, e))

bad, shared, spliced = [], 0, 0
for (half, cav), rows in sorted(hits.items(), key=lambda kv: (kv[0][0], int(kv[0][1][1:]))):
    if len(rows) < 2:
        continue
    hole = g.node(rows[0][0], rows[0][4])
    circ = []
    for loom, wid, far, screen, e in rows:
        ident, power = circuit(loom, far, hole)
        circ.append((loom, wid, ident, "shield" if screen else power))
    idents = {c[2] for c in circ}
    if len(idents) == 1:
        spliced += 1                                     # B1 one circuit, spliced
        continue
    cats = {c[3] for c in circ}
    if len(cats) == 1 and None not in cats:
        shared += 1                                      # B2 all +5V, all ground, all +12V or all shield
        continue
    # B1 also covers ONE ECU signal fanned out to several devices through this hole: the
    # hole's net carries exactly one ECU signal, no conductor brings a different ECU net,
    # and none of them is a power feed.
    # (c[3] is the kind; a fan-out must carry no power kind at all)
    whole = g.reach(hole, stop=lambda m: m[0] not in THROUGH)
    sig = {sot[(m[1], m[2])]["net"] for m in whole if m[0] == "ECU" and (m[1], m[2]) in sot
           and sot[(m[1], m[2])]["class"] == "signal"}
    ecu_idents = {n for c in circ for n in c[2] if not n.startswith(("C:", "T:", "ENC:"))}
    marked = re.search(r"splice", cav_label.get((half, cav), ""), re.I)
    if len(sig) == 1 and not any(c[3] for c in circ) and ecu_idents <= sig and marked:
        spliced += 1
        continue
    bad.append("%s %s: %d conductors on one half carry %d different circuits, not all "
               "one kind of +5V/ground/+12V/shield%s:" % (half, cav, len(circ), len(idents),
                                              " (one ECU signal fanned out - if that is "
                                              "intended, put 'splice' in the cavity label)"
                                              if len(sig) == 1 and not any(c[3] for c in circ) else ""))
    for loom, wid, ident, power in circ:
        bad.append("      %-13s %-16s %s  [%s]" % (loom, wid, " / ".join(ident)[:90],
                                                power or "signal"))

for line in bad:
    print(line)
print()
print("bulkhead holes with a splice of one circuit (B1, allowed): %d" % spliced)
print("bulkhead holes shared by +5V/ground/+12V/shield circuits (B2, allowed): %d" % shared)
n = sum(1 for l in bad if not l.startswith(" "))
print("%d bulkhead holes shared by circuits that may not share." % n)
sys.exit(1 if n else 0)
