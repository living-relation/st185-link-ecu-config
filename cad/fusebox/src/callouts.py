"""Draw numbered callouts on the fuse box renders (rev 5, Dan's point 11: numbers + a legend, never crowded labels).
Fusion's build records, per image, every callout's number, the screen position of the part it points at and its text
(fusebox_report.json "callouts"). This puts a numbered circle in a column at the left or right edge, a leader line to the
part, and nothing else on the picture - the text goes in the legend under the image on the summary page.
    python cad/fusebox/src/callouts.py <dir with fusebox_report.json + renders>
Claude Code, 2026-10-14.
"""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont

d = sys.argv[1]
rep = json.load(open(os.path.join(d, 'fusebox_report.json')))


def font(sz):
    for f in ('arialbd.ttf', 'arial.ttf', 'DejaVuSans-Bold.ttf'):
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            pass
    return ImageFont.load_default()


F = font(30)
R = 24
for fn, pts in rep.get('callouts', {}).items():
    p = os.path.join(d, fn)
    if not os.path.exists(p):
        continue
    im = Image.open(p).convert('RGB')
    W, H = im.size
    dr = ImageDraw.Draw(im)
    sides = {'L': [], 'R': []}
    for (n, x, y, text) in pts:
        sides['L' if x < W / 2 else 'R'].append((n, x, y))
    for side, items in sides.items():
        items.sort(key=lambda t: t[2])
        k = len(items)
        if not k:
            continue
        top, bot, gap = 40, H - 40, 2 * R + 10
        ys = []
        for (n, x, y) in items:               # each circle at its part's height, pushed down only to clear the one above
            ys.append(max(min(max(y, top), bot), ys[-1] + gap) if ys else min(max(y, top), bot))
        over = ys[-1] - bot
        if over > 0:                          # ran off the bottom: shift up, keeping the spacing
            for i in range(len(ys) - 1, -1, -1):
                lim = bot if i == len(ys) - 1 else ys[i + 1] - gap
                ys[i] = min(ys[i], lim)
        cx = 50 if side == 'L' else W - 50
        for i, (n, x, y) in enumerate(items):
            cy = ys[i]
            ex = cx + (R if side == 'L' else -R)
            dr.line([(ex, cy), (x, y)], fill=(255, 210, 0), width=4)
            dr.line([(ex, cy), (x, y)], fill=(20, 20, 20), width=2)
            dr.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(255, 210, 0), outline=(20, 20, 20), width=2)
            dr.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(255, 210, 0), outline=(20, 20, 20), width=3)
            s = str(n)
            bb = dr.textbbox((0, 0), s, font=F)
            dr.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), s, fill=(20, 20, 20), font=F)
    im.save(p)
    print('callouts on', fn, len(pts))
