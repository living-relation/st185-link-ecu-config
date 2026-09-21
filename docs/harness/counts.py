"""Print a one-line fingerprint of every rebuild file.

Used to check an upload landed intact: the same numbers must come back from
get_harness_summary / get_nets on harness.design. A transcription slip during
an upload shows up here as a count that does not match.
"""
import json, glob, os

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
KEYS = ("connectors", "wires", "cables", "splices", "terminals", "resistors",
        "schematicNotes")

for path in sorted(glob.glob(os.path.join(SRC, "*.harness"))):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    cores = sum(len(c.get("cores", [])) + (1 if c.get("shield") else 0)
                for c in d.get("cables", []))
    cav = sum(len(c.get("cavities", [])) for c in d.get("connectors", []))
    bits = " ".join("%s=%d" % (k[:4], len(d.get(k, []))) for k in KEYS)
    print("%-30s %s cores=%d cavities=%d" % (os.path.basename(path), bits,
                                             cores, cav))
