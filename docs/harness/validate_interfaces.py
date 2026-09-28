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

print("%d inline interface(s) declared." % len(reg.get("interfaces", [])))
for line in bad:
    print(line)
print("\n%d interface finding(s)." % len(bad))
sys.exit(1 if bad else 0)
