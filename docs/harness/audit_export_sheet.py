"""The finished-harness drawing package (DECISIONS R88): harness.design's own PDF export on its
drawing template - every view plus the parts list, title block on, harness title filled in, every
note inside the view and readable on the exported sheet.

The export setup is saved in the .harness file ("pdfExportSettings", "titleBlock", "exportNotes";
https://docs.harness.design/feature/export#pdf), so it is set and checked here; only pressing
Export is done in the app. A harness that carries "pdfExportSettings" is a finished one and must
pass every check below; the others are listed only.

  E1  the export setup: schematic + layout + parts + connections pages (all connections and each
      component, Ident column), title block on, schematic / layout page size Fit (the sheet is
      sized to the drawing, so nothing is shrunk below its drawn size)
  E2  the title block: title names the harness ("ST185-<name> ..."), drawing number = ST185-<name>
  E3  every schematic note sits inside the schematic view - the frame of its electrical nodes
      (connectors, terminals, splices, cables, diodes, resistors) - so it never grows the sheet
      or floats off on its own; every layout note inside the layout frame the same way
  E4  no note sits in the sheet corners the export draws over: the title block (bottom right)
      and, when export notes are on, the notes block (bottom left). Corner sizes are estimates
      (TB_W x TB_H, NOTES_W) until checked on an exported sheet
  E5  every note is readable: at most MAX_LINES wrapped lines at its width (widen it, up to 390,
      or split it) - note height estimated as in audit_drawing_rules.py

Exit 1 on any finding.
"""
import sys

import model
from audit_drawing_rules import note_box

TB_W, TB_H = 600, 210        # title block, schematic units (estimate)
NOTES_W = 600                # export notes block width (estimate); height from its text
MAX_LINES = 45
NODE_KINDS = ("connectors", "terminals", "splices", "cables", "diodes", "resistors", "twistedWires")
PAGES = ("includeSchematic", "includeLayout", "includeParts", "includeConnections", "includeTitleBlock")


def frame(d, pos):
    """bounding box of the electrical nodes in one view (pos = schematicPosition / layoutPosition)."""
    xs, ys = [], []
    for k in NODE_KINDS + (("branchPoints",) if pos == "layoutPosition" else ()):
        for n in d.get(k, []):
            p = n.get(pos)
            if not p:
                continue
            w = n.get("width") or 150
            h = 30 * (1 + len(n.get("cavities", []) or n.get("cores", []) or n.get("wires", [])))
            xs += [p["x"], p["x"] + w]
            ys += [p["y"], p["y"] + h]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def check(name, d):
    bad = []
    s = d.get("pdfExportSettings") or {}
    for k in PAGES:
        if not s.get(k):
            bad.append("E1 %s: pdfExportSettings.%s is not true" % (name, k))
    c = s.get("connections") or {}
    if not (c.get("includeAll") and c.get("includeComponents")):
        bad.append("E1 %s: connections pages need includeAll and includeComponents" % name)
    if "Ident" not in (c.get("columns") or []):
        bad.append("E1 %s: connections columns need Ident (R87 bands)" % name)
    for v in ("schematic", "layout"):
        if (s.get(v) or {}).get("pageSize") != "Fit":
            bad.append("E1 %s: %s pageSize must be Fit (got %s)" % (name, v, (s.get(v) or {}).get("pageSize")))
    tb = d.get("titleBlock") or {}
    stem = "ST185-" + name
    if not (tb.get("title") or "").startswith(stem):
        bad.append("E2 %s: titleBlock.title must start with %s" % (name, stem))
    if tb.get("drawingNumber") != stem:
        bad.append("E2 %s: titleBlock.drawingNumber must be %s" % (name, stem))
    for notes, pos, view in (("schematicNotes", "schematicPosition", "schematic"),
                             ("layoutNotes", "layoutPosition", "layout")):
        f = frame(d, pos)
        for n in d.get(notes, []):
            p = n.get(pos)
            if not p or not f:
                continue
            w, h = note_box(n)
            x0, y0, x1, y1 = p["x"], p["y"], p["x"] + w, p["y"] + h
            if x0 < f[0] or y0 < f[1] or x1 > f[2] or y1 > f[3]:
                bad.append("E3 %s: %s note %s (%d,%d)-(%d,%d) is outside the %s view frame (%d,%d)-(%d,%d)"
                           % (name, view, n["id"], x0, y0, x1, y1, view, *f))
            if x1 > f[2] - TB_W and y1 > f[3] - TB_H:
                bad.append("E4 %s: %s note %s reaches the title block corner (bottom right)" % (name, view, n["id"]))
            if s.get("includeNotes") and d.get("exportNotes"):
                nh = note_box({"text": d["exportNotes"], "width": NOTES_W})[1]
                if x0 < f[0] + NOTES_W and y1 > f[3] - nh:
                    bad.append("E4 %s: %s note %s reaches the export notes corner (bottom left)" % (name, view, n["id"]))
            lines = (h - 30) // 18
            if lines > MAX_LINES:
                bad.append("E5 %s: %s note %s is %d lines at width %d - widen it (max 390) or split it"
                           % (name, view, n["id"], lines, w))
    return bad


def main():
    bad, done, todo = [], [], []
    for name, fn in model.harness_files().items():
        d = model.load(fn)
        if d.get("pdfExportSettings"):
            done.append(name)
            bad += check(name, d)
        else:
            todo.append(name)
    print("export package set up: %s" % (", ".join(done) or "none"))
    print("not yet: %s" % ", ".join(todo))
    for line in bad:
        print(line)
    print("\n%d export-sheet finding(s)." % len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
