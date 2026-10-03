"""Write the upload copy of every rebuild file into min/.

The uploads go through set_document_json, which takes the whole document in one
call. Pretty-printed JSON roughly doubles the payload for no benefit at the far
end, so min/ holds the same documents with the whitespace stripped. rebuild/ is
what a human reads and what git diffs; min/ is what goes over the wire.

Run it after any fix_*/gen_*/layout script touches rebuild/, or min/ goes stale
and an upload silently ships the previous revision.

    python docs/harness/make_min.py            write min/ (default; same as --write)
    python docs/harness/make_min.py --check    compare only, exit 1 if min/ is stale
                                               (what check_all.py and CI run)
"""
import json, glob, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "rebuild")
DST = os.path.join(HERE, "min")
CHECK = "--check" in sys.argv[1:]

stale = []
names = set()
if not CHECK:
    os.makedirs(DST, exist_ok=True)
for path in sorted(glob.glob(os.path.join(SRC, "*.harness"))):
    name = os.path.basename(path)
    names.add(name)
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    out = os.path.join(DST, name)
    text = json.dumps(d, separators=(",", ":"))
    if CHECK:
        old = open(out, encoding="utf-8").read() if os.path.exists(out) else None
        if old != text:
            stale.append(name + (" (missing)" if old is None else ""))
        continue
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("%-30s %7d bytes" % (name, os.path.getsize(out)))

extra = sorted(os.path.basename(p) for p in glob.glob(os.path.join(DST, "*.harness"))
               if os.path.basename(p) not in names)
if CHECK:
    if extra:
        stale += [n + " (no rebuild/ source - delete it)" for n in extra]
    if stale:
        print("STALE min/ copies - run python docs/harness/make_min.py and commit:")
        for n in stale:
            print("   " + n)
        sys.exit(1)
    print("min/ up to date: %d files" % len(names))
elif extra:
    print("WARNING: min/ has files with no rebuild/ source: " + ", ".join(extra))
