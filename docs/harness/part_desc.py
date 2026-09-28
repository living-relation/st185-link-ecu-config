"""Standard part descriptions: a part's description describes the part and nothing else.

Format: upper case, comma separated, general to specific -
    NOUN, TYPE, SERIES / FAMILY, KEY SPECS (positions, gender, size, gauge range,
    rating, material / plating, colour, seal, standard)
Never: where or how the part is used, a device, sensor, signal, net, pin, circuit,
harness, loom, bulkhead, group or layer, what it mates with, stock or quantity owned,
dates, plan references, assumptions or TBD reasoning. Those belong on the drawing
(cavity signals, labels, notes), not on the part.

    python docs/harness/part_desc.py          # check every rebuild/ drawing
    python docs/harness/part_desc.py --fix    # rewrite descriptions to the standard

Wires, cables and resistors are generated from the part's own fields, so every one
of them reads the same; other parts are checked against the banned-content rules.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "rebuild")
MAX_LEN = 170

BANNED = [
    (r" - |\s[\u2013\u2014]\s?", "a dash clause (usage note)"),
    (r"->|<-", "an arrow (circuit path)"),
    (r";", "a ';' clause"),
    (r"\bOWNED\b|\bQTY\b|\bIN STOCK\b", "stock / quantity"),
    (r"\b20\d\d-\d\d-\d\d\b", "a date"),
    (r"\bPLAN\b|\bSEE\b|\bNEED-TO-BUY\b", "a document reference"),
    (r"\bECU\b|\bECUMASTER\b|\bCSB3\b|\bST185\b|\bHARNESS\b|\bLOOM\b|\bBULKHEAD\b", "the harness it is used in"),
    (r"\bSENSOR\b|\bSIGNAL\b|\bNET\b|\bCIRCUIT\b|\bDEVICE\b|\bGROUP\b|\bLAYER\b", "use / net / group"),
    (r"\bFEEDS?\b|\bMATES?\b|\bUSED\b|\bFOR THE\b|\bREPLACES\b|\bASSUMED\b|\bASSUMPTION\b", "a use or relation"),
    (r"\b(FAN|PUMP|INJECTOR|IGNITION COIL|THROTTLE|ALTERNATOR|STARTER|HEADLIGHT|RADIATOR|CRUISE|KNOCK|LAMBDA|VRC|CLUSTER)\b", "the device it serves"),
]
EXEMPT = {  # (part collection, word) a part may carry because it IS that thing
    ("groupParts", "SENSOR"), ("groupParts", "PUMP"), ("groupParts", "THROTTLE"),
    ("groupParts", "ECU"), ("groupParts", "LAMBDA"), ("groupParts", "CLUSTER"),
}

OVERRIDES = {  # by part number: parts whose own spec text is more than the first clause
    "4-1904124-2": "RELAY, PLUG-IN, MICRO ISO, TE V23074-A1001-A402, 1 FORM A, 25 A, 12 VDC COIL 119 OHM, 680 OHM PARALLEL RESISTOR",
    "1-1414147-0": "RELAY, PLUG-IN, MAXI ISO F7, TE V23134-J0052-X429, 1 FORM A, 70 A AT 23 C / 50 A AT 85 C, 12 VDC COIL 90 OHM, 680 OHM PARALLEL RESISTOR",
    "1-1393304-0": "RELAY, PLUG-IN, MAXI ISO F7, TE V23134-J1052-X281, 1 FORM A, 70 A AT 23 C / 50 A AT 85 C, 12 VDC COIL 90 OHM, 560 OHM PARALLEL RESISTOR, MOUNTING BRACKET",
    "7-1904094-9": "RELAY, PLUG-IN, MAXI ISO F7, TE V23134-J0052-X439, 1 FORM A, 70 A AT 23 C / 50 A AT 85 C, 12 VDC COIL 91 OHM, DIODE SUPPRESSED, CATHODE ON 86",
    "V23132-A2001-B200": "RELAY, HIGH CURRENT, TE HCR 150, IP67, 1 FORM A, 130 A AT 85 C, 12 VDC COIL 37 OHM 3.9 W, PARALLEL RESISTOR, STUD LOAD TERMINALS",
    "1-1355844-1": "CONTACT, BUSBAR, CUNISI PRE-TINNED, 4.0-6.0 MM2 (10 AWG)",
    "MR-S ZZW30 EHPS pump - A 90980-12068 / B 90980-10897 / C 90980-10942":
        "CONNECTOR SET, TOYOTA, 3 HOUSINGS: 90980-12068 2 POS, 90980-10897 6 POS, 90980-10942 2 POS",
    "TBD - A/C coolant temperature switch connector": "CONNECTOR, 2 POS, TYPE TBD",
}

COLORS = {"Light Yellow": "LIGHT YELLOW", "Light Green": "LIGHT GREEN", "Light Blue": "LIGHT BLUE",
          "Light Gray": "LIGHT GRAY", "Gray": "GRAY"}
CODES = {"BLK": "BLACK", "WHT": "WHITE", "RED": "RED", "ORG": "ORANGE", "YEL": "YELLOW", "GRN": "GREEN",
         "BLU": "BLUE", "VIO": "VIOLET", "BRN": "BROWN", "PNK": "PINK", "GRY": "GRAY"}


def colour(p):
    c = COLORS.get(p.get("color"), (p.get("color") or "").upper())
    if p.get("stripeColor"):
        c += "/" + COLORS.get(p["stripeColor"], p["stripeColor"].upper())
    return c


def gauge_txt(g, pn=""):
    m = re.search(r"-(\d+/0)-", pn or "")
    if m:
        return "%s AWG" % m.group(1)
    if not g:
        m = re.search(r"-1C(\d+)-", pn or "")
        return "%s AWG" % m.group(1) if m else "GAUGE TBD"
    return "%s %s" % (g["value"], "MM2" if g.get("unit") == "Metric" else "AWG")


def wire_desc(p):
    pn = (p.get("partNumber") or "").upper()
    if "DRAIN" in pn:
        return "WIRE, DRAIN, %s, TINNED COPPER, CLEAR ETFE SLEEVE" % gauge_txt(p.get("gauge"), pn)
    if pn.startswith("BC-"):
        return "CABLE, BATTERY, %s, %s, FINE-STRAND COPPER, SAE J1127 SGX 125 C OR EQUIV" % (
            gauge_txt(p.get("gauge"), pn), colour(p))
    if not pn.startswith("EW-"):
        return None
    c = colour(p)
    m = re.match(r"EW-1C\d+-([A-Z]+)-([A-Z]+)$", pn)
    if not p.get("stripeColor") and m and m.group(1) in CODES and m.group(2) in CODES:
        c = "%s/%s" % (CODES[m.group(1)], CODES[m.group(2)])
    return "WIRE, ELECTRICAL, %s, %s, ETFE (TEFZEL) INSULATED, 150 C, M22759/16 OR EQUIV" % (
        gauge_txt(p.get("gauge"), pn), c)


def cable_desc(p):
    cores = p.get("cores") or []
    gs = {gauge_txt(c.get("gauge")) for c in cores}
    m = re.search(r"\dC-?(\d\d)\b", p.get("partNumber") or "")
    if gs == {"GAUGE TBD"} and m:
        gs = {"%s AWG" % m.group(1)}
    tp = any(c.get("twistedWithNext") for c in cores)
    kind = "SHIELDED" if p.get("shielded") else "UNSHIELDED"
    if not cores:
        return None
    s = "CABLE, %s, %d CONDUCTOR%s, %s" % (kind, len(cores), " TWISTED PAIR" if tp and len(cores) == 2 else "",
                                         "/".join(sorted(gs)) or "GAUGE TBD")
    if len(cores) == 1 and cores[0].get("color"):
        s += ", " + colour(cores[0])
    if p.get("shielded"):
        s += ", FOIL + TINNED COPPER BRAID"
    return s + ", JACKETED"


def resistor_desc(p):
    pn = (p.get("partNumber") or "").upper().replace("OHM", "R")
    m = re.match(r"\s*([\d.]+)\s*([RKM]?)\s*([\d/.]+\s*W)", pn)
    if not m:
        return None
    v, mult, w = m.groups()
    unit = {"": "OHM", "R": "OHM", "K": "KOHM", "M": "MOHM"}[mult]
    old = (p.get("description") or "").upper()
    kind = "WIREWOUND" if "WIREWOUND" in old else "METAL FILM" if "METAL FILM" in old else None
    tol = re.search(r"\b(\d+) PCT\b", old)
    parts = ["RESISTOR", "FIXED"] + ([kind] if kind else []) + ["%s %s" % (v, unit)] + \
        (["%s PCT" % tol.group(1)] if tol else []) + [re.sub(r"\s*W$", " W", w.strip())]
    return ", ".join(parts)


GENERATED = {"wireParts": wire_desc, "cableParts": cable_desc, "resistorParts": resistor_desc}


def trim(desc):
    """Keep the part's own spec text: cut usage clauses and stock notes."""
    d = desc or ""
    d = re.split(r" - |\s[\u2013\u2014]\s?|;|\s->|\s<-", d)[0]
    d = re.sub(r"\s*\((?:[^)]*\b(?:OWNED|qty|assumed|plan|see)\b[^)]*)\)", "", d, flags=re.I)
    d = re.sub(r"\s*,\s*OWNED\b.*$", "", d, flags=re.I)
    return re.sub(r"\s+", " ", d).strip(" ,.").upper()


def standard(kind, p):
    if p.get("partNumber") in OVERRIDES:
        return OVERRIDES[p["partNumber"]]
    f = GENERATED.get(kind)
    if f:
        s = f(p)
        if s:
            return s
    return trim(p.get("description"))


def problems(kind, p):
    d = p.get("description") or ""
    out = []
    if not d.strip():
        out.append("no description")
    if d != d.upper():
        out.append("not upper case")
    if len(d) > MAX_LEN:
        out.append("longer than %d characters" % MAX_LEN)
    for pat, why in BANNED:
        for m in re.finditer(pat, d.upper()):
            if (kind, m.group(0).strip()) not in EXEMPT:
                out.append("has %s (%r)" % (why, m.group(0).strip()))
                break
    s = standard(kind, p) if (kind in GENERATED or p.get("partNumber") in OVERRIDES) else None
    if s and s != d:
        out.append("is not the standard text %r" % s)
    return out


def check_doc(d):
    bad = []
    for kind, parts in d.items():
        if not kind.endswith("Parts"):
            continue
        for p in parts:
            for why in problems(kind, p):
                bad.append("%s %s: description %s" % (kind, p.get("id"), why))
    return bad


def main():
    fix = "--fix" in sys.argv
    total = 0
    for fn in sorted(f for f in os.listdir(SRC) if f.endswith(".harness")):
        path = os.path.join(SRC, fn)
        raw = open(path, "rb").read()
        d = json.loads(raw.decode("utf-8"))
        if fix:
            for kind, parts in d.items():
                if kind.endswith("Parts"):
                    for p in parts:
                        p["description"] = standard(kind, p)
            s = json.dumps(d, indent=2, ensure_ascii=False) + ("\n" if raw.endswith(b"\n") else "")
            if b"\r\n" in raw:
                s = s.replace("\r\n", "\n").replace("\n", "\r\n")
            open(path, "wb").write(s.encode("utf-8"))
        bad = check_doc(d)
        total += len(bad)
        print("%-30s %s" % (fn, "OK" if not bad else "%d PROBLEMS" % len(bad)))
        for b in bad:
            print("      " + b)
    print("\n%d part-description problem(s)." % total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
