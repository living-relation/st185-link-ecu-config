"""Print the node inventory of each rebuild file so layout can be assigned."""
import json, os, sys

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
names = sys.argv[1:] or sorted(f for f in os.listdir(D) if f.endswith(".harness"))
for fn in names:
    with open(os.path.join(D, fn)) as fh:
        d = json.load(fh)
    print("== %s  wires=%d" % (fn, len(d.get("wires", []))))
    for c in d.get("connectors", []):
        sp = c.get("schematicPosition") or {}
        print("   %-22s %-28s cav=%-3d x=%-7s y=%-7s" % (
            c.get("id"), (c.get("label") or "")[:28], len(c.get("cavities", [])),
            sp.get("x"), sp.get("y")))
    for s in d.get("splices", []):
        print("   SPLICE %-16s %s" % (s.get("id"), s.get("label")))
    print()
