"""Give the engine half of the bulkhead the same pin names as the cabin half (gate R2 in
audit_pin_names.py: a mating pair shares one name). Text only: no pin, wire or part changes.

Reads the bulkhead pin names from ST185-A-cabin.harness (bh_a_fw), writes them onto the same
cavities of bh_a_eng in ST185-A-engine.harness, and moves the matching full_text.json pairs to
the new shown text (their long text is kept).

    python docs/harness/cleanroom/sync_bulkhead_names.py
"""
import json
import os

HARNESS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REB = os.path.join(HARNESS, "rebuild")


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(p, d, indent):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=indent, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, p)


cab = load(os.path.join(REB, "ST185-A-cabin.harness"))
names = {c["id"]: c.get("signal") for c in next(x for x in cab["connectors"] if x["id"] == "bh_a_fw")["cavities"]
         if c.get("signal") and not c.get("notConnected")}
eng_path = os.path.join(REB, "ST185-A-engine.harness")
eng = load(eng_path)
ft_path = os.path.join(HARNESS, "full_text.json")
ft = load(ft_path)
pairs = ft["ST185-A-engine.harness"]["connectors"]["bh_a_eng"]["cavities"]
n = 0
for cav in next(x for x in eng["connectors"] if x["id"] == "bh_a_eng")["cavities"]:
    new = names.get(cav["id"])
    if new and not cav.get("notConnected") and cav.get("signal") != new:
        if cav["id"] in pairs:
            pairs[cav["id"]][0] = new
        cav["signal"] = new
        n += 1
save(eng_path, eng, 2)
save(ft_path, ft, 1)
print("bh_a_eng: %d pin names synced from bh_a_fw" % n)
