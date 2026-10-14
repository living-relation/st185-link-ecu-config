"""Ident bands - colour bands that name each circuit on the wire ends (DECISIONS R87).

harness.design draws a wire's `identColors` as colour bands along the wire
(https://docs.harness.design/component/wire#assigning-idents); on the car they are short
RNF-100 heat-shrink bands at both ends of the wire. The circuit each wire belongs to is not a
field the app accepts on a wire, so it lives in `interfaces.json` "identBands":

    "identBands": {"<harness>": {"<CIRCUIT>": {"bands": ["Blue", "Yellow"], "wires": [ids]}}}

A harness listed there has the scheme applied, and then every conductor in it must be listed.

  I1  identColors use the palette only (Blue, Yellow, White), 1 to 4 bands
  I2  a listed harness lists every conductor once; each wire's identColors equal its circuit's
      bands, except a wire 6 AWG or heavier, which carries none (no stock band fits it); a
      circuit with bands: [] is one whose wires are all that heavy
  I3  within one harness no two circuits share a band code
  I4  a circuit name has one band code in every harness
  I5  a broken-off pair (interfaces.json "breaks") carries one circuit on both sections, once
      both harnesses are listed
  I6  a wire in an unlisted harness carries no identColors (apply the scheme by listing it)

Exit 1 on any finding.
"""
import json
import os
import sys

import model

PALETTE = ("Blue", "Yellow", "White")   # RNF-100 colours stocked in both band sizes, seen on red / black
MAX_BANDS = 4
BAND_MM = 6            # one band, cut from the stick
STICK_MM = 1200        # RNF-100 4 ft stick
BANDS_PER_STICK = 180  # 200 cuts per stick less 10 % waste
# band stock by wire size: (heaviest AWG it fits, lightest AWG, size code, expanded, recovered mm)
SIZES = (("3/32", 14, 20, 2.4, 1.2), ("3/16", 8, 12, 4.8, 2.4))
DIGIT = {"Blue": "6", "Yellow": "4", "White": "9"}


def band_part(colour, size):
    return "RNF-100-%s-%s-STK" % (size, DIGIT[colour])


def awg(w, parts):
    """Wire gauge in AWG, or None when it is not an AWG wire (Metric = heavy battery cable)."""
    g = (parts.get(w.get("partId")) or {}).get("gauge") or {}
    if g.get("unit") == "AWG":
        return g.get("value")
    return None if g else 20


def band_size(w, parts):
    """The band stock size for this wire, or None when no band fits (6 AWG and heavier)."""
    a = awg(w, parts)
    for size, heavy, light, _, _ in SIZES:
        if a is not None and heavy <= a <= light:
            return size
    return None


def registry_wires(reg):
    """(harness, wire) -> (circuit, bands)."""
    out = {}
    for h, circuits in (reg.get("identBands") or {}).items():
        for name, c in circuits.items():
            for wid in c.get("wires", []):
                out[(h, wid)] = (name, list(c.get("bands", [])))
    return out


def main():
    reg = model.registry()
    files = model.harness_files(reg)
    ib = reg.get("identBands") or {}
    listed = registry_wires(reg)
    bad = []
    code_of = {}
    for h in sorted(ib):
        if h not in files:
            bad.append("I2 identBands lists %s, which is not a registered harness" % h)
            continue
        seen = {}
        for name, c in ib[h].items():
            b = tuple(c.get("bands", []))
            if b:
                if b in seen:
                    bad.append("I3 %s: circuits %s and %s share bands %s" % (h, seen[b], name, "-".join(b)))
                seen[b] = name
            if name in code_of and code_of[name][1] != b:
                bad.append("I4 circuit %s is %s on %s but %s on %s" % (
                    name, "-".join(code_of[name][1]) or "no bands", code_of[name][0], "-".join(b) or "no bands", h))
            code_of.setdefault(name, (h, b))
    for h, fn in sorted(files.items()):
        d = model.load(fn)
        parts = model.parts(d)
        ids = set()
        for w, cable, screen in model.conductors(d):
            ic = w.get("identColors") or []
            ids.add(w["id"])
            if ic and (len(ic) > MAX_BANDS or any(c not in PALETTE for c in ic)):
                bad.append("I1 %s: %s bands %s - use 1-%d of %s" % (h, w["id"], ic, MAX_BANDS, ", ".join(PALETTE)))
            if h not in ib:
                if ic:
                    bad.append("I6 %s: %s has identColors but %s is not in interfaces.json identBands" % (h, w["id"], h))
                continue
            if (h, w["id"]) not in listed:
                bad.append("I2 %s: %s is in no identBands circuit" % (h, w["id"]))
                continue
            name, b = listed[(h, w["id"])]
            want = b if band_size(w, parts) else []
            if ic != want:
                bad.append("I2 %s: %s identColors %s but circuit %s wants %s%s" % (
                    h, w["id"], ic, name, want, "" if want or not b else " (6 AWG or heavier: no band fits)"))
            if not b and band_size(w, parts) is not None:
                bad.append("I2 %s: %s has no bands but a band fits it (circuit %s)" % (h, w["id"], name))
        if h in ib:
            n = {}
            for name, c in ib[h].items():
                for wid in c.get("wires", []):
                    n[wid] = n.get(wid, 0) + 1
                    if wid not in ids:
                        bad.append("I2 %s: identBands circuit %s lists %s, which is not a wire" % (h, name, wid))
            bad += ["I2 %s: %s is listed %d times" % (h, wid, k) for wid, k in sorted(n.items()) if k > 1]
    # I5: the wire at each end of a broken-off pair
    at = {}
    for h, fn in files.items():
        if h not in ib:
            continue
        for w, _, _ in model.conductors(model.load(fn)):
            for e in (w.get("source"), w.get("target")):
                if e and (h, w["id"]) in listed:
                    at[(h, e.get("id"))] = listed[(h, w["id"])][0]
    for br in reg.get("breaks", []):
        names = {at.get((e["harness"], e["terminal"])) for e in br["ends"]}
        if None not in names and len(names) > 1:
            bad.append("I5 break %s: circuits %s on its two sections" % (br["id"], " / ".join(sorted(names))))
    print("ident bands: %d harness(es) applied: %s" % (len(ib), ", ".join(sorted(ib)) or "none"))
    for line in bad:
        print(line)
    print("\n%d ident-band finding(s)." % len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
