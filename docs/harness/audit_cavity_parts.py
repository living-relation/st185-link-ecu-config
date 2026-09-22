"""Find cavities that claim BOTH a contact and a cavity plug.

The harness.design editing guide is explicit: a cavity holds exactly one part,
a contact OR a cavity plug, never both ("assigning one clears the other in the
app").  The app silently resolves it in favour of the contact, so the drawings
look fine - but our buylist.py counts whatever the JSON says, so every cavity
carrying both adds a plug nobody will ever fit.  Added 2026-09-22.
"""
import json, glob, os, collections, sys

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
tot = 0
for f in sorted(glob.glob(os.path.join(R, "*.harness"))):
    d = json.load(open(f, encoding="utf-8"))
    hits = collections.Counter()
    for c in d.get("connectors", []):
        for cv in c.get("cavities", []):
            if cv.get("contactPartId") and cv.get("cavityPlugPartId"):
                hits[c["id"]] += 1
    if hits:
        print(os.path.basename(f)[6:-8])
        for cid, n in sorted(hits.items()):
            print("      %-16s %d cavities with a contact AND a plug" % (cid, n))
        tot += sum(hits.values())
print()
print("%d cavities double-booked." % tot)
sys.exit(1 if tot else 0)
