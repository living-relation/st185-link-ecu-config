"""One physical thing, one owner.

  O1  every file in rebuild/ is a harness in interfaces.json, and every listed file exists
  O2  every conductor id (wire, core, screen) is unique across all drawings - a section of
      copper is drawn and built once, by one harness
  O3  a connector drawn with a real part on more than one drawing has exactly one copy that
      is not excludeFromBom, and every copy names the same part
  O4  every cp_xref dummy is listed in interfaces.json "references" with the harness that
      really owns the connector and the reason - no unexplained cross-harness conductor
  O5  every registered real connector exists with a real part
  O6  a device endpoint terminal is Loose and claims no part

Exit 1 on any finding.
"""
import collections
import os
import sys

import model

reg = model.registry()
bad = []

files = set(f for f in os.listdir(model.REB) if f.endswith(".harness"))
listed = set(model.harness_files(reg).values())
for f in sorted(files - listed):
    bad.append("O1 %s is in rebuild/ but not in interfaces.json" % f)
for f in sorted(listed - files):
    bad.append("O1 interfaces.json lists %s, which does not exist" % f)

ds = model.docs(reg)
refs = {(x["harness"], x["connector"]): x for x in reg.get("references", [])}
owner = collections.defaultdict(list)
copies = collections.defaultdict(list)
for loom, d in ds.items():
    parts = model.parts(d)
    for cond, cable, screen in model.conductors(d):
        owner[cond["id"]].append(loom)
    for c in d.get("connectors", []):
        if model.is_xref(c):
            ref = refs.pop((loom, c["id"]), None)
            if not ref or not ref.get("reason") or ref.get("realOn") not in ds:
                bad.append("O4 %s draws cross-reference %s with no registered owner and reason"
                           % (loom, c["id"]))
            continue
        if c.get("partId"):
            copies[c["id"]].append((loom, c.get("partId"), bool(c.get("excludeFromBom"))))

for cid, looms in sorted(owner.items()):
    if len(looms) > 1:
        bad.append("O2 conductor %s is drawn on %s" % (cid, ", ".join(looms)))

for cid, cc in sorted(copies.items()):
    if len(cc) < 2:
        continue
    counted = [c for c in cc if not c[2]]
    if len(counted) != 1:
        bad.append("O3 %s is drawn on %s with %d copies counted (want 1)"
                   % (cid, ", ".join(c[0] for c in cc), len(counted)))
    if len({c[1] for c in cc}) > 1:
        bad.append("O3 %s names different parts: %s"
                   % (cid, ", ".join("%s=%s" % (c[0], c[1]) for c in cc)))

for rc in reg.get("realConnectors", []):
    d = ds.get(rc["harness"])
    c = next((x for x in (d or {}).get("connectors", []) if x["id"] == rc["connector"]), None)
    if not c or model.is_xref(c) or not c.get("partId"):
        bad.append("O5 real connector %s/%s is missing or has no part"
                   % (rc["harness"], rc["connector"]))

for ep in reg.get("endpoints", []):
    d = ds.get(ep["harness"]) or {}
    terms = {t["id"]: t for t in d.get("terminals", [])}
    for tid in ep["terminals"].values():
        t = terms.get(tid)
        if not t:
            bad.append("O6 endpoint %s terminal %s is not on %s" % (ep["id"], tid, ep["harness"]))
        elif t.get("type") != "Loose" or t.get("partId"):
            bad.append("O6 endpoint %s terminal %s must be Loose with no part" % (ep["id"], tid))

for (loom, cid) in sorted(refs):
    bad.append("O4 interfaces.json lists reference %s/%s, which is not drawn" % (loom, cid))

print("registered cross-references: %d" % len(reg.get("references", [])))
for line in bad:
    print(line)
print("\n%d ownership finding(s)." % len(bad))
sys.exit(1 if bad else 0)
