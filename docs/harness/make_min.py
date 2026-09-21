"""Write the upload copy of every rebuild file into min/.

The uploads go through set_document_json, which takes the whole document in one
call. Pretty-printed JSON roughly doubles the payload for no benefit at the far
end, so min/ holds the same documents with the whitespace stripped. rebuild/ is
what a human reads and what git diffs; min/ is what goes over the wire.

Run it after any fix_*/gen_*/layout script touches rebuild/, or min/ goes stale
and an upload silently ships the previous revision.
"""
import json, glob, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "rebuild")
DST = os.path.join(HERE, "min")

os.makedirs(DST, exist_ok=True)
for path in sorted(glob.glob(os.path.join(SRC, "*.harness"))):
    name = os.path.basename(path)
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    out = os.path.join(DST, name)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(d, fh, separators=(",", ":"))
    print("%-30s %7d bytes" % (name, os.path.getsize(out)))
