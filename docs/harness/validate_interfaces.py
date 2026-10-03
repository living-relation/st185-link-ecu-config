"""Every inline interface is a real connector pair that ends one harness and starts the next.

  I1  interface ids are unique
  I2  exactly two halves, on two different harnesses, one `source` and one `receiving`
  I3  both halves exist as real connectors (a real part, not a cross-reference)
  I4  the two parts are opposite genders
  I5  both halves have the same cavity ids, and each cavity has the same signal text on both
  I6  every declared pin is a cavity of the connector
  I7  a cavity is wired on both halves or on neither
  I8  a wired cavity has a contact, an unwired cavity a sealing plug (from the cavity or the
      part's default configuration)
  I9  pin for pin, the same circuit: when a cavity's label (on either half, or the
      registry's pin note) names an ECU pin ("ECU-B B20", "SHIELD_B (B17)", "-> B24"), the
      net through that cavity reaches that ECU pin - and no cavity's net reaches an ECU pin
      that a DIFFERENT cavity of the same pair names (catches crossed / swapped pins)
  I10 a cavity left unwired on both halves is an explicit spare: its label says "spare" (or
      "plug") on both halves
  The same I7 / I9 / I10 rules also cover connector pairs mated inside one drawing
  (interfaces.json "inFileMates", e.g. IX_APS).

Exit 1 on any finding.
"""
import collections
import sys

import model

reg = model.registry()
ds = model.docs(reg)
bad = []

seen = collections.Counter(ix["id"] for ix in reg.get("interfaces", []))
for k, n in seen.items():
    if n > 1:
        bad.append("I1 interface %s is declared %d times" % (k, n))


def wired(h, cid):
    """Cavities wired on this half, on its harness and on every harness listed in
    alsoDrawnOn (a receiving half whose pins belong to both ECU letter looms)."""
    out = set()
    for loom in [h["harness"]] + h.get("alsoDrawnOn", []):
        for cond, cable, screen in model.conductors(ds.get(loom) or {}):
            for e in (cond.get("source") or {}, cond.get("target") or {}):
                if e.get("id") == cid:
                    out.add(e.get("handle"))
    return out


for ix in reg.get("interfaces", []):
    hs = ix["halves"]
    if len(hs) != 2 or hs[0]["harness"] == hs[1]["harness"] \
            or sorted(h["role"] for h in hs) != ["receiving", "source"]:
        bad.append("I2 %s needs two halves on two harnesses, one source and one receiving" % ix["id"])
        continue
    sides = []
    for h in hs:
        d = ds.get(h["harness"])
        c = next((x for x in (d or {}).get("connectors", []) if x["id"] == h["connector"]), None)
        if not c or model.is_xref(c) or not c.get("partId"):
            bad.append("I3 %s half %s/%s is missing or has no real part"
                       % (ix["id"], h["harness"], h["connector"]))
            break
        p = model.parts(d)
        sides.append((h, c, p, d))
    if len(sides) != 2:
        continue
    (ha, ca, pa, da), (hb, cb, pb, db) = sides
    ga = (pa.get(ca["partId"]) or {}).get("gender")
    gb = (pb.get(cb["partId"]) or {}).get("gender")
    if not ga or ga == gb:
        bad.append("I4 %s halves are %s / %s - they must be opposite genders" % (ix["id"], ga, gb))
    sa = {x["id"]: (x.get("signal") or "") for x in ca["cavities"]}
    sb = {x["id"]: (x.get("signal") or "") for x in cb["cavities"]}
    if set(sa) != set(sb):
        bad.append("I5 %s cavity sets differ: %s vs %s" % (ix["id"], sorted(sa), sorted(sb)))
    for cav in sorted(set(sa) & set(sb)):
        if sa[cav] != sb[cav]:
            bad.append("I5 %s %s is %r on %s but %r on %s"
                       % (ix["id"], cav, sa[cav], ha["harness"], sb[cav], hb["harness"]))
    for pin in ix.get("pins", {}):
        if pin not in sa:
            bad.append("I6 %s declares pin %s, which %s does not have" % (ix["id"], pin, ca["id"]))
    wa, wb = wired(ha, ca["id"]), wired(hb, cb["id"])
    for cav in sorted(wa ^ wb):
        side = ha["harness"] if cav in wa else hb["harness"]
        bad.append("I7 %s %s is wired on %s only" % (ix["id"], cav, side))
    for (h, c, p, d), w in (((ha, ca, pa, da), wa), ((hb, cb, pb, db), wb)):
        cfg = ((p.get(c["partId"]) or {}).get("configurations") or [{}])[0]
        for x in c["cavities"]:
            ct = x.get("contactPartId") or (cfg.get("contactPartId") if "cavityPlugPartId" not in x else None)
            pl = x.get("cavityPlugPartId") or (cfg.get("cavityPlugPartId") if "contactPartId" not in x else None)
            if x["id"] in w and not ct:
                bad.append("I8 %s/%s %s is wired but has no contact" % (h["harness"], c["id"], x["id"]))
            if x["id"] not in w and not pl:
                bad.append("I8 %s/%s %s is unused but has no sealing plug" % (h["harness"], c["id"], x["id"]))

# ---- I9 / I10: pin-for-pin circuits (added 2026-10-03, Daniel) -----------------------
import re

ECU_PIN = re.compile(r"(?<![A-Za-z0-9_])([AB])\s?(\d{1,2})(?![0-9])")
graph = model.Graph(reg, ds)
THROUGH = ("SP", "BH", "IX", "BRK")


# ECU rails named in labels without a pin number: the label must reach ONE of the SoT pins
# with that channel name ("+5V" -> A32 +5V Out; "Gnd Out" -> A24 or B22).
RAILS = {}
for r in model.sot_rows():
    if r["owner"] == "ECU" and r["channel"] in ("+5V Out", "Gnd Out", "+8V Out"):
        RAILS.setdefault(r["channel"], set()).add(("ECU", r["conn"], r["pin"]))
RAIL_WORDS = (("+5V Out", re.compile(r"\+5\s?V(?![0-9])", re.I)),
              ("+8V Out", re.compile(r"\+8\s?V(?![0-9])", re.I)),
              ("Gnd Out", re.compile(r"\bGnd Out\b", re.I)))


def named_pins(*texts):
    """ECU pins a label names, as graph nodes. Only text after an arrow or inside
    parentheses counts ("-> ECU-B B20", "SHIELD_B (B17)"), so part numbers and
    harness names never match."""
    out = set()
    for t in texts:
        for frag in re.findall(r"->([^,;]*)|\(([^)]*)\)", t or ""):
            for letter, num in ECU_PIN.findall(" ".join(frag)):
                out.add(("ECU", "ecu_" + letter.lower(), letter.lower() + num))
    return out


def named_rails(*texts):
    return {ch for ch, rx in RAIL_WORDS for t in texts if rx.search(t or "")}


def reached(node):
    net = graph.reach(node, stop=lambda m: m[0] not in THROUGH)
    return {m for m in net if m[0] == "ECU"}


def pin_rules(name, node_of, cavs, labels, note):
    """cavs: cavity ids; labels: cav -> [label on each half]; node_of: cav -> graph node."""
    names = {cv: named_pins(note.get(cv, ""), *labels[cv]) for cv in cavs}
    for cv in cavs:
        node = node_of(cv)
        if node not in graph.adj:
            if not all(re.search(r"spare|plug", l or "", re.I) for l in labels[cv]):
                bad.append("I10 %s %s is unwired but not labelled spare on both halves: %s"
                           % (name, cv, labels[cv]))
            continue
        got = reached(node)
        for ch in sorted(named_rails(note.get(cv, ""), *labels[cv])):
            if not (RAILS.get(ch, set()) & got):
                bad.append("I9 %s %s is labelled %r but its net reaches no ECU %s pin (%s)"
                           % (name, cv, labels[cv][0], ch,
                              "/".join(sorted(p[2].upper() for p in RAILS.get(ch, ())))))
        for want in sorted(names[cv]):
            if want not in got:
                bad.append("I9 %s %s is labelled %s but its net never reaches ECU %s"
                           % (name, cv, labels[cv][0], want[2].upper()))
        for other in cavs:
            if other != cv:
                for clash in sorted(names[other] & got):
                    bad.append("I9 %s %s reaches ECU %s, which %s names - crossed pins?"
                               % (name, cv, clash[2].upper(), other))


for ix in reg.get("interfaces", []):
    hs = ix["halves"]
    if len(hs) != 2:
        continue
    cons = []
    for h in hs:
        d = ds.get(h["harness"]) or {}
        c = next((x for x in d.get("connectors", []) if x["id"] == h["connector"]), None)
        if c:
            cons.append(c)
    if len(cons) != 2:
        continue
    cavs = [x["id"] for x in cons[0]["cavities"]]
    lab = {cv: [next((x.get("signal") or "" for x in c["cavities"] if x["id"] == cv), "")
                for c in cons] for cv in cavs}
    pin_rules(ix["id"], lambda cv, i=ix["id"]: ("IX", i, cv), cavs, lab, ix.get("pins", {}))

for m in reg.get("inFileMates", []):
    d = ds.get(m["harness"]) or {}
    mate = next((x for x in d.get("mates", []) if x["id"] == m["mate"]), None)
    if not mate:
        bad.append("I9 inFileMate %s/%s is not drawn" % (m["harness"], m["mate"]))
        continue
    cons = [next((x for x in d.get("connectors", []) if x["id"] == k), None)
            for k in (mate["sourceId"], mate["targetId"])]
    if None in cons:
        bad.append("I9 inFileMate %s/%s names a connector that is not drawn" % (m["harness"], m["mate"]))
        continue
    key = "%s:%s" % (m["harness"], m["mate"])
    # I7 for in-file pairs: wired on both halves or neither
    wired_by = []
    for c in cons:
        w = set()
        for cond, cable, screen in model.conductors(d):
            for e in (cond.get("source") or {}, cond.get("target") or {}):
                if e.get("id") == c["id"]:
                    w.add(e.get("handle"))
        wired_by.append(w)
    for cv in sorted(wired_by[0] ^ wired_by[1]):
        bad.append("I7 %s %s is wired on %s only" % (key, cv, cons[0]["id"] if cv in wired_by[0] else cons[1]["id"]))
    cavs = [x["id"] for x in cons[0]["cavities"]]
    lab = {cv: [next((x.get("signal") or "" for x in c["cavities"] if x["id"] == cv), "")
                for c in cons] for cv in cavs}
    pin_rules(key, lambda cv, k=key: ("IX", k, cv), cavs, lab, {})

print("%d inline interface(s) declared." % len(reg.get("interfaces", [])))
for line in bad:
    print(line)
print("\n%d interface finding(s)." % len(bad))
sys.exit(1 if bad else 0)
