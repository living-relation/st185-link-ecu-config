"""OEM connections are flying leads with an EWD locator, never a modelled OEM housing.

  E1  every registered flying lead is a Loose terminal on its harness
  E2  every flying lead has EWD fields: page, connector, pin, function, method.
      A field not yet known is written "TBD - <reason>"; those are listed, not failed.
  E3  the terminal's signal text carries the EWD page and connector, so the drawing is
      buildable without this file
  E4  no connector is an OEM housing (a part whose number starts "(OEM" or
      "(unspecified - OEM") unless interfaces.json lists it as a real connector the build
      plugs into (the J/B2 dummy headers)

Exit 1 on any finding.
"""
import sys

import model

FIELDS = ("page", "connector", "pin", "function", "method")
reg = model.registry()
ds = model.docs(reg)
bad, tbd = [], []

for fl in reg.get("flyingLeads", []):
    d = ds.get(fl["harness"]) or {}
    t = next((x for x in d.get("terminals", []) if x["id"] == fl["terminal"]), None)
    if not t or t.get("type") != "Loose":
        bad.append("E1 flying lead %s/%s is not a Loose terminal" % (fl["harness"], fl["terminal"]))
        continue
    ewd = fl.get("ewd") or {}
    for k in FIELDS:
        v = str(ewd.get(k) or "").strip()
        if not v:
            bad.append("E2 %s/%s has no EWD %s" % (fl["harness"], fl["terminal"], k))
        elif v.upper().startswith("TBD"):
            tbd.append("%s/%s %s: %s" % (fl["harness"], fl["terminal"], k, v))
    sig = t.get("signal") or ""
    if "EWD" not in sig or str(ewd.get("connector", "")).split(" ")[0] not in sig:
        bad.append("E3 %s/%s signal %r does not carry the EWD page and connector"
                   % (fl["harness"], fl["terminal"], sig))

real = {(r["harness"], r["connector"]) for r in reg.get("realConnectors", [])}
for loom, d in ds.items():
    p = model.parts(d)
    for c in d.get("connectors", []):
        pn = (p.get(c.get("partId")) or {}).get("partNumber", "")
        if pn.startswith(("(OEM", "(unspecified - OEM")) and (loom, c["id"]) not in real:
            bad.append("E4 %s/%s is drawn as an OEM housing (%s) - make it flying leads"
                       % (loom, c["id"], pn))

print("%d flying lead(s) registered, %d EWD field(s) still TBD." % (len(reg.get("flyingLeads", [])), len(tbd)))
for line in tbd:
    print("  TBD " + line)
for line in bad:
    print(line)
print("\n%d OEM endpoint finding(s)." % len(bad))
sys.exit(1 if bad else 0)
