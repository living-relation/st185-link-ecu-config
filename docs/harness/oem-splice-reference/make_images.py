"""Crop + highlight OEM connector drawings from the repair-manual repo for the splice reference.
Run: python make_images.py   (writes img/*.png next to this script)
All coordinates are pixels of the page rendered at the stated dpi (see marks below).
"""
import fitz, os, shutil
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, 'img')
CIRC = r'C:\projects\active\st185-celica-repair-manual\electrical\circuits'
MAN = r'C:\projects\active\st185-celica-repair-manual\manuals-electrical'
SNIPS = r'C:\projects\active\st185-link-ecu-config\docs\electrical\ewd-snips'
RED = (230, 0, 0)
ORG = (255, 140, 0)
BLU = (0, 90, 255)
try:
    FONT = ImageFont.truetype('arialbd.ttf', 22)
except Exception:
    FONT = ImageFont.load_default()


def render(pdf, idx, dpi):
    doc = fitz.open(pdf)
    pix = doc[idx].get_pixmap(dpi=dpi)
    return Image.frombytes('RGB', (pix.width, pix.height), pix.samples)


def make(out, pdf, idx, dpi, box, marks, scale=3, title=None):
    """marks: list of (x, y, r, colour, label-or-None) in page px at dpi."""
    im = render(pdf, idx, dpi)
    x0, y0, x1, y1 = box
    cr = im.crop(box).resize(((x1 - x0) * scale, (y1 - y0) * scale), Image.LANCZOS)
    dr = ImageDraw.Draw(cr)
    for (x, y, r, col, lab) in marks:
        X, Y, R = (x - x0) * scale, (y - y0) * scale, r * scale
        dr.ellipse([X - R, Y - R, X + R, Y + R], outline=col, width=max(3, scale))
        if lab:
            tw = dr.textlength(lab, font=FONT)
            tx = X + R + 3 if X + R + 3 + tw < cr.width else X - R - 3 - tw
            ty = Y + R + 1
            dr.rectangle([tx - 2, ty - 1, tx + tw + 2, ty + 24], fill=(255, 255, 255))
            dr.text((tx, ty), lab, fill=col, font=FONT)
    if title:
        tmp = ImageDraw.Draw(cr)
        lines, cur = [], ''
        for w in title.split(' '):
            t = (cur + ' ' + w).strip()
            if tmp.textlength(t, font=FONT) > cr.width - 12 and cur:
                lines.append(cur)
                cur = w
            else:
                cur = t
        lines.append(cur)
        pad = 8 + 28 * len(lines)
        canvas = Image.new('RGB', (cr.width, cr.height + pad), 'white')
        cd = ImageDraw.Draw(canvas)
        for i, ln in enumerate(lines):
            cd.text((6, 4 + 28 * i), ln, fill=(0, 0, 0), font=FONT)
        canvas.paste(cr, (0, pad))
        cr = canvas
    cr.save(os.path.join(IMG, out))
    print('wrote', out, cr.size)


def pins(table, ox, oy, s, sel, col):
    """table: {pin:(X,Y)} in zoomed-crop px (origin ox,oy, zoom s) -> page-px marks for pins in sel."""
    return [(ox + table[p][0] / s, oy + table[p][1] / s, 6, col, None) for p in sel if p in table]


RL = CIRC + r'\tis1993-relay-locations.pdf'
WR2 = CIRC + r'\tis1993-wiring-routing-2.pdf'
WR = CIRC + r'\tis1993-wiring-routing.pdf'

# ---- 1. Instrument-panel overview (where J/B1, J/B3, R/B2, R/B4, A/C amp sit) ----
make('loc_relay_blocks.png', RL, 0, 130, (60, 755, 1000, 1340), [
    (150, 1110, 60, RED, 'J/B 1'), (215, 1175, 38, RED, 'R/B 2'),
    (455, 910, 42, RED, 'J/B 3'), (640, 980, 38, RED, 'R/B 4'),
    (640, 1039, 22, BLU, 'A/C amp (approx)')], 1,
    '1993 EWD p.18 - instrument panel: relay / junction block locations')

# ---- 2. J/B No.1 plugs (1993 EWD p.20) ----
# 1H: harness plug (left) and J/B receptacle (right), pins 2 4 5 6 7 8 used
h_h = {8: (85, 385), 7: (97, 385), 6: (107.5, 385), 5: (118, 385), 4: (125.5, 385), 3: (85, 400), 2: (117, 400), 1: (126, 400)}
h_j = {4: (254, 385), 5: (264.5, 385), 6: (274, 385), 7: (283, 385), 8: (294, 385), 1: (254, 399.5), 2: (265, 399.5), 3: (294, 399.5)}
sel = [2, 4, 5, 6, 7, 8]
marks = [(h_h[p][0], h_h[p][1], 6, RED, None) for p in sel] + [(h_j[p][0], h_j[p][1], 6, RED, None) for p in sel]
make('jb1_1H.png', RL, 2, 130, (55, 360, 320, 425), marks, 5, 'J/B No.1 plug 1H - LEFT: harness-side plug (from engine room main wire), RIGHT: J/B receptacle. Pins 2 4 5 6 7 8 circled')
make('jb1_1I.png', RL, 2, 130, (335, 365, 590, 470), [(374.5, 392, 8, RED, None), (545.6, 408.8, 8, RED, None)], 4,
     'J/B No.1 plug 1I (1 pin) - LEFT: J/B receptacle, RIGHT: harness plug (from engine room main wire). Pin 1 circled')
f_j = {1: (305, 721), 2: (317.5, 721), 3: (355, 721)}
f_h = {1: (585.5, 721), 2: (576, 721), 3: (524, 721)}
marks = [(f_j[p][0], f_j[p][1], 6, RED, None) for p in f_j] + [(f_h[p][0], f_h[p][1], 6, RED, None) for p in f_h]
make('jb1_1F.png', RL, 2, 130, (280, 662, 612, 768), marks, 4, 'J/B No.1 plug 1F (14 pin, dark gray, from floor wire) - LEFT: J/B receptacle, RIGHT: harness plug. Pins 1 2 3 circled')

# ---- 3. IE1 (1993 EWD p.43), both halves ----
L = {'X': (140, 225), 2: (222, 225), 3: (305, 225), 7: (142, 345), 8: (225, 345), 9: (305, 345), 14: (140, 470), 15: (228, 470), 16: (310, 470),
     10: (540, 310), 17: (540, 435), 4: (675, 222), 6: (838, 222), 11: (668, 342), 12: (752, 342), 13: (835, 342), 18: (668, 468), 19: (752, 468), 20: (838, 468)}
R = {6: (165, 255), 4: (325, 255), 13: (155, 378), 12: (245, 378), 11: (325, 378), 20: (155, 505), 19: (245, 505), 18: (330, 505), 10: (445, 350), 17: (445, 470),
     3: (762, 252), 2: (842, 252), 9: (762, 378), 8: (842, 378), 7: (922, 378), 16: (762, 500), 15: (842, 500), 14: (922, 500)}
ACTIVE = [3, 10, 12, 17, 19]
SKIPDEV = [2, 11, 18, 6, 13, 20, 7, 8, 9, 14, 15, 16]
marks = pins(L, 95, 515, 6, ACTIVE, RED) + pins(L, 95, 515, 6, SKIPDEV, ORG) + pins(R, 270, 505, 6, ACTIVE, RED) + pins(R, 270, 505, 6, SKIPDEV, ORG)
make('ie1.png', WR2, 7, 130, (95, 500, 460, 625), marks, 3,
     'IE1 (20 pin, blue, left kick panel) both mating halves. RED = taps for kept circuits (3 10 12 17 19); ORANGE = pins for headlight / wiper / retract circuits')

# ---- 4. IG2 ----
IGL = {15: (525, 255), 16: (615, 255)}
IGR = {16: (520, 272), 15: (590, 272)}
marks = pins(IGL, 115, 995, 5, [15, 16], RED) + pins(IGR, 345, 990, 5, [15, 16], RED)
make('ig2.png', WR2, 7, 130, (110, 985, 590, 1072), marks, 3, 'IG2 (20 pin, dark gray, under the engine ECU) both mating halves. Pins 15 and 16 circled')

# ---- 5. J/B No.3 plug 3B pin 9 (1993 EWD p.25) ----
make('jb3_3B_jb_side.png', RL, 7, 130, (435, 355, 620, 475), [(497.5, 423, 8, RED, None)], 4, 'J/B No.3 plug 3B - J/B receptacle side. Pin 9 circled')
make('jb3_3B_cowl_side.png', RL, 7, 130, (735, 335, 925, 485), [(860.8, 412, 8, RED, None)], 4, 'J/B No.3 plug 3B - cowl-wire plug side. Pin 9 circled')

# ---- 6. R/B2 and R/B4 (1993 EWD p.26-27) ----
make('rb2.png', RL, 8, 130, (450, 505, 700, 660), [(543, 574, 9, RED, None), (486, 574, 9, RED, None), (626, 560, 9, ORG, None)], 4,
     'R/B No.2 (left kick): Power Main Relay pins 1 and 2 circled (red); 30A fuse pin 2 (orange) = possible W-L lead, verify')
make('rb4.png', RL, 9, 130, (440, 335, 690, 445), [(492.4, 378, 8, RED, None), (610, 376, 8, RED, None), (633.6, 376, 8, RED, None)], 4,
     'R/B No.4 (right kick): starter relay (M/T) pin 1; heater relay pins 1 and 3 circled')

# ---- 7. Where the part plugs are (1993 + 1990 locator pages) ----
make('loc_dash_1993.png', WR, 4, 110, (40, 85, 870, 650), [
    (68, 408, 16, RED, None), (340, 160, 16, RED, None), (373, 160, 16, RED, None), (436, 132, 16, RED, None),
    (358, 132, 16, BLU, None), (803, 325, 16, RED, None), (832, 310, 16, RED, None)], 1,
    '1993 EWD p.32 parts: C11 clutch start SW, C12/C13/C14 cluster, C16 cruise stalk (blue), A15 A/C amp, B4 blower')
make('loc_dash_1993_b.png', WR, 5, 110, (60, 85, 900, 650), [(316, 141, 16, RED, None)], 1, '1993 EWD p.33 - parts in instrument panel: S9 stop light switch')
make('loc_rear_lamps.png', WR, 6, 110, (40, 85, 880, 660), [
    (815, 404, 16, RED, None), (815, 541, 16, RED, None), (815, 503, 16, RED, None), (815, 326, 16, RED, None)], 1,
    '1993 EWD p.34 - parts in body (L/B): rear combination lamps R11/R12, licence light L1, high-mount stop H6')

# ---- 8. Schematic crops with the tapped pins circled ----
CM = CIRC + r'\tis1993-combination-meter.pdf'
make('sch_cluster_1.png', CM, 0, 110, (60, 400, 700, 680), [(88, 490, 11, RED, None), (191, 490, 11, RED, None), (241, 490, 11, RED, None), (299, 630, 11, RED, None)], 2,
     '1993 EWD p.206 combination meter: C13(B) pins 12 2 11 (top row), C14(C) pin 1 R-G park brake')
make('sch_cluster_2.png', CM, 1, 110, (480, 400, 880, 680), [(633, 490, 11, RED, None), (633, 630, 11, RED, None)], 2,
     '1993 EWD p.207 combination meter: C14(C) pin 9 B-O (IG feed) and pin 8 Y (charge lamp)')
make('sch_cruise_1990.png', CIRC + r'\ewd1990-cruise-control.pdf', 0, 110, (600, 480, 880, 1010), [(648, 738, 11, RED, None), (714, 738, 11, RED, None), (648, 946, 11, RED, None)], 2,
     '1990 EWD p.118 cruise switch C14 (comb. SW): pins 15 Y-B, 5 W, 17 BR circled')
make('sch_start_1993.png', CIRC + r'\tis1993-starting-ignition-all-trac-4wd.pdf', 0, 110, (360, 280, 860, 720), [(795, 626, 11, RED, None), (437, 363, 11, RED, None)], 2,
     '1993 EWD p.66: clutch start SW C11 pin 1 (B) and starter relay coil pin 1 (B-W)')
make('sch_stop_1993.png', CIRC + r'\tis1993-stop-light.pdf', 0, 110, (200, 180, 800, 880), [
    (413, 343, 11, RED, None), (262, 781, 11, RED, None), (415, 781, 11, RED, None), (722, 793, 11, RED, None)], 1,
    '1993 EWD p.126 stop light: S9 pin 1 (G-W), R11 pin 1, R12 pin 1, H6 pin 1')

# ---- 9. Mitchell A/C amplifier face (manual A/C, 18 pin) with pins 11 and 13 circled ----
make('acamp_face.png', MAN + r'\1993 Celica Service Manual (Mitchell) - Electrical.pdf', 6, 100, (90, 170, 800, 480), [(297, 342, 22, RED, '11'), (415, 332, 22, RED, '13')], 1,
     'Mitchell 1993 Fig.5: A/C amplifier harness connector (18 pin), pins 11 and 13 circled')

# ---- 9b. 1993 manual A/C pages (printed 222-223): A15 amp pins 11 and 13, blower B4 pin 2 ----
HM = CIRC + r'\tis1993-hvac-manual-manual-air-conditioner.pdf'
make('sch_ac_223.png', HM, 1, 110, (60, 95, 700, 880), [(217, 790, 11, RED, None), (622, 178, 11, RED, None)], 2,
     '1993 EWD p.223 (manual A/C): A15 amplifier pin 11 G-Y (from engine ECU) and blower motor B4 pin 2 (B)')
make('sch_ac_222.png', HM, 0, 110, (420, 560, 880, 800), [(705, 722, 11, RED, None)], 2,
     '1993 EWD p.222 (manual A/C): A15 amplifier pin 13 Y-R (to A/C pressure switch / ECU)')
