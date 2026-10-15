"""Put the cable labels (with leader lines), a title and a footer on the raw renders of render_views_rev7.py.
    python cad/fusebox/src/label_views_rev7.py cad/fusebox/rev7 [raw_dir]
Claude Code, 2026-10-14."""
import json, os, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

RAW = sys.argv[2] if len(sys.argv) > 2 else os.path.join(tempfile.gettempdir(), 'st185_rev7_views')
OUT = sys.argv[1]
D = json.load(open(os.path.join(RAW, 'labels.json')))
F = ImageFont.truetype(r'C:\Windows\Fonts\segoeui.ttf', 21)
FB = ImageFont.truetype(r'C:\Windows\Fonts\segoeuib.ttf', 27)
FS = ImageFont.truetype(r'C:\Windows\Fonts\segoeui.ttf', 19)

NAMES = {   # raw -> (published name, title)
    'power_side_long.png': ('fusebox_power_side_long.png', 'POWER box rev 7 - long side (outboard), 20 deg above: AMI OUT row and the + bar cables end-on, NEG cables out the rear'),
    'power_side_end.png': ('fusebox_power_side_end.png', 'POWER box rev 7 - short end (front), 20 deg above: OUT row and + bar cables out the outboard end, relay tails out the inboard end'),
    'logic_side_long.png': ('fusebox_logic_side_long.png', 'LOGIC box (rev 6, unchanged) - long side (inboard), 20 deg above: Bus 1 feed + tails out the front, Bus 2 feed in at the rear'),
    'logic_side_end.png': ('fusebox_logic_side_end.png', 'LOGIC box - short end (front), 30 deg off-axis so the cables show'),
    'battrelay_side_long.png': ('battrelay_side_long.png', 'Battery relay block (rev 6, unchanged) - long side (front), 20 deg above: feed in one end, pump + coil out the other'),
    'battrelay_side_end.png': ('battrelay_side_end.png', 'Battery relay block - short end (feed end), off-axis'),
    'arr_glove_closed.png': ('fusebox_arrangement_glovebox.png', 'Typical arrangement, glove box: POWER (rev 7) + LOGIC, every cable run on to where it leaves'),
    'arr_glove_rear.png': ('fusebox_arrangement_glovebox_rear.png', 'Typical arrangement, glove box, from the rear: the 1/0 cables out of the bus zone'),
    'arr_glove_open.png': ('fusebox_arrangement_glovebox_open.png', 'Typical arrangement, covers and belly pans off: AMI fuses on the + bar, LOGIC 14 AWG input jumpers'),
    'arr_glove_top.png': ('fusebox_arrangement_glovebox_top.png', 'Typical arrangement, glove box, top view (front of the car at the bottom, outboard / RH door on the right)'),
    'arr_trunk.png': ('fusebox_arrangement_trunk.png', 'Typical arrangement, trunk: battery relay block on its own with its 3 cables'),
}
FOOT = 'Wire colours and ident bands from the harness drawings (CabinPower, EngineRoom-C, HeavyDC). Render only - no design change. Claude Code, 2026-10-14.'


def wrap(text, n=44):
    out, cur = [], ''
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > n:
            out.append(cur)
            cur = w
        else:
            cur = (cur + ' ' + w).strip()
    out.append(cur)
    return out


def _leader(b):
    ex = b[0] + b[2] if b[7] == 'L' else b[0]
    return (ex, b[1] + b[3] / 2), (b[4], b[5])


def _cross(p1, p2, q1, q2):
    d = lambda a, b, c: (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return (d(p1, p2, q1) * d(p1, p2, q2) < 0) and (d(q1, q2, p1) * d(q1, q2, p2) < 0)


def untangle(col):
    """Swap the anchors (and texts) of two boxes in one column while their leader lines cross; box slots stay."""
    for _ in range(200):
        done = True
        for i in range(len(col)):
            for j in range(i + 1, len(col)):
                if _cross(*_leader(col[i]), *_leader(col[j])):
                    a, b = col[i], col[j]
                    if len(a[6]) != len(b[6]):
                        continue          # only same-height boxes swap
                    a[4], b[4] = b[4], a[4]
                    a[5], b[5] = b[5], a[5]
                    a[6], b[6] = b[6], a[6]
                    a[2] = b[2] = max(a[2], b[2])
                    if a[7] == 'R':
                        a[0] = b[0] = min(a[0], b[0])
                    done = False
        if done:
            return


def place(labels, W, H, top):
    """Labels in a column on the side of their anchor, sorted by height, stacked so no two boxes overlap."""
    cx = W / 2
    boxes = []
    for side in ('L', 'R'):
        items = sorted([l for l in labels if (l[0] < cx) == (side == 'L')], key=lambda l: l[1])
        col = []
        y_next = top + 8
        for (ax, ay, text) in items:
            lines = wrap(text)
            tw = max(F.getbbox(t)[2] for t in lines) + 16
            th = 26 * len(lines) + 6
            bx = 10 if side == 'L' else W - tw - 10
            by = max(y_next, min(ay - th / 2, H - 44 - th))
            col.append([bx, by, tw, th, ax, ay, lines, side])
            y_next = by + th + 6
        over = y_next - (H - 40)
        if over > 0:
            for b in col:
                b[1] -= over
        untangle(col)
        boxes += col
    return boxes


def main():
    os.makedirs(OUT, exist_ok=True)
    for raw, (pub, title) in NAMES.items():
        p = os.path.join(RAW, raw)
        if not os.path.exists(p):
            print('missing', raw)
            continue
        im = Image.open(p).convert('RGB')
        W, H = im.size
        dr = ImageDraw.Draw(im)
        dr.rectangle([0, 0, W, 46], fill=(28, 28, 30))
        dr.text((14, 7), title, font=FB, fill=(245, 245, 240))
        dr.rectangle([0, H - 34, W, H], fill=(28, 28, 30))
        dr.text((14, H - 30), FOOT, font=FS, fill=(210, 210, 205))
        labels = D['labels'].get(raw, [])
        boxes = place(labels, W, H, 52)
        for (bx, by, tw, th, ax, ay, text, side) in boxes:          # every leader first, then every box on top
            ex = bx + tw if side == 'L' else bx
            dr.line([(ex, by + th / 2), (ax, ay)], fill=(20, 20, 20), width=5)
            dr.line([(ex, by + th / 2), (ax, ay)], fill=(255, 214, 0), width=2)
            dr.ellipse([ax - 6, ay - 6, ax + 6, ay + 6], fill=(255, 214, 0), outline=(20, 20, 20), width=2)
        for (bx, by, tw, th, ax, ay, text, side) in boxes:
            dr.rounded_rectangle([bx, by, bx + tw, by + th], radius=6, fill=(255, 255, 250), outline=(20, 20, 20), width=2)
            for i, t in enumerate(text):
                dr.text((bx + 8, by + 2 + 26 * i), t, font=F, fill=(15, 15, 15))
        im.save(os.path.join(OUT, pub), optimize=True)
        print('wrote', pub, len(labels), 'labels')


main()
