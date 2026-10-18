"""Apply R156 wire-end labels to one drawing (DECISIONS R156, Dan 2026-10-17).

    python docs/harness/relabel_ends.py <spec.json>            dry run: prints what would change
    python docs/harness/relabel_ends.py <spec.json> --write    writes the drawing and full_text.json

The spec names one drawing and the new text, nothing else:

    {"harness": "ClusterLED",
     "terminals": {"<terminal id>": "<where this end lands> - <what it is>", ...},
     "splices":   {"<splice id>":   "<what it joins> - <detail>", ...},
     "diodes" / "resistors": {"<id>": "<plain name, e.g. High beam LED>", ...},   (optional)
     "connectors": {"<connector id>": "<name, what + where, <= 48>"},   (optional)
     "schematic": {"<node id>": {"x": 0, "y": 0, "width": 390}, ...},      (optional, schematic only)
     "notes":     {"<note id>": {"text": "...", "width": 390, "x": 0, "y": 0} | null, ...}  (optional)}

For every terminal in the spec it sets `label` and drops `signal` (the label already says what
the wire is). The old signal is kept for the gates: its full_text.json pair becomes ["", long]
(or ["", old signal] when it had none), so model.full_text still hands the gates the long text.
Layout positions are never touched (R156: the layout geometry stays).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout_tree  # noqa: E402
import model  # noqa: E402


def main(argv):
    spec = json.load(open(argv[1], encoding="utf-8"))
    write = "--write" in argv
    fn = model.harness_files()[spec["harness"]]
    path = os.path.join(model.REB, fn)
    d = json.load(open(path, encoding="utf-8"))
    ft = json.load(open(model.FULL_TEXT, encoding="utf-8"))
    rec = ft.setdefault(fn, {"connectors": {}, "terminals": {}})
    rec.setdefault("terminals", {})
    changes = []
    by_id = {x["id"]: x for k in ("terminals", "splices", "connectors", "diodes", "resistors")
             for x in d.get(k, [])}
    for kind in ("terminals", "splices", "diodes", "resistors"):
        for tid, lab in spec.get(kind, {}).items():
            t = by_id[tid]
            if t.get("label") != lab:
                changes.append("%s label %r -> %r" % (tid, t.get("label"), lab))
                t["label"] = lab
            if kind == "terminals" and "signal" in t:
                old = t.pop("signal")
                pair = rec["terminals"].get(tid)
                # pair[0] == "" means an earlier run already kept the long text: never overwrite it
                rec["terminals"][tid] = ["", pair[1] if pair and pair[0] in (old, "") else old]
                changes.append("%s signal %r dropped" % (tid, old))
    for cid, lab in spec.get("connectors", {}).items():     # connector names, R156: up to 48
        c = by_id[cid]
        if c.get("label") != lab:
            changes.append("%s label %r -> %r" % (cid, c.get("label"), lab))
            pair = rec.setdefault("connectors", {}).setdefault(cid, {}).get("label")
            rec["connectors"][cid]["label"] = [lab, pair[1] if pair and pair[0] == c.get("label") else c.get("label")]
            c["label"] = lab
    for nid, pos in spec.get("schematic", {}).items():
        x = by_id[nid]
        new = {"x": pos["x"], "y": pos["y"]}
        if x.get("schematicPosition") != new:
            changes.append("%s schematic %s -> %s" % (nid, x.get("schematicPosition"), new))
            if "layoutPosition" not in x and "schematicPosition" not in x:
                raise SystemExit("%s has no position to keep" % nid)
            if "schematicPosition" not in x:      # one position serves both views: keep the layout
                x["layoutPosition"] = dict(x.get("layoutPosition"))
            x["schematicPosition"] = new
        if "width" in pos and x.get("width") != pos["width"]:
            changes.append("%s width %s -> %s" % (nid, x.get("width"), pos["width"]))
            x["width"] = pos["width"]
    notes = {n["id"]: n for n in d.get("schematicNotes", [])}
    for nid, new in spec.get("notes", {}).items():
        if new is None:
            if nid not in notes:
                continue
            d["schematicNotes"] = [n for n in d["schematicNotes"] if n["id"] != nid]
            changes.append("note %s removed" % nid)
            continue
        n = notes[nid]
        for k in ("text", "width"):
            if k in new and n.get(k) != new[k]:
                changes.append("note %s %s changed" % (nid, k))
                n[k] = new[k]
        if "x" in new and n.get("schematicPosition") != {"x": new["x"], "y": new["y"]}:
            n["schematicPosition"] = {"x": new["x"], "y": new["y"]}
            changes.append("note %s moved to %s,%s" % (nid, new["x"], new["y"]))
    for c in changes:
        print("  " + c)
    print("%s: %d change(s)%s" % (fn, len(changes), "" if write else " (dry run, --write to apply)"))
    if write and changes:
        with open(path, "rb") as f:
            nl = "\r\n" if b"\r\n" in f.read(4096) else "\n"
        layout_tree.write_atomic(path, d, nl)      # the drawings' own format and line ending
        with open(model.FULL_TEXT, "w", encoding="utf-8") as f:
            f.write(json.dumps(ft, indent=1))


if __name__ == "__main__":
    main(sys.argv)
