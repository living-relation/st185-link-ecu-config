"""Tiny SVG writer for the wiring diagrams (no dependencies). Units are millimetres; the page is the viewBox.

A wire is drawn as: white halo (so a wire drawn later visibly passes OVER an earlier one it crosses), dark casing, insulation-colour core.
Text is Helvetica / Arial; widths are estimated (est_w) so labels can be wrapped and checked against the sheet edge.
"""
from xml.sax.saxutils import escape

INK = '#14213d'
GRID = '#9aa5b8'
PAPER = '#ffffff'
BOXFILL = '#f4f7fb'
PARTFILL = '#ffffff'
WIRE = {'Red': '#c62828', 'White': '#f8f8f8', 'Black': '#1b1b1b', 'Violet': '#7b3fa0', 'Gray': '#8a8a8a', 'Grey': '#8a8a8a',
        'Brown': '#8b5a2b', 'Yellow': '#f2c200', 'Green': '#2e9d4f', 'Blue': '#2f6fd6', 'Orange': '#ee7a00', 'Pink': '#e58fb4'}
FONT = "font-family=\"Helvetica, Arial, sans-serif\""


def est_w(s, size, bold=False):
    return len(s) * size * (0.56 if bold else 0.52)


def wrap(s, width, size, bold=False, max_lines=None):
    """Greedy word wrap to `width` mm; the last line is cut with ... when max_lines is hit."""
    words, lines, cur = s.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if est_w(t, size, bold) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if max_lines and len(lines) > max_lines:
        keep = lines[:max_lines]
        last = keep[-1]
        while est_w(last + '...', size, bold) > width and len(last) > 4:
            last = last[:-1]
        keep[-1] = last.rstrip() + '...'
        lines = keep
    return lines


class Svg:
    def __init__(self, w, h, title=''):
        self.w, self.h, self.title = w, h, title
        self.back, self.parts, self.over = [], [], []
        self.texts = []          # (x0, x1, y, text) for the edge check

    def _add(self, s, layer):
        {'back': self.back, 'main': self.parts, 'over': self.over}[layer].append(s)

    def rect(self, x, y, w, h, fill=PARTFILL, stroke=INK, sw=0.35, rx=0.0, dash=None, layer='main'):
        d = ' stroke-dasharray="%s"' % dash if dash else ''
        self._add('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="%.2f" fill="%s" stroke="%s" stroke-width="%.2f"%s/>'
                  % (x, y, w, h, rx, fill, stroke, sw, d), layer)

    def line(self, x1, y1, x2, y2, stroke=INK, sw=0.3, dash=None, layer='main'):
        d = ' stroke-dasharray="%s"' % dash if dash else ''
        self._add('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%.2f"%s/>' % (x1, y1, x2, y2, stroke, sw, d), layer)

    def circle(self, x, y, r, fill=INK, stroke='none', sw=0.2, layer='main'):
        self._add('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s" stroke="%s" stroke-width="%.2f"/>' % (x, y, r, fill, stroke, sw), layer)

    def text(self, x, y, s, size=2.2, anchor='start', bold=False, fill=INK, italic=False, rot=None, layer='over', track=True):
        if not s:
            return
        tf = ' transform="rotate(%d %.2f %.2f)"' % (rot, x, y) if rot else ''
        self._add('<text x="%.2f" y="%.2f" font-size="%.2f" text-anchor="%s" fill="%s" %s%s%s%s>%s</text>'
                  % (x, y, size, anchor, fill, FONT, ' font-weight="bold"' if bold else '', ' font-style="italic"' if italic else '',
                     tf, escape(s)), layer)
        if track and not rot:
            wd = est_w(s, size, bold)
            x0 = x if anchor == 'start' else (x - wd if anchor == 'end' else x - wd / 2)
            self.texts.append((x0, x0 + wd, y, s))

    def wire(self, pts, colour='Red', sw=0.75):
        """Polyline wire: halo, casing, insulation core."""
        p = ' '.join('%.2f,%.2f' % q for q in pts)
        core = WIRE.get(colour, '#c62828')
        self._add('<polyline points="%s" fill="none" stroke="%s" stroke-width="%.2f" stroke-linejoin="round" stroke-linecap="butt"/>' % (p, PAPER, sw + 1.5), 'main')
        self._add('<polyline points="%s" fill="none" stroke="#111" stroke-width="%.2f" stroke-linejoin="round" stroke-linecap="butt"/>' % (p, sw + 0.35), 'main')
        self._add('<polyline points="%s" fill="none" stroke="%s" stroke-width="%.2f" stroke-linejoin="round" stroke-linecap="butt"/>' % (p, core, sw - 0.1), 'main')

    def thin(self, pts, stroke=INK, sw=0.3, dash=None):
        p = ' '.join('%.2f,%.2f' % q for q in pts)
        d = ' stroke-dasharray="%s"' % dash if dash else ''
        self._add('<polyline points="%s" fill="none" stroke="%s" stroke-width="%.2f"%s/>' % (p, stroke, sw, d), 'main')

    def render(self):
        head = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.1f %.1f" width="%.1fmm" height="%.1fmm">\n<title>%s</title>\n'
                '<rect x="0" y="0" width="%.1f" height="%.1f" fill="%s"/>\n' % (self.w, self.h, self.w, self.h, escape(self.title), self.w, self.h, PAPER))
        return head + '\n'.join(self.back + self.parts + self.over) + '\n</svg>\n'

    def save(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.render())

    def overflow(self):
        return [t for t in self.texts if t[0] < 0 or t[1] > self.w]
