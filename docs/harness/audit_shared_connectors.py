"""Shared connectors are drawn whole in every file that uses them (Daniel, 2026-10-12, binding).

A physical connector used by more than one harness file is listed in interfaces.json
"physicalPartGroups" (today the DRB102 bulkhead: the cabin receptacle on ST185-A-cabin and
-B-cabin, the engine plug on ST185-A-engine and -B-engine). Each file draws the WHOLE
connector - real part, real cavity count, the same designations - and marks the cavities
another file owns Not Connected (harness.design N/C cavity,
https://docs.harness.design/component/connector), with a note naming that file.

  SC1  every member uses the same part (part number and every part field but the id)
  SC2  every member draws the full part: cavities == the part's numberOfCavities, each
       designation once, and the same designation set in every member
  SC3  each designation is live (not N/C) in exactly one member of the group; every other
       member marks it N/C
  SC4  an N/C cavity carries no signal, no contact and no sealing plug (cavityPlugPartId null),
       so the owning file is the only one that counts its contact or plug
  SC5  a file whose connector has N/C cavities has a schematic note saying "see ST185-<owner>"
       for every file that owns some of them

Exit 1 on any finding.
"""
import collections
import json
import sys

import model

reg = model.registry()
docs = model.docs(reg)
bad = []


def part_of(d, c):
    return next((p for p in d.get("connectorParts", []) if p["id"] == c.get("partId")), None)


def strip(p):
    return json.dumps({k: v for k, v in (p or {}).items() if k not in ("id", "configurations")}, sort_keys=True)


for pg, members in reg.get("physicalPartGroups", {}).items():
    if pg.startswith("_"):
        continue
    got = []
    for m in members:
        d = docs.get(m["harness"])
        c = next((x for x in (d or {}).get("connectors", []) if x["id"] == m["connector"]), None)
        if c is None:
            bad.append("SC0 %s: %s has no connector %s" % (pg, m["harness"], m["connector"]))
            continue
        got.append((m["harness"], d, c, part_of(d, c)))
    if not got:
        continue
    ref = got[0]
    for loom, d, c, p in got:
        if p is None:
            bad.append("SC1 %s: %s %s has no part" % (pg, loom, c["id"]))
            continue
        if strip(p) != strip(ref[3]):
            bad.append("SC1 %s: %s %s part %s differs from %s's" % (pg, loom, c["id"], p.get("partNumber"), ref[0]))
        des = [str(cv.get("designation")) for cv in c["cavities"]]
        if len(des) != p.get("numberOfCavities"):
            bad.append("SC2 %s: %s %s draws %d of the part's %s cavities - draw the whole connector"
                       % (pg, loom, c["id"], len(des), p.get("numberOfCavities")))
        dup = [x for x, n in collections.Counter(des).items() if n > 1]
        if dup:
            bad.append("SC2 %s: %s %s repeats designation(s) %s" % (pg, loom, c["id"], ", ".join(sorted(dup))))
        if set(des) != {str(cv.get("designation")) for cv in ref[2]["cavities"]}:
            bad.append("SC2 %s: %s %s designations differ from %s" % (pg, loom, c["id"], ref[0]))
    owner = collections.defaultdict(list)          # designation -> files where it is live
    for loom, d, c, p in got:
        for cv in c["cavities"]:
            if not cv.get("notConnected"):
                owner[str(cv.get("designation"))].append(loom)
    for des in sorted({str(cv.get("designation")) for _, _, c, _ in got for cv in c["cavities"]}, key=lambda s: (len(s), s)):
        if len(owner.get(des, [])) != 1:
            bad.append("SC3 %s: cavity %s is live in %d files (%s) - exactly one owns it, the rest mark it N/C"
                       % (pg, des, len(owner.get(des, [])), ", ".join(owner.get(des, [])) or "none"))
    for loom, d, c, p in got:
        owners = set()
        for cv in c["cavities"]:
            if not cv.get("notConnected"):
                continue
            if cv.get("signal") or cv.get("contactPartId") or cv.get("cavityPlugPartId") is not None:
                bad.append("SC4 %s: %s %s %s is N/C but carries a signal, contact or plug"
                           % (pg, loom, c["id"], cv["id"]))
            owners.update(o for o in owner.get(str(cv.get("designation")), []) if o != loom)
        text = " ".join(n.get("text", "") for n in d.get("schematicNotes", []))
        for o in sorted(owners):
            if "see ST185-%s" % o not in text:
                bad.append("SC5 %s: %s has N/C cavities owned by ST185-%s but no note \"see ST185-%s\""
                           % (pg, loom, o, o))

for line in bad:
    print(line)
print("\n%d shared-connector finding(s)." % len(bad))
sys.exit(1 if bad else 0)
