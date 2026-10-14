"""No wire heavier than 12 AWG on a LOGIC box fuse / relay cavity (Daniel 2026-10-12, F2;
moved from the Eaton RFRM to the custom LOGIC box 2026-10-14, DECISIONS R75).

The LOGIC box (cad/fusebox rev 5, `ST185-FB-LOGIC`) takes mini blade fuses and micro relays,
whose 2.8 / 4.8 / 6.35 mm receptacles carry 12-22 AWG at most (CAD summary bend table: largest
12 AWG). Power comes in on the two strip feeds, M5 bolts into brass standoffs. So:

  F1  every conductor on a LOGIC cavity is 12-22 AWG, except on a strip feed
  F2  a strip feed (designation BUS1 / BUS2) carries a ring / tubular lug for M5, never a
      blade receptacle
  F3  every LOGIC conductor has a known gauge

Anything 10 AWG or heavier goes to the POWER box instead.

Exit 1 on any finding, and when no LOGIC box is drawn at all (the gate must check something).
"""
import sys

import model

STUDS = {"BUS1", "BUS2"}
bad = []
seen = 0
for loom, d in model.docs().items():
    P = model.parts(d)
    box = {c["id"]: c for c in d.get("connectors", [])
           if str((P.get(c.get("partId")) or {}).get("partNumber", "")).startswith("ST185-FB-LOGIC")}
    if not box:
        continue
    seen += len(box)
    cables = {cb["id"]: cb for cb in d.get("cables", [])}
    for cond, cab, screen in model.conductors(d):
        for end in ("source", "target"):
            e = cond.get(end) or {}
            c = box.get(e.get("id"))
            if not c:
                continue
            cv = next((x for x in c.get("cavities", []) if x["id"] == e.get("handle")), {})
            where = "%s: %s %s (%s)" % (loom, c["id"], cv.get("designation", e.get("handle")), cond["id"])
            part = P.get(cables[cab].get("partId")) if cab else P.get(cond.get("partId"))
            g = ((part or {}).get("gauge") or {}).get("value")
            if cab or g is None:
                bad.append("F3 %s: gauge unknown" % where)
                continue
            if cv.get("designation") in STUDS:
                ct = P.get(cv.get("contactPartId")) or {}
                if "M5" not in str(ct.get("description", "")):
                    bad.append("F2 %s: strip feed needs an M5 lug, has %r" % (where, ct.get("partNumber")))
            elif not 12 <= g <= 22:
                bad.append("F1 %s: %s AWG - the LOGIC box takes 12-22 AWG only; move it to the POWER box" % (where, g))
if not seen:
    bad.append("F0 no LOGIC box (part ST185-FB-LOGIC) in any drawing")

for b in bad:
    print(b)
print("\n%d LOGIC box gauge finding(s)." % len(bad))
sys.exit(1 if bad else 0)
