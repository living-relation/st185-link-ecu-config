"""2D drawing PDF (A3, 1:1) per bus-bar design from the shared spec. Claude Code, 2026-10-13.
Usage: python drawings.py  -> design-A/A_drawing.pdf, design-B/B_drawing.pdf (+ .svg)
"""
import os, sys, json
import fitz  # PyMuPDF: SVG -> PDF
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSC, NEGC, SPC, UNIC = "#c62828", "#1565c0", "#6d6d6d", "#6a1b9a"
PCOL = {"POS": POSC, "NEG": NEGC, "UNI": UNIC}
PNAME = {"POS": "POS (+) ", "NEG": "NEG (-) ", "UNI": "UNIVERSAL (U) "}


class Svg:
    def __init__(self, w=420, h=297):
        self.w, self.h, self.items = w, h, []

    def add(self, s):
        self.items.append(s)

    def line(self, x0, y0, x1, y1, c="#000", w=0.25, dash=None):
        da = ' stroke-dasharray="%s"' % dash if dash else ""
        self.add('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%.2f"%s/>' % (x0, y0, x1, y1, c, w, da))

    def rect(self, x0, y0, x1, y1, c="#000", w=0.3, fill="none", dash=None, op=1.0):
        da = ' stroke-dasharray="%s"' % dash if dash else ""
        self.add('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" stroke="%s" stroke-width="%.2f" fill="%s" fill-opacity="%.2f"%s/>'
                 % (min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0), c, w, fill, op, da))

    def circle(self, x, y, r, c="#000", w=0.3, fill="none"):
        self.add('<circle cx="%.2f" cy="%.2f" r="%.2f" stroke="%s" stroke-width="%.2f" fill="%s"/>' % (x, y, r, c, w, fill))

    def text(self, x, y, s, size=2.5, c="#000", anchor="start", bold=False, rot=0):
        tr = ' transform="rotate(%d %.2f %.2f)"' % (rot, x, y) if rot else ""
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.add('<text x="%.2f" y="%.2f" font-family="Arial" font-size="%.2f" fill="%s" text-anchor="%s"%s%s>%s</text>'
                 % (x, y, size, c, anchor, ' font-weight="bold"' if bold else "", tr, s))

    def arrow(self, x0, y0, x1, y1, c="#000", w=0.35):
        self.line(x0, y0, x1, y1, c, w)
        import math
        a = math.atan2(y1 - y0, x1 - x0)
        for da in (2.7, -2.7):
            self.line(x1, y1, x1 - 2.5 * math.cos(a + da / 6), y1 - 2.5 * math.sin(a + da / 6), c, w)

    def dim_h(self, x0, x1, y, yref, label, above=True):
        self.line(x0, yref, x0, y + (-1 if above else 1), "#444", 0.15)
        self.line(x1, yref, x1, y + (-1 if above else 1), "#444", 0.15)
        self.line(x0, y, x1, y, "#444", 0.18)
        for x, s in ((x0, 1), (x1, -1)):
            self.line(x, y, x + 1.8 * s, y - 0.7, "#444", 0.18)
            self.line(x, y, x + 1.8 * s, y + 0.7, "#444", 0.18)
        self.text((x0 + x1) / 2, y - 0.8, label, 2.3, "#222", "middle")

    def dim_v(self, y0, y1, x, xref, label):
        self.line(xref, y0, x + 1, y0, "#444", 0.15)
        self.line(xref, y1, x + 1, y1, "#444", 0.15)
        self.line(x, y0, x, y1, "#444", 0.18)
        for y, s in ((y0, 1), (y1, -1)):
            self.line(x, y, x - 0.7, y + 1.8 * s, "#444", 0.18)
            self.line(x, y, x + 0.7, y + 1.8 * s, "#444", 0.18)
        self.text(x - 1.2, (y0 + y1) / 2, label, 2.3, "#222", "middle", rot=-90)

    def save(self, path):
        body = "\n".join(self.items)
        s = ('<svg xmlns="http://www.w3.org/2000/svg" width="%dmm" height="%dmm" viewBox="0 0 %d %d">'
             '<rect width="100%%" height="100%%" fill="white"/>%s</svg>' % (self.w, self.h, self.w, self.h, body))
        open(path, "w", encoding="utf-8").write(s)
        src = fitz.open(stream=s.encode("utf-8"), filetype="svg")
        open(path.replace(".svg", ".pdf"), "wb").write(src.convert_to_pdf())


def pole_color(pole, label):
    return SPC if "SPARE" in label else PCOL[pole]


def draw(d, out_dir):
    S = Svg()
    b = d["body"]
    fl = d["flanges"]
    xmin = min(f["x0"] for f in fl)
    xmax = max(f["x1"] for f in fl)
    ox = 20 - xmin                       # page x = ox + x   (1:1)
    oy = 42 + d["body"]["y1"]               # page y = oy - y   (top view, +y = rear = up on page)
    X = lambda x: ox + x
    Y = lambda y: oy - y
    # frame + title
    S.rect(5, 5, 415, 292, "#000", 0.5)
    S.text(10, 13, "ST185 glove-box combined +/- bus bar  -  " + d["title"] + ("  (REV 2: metal pockets)" if d.get("metal_pockets") and " rev " not in d["title"] else ""), 4.2, bold=True)
    S.text(10, 18.5, "Scale 1:1 on A3, mm.  TOP VIEW (cover off) and FRONT ELEVATION.  Claude Code 2026-10-13.  Not for fab until Dan signs off.", 2.6, "#333")

    # ---- top view
    for f in fl:
        S.rect(X(f["x0"]), Y(f["y0"]), X(f["x1"]), Y(f["y1"]), "#000", 0.35)
        for (sx, sy) in f["slots"]:
            S.rect(X(sx - 3.3), Y(sy - 6), X(sx + 3.3), Y(sy + 6), "#000", 0.25)
    S.rect(X(b["x0"]), Y(b["y0"]), X(b["x1"]), Y(b["y1"]), "#000", 0.45)
    bar_d = d["barrier"]
    if bar_d["axis"] == "x":
        S.rect(X(bar_d["at"] - 2), Y(b["y0"] + 2.8), X(bar_d["at"] + 2), Y(b["y1"] - 2.8), "#000", 0.3, "#000", op=0.6)
    else:
        S.rect(X(b["x0"] + 2.8), Y(bar_d["at"] - 2), X(b["x1"] - 2.8), Y(bar_d["at"] + 2), "#000", 0.3, "#000", op=0.6)
    for (bx, by) in d["bosses"]:
        S.circle(X(bx), Y(by), 6, "#000", 0.3, "#888")
    for bar in d["bars"]:
        c = PCOL[bar["pole"]]
        S.rect(X(bar["x0"]), Y(bar["y0"]), X(bar["x1"]), Y(bar["y1"]), c, 0.5, c, op=0.10)
        if "lands" in bar:
            S.line(X(bar["x0"]), Y(0), X(bar["x1"]), Y(0), c, 0.25, "1.5,1")
        else:
            for (bx0, bx1) in bar["blocks"]:
                S.rect(X(bx0), Y(bar["y0"]), X(bx1), Y(bar["y1"]), c, 0.3, c, op=0.15)
        S.text(X((bar["x0"] + bar["x1"]) / 2), Y(bar["y1"]) - 1.2 if bar["y1"] > 0 and bar["y0"] >= 0 else Y(bar["y0"]) + 3.2,
               PNAME[bar["pole"]] + "6061-T6 bar", 2.4, c, "middle", True)
    # extra walls, strap notches, stow slot, plug park (design B rev 2)
    for xw in d.get("xwalls", []):
        S.rect(X(xw["x"] - xw["thk"] / 2), Y(bar_d["at"]), X(xw["x"] + xw["thk"] / 2), Y(b["y1"] - 2.8), "#000", 0.3, "#000", op=0.6)
    for nt in d.get("notches", []):
        if nt["wall"] == "main":
            S.rect(X(nt["at"] - 11), Y(bar_d["at"] - 2.6), X(nt["at"] + 11), Y(bar_d["at"] + 2.6), "#e65100", 0.45, "#ffcc80", op=0.9)
            S.text(X(nt["at"] + 12.5), Y(bar_d["at"]) + 1, "notch %s + plug" % nt["name"], 2.0, "#e65100")
        else:
            xw = d["xwalls"][0]
            S.rect(X(xw["x"] - 2.6), Y(nt["at"] - 11), X(xw["x"] + 2.6), Y(nt["at"] + 11), "#e65100", 0.45, "#ffcc80", op=0.9)
            S.text(X(xw["x"] + 3.5), Y(nt["at"] + 12.5), "notch %s" % nt["name"], 2.0, "#e65100")
    if d.get("stow"):
        st_ = d["stow"]
        S.rect(X(st_["x0"]), Y(st_["y0"]), X(st_["x1"]), Y(st_["y1"]), "#000", 0.25, "#bbb", op=0.4)
        S.text(X((st_["x0"] + st_["x1"]) / 2), Y(st_["y0"]) + 3.2, "strap stow slot (insulated)", 2.0, "#333", "middle")
    if d.get("plug_park"):
        pk = d["plug_park"]
        S.rect(X(pk["x0"]), Y(pk["y0"]), X(pk["x1"]), Y(pk["y1"]), "#000", 0.25, "#bbb", op=0.4)
        S.text(X((pk["x0"] + pk["x1"]) / 2), Y(pk["y0"]) + 3.2, "spare-plug park", 2.0, "#333", "middle")
    if d.get("links"):
        lk = {l_[2]: (l_[0], l_[1]) for l_ in d["links"]}
        sp = d["strap"]
        for tgt in ("NEG", "POS"):
            (ax, ay), (bx_, by_) = lk["UNI"], lk[tgt]
            inst = tgt in sp["installed"]
            if ax == bx_:
                S.rect(X(ax - sp["w"] / 2), Y(min(ay, by_) - sp["w"] / 2), X(ax + sp["w"] / 2), Y(max(ay, by_) + sp["w"] / 2),
                       UNIC, 0.5 if inst else 0.3, UNIC, None if inst else "2,1.2", 0.25 if inst else 0.0)
            else:
                S.rect(X(min(ax, bx_) - sp["w"] / 2), Y(ay - sp["w"] / 2), X(max(ax, bx_) + sp["w"] / 2), Y(ay + sp["w"] / 2),
                       UNIC, 0.5 if inst else 0.3, UNIC, None if inst else "2,1.2", 0.25 if inst else 0.0)
        for (lx, ly, lp, ll) in d["links"]:
            S.circle(X(lx), Y(ly), 7.5, PCOL[lp], 0.4, "white")
            S.text(X(lx), Y(ly) + 0.9, "L", 2.6, PCOL[lp], "middle", True)
    for (cx, cy) in d.get("bar_screws", []):
        S.circle(X(cx), Y(cy), spec.BAR_SCREW["cbore_d"] / 2, "#000", 0.3, "white")
        S.circle(X(cx), Y(cy), 2.25, "#000", 0.25)
    for (cx, cy) in d.get("clamps", []):
        S.circle(X(cx), Y(cy), 3.8, "#333", 0.25)
        S.circle(X(cx), Y(cy), 2.0, "#333", 0.2)
    rows = []
    n = 0
    for (x, y, lug, ex, pole, label) in d["studs"]:
        n += 1
        L = spec.LUGS[lug]
        c = pole_color(pole, label)
        # anti-rotation pocket (locator plate, through to Al) + barrel trough in the body
        bar = [bb for bb in d["bars"] if bb["pole"] == pole][0]
        edge_b = bar["y0"] if ex < 0 else bar["y1"]
        edge_body = b["y0"] + b["wall"] if ex < 0 else b["y1"] - b["wall"]
        sw, tw, rr = spec.pocket_slot(lug), spec.trough_w(lug), spec.pocket_ring(lug)
        S.rect(X(x - sw / 2), Y(y), X(x + sw / 2), Y(edge_b), c, 0.3, c, op=0.10)
        if d.get("metal_pockets"):
            S.rect(X(x - tw / 2), Y(y + ex * rr / 2), X(x + tw / 2), Y(edge_b), c, 0.3, c, "1.2,0.6", 0.10)
        else:
            S.rect(X(x - tw / 2), Y(edge_b), X(x + tw / 2), Y(edge_body), c, 0.3, c, "1.2,0.6", 0.06)
        S.circle(X(x), Y(y), rr / 2, c, 0.3, "none")
        S.circle(X(x), Y(y), L["b"] / 2, c, 0.25)
        S.circle(X(x), Y(y), 4 if L["stud"] == "M8" else 5, c, 0.35, "white")
        S.text(X(x), Y(y) + 0.9, str(n), 2.4, c, "middle", True)
        edge = b["y0"] if ex < 0 else b["y1"]
        S.arrow(X(x), Y(edge), X(x), Y(edge + ex * 9), c)
        w_, h_ = spec.notch(d, stud=(x, y, lug, ex, pole, label))
        rows.append((str(n), pole, label, L["stud"], lug, "%.0fx%.0f" % (w_, h_), "fwd" if ex < 0 else "rear"))
    for (x, fy, dr, pole, label) in d["ports"]:
        n += 1
        c = pole_color(pole, label)
        pp = d["port"]
        S.rect(X(x - pp["bore"] / 2), Y(fy), X(x + pp["bore"] / 2), Y(fy + dr * pp["depth"]), c, 0.3, c, "1.2,0.8", 0.12)
        for so in pp["screws"]:
            S.circle(X(x), Y(fy + dr * so), 4, c, 0.25)
        S.text(X(x), Y(fy + dr * 14) + 0.9, str(n), 2.4, c, "middle", True)
        edge = b["y0"] if dr > 0 else b["y1"]
        S.arrow(X(x), Y(edge), X(x), Y(edge - dr * 9), c)
        w_, h_ = spec.notch(d, port=(x, fy, dr, pole, label))
        rows.append((str(n), pole, label, "D13.5", "H50,0/25", "%.0fx%.0f" % (w_, h_), "fwd" if dr > 0 else "rear"))

    for (lx, ly, lp, ll) in d.get("links", []):
        n += 1
        rows.append(("L", lp, ll + " (strap)", "M8", "link strap", "-", "-"))

    # dims (top view)
    S.dim_h(X(xmin), X(xmax), Y(b["y1"]) - 14, Y(b["y1"]), "%.0f overall (flanges)" % (xmax - xmin))
    S.dim_h(X(b["x0"]), X(b["x1"]), Y(b["y1"]) - 8, Y(b["y1"]), "%.0f body" % (b["x1"] - b["x0"]))
    S.dim_v(Y(b["y1"]), Y(b["y0"]), X(xmin) - 6, X(b["x0"]), "%.0f" % (b["y1"] - b["y0"]))
    f0 = fl[0]
    s0, s1 = f0["slots"][0], f0["slots"][1]
    S.dim_v(Y(s1[1]), Y(s0[1]), X(xmin) - 12, X(s0[0]), "%.0f slots" % (s1[1] - s0[1]))
    S.text(X(fl[1]["x1"]) + 1.5, Y(fl[1]["slots"][1][1]) + 1, "4x M6 slot 6.6x12 (along y)", 2.2, "#222")
    S.text(X(fl[1]["x1"]) + 1.5, Y(fl[1]["slots"][1][1]) + 4, "slot c-c %.0f" % (fl[1]["slots"][0][0] - fl[0]["slots"][0][0]), 2.2, "#222")
    # stud pitch chain along front row
    fr = sorted(set(s[0] for s in d["studs"] if s[3] < 0 and s[4] == "POS"))
    ychain = Y(b["y0"]) + 17
    if len(fr) > 1:
        for a, c2 in zip(fr, fr[1:]):
            S.dim_h(X(a), X(c2), ychain, ychain - 2, "%.0f" % (c2 - a), above=False)
    # pole gap
    pos = [bb for bb in d["bars"] if bb["pole"] == "POS"][0]
    neg = [bb for bb in d["bars"] if bb["pole"] == "NEG"][0]
    if bar_d["axis"] == "x":
        g = neg["x0"] - pos["x1"]
        S.dim_h(X(pos["x1"]), X(neg["x0"]), Y(b["y0"]) + 24, Y(b["y0"]), "pole gap %.0f (incl. 4 wall)" % g, above=False)
    else:
        g = neg["y0"] - pos["y1"]
        xg = X(neg["x1"]) + 30
        S.dim_v(Y(neg["y0"]), Y(pos["y1"]), xg, X(neg["x1"]), "gap %.0f" % g)

    # ---- front elevation (looking at -y face), below
    ez = oy - d["body"]["y0"] + 34 + d["ceiling"] + spec.COVER_TOP   # page y of z=0
    Z = lambda z: ez - z
    S.text(X(xmin), Z(d["ceiling"] + spec.COVER_TOP) - 6, "FRONT ELEVATION (cover on, dashed = cover)", 2.6, bold=True)
    for f in fl:
        S.rect(X(f["x0"]), Z(0), X(f["x1"]), Z(6), "#000", 0.3)
    S.rect(X(b["x0"]), Z(0), X(b["x1"]), Z(spec.FLOOR), "#000", 0.35)
    S.rect(X(b["x0"]), Z(spec.FLOOR), X(b["x1"]), Z(spec.RIM_TOP), "#000", 0.25)
    S.rect(X(b["x0"]), Z(spec.RIM_TOP), X(b["x1"]), Z(d["ceiling"] + spec.COVER_TOP), "#555", 0.3, dash="2,1")
    for bar in d["bars"]:
        c = PCOL[bar["pole"]]
        if "lands" in bar:
            for (y0, y1, top) in bar["lands"]:
                S.rect(X(bar["x0"]), Z(spec.FLOOR), X(bar["x1"]), Z(top + d.get("bar_raise", 0)), c, 0.3, c, op=0.08)
        else:
            S.rect(X(bar["x0"]), Z(spec.FLOOR), X(bar["x1"]), Z(bar["field_top"]), c, 0.3, c, op=0.08)
            for (bx0, bx1) in bar["blocks"]:
                S.rect(X(bx0), Z(spec.FLOOR), X(bx1), Z(bar["block_top"]), c, 0.3, c, op=0.1)
    for (x, y, lug, ex, pole, label) in d["studs"]:
        size = spec.LUGS[lug]["stud"]
        bar = [bb for bb in d["bars"] if bb["pole"] == pole][0]
        top = bar["lands"][0 if y < 0 else 1][2] if "lands" in bar else bar["field_top"]
        Lb = spec.bolt_len(size, top - spec.FLOOR)
        zt = spec.FLOOR + spec.BOLT[size]["k"] + Lb
        dn = float(size[1:])
        S.rect(X(x - dn / 2), Z(top), X(x + dn / 2), Z(zt), "#777", 0.2, "#bbb", op=0.6)
    for (x, fy, dr, pole, label) in d["ports"]:
        if dr > 0:
            S.circle(X(x), Z(d["port"]["zc"]), d["port"]["bore"] / 2, POSC, 0.3)
    S.dim_v(Z(0), Z(d["ceiling"] + spec.COVER_TOP), X(xmin) - 6, X(xmin), "%.0f" % (d["ceiling"] + spec.COVER_TOP))
    if "lands" in pos:
        tb_ = pos["lands"][0][2] + d.get("bar_raise", 0)
        S.dim_v(Z(spec.FLOOR), Z(tb_), X(pos["x0"]) + 6, X(pos["x0"]), "%.0f" % (tb_ - spec.FLOOR))
        S.text(X(pos["x0"]) + 8, Z(pos["lands"][1][2]) - 1, "rear land +%.0f (stepped)" % (pos["lands"][1][2] - pos["lands"][0][2]), 2.1, POSC)
    else:
        S.dim_v(Z(spec.FLOOR), Z(pos["block_top"]), X(pos["x0"]) + 6, X(pos["x0"]), "%.0f" % (pos["block_top"] - spec.FLOOR))
        S.text(X(pos["blocks"][0][1]) + 2, Z(pos["field_top"]) - 1, "stud field %.0f thick" % (pos["field_top"] + d.get("bar_raise", 0) - spec.FLOOR), 2.1, POSC)

    # ---- stud map table
    tx, ty = 300 if X(xmax) < 290 else X(xmax) + 10, 215
    tx = max(tx, 20)
    tx, ty = 20, 247
    S.text(tx, ty, "STUD / PORT MAP (red +, blue -, grey spare; arrows = wire exit; exit WxH = cover wire opening; all etched on cover)", 2.8, bold=True)
    cols = [0, 6, 16, 62, 74, 90, 108]
    hdr = ("#", "pole", "connection (gauge per harness)", "stud", "lug/ferrule", "exit WxH", "dir")
    for i, h in enumerate(hdr):
        S.text(tx + cols[i], ty + 5, h, 2.3, "#000", bold=True)
    half = (len(rows) + 1) // 2
    for k, r in enumerate(rows):
        cx = tx + (0 if k < half else 125)
        cy = ty + 9 + (k if k < half else k - half) * min(3.6, (288.0 - ty - 9) / half)
        if k == half:
            for i, h in enumerate(hdr):
                S.text(tx + 125 + cols[i], ty + 5, h, 2.3, "#000", bold=True)
        c = pole_color(r[1], r[2])
        for i, v in enumerate(r):
            S.text(cx + cols[i], cy, v, 2.2, c)
    nx = 275
    notes = [
        "NOTES",
        "1. Lugs: Klauke R-series Cu tin-plated. 1/0 -> 6R10 (50 mm2 M10, b20 l39 d4 14);",
        "   4 AWG -> 4R8 (25 mm2 M8, b16 l32 d4 10); 8 AWG -> 2R8 (10 mm2 M8, b15 l25).",
        "   Min lug-to-lug gap 4 mm (rule >= 3). No stacking.",
        "2. Studs: ISO 4017 hex bolt A2-70, head in hex pocket in Al underside (anti-rotation),",
        "   captured by printed floor. Lug clamps on bare Al face: washer ISO 7089 +",
        "   DIN 6796 conical spring washer + ISO 4032 nut, all A2.",
        "3. Bars: 6061-T6 (or 6101-T6). Contact faces bare, no anodize; Scotch-Brite + anti-oxidant",
        "   (e.g. Penetrox A) at assembly; tin lugs. NO metal through the floor: see sheet 2 (isolation)." if not d.get("metal_pockets") else
        "   (e.g. Penetrox A). Hold-down: 2x M4 per bar into blind inserts in printed bosses (sheet 2).",
        "4. Body + cover: ASA, 4+ walls, 40% infill. Cover: 2x M4 into heat-set inserts in",
        "   barrier bosses. Barrier wall runs to the cover ceiling.",
        "5. Pole clearance >= gap shown (through air, blocked by wall); creepage over wall",
        "   > 90 mm. IEC 60664-1 needs ~1.9 mm at 50 V / PD3 - margin is for tools/loose lugs.",
    ]
    if d["ports"]:
        notes += ["6. Ports: bore 13.5 x 28 deep for Weidmueller H50,0/25 (collar 13); 2x M8 x 12",
                  "   ISO 4029 cup set screws in M8 stainless coil inserts (1D). Re-torque after 1st heat cycle."]
    if d.get("metal_pockets"):
        notes += ["%d. Anti-rotation pockets MACHINED IN THE Al: bar +%.0f, pocket %.0f deep to the contact face. Ring/tongue" % (7 if d["ports"] else 6, d["bar_raise"], d["bar_raise"]),
                  "   b+0.6 (ring >= washer OD+0.6); dashed = barrel relief d4+1 to land-d4/2-0.5. Lug floor = bare Al."]
    else:
        notes += ["%d. Anti-rotation pockets: printed locator plate %.0f thick on each Al land, pockets cut THROUGH" % (6 if not d["ports"] else 7, spec.POCKET["T"]),
                  "   (lug sits on bare Al). Pocket = lug ring/tongue b+0.6 (ring >= washer OD+0.6); body barrel",
                  "   trough d4+1 to the wall sets the wire exit. Solid outline = pocket, dashed = trough."]
    if d.get("links"):
        notes += ["8. UNIVERSAL bar U (3x M8, 4R8 keep-out) is separate; ONE Al link strap 6x20, pitch %.1f, ties it" % d["strap"]["pitch"],
                  "   to NEG (through notch N in the U/NEG wall) or to POS (through notch P in the main barrier).",
                  "   Unused notch = printed plug, held by the cover; spare plug parks in its socket. No strap = U floating",
                  "   (strap in the stow slot). Only one strap exists, so it can never bridge POS to NEG."]
    if d.get("links"):
        notes.append("   Strap drawn solid = installed (U-NEG); dashed = the alternative position (U-POS).")
    if d.get("fuse_option"):
        fo = d["fuse_option"]
        notes += ["9. FUSED U option: link pitch %.1f = %s;" % (fo["pitch"], fo["name"].split(",")[0]),
                  "   it bolts to the same link studs in place of the strap (notches %.1f deep, U relief for its body)." % (d["notch_z0"]),
                  "   Fuse only the U-POS position; rating <= the smallest wire on U (else fuse each U circuit downstream)."]
    notes_on_sheet2 = X(b["x1"]) > 268            # long part: the elevation needs the full width, notes go to sheet 2
    y_n = min(238, 289 - len(notes) * 2.9)
    for i, s in enumerate([] if notes_on_sheet2 else notes):
        S.text(nx, y_n + i * 2.9, s, 2.15 if i else 2.6, "#000", bold=(i == 0))
    p = os.path.join(out_dir, "%s_drawing.svg" % d["name"])
    S.save(p)
    sheet2(d, out_dir, p.replace(".svg", ".pdf"), notes if notes_on_sheet2 else None)
    return p


def sheet2(d, out_dir, pdf, notes=None):
    """Sheet 2: isolation sections (Fusion section renders) + isolation table."""
    n = d["name"]
    rep_ = json.load(open(os.path.join(out_dir, n + "_report.json")))
    iso = rep_["isolation"]
    doc = fitz.open(pdf)
    pg = doc.new_page(width=doc[0].rect.width, height=doc[0].rect.height)
    k = pg.rect.width / 420.0                      # pt per mm
    pg.draw_rect(fitz.Rect(5 * k, 5 * k, 415 * k, 292 * k), width=1.4)
    pg.insert_text((10 * k, 13 * k), "ST185 bus bar - Design %s - sheet 2: electrical isolation from the car body" % n, fontsize=12, fontname="hebo")
    sy, sx = d["section_y"], d["section_x"]
    imgs = [("SECTION 1 - plane y = %.1f, looking +y (studs, floor, mounting screws)" % sy, n + "_section_mount.png"),
            ("SECTION 2 - plane x = %.1f, looking +x (bar hold-down: %s)" % (sx, "M4 screw, printed boss, blind insert" if d.get("metal_pockets") else "tab, M4 screw, blind insert"), n + "_section_clamp.png")]
    if d.get("sections") and len(d["sections"]) > 2:
        ax_, at_, _, cap_ = d["sections"][2]
        imgs.append(("SECTION 3 - plane %s = %.1f (%s)" % (ax_, at_, cap_), n + "_section_link.png"))
    wcol = 400.0 / len(imgs)
    for i, (cap, fn) in enumerate(imgs):
        r = fitz.Rect((10 + i * wcol) * k, 22 * k, (10 + i * wcol + wcol - 6) * k, (22 + 123) * k)
        pg.insert_text((r.x0, r.y0 - 2), cap, fontsize=7.5 if len(imgs) < 3 else 5.6, fontname="hebo")
        pg.insert_image(r, filename=os.path.join(out_dir, fn), keep_proportion=True)
    F = spec.FLOOR
    lines = [
        "ISOLATION (12 V system, 250 A class)  -  no metal path from any conductor to the mounting face",
        "- Conductors = aluminium bars, stainless studs (ISO 4017), set screws (B), lugs/ferrules. All sit on a SOLID printed floor,",
        "  min %.1f mm thick under every aluminium part and every stud head (stud heads are flush with the bar underside;" % F,
        "  the nut end is on top). There are no holes through the floor anywhere under a conductor.",
        ("- Bars held down by %d x %s (2 per bar), counterbored in the bar between stud columns, into" % (len(d["bar_screws"]), spec.BAR_SCREW["screw"])
         if d.get("metal_pockets") else
         "- Bars are clamped DOWN by the printed locator plates: %d x %s through plate tabs into" % (len(d["clamps"]), spec.CLAMP["screw"])),
        ("  BLIND %s in a printed boss that rises into a 10.6 x 9 recess in the bar underside;" % spec.CLAMP["insert"]
         if d.get("metal_pockets") else
         "  %s, in %s;" % (spec.CLAMP["insert"], "printed trough fingers" if n == "A" else "printed ledges beside the barrier")),
        ("  the screw and insert are LIVE (bar potential); the insert hole ends at the 4 mm solid floor, nothing goes through it."
         if d.get("metal_pockets") else
         "  insert hole %.0f mm deep, ends inside plastic with >= %.0f mm plastic below it. Clamp screws touch only plastic (floating metal)." % (
             spec.CLAMP["hole_depth"], 16 - spec.CLAMP["hole_depth"])),
        "- Mounting: 4 x %s in 6.6 x 12 slots in the end flanges, outside the body wall;" % spec.MOUNT["screw"],
        "  the screws pass only through plastic flange and never touch a conductor.",
        "",
        "MEASURED in Fusion (min distance, worst conductor = %s):" % iso["worst_face"][0],
        "  conductor -> mounting face:   %.1f mm, all of it SOLID ASA (floor)" % iso["min_to_mount_face"],
        "  conductor -> mounting screw/washer (straight line, cover off):   %.1f mm, through the 3 mm body end wall" % iso["min_to_mount_screw"],
        "CREEPAGE (along surfaces, from geometry): bar end -> floor -> up inside wall (4) -> across rim under the cover skirt (3)",
        "  -> down outside wall:  to mounting face >= 15 mm (8 mm outer wall);  to M6 washer >= 13 mm (2 mm to flange + 4 mm along flange).",
        "REQUIRED: IEC 60664-1 at <= 50 V, pollution degree 3, material group III: creepage ~1.9 mm; clearance (OV cat. II) ~0.2 mm.",
        "  Margin is >= 7x on creepage and the floor is a solid 4 mm barrier, so a crushed or chafed edge cannot short the bar to the body.",
    ]
    y = 160
    for i, t in enumerate(lines):
        pg.insert_text((14 * k, (y + i * 6.2) * k), t, fontsize=8.2 if i else 9.5, fontname="hebo" if i in (0, 10) else "helv")
    if notes:
        pg.insert_text((14 * k, 268 * k), "Sheet 1 notes are on the right (this design is too long for sheet 1).", fontsize=7, fontname="helv")
        for i, t in enumerate(notes):
            pg.insert_text((262 * k, (152 + i * 4.6) * k), t, fontsize=6.4 if i else 8, fontname="hebo" if i == 0 else "helv")
    tmp = pdf + ".tmp"
    doc.save(tmp)
    doc.close()
    os.replace(tmp, pdf)


if __name__ == "__main__":
    # B rev 1 is frozen (its drawing is kept as built); only A rev 2 and B rev 2 are regenerated
    folders = {"A": "design-A", "B_rev2": "design-B-rev2", "A_rev3": "design-A-rev3", "B_rev3": "design-B-rev3"}
    todo = [spec.A3, spec.B3] if "--older" not in sys.argv else [spec.A, spec.B2]
    for d in todo:
        out = os.path.join(ROOT, folders[d["name"]])
        os.makedirs(out, exist_ok=True)
        print(draw(d, out))
