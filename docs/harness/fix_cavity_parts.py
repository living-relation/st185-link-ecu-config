"""One cavity, one part.

Every bulkhead cavity was stamped with a contact AND a sealing plug.  The app
hides it (assigning one clears the other), but buylist.py reads the JSON, so
118 plugs were being ordered for cavities that already have a pin in them.

The rule this applies:

  a cavity that carries a wire in ANY loom  -> contact, no plug
  a cavity that carries a wire in NO loom   -> plug, no contact

The union matters because bulkhead A appears in three looms and bulkhead B in
two.  Each copy is the same physical connector, so all copies must end up with
identical contact/plug stamps - otherwise the buy list depends on which file
happens to be read first.  Written 2026-09-22.
"""
import json, glob, os, collections

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
FILES = sorted(glob.glob(os.path.join(R, "*.harness")))
docs = {f: json.load(open(f, encoding="utf-8")) for f in FILES}

# 1. which connectors are double-booked anywhere?
targets = set()
for d in docs.values():
    for c in d.get("connectors", []):
        for cv in c.get("cavities", []):
            if cv.get("contactPartId") and cv.get("cavityPlugPartId"):
                targets.add(c["id"])

# 2. union of wired cavities, and the contact/plug part each connector uses
def conductors(d):
    """Every wire in the document. WheelSpeed has no `wires` at all - its
    conductors are cable cores and shields - and A-engine runs seven bulkhead
    cavities through cables too, so anything that walks only `wires` will call
    those cavities unused and plug them shut."""
    for w in d.get("wires", []):
        yield w
    for cb in d.get("cables", []):
        for co in cb.get("cores", []):
            yield co
        if cb.get("shield"):
            yield cb["shield"]


used = collections.defaultdict(set)
contact_of = collections.defaultdict(collections.Counter)
plug_of = collections.defaultdict(collections.Counter)
for d in docs.values():
    for w in conductors(d):
        for e in (w.get("source"), w.get("target")):
            if e and e.get("id") in targets:
                used[e["id"]].add(e.get("handle"))
    for c in d.get("connectors", []):
        if c["id"] not in targets:
            continue
        for cv in c.get("cavities", []):
            if cv.get("contactPartId"):
                contact_of[c["id"]][cv["contactPartId"]] += 1
            if cv.get("cavityPlugPartId"):
                plug_of[c["id"]][cv["cavityPlugPartId"]] += 1

# a cavity can need a different size than its neighbours - the HDP bulkheads mix
# size 12, 16 and 20 - so remember the contact and the plug that cavity already
# had, and only fall back to the connector's most common plug for a cavity that
# has never had one.  Using the dominant plug everywhere put size-16 plugs in
# bulkhead B's four size-12 cavities.
per_cavity_contact = collections.defaultdict(dict)
per_cavity_plug = collections.defaultdict(dict)
for d in docs.values():
    for c in d.get("connectors", []):
        if c["id"] not in targets:
            continue
        for cv in c.get("cavities", []):
            if cv.get("contactPartId"):
                per_cavity_contact[c["id"]].setdefault(cv["id"], cv["contactPartId"])
            if cv.get("cavityPlugPartId"):
                per_cavity_plug[c["id"]].setdefault(cv["id"], cv["cavityPlugPartId"])

changed = collections.Counter()
for f, d in docs.items():
    for c in d.get("connectors", []):
        if c["id"] not in targets:
            continue
        plug = plug_of[c["id"]].most_common(1)[0][0] if plug_of[c["id"]] else None
        for cv in c["cavities"]:
            before = (cv.get("contactPartId"), cv.get("cavityPlugPartId"))
            if cv["id"] in used[c["id"]]:
                ct = per_cavity_contact[c["id"]].get(cv["id"])
                if ct:
                    cv["contactPartId"] = ct
                cv.pop("cavityPlugPartId", None)
            else:
                cv.pop("contactPartId", None)
                pl = per_cavity_plug[c["id"]].get(cv["id"]) or plug
                if pl:
                    cv["cavityPlugPartId"] = pl
            if (cv.get("contactPartId"), cv.get("cavityPlugPartId")) != before:
                changed[os.path.basename(f)[6:-8] + " " + c["id"]] += 1

for f, d in docs.items():
    json.dump(d, open(f, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

for k, n in sorted(changed.items()):
    print("%-28s %3d cavities" % (k, n))
print()
for cid in sorted(targets):
    tot = max(len(c["cavities"]) for d in docs.values()
              for c in d.get("connectors", []) if c["id"] == cid)
    print("%-10s %2d of %2d cavities wired -> %2d contacts, %2d plugs"
          % (cid, len(used[cid]), tot, len(used[cid]), tot - len(used[cid])))
