"""Renders of one POWER copper-strap station (DECISIONS R155, N14 = B) from the Fusion assembly STEP: half-section at the fuse line and
an iso with the printed base see-through. Smooth shading, real edges only (no mesh lines, R152), labelled, framed.

    ~/projects/handbuilt-cad/.venv/bin/python cad/fusebox/src/render_strap_station.py <ST185_fusebox_rev7_assembly.step> <dest dir>

Writes <dest>/N14_B_final_1_half_section_OUT_JB1.png, _2_iso_OUT_JB1.png, _3_half_section_IN_HTR.png.
Claude Code, 2026-10-17.
"""
import os
import sys

os.environ.setdefault('PYVISTA_OFF_SCREEN', 'true')
import numpy as np  # noqa: E402
import pyvista as pv  # noqa: E402
from build123d import import_step  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spec as S  # noqa: E402

pv.OFF_SCREEN = True
COL = [('Power_Base_PA12', '#e9e6df'), ('Power_Pan_PA12', '#d8d4cc'), ('Power_Strap_', '#d9895b'), ('Power_Nut_PEM', '#8f969e'),
       ('Power_EarBolt', '#b9c0c7'), ('Power_LugBolt', '#b9c0c7'), ('Power_Nut_Keps', '#b9c0c7'), ('Power_BarBolt', '#b9c0c7'),
       ('Power_Bar_Power', '#d99a6c'), ('Power_Lug_Klauke', '#c97b4a'), ('Power_Wire_feed', '#2b2b2b'), ('Power_Fuse_AMI_yellow', '#f0c020'),
       ('Power_Fuse_AMI_ltgreen', '#7fcf7f'), ('Power_Fuse_AMI_red', '#d84040'), ('Power_Fuse_AMI_orange', '#f0a020')]


def colour(label):
    for k, c in COL:
        if label.startswith(k):
            return c
    return None


def to_mesh(solid):
    vs, fs = solid.tessellate(0.01, 0.15)
    v = np.array([[p.X, p.Y, p.Z] for p in vs])
    f = np.hstack([[3, *t] for t in fs])
    return pv.PolyData(v, f).clean().compute_normals(split_vertices=True, feature_angle=30)


def station(asm, row, name):
    i = [n for n, _a in S.AMI_ROWS[row]].index(name)
    sgn = 1 if row == 'OUT' else -1
    px, py = S.PLACE['POWER']
    y = S.AMI_Y0 + i * S.AMI_PITCH + py
    xo = S.POWER['x_bar'] + sgn * (S.AMI_IN_OFF + S.AMI['c']) + px
    x0, x1 = (xo - 26, xo + 32) if sgn > 0 else (xo - 32, xo + 26)
    box = (x0, x1, y - S.AMI_PITCH / 2 + 0.05, y + S.AMI_PITCH / 2 - 0.05, -1.0, 66.0)
    parts = []
    for ch in asm.children:
        c = colour(ch.label or '')
        if c is None:
            continue
        for so in ch.solids():
            bb = so.bounding_box()
            if bb.max.X < box[0] or bb.min.X > box[1] or bb.max.Y < box[2] - 6 or bb.min.Y > box[3] + 6:
                continue
            big = (bb.max.X - bb.min.X) > 70 or (bb.max.Y - bb.min.Y) > 70
            if not big and not (box[2] - 1 <= (bb.min.Y + bb.max.Y) / 2 <= box[3] + 1):
                continue                                  # a neighbouring station's part
            m = to_mesh(so)
            if big:                                       # base, pan, bar: clip to the station window
                m = m.clip_box(box, invert=False).extract_surface(algorithm='dataset_surface').compute_normals(split_vertices=True, feature_angle=30)
            if m.n_points:
                parts.append((ch.label, m, c))
    return dict(parts=parts, y=y, xo=xo, sgn=sgn, box=box)


def frame(png, title, sub):
    im = Image.open(png).convert('RGB')
    d = ImageDraw.Draw(im)
    W, H = im.size
    try:
        f1, f2 = ImageFont.truetype('DejaVuSans-Bold.ttf', 30), ImageFont.truetype('DejaVuSans.ttf', 20)
    except OSError:
        f1 = f2 = ImageFont.load_default()
    d.rectangle([6, 6, W - 7, H - 7], outline='#333333', width=3)
    d.text((24, 18), title, fill='#111111', font=f1)
    d.text((24, 56), sub, fill='#444444', font=f2)
    im.save(png)


def shot(path, st, labels, cam, title, sub, cut=False, see_base=False, zoom=1.3, size=(1800, 1300)):
    p = pv.Plotter(off_screen=True, window_size=size)
    p.set_background('white')
    for lab, m, c in st['parts']:
        if cut:                       # solid cut faces where the mesh is closed (concept B renders), plain clip otherwise
            try:
                m2 = m.clean().triangulate().clip_closed_surface(normal=(0, 1, 0), origin=(0, st['y'] + 0.001, 0))
            except Exception:
                m2 = None
            if m2 is None or not m2.n_points:
                m2 = m.clip(normal=(0, 1, 0), origin=(0, st['y'] + 0.001, 0), invert=True).extract_surface(algorithm='dataset_surface')
            if not m2.n_points:
                continue
            m = m2.compute_normals(split_vertices=True, feature_angle=30)
        op = 0.35 if (see_base and lab.startswith(('Power_Base', 'Power_Pan'))) else 1.0
        p.add_mesh(m, color=c, smooth_shading=True, show_edges=False, specular=0.25, opacity=op)
        fe = m.extract_feature_edges(30, boundary_edges=cut, non_manifold_edges=False, manifold_edges=False)
        if fe.n_points:
            p.add_mesh(fe, color='#202020', line_width=1.0)
    if labels:
        p.add_point_labels(np.array([l[1] for l in labels]), [l[0] for l in labels], font_size=17, point_size=9, point_color='#c0002a',
                           shape_color='white', shape_opacity=0.85, always_visible=True, margin=4)
    p.camera_position = cam
    p.enable_parallel_projection()
    p.reset_camera()
    p.camera.zoom(zoom)
    p.screenshot(path)
    p.close()
    frame(path, title, sub)


def main(argv):
    asm = import_step(argv[0])
    dest = argv[1]
    os.makedirs(dest, exist_ok=True)
    ST, T = S.STRAP, S.STRAP_TAB
    bt = S.POWER['bar_top']
    for row, name, n in (('OUT', 'JB1', 1), ('IN', 'HTR', 3)):
        st = station(asm, row, name)
        y, xo, s = st['y'], st['xo'], st['sgn']
        g = lambda dx: xo + s * dx
        sub = 'ST185 POWER box rev 7, %s row %s (%d A) - copper C-strap 3 x 15 tinned C110, PEM FHS-M5-12 lug stud + DIN 934 top nut in a PA12 holder (N37), mm' % (
            row, name, dict(S.AMI_ROWS[row])[name])
        L = [('copper C-strap 3 x 15 tinned C110', (g(-2.0), y, bt - 1.5)),
             ('lips rest on the printed ledge (stops DOWN)', (g(ST['web'][1] + 1.0), y - 5.5, bt - ST['t'])),
             ('printed snap hook over the lips (stops UP)', (g(ST['web'][1] + ST['lip'] + 1.5), y - 5.0, bt + 1.4)),
             ('DIN 934 M5 nut in the printed PA12 holder (FB-118)', (xo, y, bt - ST['t'] - 1.0)),
             ('AMI ear clamped flat on copper, M5 x 10', (g(2.5), y, bt + 0.8)),
             ('web through the deck well', (g((ST['web'][0] + ST['web'][1]) / 2), y, 33.0)),
             ('lug palm up on the PEM FHS-M5-12 stud, Keps nut', (g(ST['lug']), y, ST['z_bl'] - 1.0)),
             ('lug barrel passes under the web', (g(ST['web'][1] + 6.0), y, ST['z_bl'] - 4.0))]
        side = 1 if s > 0 else -1
        cam = [(xo + side * -10, y + 260, 120), (xo + side * 2, y, 33), (0, 0, 1)]
        shot(os.path.join(dest, 'N14_B_final_%d_half_section_%s_%s.png' % (n, row, name)), st, L, cam,
             'N14 = B as built - half-section at the fuse line, %s row (%s)' % (row, name), sub, cut=True)
        if row == 'OUT':
            L2 = [('copper C-strap', (g(1.0), y + 7.5, bt)), ('snap hook over both lips', (g(ST['web'][1] + ST['lip']), y, bt + 2.6)),
                  ('skirt freed by 2 side slots + inner slot = snap arm', (g(ST['web'][1] + 15.0), y + 6.0, 45.0)),
                  ('lug + cable out under the skirt', (g(26.0), y, 9.75))]
            shot(os.path.join(dest, 'N14_B_final_2_iso_%s_%s.png' % (row, name)), st, L2, [(xo + 110, y - 190, 160), (xo + 6, y, 32), (0, 0, 1)],
                 'N14 = B as built - station iso (printed base and pan see-through)', sub, see_base=True, zoom=1.05)
    print('\n'.join(sorted(os.listdir(dest))))


if __name__ == '__main__':
    main(sys.argv[1:])
