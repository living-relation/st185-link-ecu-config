"""Make the retired c1 drain label say the same thing in every copy.

fix_shield_passthrough.py retired the shared c1 drain but only relabelled the
two files it touched.  B-ECU, B-engine and CAN still call c1 "Shield drain
(engine bay, single)", which is now a lie and exactly the kind of drift the
shared-connector check in buylist.py exists to catch.  Signals are not part of
that check, so it slipped through.  Fixed 2026-09-22.
"""
import json, glob, os

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
TEXT = "spare (size 16) - was the shared shield drain, retired by 6.32"

for f in sorted(glob.glob(os.path.join(R, "*.harness"))):
    d = json.load(open(f, encoding="utf-8"))
    hit = False
    for c in d.get("connectors", []):
        if c["id"] not in ("bh_a_fw", "bh_a_eng"):
            continue
        for cv in c.get("cavities", []):
            if cv["id"] == "c1" and cv.get("signal") != TEXT:
                print("%-14s %-9s c1  %r -> retired" % (os.path.basename(f)[6:-8],
                                                        c["id"], cv.get("signal")))
                cv["signal"] = TEXT
                hit = True
    if hit:
        json.dump(d, open(f, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
