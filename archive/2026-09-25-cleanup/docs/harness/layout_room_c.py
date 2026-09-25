"""Compact, zoned, orthogonal layout for ST185-EngineRoom-C.

The old layout spread 38 nodes over 5500 x 3300 with the four section headers all
stacked at x=0, nowhere near the zones they label. This puts each zone under its
own header, in reading order, and drops the canvas to roughly 2300 x 1600.

Writes rebuild/ST185-EngineRoom-C.harness and prints the edit_document ops needed
to push the same positions to harness.design.

Run from docs/harness:  python layout_room_c.py
"""
import json, io, os, sys

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
P = os.path.join(R, "ST185-EngineRoom-C.harness")
G = 30

# Four zones, left to right then wrapping. Each is (header id, x, y, [node ids]).
# Order inside a zone is the order they are stacked down the column.
ZONES = [
    ("shdr_0", 0, 0, [
        "t_trunk_pos", "t_trunk_neg", "pdb", "pmu", "k_fan", "k_fan2",
    ]),
    ("shdr_1", 720, 0, [
        "rl_pos_fw", "rl_pos_eng", "rl_neg_fw", "rl_neg_eng",
        "t_starter_b", "t_alt_b", "jump_pos", "t_eng_block",
    ]),
    ("shdr_2", 1440, 0, [
        "oem_ie1", "oem_jb1_1h", "oem_jb1_1i", "oem_rb2", "oem_rb4",
        "oem_jb2_2a", "oem_jb2_2d", "oem_jb2_2e", "t_gnd_id", "t_gnd_ig",
    ]),
    ("shdr_3", 2160, 0, [
        "k_eps", "mrs_en", "mrs_pwr", "mrs_ctrl", "rad_fan", "fan2",
        "t_gnd_ea", "t_gnd_eb",
    ]),
]

# Cross-reference stubs and grounds go in a fifth column on the right.
ZONE_X = {z[0]: z[1] for z in ZONES}
EXTRA_COL = 2880


def node_height(e, kind):
    if kind == "connector":
        n = len(e.get("cavities") or [])
        h = 30 + n * 30
        if e.get("shell"):
            h += 30
        return h
    if kind == "terminal":
        return 30
    return 30


def main():
    d = json.load(io.open(P, encoding="utf-8"))

    index = {}
    for kind, key in (("connector", "connectors"), ("terminal", "terminals"),
                      ("splice", "splices"), ("resistor", "resistors"),
                      ("diode", "diodes")):
        for e in d.get(key, []):
            index[e["id"]] = (kind, e, key)

    placed = set()
    ops = []

    def place(eid, x, y):
        if eid not in index:
            return 0
        kind, e, key = index[eid]
        pos = {"x": int(x), "y": int(y)}
        e["schematicPosition"] = dict(pos)
        e["layoutPosition"] = dict(pos)
        placed.add(eid)
        ops.append({"op": "update", "collection": key, "id": eid,
                    "value": {"schematicPosition": dict(pos),
                              "layoutPosition": dict(pos)}})
        return node_height(e, kind)

    # Headers sit 90 px above the first node of their zone.
    notes = {n["id"]: n for n in d.get("schematicNotes", [])}
    for hid, x, y, ids in ZONES:
        if hid in notes:
            notes[hid]["schematicPosition"] = {"x": int(x), "y": int(y)}
        cy = y + 90
        for eid in ids:
            h = place(eid, x, cy)
            if h:
                cy += h + 90

    # Everything not named above - grounds, dummies, splices - into the right column.
    cy = 90
    for eid in sorted(index):
        if eid in placed:
            continue
        h = place(eid, EXTRA_COL, cy)
        cy += (h or 30) + 90

    # The four prose notes ride above the whole drawing, in one row, not a stack.
    for i, nid in enumerate(("n_intro", "n_heavy", "n_split", "n_probe")):
        if nid in notes:
            notes[nid]["schematicPosition"] = {"x": i * 420, "y": -390}

    if "--write" in sys.argv:
        with io.open(P, "w", encoding="utf-8", newline="\n") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("wrote rebuild/ST185-EngineRoom-C.harness")

    io.open(os.path.join(os.path.dirname(P), "_room_c_ops.json"), "w").write(
        json.dumps(ops))
    print("%d nodes placed, ops written to rebuild/_room_c_ops.json" % len(ops))
    xs = [o["value"]["schematicPosition"]["x"] for o in ops]
    ys = [o["value"]["schematicPosition"]["y"] for o in ops]
    print("canvas %d x %d" % (max(xs) + 270, max(ys) + 300))


if __name__ == "__main__":
    main()
