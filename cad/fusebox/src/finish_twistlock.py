"""Titles and notes on the twist-lock section renders (render_twistlock.py writes the raw PNGs). Plain Python + PIL.
    python cad/fusebox/src/finish_twistlock.py
Claude Code, 2026-11-16.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, '..', 'rev8', 'renders', 'twistlock')


def font(sz, bold=False):
    for f in (('arialbd.ttf' if bold else 'arial.ttf'), 'DejaVuSans%s.ttf' % ('-Bold' if bold else '')):
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            pass
    return ImageFont.load_default()


def main():
    info = json.load(open(os.path.join(DIR, 'raw', 'twistlock_render.json')))
    t = info['c86']
    rl = '%s %s' % (info['box'], info['relay'])
    e = info['engage']
    common = ('TE 42281-1, 18 AWG %.2f - %.2f (M22759/16 min to GXL max), crimped %.2f - %.2f with RNF-100 where needed. Slot %.2f x %.2f, '
              'ledge %.2f a side, recess %.1f deep, chamber %.2f square, gap over the box %.1f.' % (
                  t['od_range'][0], t['od_range'][1], t['crimp_range'][0], t['crimp_range'][1], t['slot'][1] - t['slot'][0],
                  t['slot'][3] - t['slot'][2], t['bear'], info['d_r'], t['chamber'], info['gap']))
    blade = ('Relay blade 6.3 x 0.8, 11 +-0.5 below the body (TE F7 data sheet): it goes %.1f into the box (%.1f - %.1f), '
             'past the 8.0 tab mating length, short of the 10.25 box end.' % (e[1], e[0], e[2]))
    pages = {
        'twistlock_1_section_85_passing_86_seated.png': ('%s coil terminals, section through 85 and 86' % rl,
                                                          ['Left, 85: PASSING - box turned 90 deg, going up the slot (only way it fits).',
                                                           'Right, 86: SEATED - turned back to the blade direction, dropped into its recess.', common]),
        'twistlock_2_section_86_seated_on_ledge.png': ('%s 86 seated, section across the blade' % rl,
                                                       ['Box ends sit on the ledge either side of the slot: it cannot pull out.',
                                                        'Recess walls stop it turning back. Relay blade comes down through the deck slot.', common]),
        'twistlock_3_section_85_passing_slot.png': ('%s 85 passing, section across the blade' % rl,
                                                    ['Turned 90 deg, the box is narrow enough for the slot; the crimped barrels follow.',
                                                     'Up into the chamber, turn 90 deg, pull the wire back down to seat.', common]),
        'twistlock_5_section_86_blade_engaged.png': ('%s 86 seated with the relay coil blade in' % rl, [blade, common]),
        'twistlock_4_from_below.png': ('%s from below' % rl, ['Slot (wire way) crossed with the box recess. 86 shown seated.', common]),
    }
    for fn, (title, lines) in pages.items():
        im = Image.open(os.path.join(DIR, 'raw', fn)).convert('RGB')
        W, H = im.size
        out = Image.new('RGB', (W, H + 230), (255, 255, 255))
        out.paste(im, (0, 70))
        d = ImageDraw.Draw(out)
        d.text((24, 18), 'Keyed twist-lock seat (pilot) - ' + title, fill=(20, 20, 20), font=font(34, True))
        y = H + 82
        for ln in lines:
            for part in ([ln] if len(ln) < 120 else ln.split('. ', 1)):
                d.text((24, y), part if part.endswith('.') else part + '.', fill=(30, 30, 30), font=font(24))
                y += 32
        out.save(os.path.join(DIR, fn))
        print(os.path.join(DIR, fn))


if __name__ == '__main__':
    sys.exit(main())
