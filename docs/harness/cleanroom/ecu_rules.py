"""ECU-pin, ground-class and relay rules for the master wire lists (DECISIONS R212-R219 (no R218)).

Called by wirelist.py with the loaded rows. Each finding is a dict: rule, key, harness, item, text.
wirelist.py turns the findings into GAPS.md lines and, in --check, FAILS on any finding that is not in
PENDING. PENDING is the explicit list of known violations waiting for the wiring fix session
(OPEN-ITEMS N55 / N56): the fix session deletes entries as it fixes them, and --check also fails on a PENDING
entry that no longer violates, so the list can only shrink.

  R212  every ECU-pin wire: far ends must match the pin's Quick Start Guide class
        (ground -> ECU ground pins + battery negative; Gnd Out -> sensor returns; shield -> drains;
         +5 V / +8 V -> sensor supplies; power -> fused +12 V)
  R213  ground classes: ECU power ground and low-voltage electronics (PCBs, CAN nodes, LEDs, cruise ladder)
        -> battery-negative bus, never chassis; sensors -> Gnd Out only; high-current loads may use chassis
  R216  the ECU power grounds (A25 A34 B25 B34) share one splice with nothing else (N55); same check as R212
  R219  an ECU output that drives a relay is a low-side output (QSG: Aux 1-4 low side only, Aux 5-8 high / low
        selectable): it goes to coil pin 85, and coil pin 86 goes to a fused +12 V source
"""
import re

# --- R212: far-end rules per QSG class -------------------------------------------------------------------
QSG_ENDS = {
    "ground": ("ECU ground pins and battery negative", None),
    "gndout": ("sensor returns", re.compile(r"gnd|ground|return|rtn|\(-\)", re.I)),
    "screen": ("shield drains", re.compile(r"shield|screen|drain", re.I)),
    "rail": ("sensor supply pins", re.compile(r"\+?\s?[58]\s?V|sensor|cam|pedal|cruise|supply", re.I)),
    "power": ("fused +12 V", re.compile(r"\+12|12\s?V|ECU main|diode|fuse", re.I)),
}
NEG_BAR = re.compile(r"NEG bar|battery neg|negative terminal|neg bus", re.I)

# --- R213: device classes on a ground ---------------------------------------------------------------------
SINK_TERMINAL = re.compile(r"ground (stud|ring|point|bolt)|chassis stud|block ground|NEG bar|battery neg|negative terminal", re.I)
ELECTRONICS = re.compile(r"\bLED\b|CAN[- ]?LAMBDA|cluster|RealDash|\bPi\b|CSB3|opto|alarm|valet|shock|status|buck converter|cruise", re.I)
HIGH_CURRENT = re.compile(r"fan|pump|horn|lamp|light|retract|motor|siren|coil|heater|relay|starter|alternator|EHPS|engine|RADLOK|battery", re.I)
PASS_THROUGH = re.compile(r"POWER BUS|RADLOK|BULKHEAD|\bBH-|inline|\bIX-|SENSOR GND BUS", re.I)


def _ends(r):
    return (("from", "to"), ("to", "from"))


def _qsg(ctx, rows, ECU):
    wires = [r for r in rows if r["wire_id"]]
    seen, out, done = set(), [], set()
    for r in wires:
        for s, o in _ends(r):
            conn, pin = r[s + "_conn"], r[s + "_pin"]
            if r[s + "_type"] != "connector" or conn not in ECU or (conn, pin) in seen:
                continue
            seen.add((conn, pin))
            sr = ctx.sot_row(conn, pin)
            if not sr or sr["class"] not in ("ground", "rail", "screen", "power"):
                continue
            kind = "gndout" if sr["net"].startswith("GNDOUT") else sr["class"]
            todo, nodes, ends, visited = [r], set(), [], {id(r)}
            while todo:
                w = todo.pop()
                for e in ("from", "to"):
                    if w[e + "_type"] == "splice":
                        if w[e + "_conn"] in nodes:
                            continue
                        nodes.add(w[e + "_conn"])
                        for x in wires:
                            if id(x) not in visited and w[e + "_conn"] in (x["from_conn"], x["to_conn"]):
                                visited.add(id(x))
                                todo.append(x)
                    elif not (w is r and e == s):
                        ends.append((w, e))
            bad = []
            for w, e in ends:
                desc, t, c, p = w[e + "_desc"], w[e + "_type"], w[e + "_conn"], w[e + "_pin"]
                ok_row = ctx.sot_row(c, p) if t == "connector" and c in ECU else None
                name = w[e + "_conn_name"]
                if kind == "ground":
                    ok = bool((ok_row and ok_row["class"] == "ground") or (t == "terminal" and NEG_BAR.search(name)))
                elif ok_row:
                    ok = ok_row["net"] == sr["net"] or ok_row["class"] == sr["class"]
                else:
                    ok = bool(QSG_ENDS[kind][1].search(desc)) and not re.search(r"chassis|battery", name, re.I)
                if not ok:
                    bad.append("%s %s %s (%s)" % (w["harness"], c, p, (desc or name)[:40]))
            if bad and (kind, frozenset(nodes)) not in done:
                done.add((kind, frozenset(nodes)))
                pins = sorted({"%s %s" % (x[s2 + "_conn"], x[s2 + "_pin"]) for x in wires for s2 in ("from", "to")
                               if x[s2 + "_type"] == "connector" and x[s2 + "_conn"] in ECU and
                               (ctx.sot_row(x[s2 + "_conn"], x[s2 + "_pin"]) or {}).get("net") == sr["net"]})
                rule = "R216" if kind == "ground" else "R212"
                out.append(dict(rule=rule, key=sr["net"], harness=r["harness"],
                                item="%s (%s; first wire %s)" % (sr["net"], ", ".join(pins), r["wire_id"]),
                                text="a %s pin may reach only %s; it also reaches %s" % (
                                    kind, QSG_ENDS[kind][0], "; ".join(sorted(set(bad))[:6]) + (" ..." if len(set(bad)) > 6 else ""))))
    return out


def _dev_class(text):
    if ELECTRONICS.search(text):
        return "electronics"
    if HIGH_CURRENT.search(text):
        return "high-current"
    return "other"


def _ground_classes(ctx, rows, ECU):
    """R213: pair every ground sink terminal with the devices that reach it through splices."""
    wires = [r for r in rows if r["wire_id"]]
    by_splice = {}
    for w in wires:
        for e in ("from", "to"):
            if w[e + "_type"] == "splice":
                by_splice.setdefault(w[e + "_conn"], []).append(w)
    out, seen = [], set()
    for w in wires:
        for e, o in _ends(w):
            if not (w[e + "_type"] == "terminal" and SINK_TERMINAL.search(w[e + "_conn_name"])):
                continue
            sink_name = w[e + "_conn_name"]
            neg = bool(NEG_BAR.search(sink_name))
            # devices behind this sink end
            devices, todo, nodes, visited = [], [(w, o)], set(), {id(w)}
            while todo:
                x, oe = todo.pop()
                if x[oe + "_type"] == "splice":
                    sp = x[oe + "_conn"]
                    if sp in nodes:
                        continue
                    nodes.add(sp)
                    for y in by_splice.get(sp, []):
                        if id(y) in visited:
                            continue
                        visited.add(id(y))
                        for ye in ("from", "to"):
                            if y[ye + "_conn"] == sp:
                                todo.append((y, "to" if ye == "from" else "from"))
                else:
                    devices.append((x, oe))
            for x, oe in devices:
                t, c, p = x[oe + "_type"], x[oe + "_conn"], x[oe + "_pin"]
                name = x[oe + "_conn_name"]
                text = name + " " + x[oe + "_desc"]
                if t == "terminal" and SINK_TERMINAL.search(name):
                    continue           # another stud
                if t == "connector" and c in ECU:
                    continue           # the ECU power grounds are checked as a group by R216 (_qsg)
                cls = _dev_class(x[oe + "_desc"] if (PASS_THROUGH.search(name) or c.startswith(("bh_", "bus_", "ix_", "rl_"))) else text)
                if neg or cls in ("high-current", "other"):
                    continue
                key = "%s:%s" % (x["wire_id"], sink_name[:30])
                if key in seen:
                    continue
                seen.add(key)
                rule, why = "R213", "low-voltage electronics (PCBs, CAN nodes, LEDs) go to the battery-negative bus, never chassis"
                out.append(dict(rule=rule, key=x["wire_id"], harness=x["harness"],
                                item="%s (%s %s: %s)" % (x["wire_id"], c, p, x[oe + "_desc"][:36]),
                                text="%s; it ends on %s" % (why, sink_name[:60])))
    return out


def _owner(ctx, conn):
    n = ctx.node.get(conn)
    return n[0] if n else None



def _relays(ctx, rows, ECU):
    """R219: ECU output -> relay coil pin 85 (low-side); coil pin 86 fed from a fused +12 V source."""
    out = []
    wires = [r for r in rows if r["wire_id"]]
    coil86 = {}
    for r in wires:
        for s, o in _ends(r):
            if r[s + "_type"] == "connector" and r[s + "_conn"].startswith("k_") and r[s + "_pin"] == "86":
                coil86.setdefault(r[s + "_conn"], []).append(r)
    for r in wires:
        for s, o in _ends(r):
            conn, pin = r[s + "_conn"], r[s + "_pin"]
            if r[s + "_type"] != "connector" or conn not in ECU:
                continue
            sr = ctx.sot_row(conn, pin)
            if not sr or sr["dir"] != "out":
                continue
            far_c, far_p = r[o + "_conn"], r[o + "_pin"]
            if not far_c.startswith("k_"):
                continue
            if far_p != "85":
                out.append(dict(rule="R219", key=r["wire_id"], harness=r["harness"], item="%s (%s %s)" % (r["wire_id"], conn, pin),
                                text="ECU output drives relay %s pin %s; a low-side output goes to coil pin 85" % (far_c, far_p)))
            if not re.match(r"(lowside|hilo)", sr["type"]):
                out.append(dict(rule="R219", key=r["wire_id"], harness=r["harness"], item="%s (%s %s)" % (r["wire_id"], conn, pin),
                                text="ECU output type '%s' is not a low-side (QSG: Aux 1-4 low side only, Aux 5-8 high / low) output" % sr["type"]))
            feeds = coil86.get(far_c, [])
            ok = any(re.search(r"bus_sw12|BUS\d-\d|fb_logic|fb_power|splice", x["from_type"] + x["from_conn"] + x["to_conn"] + x["to_type"])
                     for x in feeds)
            if not feeds or not ok:
                out.append(dict(rule="R219", key=r["wire_id"] + "-86", harness=r["harness"], item="%s coil pin 86" % far_c,
                                text="coil pin 86 of the relay an ECU output drives has no wire from a fused +12 V source"))
    return out


# Known violations waiting for the wiring fix (OPEN-ITEMS N55 / N56). Format: "rule:key".
# The fix session deletes an entry when it fixes the wire; --check fails on any finding not listed here and on any
# entry listed here that no longer violates.
PENDING = {
    "R213:w_at_gnd_a1",
    "R213:w_at_gnd_b1",
    "R213:w_at_gnd_b2",
    "R213:w_at_gnd_c1",
    "R213:w_hb_k",
    "R213:w_tl_k",
    "R213:w_tr_k",
}


def findings(ctx, rows, ECU):
    out = []
    out += _qsg(ctx, rows, ECU)
    out += _ground_classes(ctx, rows, ECU)
    out += _relays(ctx, rows, ECU)
    for f in out:
        f["id"] = "%s:%s" % (f["rule"], f["key"])
    return out
