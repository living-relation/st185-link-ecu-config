"""Schematic positions for the clean-room A-cabin build (Dan 2026-10-19, CORRECTION).

The schematic roughly follows the layout view: nodes are sorted by their layout x into
columns (front of car on the right, as in the layout), and each column is stacked in layout-y
order with clear space, so every pinout table has room. The two ends of a wire are NOT placed
together; the same description at both ends says where a wire goes.
"""
GRID = 30
COL_BREAK = 240   # a layout-x jump larger than this starts a new column
COL_GAP = 240     # clear space between columns (wires run here)
ROW_GAP = 90      # clear space between stacked nodes
TOP = 210         # below the read-me note


def _size(kind, el):
    if kind == "connectors":
        return el.get("width", 150), GRID + GRID * len(el["cavities"])
    if kind == "terminals":
        return el.get("width", 150), GRID
    if kind == "cables":
        return 60, GRID + GRID * (len(el["cores"]) + bool(el.get("shield")))
    return GRID, GRID  # splice, resistor


def _note_h(note):
    per_line = max(1, note["width"] // 7)  # about 7 px a character
    lines = sum(-(-max(len(p), 1) // per_line) for p in note["text"].split("\n"))
    return GRID * -(-(lines * 18 + 20) // GRID)


def place(doc, attach=None):
    """attach: node id -> note id drawn just right of that node."""
    attach = attach or {}
    notes = {n["id"]: n for n in doc.get("schematicNotes", [])}
    by_id = {}
    for kind in ("connectors", "terminals", "splices", "resistors"):
        for el in doc.get(kind, []):
            by_id[el["id"]] = (kind, el)
    # a cable sits right after the connector its cores leave from
    cable_after = {}
    for cb in doc.get("cables", []):
        src = next(c["source"]["id"] for c in cb["cores"] if c.get("source"))
        cable_after.setdefault(src, []).append(cb)

    order = sorted(by_id.values(), key=lambda ke: (ke[1]["layoutPosition"]["x"], ke[1]["layoutPosition"]["y"]))
    columns, start = [], None
    for kind, el in order:
        x = el["layoutPosition"]["x"]
        if start is None or x - start > COL_BREAK:
            columns.append([])
            start = x
        columns[-1].append((kind, el))

    cx = 0
    for col in columns:
        col.sort(key=lambda ke: ke[1]["layoutPosition"]["y"])
        stack = []
        for kind, el in col:
            stack.append((kind, el))
            stack += [("cables", cb) for cb in cable_after.get(el["id"], [])]
        def full_w(k, e):
            n = notes.get(attach.get(e["id"]))
            return _size(k, e)[0] + ((GRID + n["width"]) if n else 0)
        width = max(full_w(k, e) for k, e in stack)
        y = TOP
        for kind, el in stack:
            w, h = _size(kind, el)
            el["schematicPosition"] = {"x": cx, "y": y}
            el.pop("rotated", None)
            n = notes.get(attach.get(el["id"]))
            if n:
                n["schematicPosition"] = {"x": cx + w + GRID, "y": y}
                h = max(h, _note_h(n))
            y += h + ROW_GAP
            y = GRID * -(-y // GRID)
        cx += width + COL_GAP
        cx = GRID * -(-cx // GRID)
    # free notes (not tied to an end): a column of their own, left of everything
    free = [n for n in notes.values() if n["id"] not in attach.values()]
    y = 0
    for n in free:
        n["schematicPosition"] = {"x": -(390 + COL_GAP), "y": y}
        y += _note_h(n) + ROW_GAP
        y = GRID * -(-y // GRID)
