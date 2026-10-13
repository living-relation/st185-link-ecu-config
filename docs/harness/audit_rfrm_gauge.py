"""No wire heavier than 12 AWG on an Eaton RFRM cavity (Daniel 2026-10-12, F2).

The Eaton Bussmann Series 15400 RFRM (`15401-*`) takes #12-22 AWG wire in its fuse and
relay cavities (Aptiv / Delphi 280 Series terminals). Power comes in on the bussed
version's input studs, M8 x 1.25, 100 A per bus bar (Eaton Series 15400 RFRM data sheet,
https://www.eaton.com/us/en-us/catalog/emobility/series-15400-rfrm.html). So:

  F1  every conductor on an RFRM cavity is 12-22 AWG, except on a bus input stud
  F2  a bus input stud (designation BUS1 / BUS2) carries an M8 ring lug, never a cavity
      terminal
  F3  every RFRM conductor has a known gauge

Anything 10 AWG or heavier goes to an MTA Maxi position or the LMI instead.

Exit 1 on any finding.
"""
import sys

import model

STUDS = {"BUS1", "BUS2"}
bad = []
for loom, d in model.docs().items():
    P = model.parts(d)
    rfrm = {c["id"]: c for c in d.get("connectors", [])
            if str((P.get(c.get("partId")) or {}).get("partNumber", "")).startswith("15401")}
    if not rfrm:
        continue
    cables = {cb["id"]: cb for cb in d.get("cables", [])}
    for cond, cab, screen in model.conductors(d):
        for end in ("source", "target"):
            e = cond.get(end) or {}
            c = rfrm.get(e.get("id"))
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
                if "M8" not in str(ct.get("partNumber", "")):
                    bad.append("F2 %s: bus input stud needs an M8 ring lug, has %r" % (where, ct.get("partNumber")))
            elif not 12 <= g <= 22:
                bad.append("F1 %s: %s AWG - the RFRM takes 12-22 AWG only; move it to an MTA Maxi or the LMI" % (where, g))

for b in bad:
    print(b)
print("\n%d RFRM gauge finding(s)." % len(bad))
sys.exit(1 if bad else 0)
