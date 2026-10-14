"""Lints Dan's route-markup HTML drawings in docs/harness/routes/ (one file per
route, current version only; git history is the revision record).

A HARD gate in docs/harness/check_all.py (no argument = docs/harness/routes/).
Run it by hand on one file or a directory:

    python docs/harness/check_route_drawings.py
    python docs/harness/check_route_drawings.py docs/harness/routes/ROUTE-5-A-CABIN.html

Checks, per file:
  1. every red route <polyline>/<path> has fill="none" (a red shape without
     it renders as a filled blob, not a line)
  2. no doubled or broken SVG/HTML attribute on a polyline/path/circle/text
     tag (same attribute twice on one tag, or an unterminated quote)
  3. every isometric route figure ("Fig. <id>" caption) is followed, before
     the next one, by a top view ("Top view" caption) - Dan's top-view rule,
     binding (route rules in docs/harness/redesign/DECISIONS.md)
  4. no two numbered marker circles overlap within one figure (<svg>)

Exit 0 if every file is clean, 1 otherwise.
"""
import sys
import os
import re
import glob

RED_STROKE = re.compile(r'stroke\s*=\s*"(#e00000|#ff0000|#c00000|#d00000|red)"', re.I)
ROUTE_TAG = re.compile(r'<(polyline|path)\b([^>]*)>', re.I)
ATTR_NAME = re.compile(r'([A-Za-z_][\w:-]*)\s*=\s*"')
MARKER = re.compile(
    r'<circle\b[^>]*\bcx="([\d.]+)"[^>]*\bcy="([\d.]+)"[^>]*\br="([\d.]+)"[^>]*/>'
    r'\s*<text\b[^>]*>\s*\d+\s*</text>',
    re.I)
FIG_CAPTION = re.compile(r'<figcaption>\s*Fig\.\s*\S+', re.I)
TOPVIEW_CAPTION = re.compile(r'<figcaption>\s*Top view', re.I)


def check_file(path):
    text = open(path, encoding="utf-8").read()
    bad = []

    # 1. red route lines must be fill="none"
    for m in ROUTE_TAG.finditer(text):
        attrs = m.group(2)
        if RED_STROKE.search(attrs) and not re.search(r'fill\s*=\s*"none"', attrs):
            bad.append('%s: red <%s> missing fill="none": %s'
                       % (path, m.group(1), attrs.strip()[:100]))

    # 2. doubled or broken attributes on drawing tags
    for m in re.finditer(r'<(polyline|path|circle|text)\b([^>]*)>', text, re.I):
        tag, attrs = m.group(1), m.group(2)
        names = ATTR_NAME.findall(attrs)
        dupes = sorted({n for n in names if names.count(n) > 1})
        if dupes:
            bad.append("%s: <%s> repeats attribute(s) %s" % (path, tag, ", ".join(dupes)))
        if attrs.count('"') % 2:
            bad.append("%s: <%s> has an unterminated quoted attribute" % (path, tag))

    # 3. every isometric figure caption is followed by a top-view caption
    #    before the next isometric figure (or end of file)
    figs = [m.start() for m in FIG_CAPTION.finditer(text)]
    tops = [m.start() for m in TOPVIEW_CAPTION.finditer(text)]
    for i, pos in enumerate(figs):
        nxt = figs[i + 1] if i + 1 < len(figs) else len(text)
        if not any(pos < t < nxt for t in tops):
            bad.append("%s: isometric figure at offset %d has no top view before the next figure"
                       % (path, pos))

    # 4. numbered marker circles must not overlap
    #    (each figure is its own <svg>, so only compare markers inside one)
    for svg in re.findall(r'<svg.*?</svg>', text, re.I | re.S):
        markers = [(float(cx), float(cy), float(r)) for cx, cy, r in MARKER.findall(svg)]
        for i in range(len(markers)):
            x1, y1, r1 = markers[i]
            for j in range(i + 1, len(markers)):
                x2, y2, r2 = markers[j]
                if abs(x1 - x2) < (r1 + r2) and abs(y1 - y2) < (r1 + r2):
                    bad.append("%s: marker labels overlap near (%.0f,%.0f) and (%.0f,%.0f)"
                               % (path, x1, y1, x2, y2))

    return bad


def main(argv):
    if len(argv) > 2:
        print("usage: python docs/harness/check_route_drawings.py [file-or-directory]")
        return 2

    target = argv[1] if len(argv) == 2 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "routes")
    if os.path.isdir(target):
        files = sorted(glob.glob(os.path.join(target, "*.html")))
    elif os.path.isfile(target):
        files = [target]
    else:
        print("not found: %s" % target)
        return 2

    if not files:
        print("no .html files found at %s" % target)
        return 1

    bad = []
    for f in files:
        bad.extend(check_file(f))

    for line in bad:
        print(line)
    print()
    print("%d route-drawing issue(s) across %d file(s)." % (len(bad), len(files)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
