import os, re, glob, collections, sys

ROOT = r"C:\Users\danie\AppData\Roaming\Claude\local-agent-mode-sessions"
OUT = r"C:\Users\danie\AppData\Roaming\Claude\local-agent-mode-sessions\1cec9723-b110-46f1-9694-4a2692e2397f\a8dc0527-c42c-4163-8eb6-e49e1c4c8497\local_e957a84a-65a7-425d-93d0-0e485ed7f050\outputs\sessions_scan.txt"
ME = "local_e957a84a"

PATS = {
 "intercooler": r"intercool",
 "efr":         r"EFR ?716|EFR ?718|BorgWarner EFR|7163",
 "boostpsi":    r"\b\d{1,2}(?:\.\d)?\s?psi\b",
 "hp":          r"\b\d{3}\s?(?:whp|wheel horsepower|hp target)",
 "inj":         r"\b(?:1000|1050|1200|1400|1500|2000)\s?cc\b",
 "cr":          r"compression ratio",
 "tb":          r"throttle body",
 "cams":        r"\b(?:264|268|272|280|288)\s?(?:deg|duration|cam)",
 "displ":       r"5S-?GTE|2\.2\s?L|2192\s?cc",
 "iatpos":      r"charge ?pipe|post-?intercooler|IAT ?2|charge temp",
 "radiator":    r"radiator|condenser",
 "e85":         r"E85 ?(?:blend|content|target|fuel)|flex ?fuel",
}

hits = collections.defaultdict(list)
files = [f for f in glob.glob(os.path.join(ROOT, "**", "*.json"), recursive=True) if ME not in f]
fh = open(OUT, "w", encoding="utf-8")
fh.write("scanned files: %d\n" % len(files))
for f in files:
    try:
        raw = open(f, encoding="utf-8", errors="ignore").read()
    except Exception:
        continue
    txt = raw.replace("\\n", "\n").replace('\\"', '"')
    for k, p in PATS.items():
        for m in re.finditer(p, txt, re.I):
            s = max(0, m.start()-260); e = min(len(txt), m.end()+260)
            frag = re.sub(r"\s+", " ", txt[s:e])
            hits[k].append((os.path.basename(f), frag))

for k in PATS:
    seen = set(); uniq = []
    for fn, frag in hits[k]:
        key = frag[150:330]
        if key in seen: continue
        seen.add(key); uniq.append((fn, frag))
    fh.write("\n\n##### %s  (%d raw, %d uniq)\n" % (k, len(hits[k]), len(uniq)))
    for fn, frag in uniq[:30]:
        fh.write("  [" + fn[:20] + "] " + frag + "\n")
fh.close()
print("OK", os.path.getsize(OUT))
