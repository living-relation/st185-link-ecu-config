"""The part library travels with the harness files (Daniel, 2026-10-12).

docs/harness/rebuild/ST185.harnesslib is the harness.design local part library (same JSON as a
.harness file, part arrays only, version 0.9). harness.design treats parts with the same part
number as the same part, so the library must hold exactly what the drawings use.

  H1  every part a drawing uses (type + partNumber) is in ST185.harnesslib
  H2  ...and is equal to it: every field but the id; configuration references are compared by
      the referenced part's type + partNumber (ids differ between files). numberOfCavities is
      not compared for connectors that are documentation halves of one physical part
      (interfaces.json "physicalPartGroups", e.g. the DRB102 bulkhead A / B halves)
  H3  the library itself: one entry per type + partNumber, every entry has a partNumber, every
      configuration reference resolves inside the library, ids are unique across the whole file,
      and the header is the documented library form - "version": 0.9, "kind": "library",
      "currency", part arrays and nothing else
      (https://docs.harness.design/feature/local-files/json-format)

Whenever a .harness file adds or changes a part, the same change goes into ST185.harnesslib in
the same PR. `--add-missing` copies parts the drawings use but the library lacks (H1 only - an
H2 difference is a decision: change the drawing or the library, never silently).

Exit 1 on any finding (check mode).
"""
import copy
import json
import os
import sys

import model

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "ST185.harnesslib")
REF = {"contactPartId": "contactParts", "lockPartId": "lockParts", "cavityPlugPartId": "cavityPlugParts",
       "mountPartId": "mountParts", "bootPartId": "bootParts", "backshellPartId": "backshellParts",
       "dustCoverPartId": "dustCoverParts", "cavitySealPartId": "cavitySealParts"}


def arrays(d):
    return [k for k in d if k.endswith("Parts") and isinstance(d[k], list)]


def norm(p, idx, skip_cav):
    q = {k: v for k, v in p.items() if k != "id" and not (skip_cav and k == "numberOfCavities")}
    if "configurations" in q:
        q["configurations"] = [{k: (idx.get(v, ("?", v)) if k in REF else v) for k, v in c.items()}
                               for c in q["configurations"]]
    return json.dumps(q, sort_keys=True)


def main():
    write = "--add-missing" in sys.argv
    with open(LIB, encoding="utf-8") as f:
        lib = json.load(f)
    bad = []
    if lib.get("version") != 0.9 or lib.get("kind") != "library" or "currency" not in lib:
        bad.append("H3 library header must be version 0.9, kind library, currency (json-format docs)")
    extra = sorted(k for k in lib if k not in ("version", "kind", "currency") and k not in arrays(lib))
    if extra:
        bad.append("H3 library holds keys other than currency and part arrays: %s" % ", ".join(extra))
    allids = [p["id"] for t in arrays(lib) for p in lib[t]]
    for i in sorted({i for i in allids if allids.count(i) > 1}):
        bad.append("H3 library id %s is used more than once" % i)
    lidx = {p["id"]: (t, p.get("partNumber")) for t in arrays(lib) for p in lib[t]}
    lpn = {}
    for t in arrays(lib):
        for p in lib[t]:
            if not p.get("partNumber"):
                bad.append("H3 library %s %s has no partNumber" % (t, p["id"]))
            elif (t, p["partNumber"]) in lpn:
                bad.append("H3 library has %s %s twice" % (t, p["partNumber"]))
            lpn[(t, p.get("partNumber"))] = p
            for c in p.get("configurations", []):
                for k, v in c.items():
                    if k in REF and v not in lidx:
                        bad.append("H3 library %s %s %s -> %s does not resolve" % (t, p.get("partNumber"), k, v))
    reg = model.registry()
    grouped = {m["connector"] for pg, ms in reg.get("physicalPartGroups", {}).items() if not pg.startswith("_")
               for m in ms}
    added = 0
    for loom, d in model.docs(reg).items():
        fidx = {p["id"]: (t, p.get("partNumber")) for t in arrays(d) for p in d[t]}
        grouped_parts = {c.get("partId") for c in d.get("connectors", []) if c["id"] in grouped}
        for t in arrays(d):
            for p in d[t]:
                key = (t, p.get("partNumber"))
                lp = lpn.get(key)
                if lp is None:
                    if write:
                        q = copy.deepcopy(p)
                        if q["id"] in lidx:
                            q["id"] = "%s_%s" % (q["id"], loom.lower().replace("-", "_"))
                        for c in q.get("configurations", []):
                            for k, v in list(c.items()):
                                if k in REF and v in fidx:
                                    hit = lpn.get(fidx[v])
                                    if hit:
                                        c[k] = hit["id"]
                        lib.setdefault(t, []).append(q)
                        lpn[key], lidx[q["id"]] = q, key
                        added += 1
                    else:
                        bad.append("H1 %s: %s %s is not in ST185.harnesslib" % (loom, t, p.get("partNumber")))
                    continue
                skip = t == "connectorParts" and p["id"] in grouped_parts
                if norm(p, fidx, skip) != norm(lp, lidx, skip):
                    diff = sorted(k for k in set(p) | set(lp) if k != "id" and p.get(k) != lp.get(k)
                                  and not (skip and k == "numberOfCavities"))
                    bad.append("H2 %s: %s %s differs from ST185.harnesslib (%s)"
                               % (loom, t, p.get("partNumber"), ", ".join(diff) or "configuration refs"))
    if write and added:
        for t in arrays(lib):
            lib[t].sort(key=lambda p: p.get("partNumber") or "")
        with open(LIB, "w", encoding="utf-8", newline="\r\n") as f:
            json.dump(lib, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("added %d part(s) to %s" % (added, LIB))
    n = sum(len(lib[t]) for t in arrays(lib))
    print("ST185.harnesslib: %d parts in %d lists" % (n, len(arrays(lib))))
    for line in bad:
        print(line)
    print("\n%d harnesslib finding(s)." % len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
