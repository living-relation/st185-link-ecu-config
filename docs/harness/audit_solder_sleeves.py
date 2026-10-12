"""Every terminated screen has a Raychem SolderSleeve sized to its cable (Daniel, 2026-10-12, binding).

Our Raychem shielded cables have no drain wire, so wherever a cable's screen is terminated a
SolderSleeve shield terminator with a pre-attached drain lead goes on, right behind the
connector (or T-splice) the drain lands on. Drawn the way Daniel's WS-Front example does it:
a splice whose covering is the sleeve, joining the screen and the sleeve's drain lead
(https://docs.harness.design/component/splice, /part/covering/heatshrink).

  SS1  every shielded cable's screen end that is terminated (not floating, not broken off to
       another file) ends at a SolderSleeve splice
  SS2  a sleeve splice has exactly one sleeve covering and joins exactly the screen and one
       drain lead wire whose gauge is the sleeve's lead gauge
  SS3  the sleeve fits the cable: cable jacket OD <= the sleeve's jacket OD max and screen OD
       >= its shield OD min (TE datasheet), and the covering part's min / max diameter carry
       those datasheet values. Sizes live in cable_dimensions.json
  SS4  every shielded cable run has at least one sleeve - a run is the cable plus its
       broken-off continuations in other files (interfaces.json "breaks"); a screen that
       floats at both ends of its whole run is a finding

Exit 1 on any finding.
"""
import collections
import json
import os
import sys

import model

HERE = os.path.dirname(os.path.abspath(__file__))
DIM = json.load(open(os.path.join(HERE, "cable_dimensions.json"), encoding="utf-8"))
SLV = {k: v for k, v in DIM["sleeves"].items() if not k.startswith("_")}
IN = 25.4

reg = model.registry()
ds = model.docs(reg)
brk = model.break_ends(reg)                       # (loom, terminal id) -> break id
bad = []
has_sleeve = {}                                   # (loom, cable id) -> bool
links = collections.defaultdict(set)              # break id -> {(loom, cable id)}


def cable_dims(pn):
    c = DIM["cables"].get(pn)
    if not c:
        return None
    return (c.get("shield_in", c.get("shield_in_min")) * IN, c.get("jacket_in", c.get("jacket_in_min")) * IN)


for loom, d in ds.items():
    P = model.parts(d)
    sl = model.sleeves(d)
    spl = {s["id"]: s for s in d.get("splices", [])}
    conds = list(model.conductors(d))
    for cb in d.get("cables", []):
        cp = P.get(cb.get("partId")) or {}
        sh = cb.get("shield")
        if not cp.get("shielded") or not sh:
            continue
        has_sleeve[(loom, cb["id"])] = False
        for side in ("source", "target"):
            e = sh.get(side)
            if not e:
                continue                            # floats here by rule
            if e.get("handle") == "Terminal" and (loom, e["id"]) in brk:
                links[brk[(loom, e["id"])]].add((loom, cb["id"]))
                continue                            # continues in another file
            if e.get("handle") != "Splice" or e["id"] not in sl:
                bad.append("SS1 %s: %s screen is terminated at %s.%s with no SolderSleeve"
                           % (loom, cb["id"], e["id"], e.get("handle")))
                continue
            has_sleeve[(loom, cb["id"])] = True
            s = spl[e["id"]]
            covs = [P[c]["partNumber"] for c in s.get("coveringIds", []) if c in P]
            sleeve_pns = [c for c in covs if c.startswith(model.SLEEVE_PREFIXES)]
            if len(sleeve_pns) != 1:
                bad.append("SS2 %s: %s carries %d sleeves (%s)" % (loom, s["id"], len(sleeve_pns), ", ".join(covs)))
                continue
            pn = sleeve_pns[0]
            spec = SLV.get(pn)
            if not spec:
                bad.append("SS3 %s: %s sleeve %s has no datasheet sizing in cable_dimensions.json" % (loom, s["id"], pn))
                continue
            others = [c for c, _, _ in conds if c is not sh and s["id"] in
                      ((c.get("source") or {}).get("id"), (c.get("target") or {}).get("id"))]
            leads = [c for c in others if "partId" in c]
            g = ((P.get(leads[0].get("partId")) or {}).get("gauge") or {}).get("value") if len(leads) == 1 else None
            if len(others) != 1 or len(leads) != 1 or g != spec["lead_awg"]:
                bad.append("SS2 %s: %s should join only the %s screen and one %d AWG drain lead, joins %s"
                           % (loom, s["id"], cb["id"], spec["lead_awg"],
                              ", ".join("%s (%s AWG)" % (c.get("id"), ((P.get(c.get("partId")) or {}).get("gauge") or {}).get("value"))
                                        for c in others) or "nothing"))
            cov = next(P[c] for c in s.get("coveringIds", []) if P.get(c, {}).get("partNumber") == pn)
            if ((cov.get("minDiameter") or {}).get("value") != spec["shield_min_mm"]
                    or (cov.get("maxDiameter") or {}).get("value") != spec["jacket_max_mm"]):
                bad.append("SS3 %s: covering part %s diameters %s-%s mm differ from the datasheet %s-%s mm"
                           % (loom, pn, (cov.get("minDiameter") or {}).get("value"),
                              (cov.get("maxDiameter") or {}).get("value"), spec["shield_min_mm"], spec["jacket_max_mm"]))
            dims = cable_dims(cp.get("partNumber"))
            if not dims:
                bad.append("SS3 %s: cable part %s has no dimensions in cable_dimensions.json"
                           % (loom, cp.get("partNumber")))
                continue
            shield, jacket = dims
            if jacket > spec["jacket_max_mm"] or shield < spec["shield_min_mm"]:
                bad.append("SS3 %s: %s on %s (%s, screen %.2f mm, jacket %.2f mm) is outside %s (shield >= %.2f, jacket <= %.2f)"
                           % (loom, s["id"], cb["id"], cp.get("partNumber"), shield, jacket, pn,
                              spec["shield_min_mm"], spec["jacket_max_mm"]))

# SS4 - one sleeve per run, a run joined across broken-off pairs
adj = collections.defaultdict(set)
for members in links.values():
    for a in members:
        adj[a] |= members - {a}
seen = set()
for start in has_sleeve:
    if start in seen:
        continue
    run, todo = {start}, [start]
    while todo:
        for n in adj[todo.pop()] - run:
            run.add(n); todo.append(n)
    seen |= run
    if not any(has_sleeve.get(n) for n in run):
        bad.append("SS4 shielded run %s has no SolderSleeve - its screen is never terminated"
                   % ", ".join("%s/%s" % n for n in sorted(run)))

for line in bad:
    print(line)
print("\n%d solder-sleeve finding(s) over %d shielded cable(s)." % (len(bad), len(has_sleeve)))
sys.exit(1 if bad else 0)
