"""Find parts counted more than once across the eight looms.

A contact or a seal legitimately sums across files - you buy 68 of them. A
CONNECTOR usually does not: one physical housing drawn on two sheets must be
bought once, so only one sheet may carry its partId. The other shows it with no
part, which is the cross-reference convention.

This prints, per part number, which files use it and how many components claim it,
and flags the ones that look like a single physical item counted twice.

Run from docs/harness:  python audit_parts.py
"""
import json, io, os, collections

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")

# Component collections whose parts are ONE physical item each. Contacts, seals,
# plugs and wire are bought by quantity and are expected to sum.
SINGLETON = {
    "connectors": "connectorParts",
    "terminals": "terminalParts",
    "diodes": "diodeParts",
    "resistors": "resistorParts",
}


def main():
    files = sorted(f for f in os.listdir(SRC) if f.endswith(".harness"))
    # partNumber -> file -> [component ids]
    use = collections.defaultdict(lambda: collections.defaultdict(list))
    pn_of = {}

    for fn in files:
        d = json.load(io.open(os.path.join(SRC, fn), encoding="utf-8"))
        for coll, partkey in SINGLETON.items():
            parts = {p["id"]: p for p in d.get(partkey, [])}
            for c in d.get(coll, []):
                pid = c.get("partId")
                if not pid:
                    continue
                p = parts.get(pid)
                if not p:
                    continue
                pn = p.get("partNumber") or "(no part number)"
                pn_of[pn] = p.get("description", "")
                use[pn][fn[6:-8]].append(c["id"])

    print("=" * 78)
    print("PARTS CLAIMED BY MORE THAN ONE LOOM")
    print("=" * 78)
    flagged = 0
    for pn in sorted(use):
        files_using = use[pn]
        if len(files_using) < 2:
            continue
        total = sum(len(v) for v in files_using.values())
        flagged += 1
        print("\n%-28s  %d components across %d looms"
              % (pn[:28], total, len(files_using)))
        for fn in sorted(files_using):
            print("      %-14s %s" % (fn, ", ".join(sorted(files_using[fn]))))

    print("\n%d part numbers span more than one loom." % flagged)

    print()
    print("=" * 78)
    print("COMPONENTS WITH NO PART AT ALL")
    print("=" * 78)
    for fn in files:
        d = json.load(io.open(os.path.join(SRC, fn), encoding="utf-8"))
        miss = []
        for coll in SINGLETON:
            for c in d.get(coll, []):
                if not c.get("partId") and not c.get("excludeFromBom"):
                    miss.append("%s/%s" % (coll[:4], c["id"]))
        print("%-14s %s" % (fn[6:-8], ", ".join(miss) if miss else "-"))


if __name__ == "__main__":
    main()
