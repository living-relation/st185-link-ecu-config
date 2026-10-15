"""Finish the fuse box close-up renders (render_closeups.py, run in Fusion first): each raw PNG in
cad/fusebox/rev7/renders/closeups/raw/ gets a display-bounds border, a title bar and a key, and is written to
cad/fusebox/rev7/renders/closeups/. On the LOGIC top view (b) the micro relay column centre lines are drawn old (rev 7 before R123,
dashed) and new (solid), with the box edge, scaled from the deck outline found in the image.
    python cad/fusebox/src/finish_closeups.py
Claude Code, 2026-10-15.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spec as S

D = os.path.join(os.path.dirname(HERE), 'rev7', 'renders', 'closeups')
RAW = os.path.join(D, 'raw')
BORDER, BAR = 10, 92
INK, FRAME, PAPER = (20, 24, 30), (40, 44, 52), (246, 246, 242)

KEYS = {
    'closeup_a1_cavity_880398-2.png': [((196, 160, 96), 'terminal (880398-2, simplified)'), ((214, 116, 48), 'locking lances in their window'),
                                       ((165, 168, 170), 'PA12 base, cut through the cavity'), ((214, 178, 60), 'wire')],
    'closeup_a2_cavity_280919-2.png': [((196, 160, 96), 'terminal (280919-2, simplified)'), ((214, 116, 48), 'locking lance in its window'),
                                       ((40, 40, 40), 'RNF-100 build-up'), ((165, 168, 170), 'PA12 base, cut through the cavity')],
    'closeup_b_logic_micro_columns_top.png': [((220, 60, 50), 'before R123 (dashed)'), ((40, 170, 80), 'now: +2.0 mm (solid)')],
    'closeup_c1_r1_retainer_on.png': [((70, 120, 200), 'R1 retainer clip (PA12)'), ((40, 40, 40), 'RNF-100 build-up (cut to the barrel)'),
                                      ((214, 178, 60), 'R1 wires')],
    'closeup_c2_r1_retainer_exploded.png': [((70, 120, 200), 'R1 retainer clip, 22 mm down'), ((214, 178, 60), 'R1 wires')],
    'closeup_d_lid_catch_screw_section.png': [((120, 124, 128), 'cover (PA12)'), ((165, 168, 170), 'base skirt + insert boss (PA12)'),
                                              ((206, 170, 100), 'M3 brass heat-set insert'), ((150, 150, 145), 'M3 x 10 cap screw')],
    'closeup_e_rnf100_buildup_section.png': [((214, 178, 60), 'wire (M22759/16)'), ((40, 40, 40), 'RNF-100-3/32'), ((85, 85, 90), 'RNF-100-1/8'),
                                             ((196, 160, 96), 'crimped insulation barrel + terminal')],
}
SUB = {
    'closeup_a1_cavity_880398-2.png': 'Hole sized by everything that passes (R120); above the neck the cavity steps in to the box: the lances spring out over that ledge (R121). Stop flange under the 3.8 mm shoulder.',
    'closeup_a2_cavity_280919-2.png': 'R123 swap for 2293255-1: same 4.75 tab and 20-15 AWG, with a locking lance. Window on the side with the most room; deck blade slot above = stop.',
    'closeup_b_logic_micro_columns_top.png': 'Micro relay columns %.1f / %.1f -> %.1f / %.1f mm, box %.1f -> %.1f wide: the Bus 2 output ledges keep 2.0 mm walls.' % (
        51.5, 70.0, S.MICRO_COLS[0], S.MICRO_COLS[1], 81.5, S.LOGIC['L']),
    'closeup_c1_r1_retainer_on.png': 'From below. No 8 AWG 6.3 lance terminal exists, so the clip stops every R1 terminal backing out; legs snap into the collar.',
    'closeup_c2_r1_retainer_exploded.png': 'Thread the clip onto the 5 R1 wires before crimping, seat the terminals from below, push the clip up until both legs click.',
    'closeup_d_lid_catch_screw_section.png': 'Optional backup screw %.0f mm from the catch: insert pressed into a boss hung from the deck plate (never floating, R101), walls >= 2.0.' % S.SCREW['off'],
    'closeup_e_rnf100_buildup_section.png': 'Thin-wall wire below the 42281-1 insulation range: two RNF-100 layers bring it into range under the insulation crimp (M6 = A).',
}


def font(sz, bold=False):
    for f in (('segoeuib.ttf' if bold else 'segoeui.ttf'), ('arialbd.ttf' if bold else 'arial.ttf'), 'DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            continue
    return ImageFont.load_default()


def deck_edges(im):
    """x pixels of the LOGIC deck's left / right edge on the row through the middle: the outer ends of the light stretches at least 30 px
    long (the deck is light; its pockets and the 1 px background grid lines are not deck edges)."""
    w, h = im.size
    lit = [sum(im.getpixel((x, h // 2))[:3]) / 3 > 150 for x in range(w)]
    runs, s0 = [], None
    for i, v in enumerate(lit + [False]):
        if v and s0 is None:
            s0 = i
        elif not v and s0 is not None:
            if i - s0 >= 30:
                runs.append((s0, i - 1))
            s0 = None
    return runs[0][0], runs[-1][1]


def dashed(dr, x, y0, y1, col, w=3, on=14, off=10):
    y = y0
    while y < y1:
        dr.line([(x, y), (x, min(y + on, y1))], fill=col, width=w)
        y += on + off


def main():
    notes = json.load(open(os.path.join(RAW, 'closeups.json'), encoding='utf-8'))
    out = []
    for fn in sorted(notes):
        im = Image.open(os.path.join(RAW, fn)).convert('RGB')
        dr = ImageDraw.Draw(im)
        if fn.startswith('closeup_b_'):
            a, b = deck_edges(im)
            k = (b - a) / S.LOGIC['L']                    # deck spans x 0 .. L
            h = im.size[1]
            for j, (xo, xn, lab) in enumerate(((51.5, S.MICRO_COLS[0], 'micro column 1'), (70.0, S.MICRO_COLS[1], 'micro column 2'),
                                               (81.5, S.LOGIC['L'], 'box edge'))):
                po, pn = a + xo * k, a + xn * k
                dashed(dr, po, 40, h - 40, (220, 60, 50))
                dr.line([(pn, 40), (pn, h - 40)], fill=(40, 170, 80), width=3)
                ty = 40 + 64 * j
                dr.rectangle([pn + 4, ty - 2, pn + 250, ty + 54], fill=(250, 250, 248))
                dr.text((pn + 10, ty), '%s: %.1f' % (lab, xn), fill=(20, 110, 50), font=font(22, True))
                dr.text((pn + 10, ty + 28), 'was %.1f (dashed)' % xo, fill=(180, 40, 30), font=font(19))
        W, H = im.size
        page = Image.new('RGB', (W + 2 * BORDER, H + 2 * BORDER + BAR), PAPER)
        page.paste(im, (BORDER, BORDER + BAR))
        d2 = ImageDraw.Draw(page)
        d2.rectangle([0, 0, page.size[0] - 1, page.size[1] - 1], outline=FRAME, width=BORDER)            # display bounds
        d2.rectangle([BORDER - 1, BORDER + BAR - 1, BORDER + W, BORDER + BAR + H], outline=INK, width=2)
        sz = 30
        while sz > 16 and d2.textlength(notes[fn]['title'], font=font(sz, True)) > W - 40:
            sz -= 1
        d2.text((BORDER + 18, BORDER + 10), notes[fn]['title'], fill=INK, font=font(sz, True))
        d2.text((BORDER + 18, BORDER + 52), SUB.get(fn, ''), fill=(70, 74, 80), font=font(20))
        y = BORDER + BAR + H - 34 * len(KEYS.get(fn, [])) - 14
        for (col, lab) in KEYS.get(fn, []):
            x0 = BORDER + 18
            d2.rectangle([x0 - 6, y - 4, x0 + 26 + 11 * len(lab), y + 26], fill=(250, 250, 248))
            d2.rectangle([x0, y + 2, x0 + 18, y + 20], fill=col, outline=INK)
            d2.text((x0 + 26, y), lab, fill=INK, font=font(20))
            y += 34
        d2.text((page.size[0] - BORDER - 16, page.size[1] - BORDER - 30), 'ST185 fuse box rev 7 - DECISIONS R120-R123 - simplified terminal / insert / screw models',
                fill=(90, 94, 100), font=font(16), anchor='ra')
        p = os.path.join(D, fn)
        page.save(p, optimize=True)
        out.append(os.path.relpath(p, os.path.dirname(os.path.dirname(os.path.dirname(HERE)))))
    for p in out:
        print(p)


if __name__ == '__main__':
    main()
