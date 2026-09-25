"""Put back connectorParts that an over-eager prune removed.

fix_relay_parts.py's first run treated connectorParts as housings only and
deleted the sealing plugs and the DTM wedgelock, which cavities reference.
This re-adds any part present at git HEAD and still referenced now.  One-shot
repair, 2026-09-22 - safe to delete once committed.
"""
import json, os, subprocess

ROOT = subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                               text=True).strip()
R = os.path.join(ROOT, "docs", "harness", "rebuild")

for name in sorted(os.listdir(R)):
    if not name.endswith(".harness"):
        continue
    rel = "docs/harness/rebuild/" + name
    try:
        head = json.loads(subprocess.check_output(["git", "show", "HEAD:" + rel],
                                                  text=True, encoding="utf-8"))
    except subprocess.CalledProcessError:
        continue
    p = os.path.join(R, name)
    d = json.load(open(p, encoding="utf-8"))
    lib = d.setdefault("connectorParts", [])
    have = {q["id"] for q in lib}
    used = set()
    for x in d.get("connectors", []):
        used.add(x.get("partId"))
        for cv in x.get("cavities", []) + ([x["shell"]] if x.get("shell") else []):
            used.add(cv.get("contactPartId"))
            used.add(cv.get("cavityPlugPartId"))
        for a in x.get("coveringIds", []) or []:
            used.add(a)
    for q in lib + head.get("connectorParts", []):
        for cfg in q.get("configurations", []) or []:
            for v in cfg.values():
                if isinstance(v, str):
                    used.add(v)
    back = [q for q in head.get("connectorParts", [])
            if q["id"] in used and q["id"] not in have]
    if back:
        lib.extend(back)
        json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        for q in back:
            print("%-14s restored %s (%s)" % (name[6:-8], q["id"], q.get("partNumber")))
