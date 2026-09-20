"""Check every rebuild file against the v0.9 rules we have learned by
rejection, so an upload is not a guess.

Each rule here cost a failed set_document_json at least once:
  - width is an enum, not a number
  - wire colour is an enum with no striped values; the stripe is its own field
  - wires take no 'signal'
  - cavities take no 'description'
  - connectors take no 'notes'
  - connectors take no 'shell' (6.27: no connector on this car has one)
  - every partId / contactPartId / cavityPlugPartId must resolve
  - every wire end must point at a node and a cavity that exist
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "rebuild")

WIDTHS = {60, 90, 150, 210, 270, 390}
COLORS = {"Black", "Brown", "Red", "Orange", "Yellow", "Green", "Blue",
          "Violet", "Gray", "White", "Pink", "Tan", "Maroon", "Light Yellow",
          "Light Green", "Light Blue", "Light Gray", "Transparent", "Shield"}


def check(fn):
    with open(os.path.join(SRC, fn), encoding="utf-8") as fh:
        d = json.load(fh)
    bad = []

    parts = set()
    for key in ("connectorParts", "contactParts", "resistorParts",
                "cableParts", "wireParts", "bootParts", "spliceParts",
                "terminalParts", "tapeParts", "tubeParts"):
        for p in d.get(key, []):
            parts.add(p.get("id"))

    # nodes and their cavity ids
    cav = {}
    for c in d.get("connectors", []):
        cav[c["id"]] = {x.get("id") for x in c.get("cavities", [])}
        if c.get("width") is not None and c["width"] not in WIDTHS:
            bad.append("connector %s width %s" % (c["id"], c["width"]))
        if "shell" in c:
            bad.append("connector %s still has a shell (6.27)" % c["id"])
        if "notes" in c:
            bad.append("connector %s has a notes key" % c["id"])
        for x in c.get("cavities", []):
            if "description" in x:
                bad.append("cavity %s/%s has a description key"
                           % (c["id"], x.get("id")))
        for k in ("partId",):
            if c.get(k) and c[k] not in parts:
                bad.append("connector %s %s -> missing part %s"
                           % (c["id"], k, c[k]))
        for x in c.get("cavities", []):
            for k in ("contactPartId", "cavityPlugPartId"):
                if x.get(k) and x[k] not in parts:
                    bad.append("cavity %s/%s %s -> missing part %s"
                               % (c["id"], x.get("id"), k, x[k]))

    for s in d.get("splices", []):
        cav[s["id"]] = {"Splice"}
    for t in d.get("terminals", []):
        cav[t["id"]] = {"Terminal"}
        if t.get("width") is not None and t["width"] not in WIDTHS:
            bad.append("terminal %s width %s" % (t["id"], t["width"]))
    for r in d.get("resistors", []):
        cav[r["id"]] = {"Left", "Right"}
        if r.get("partId") and r["partId"] not in parts:
            bad.append("resistor %s -> missing part %s" % (r["id"], r["partId"]))

    for n in d.get("schematicNotes", []):
        if n.get("width") is not None and n["width"] not in WIDTHS:
            bad.append("note %s width %s" % (n.get("id"), n["width"]))

    seen = set()
    for w in d.get("wires", []) + d.get("cables", []):
        wid = w.get("id")
        if wid in seen:
            bad.append("duplicate wire id %s" % wid)
        seen.add(wid)
        if "signal" in w:
            bad.append("wire %s has a signal key" % wid)
        for k in ("color", "stripeColor"):
            if w.get(k) and w[k] not in COLORS:
                bad.append("wire %s %s %r" % (wid, k, w[k]))
        for end in ("source", "target"):
            e = w.get(end)
            if not e:
                continue          # a shield core legitimately has one end
            nid, h = e.get("id"), e.get("handle")
            if nid not in cav:
                bad.append("wire %s %s -> unknown node %s" % (wid, end, nid))
            elif h not in cav[nid]:
                bad.append("wire %s %s -> %s has no cavity %s"
                           % (wid, end, nid, h))
    return bad


def main():
    files = sys.argv[1:] or sorted(f for f in os.listdir(SRC)
                                   if f.endswith(".harness"))
    total = 0
    for fn in files:
        bad = check(fn)
        total += len(bad)
        print("%-30s %s" % (fn, "OK" if not bad else "%d PROBLEMS" % len(bad)))
        for b in bad:
            print("      " + b)
    print("\n%d problems total" % total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
