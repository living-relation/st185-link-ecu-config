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

# ---- 2026-09-25: parts rule 1, second half ---------------------------------
# A bulkhead cavity wired in ANY loom gets a contact, in every copy of that
# half; a cavity wired in NO loom gets a sealing plug. Found 11 wired cavities
# (knock c16-c18, VSS c15, screens c33/c34, MRS c36, EPS enable c14) carrying
# plugs and 10 spares carrying contacts - the buy list was counting both wrong.
BH = ("bh_a_fw", "bh_a_eng", "bh_b_fw", "bh_b_eng")
used = collections.defaultdict(set)
docs = {os.path.basename(f)[6:-8]: json.load(open(f, encoding="utf-8"))
        for f in sorted(glob.glob(os.path.join(R, "*.harness")))}
for d in docs.values():
    conds = list(d.get("wires", []))
    for cb in d.get("cables", []):
        conds += cb.get("cores", [])
        if cb.get("shield"):
            conds.append(cb["shield"])
    for w in conds:
        for e in (w.get("source"), w.get("target")):
            if not e:
                continue
            if e["id"].startswith("dm_bh_"):
                b, c = e["id"][3:].rsplit("_", 1)
                used[b].add(c)
            elif e["id"] in BH:
                used[e["id"]].add(e.get("handle"))
wrong = 0
for loom, d in docs.items():
    for c in d.get("connectors", []):
        if c["id"] not in BH:
            continue
        for cv in c.get("cavities", []):
            wired = cv["id"] in used[c["id"]]
            if wired and not cv.get("contactPartId"):
                print("  %-12s %s %s is wired but has no contact" % (loom, c["id"], cv["id"]))
                wrong += 1
            elif not wired and not cv.get("cavityPlugPartId"):
                print("  %-12s %s %s is unused but has no sealing plug" % (loom, c["id"], cv["id"]))
                wrong += 1
print("%d bulkhead cavities with the wrong part for their use." % wrong)
sys.exit(1 if (tot or wrong) else 0)
