import os as _o, sys as _s
_TK=_o.environ.get('HANDBUILT_CAD') or _o.path.expanduser('~/projects/handbuilt-cad')   # handbuilt-cad checkout (drawing engine, checks, renders)
for _d in ('tools','tools/checks','tools/render','drawing'): _s.path.insert(0,_o.path.join(_TK,_d))
_s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__)))
if _o.environ.get('ST185_WORK'): _o.chdir(_o.environ['ST185_WORK'])
"""Before/after section images of the key fixes."""
import sys, os, math, numpy as np
pass
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from build123d import *
from secplot import section, draw_section
O, N, I = 'orig/', 'out/', 'images/'
L = lambda p: import_step(p).solids()[0]
def hexagon(ax, cx, cy, af=13.0, **kw):
    r = af / math.sqrt(3); t = np.radians(np.arange(0, 361, 60))
    ax.plot(cx + r * np.cos(t), cy + r * np.sin(t), **kw)
def pair(fn, title, panels, lims, notes):
    fig, axs = plt.subplots(1, 2, figsize=(13, 6.2))
    for ax, side in zip(axs, ('BEFORE (original)', 'AFTER (scratch fix)')):
        for shp, pl, col in panels[side]: draw_section(ax, section(shp, pl), col)
        for fnc in notes[side]: fnc(ax)
        ax.set_xlim(*lims[0]); ax.set_ylim(*lims[1]); ax.set_aspect('equal'); ax.grid(alpha=.25); ax.set_title(side, fontsize=11)
    fig.suptitle(title, fontsize=12); fig.tight_layout(); fig.savefig(I + fn, dpi=120); plt.close(fig); print(fn)

# 1. F05 NEG end stud: z 51.3 (bar) and z 40 (base hex pockets) + nut outline
F = 'fusebox_rev7/'
bo, bn = L(O + F + 'Power_BarNeg_CuC110_25x6p35_L105.step'), L(N + F + 'Power_BarNeg_CuC110_25x6p35_L105.step')
po, pn = L(O + F + 'Power_Base_PA12_printed.step'), L(N + F + 'Power_Base_PA12_printed.step')
z1 = Plane(origin=(0, 0, 51.3)); z2 = Plane(origin=(0, 0, 40.0))
def nut(x, ok):
    def f(ax):
        hexagon(ax, x, 205, 13.0, color='r' if not ok else 'g', lw=2)
        ax.axvline(270.5, color='b', ls='--'); ax.text(270.8, 222, 'base wall\nx 270.5 (z>52.5)', color='b', fontsize=8)
        ax.text(242, 188, ('M8 nut (AF13) at x %.1f: ' % x) + ('overlaps wall 2.9 mm³' if not ok else '2.5 mm clear of wall'), color='r' if not ok else 'g', fontsize=9)
        ax.text(242, 184.5, 'hole edge to bar end: %.2f mm' % ((269.0 - x) - (4.25 if not ok else 4.5)) + ('  (centre-to-end %.1f)' % (269.0 - x)), fontsize=9)
    return f
pair('F05_NEG_bar_end_stud_before_after.png', 'F05  POWER NEG bar end stud: hole 263.5 -> 260.5 (1.0xD centre-to-end), Ø8.5 -> Ø9.0; nut clear of wall (section z 51.3 + nut outline)',
     {'BEFORE (original)': [(po, z1, '#e8c79a'), (bo, z1, '#d08a50')], 'AFTER (scratch fix)': [(pn, z1, '#e8c79a'), (bn, z1, '#d08a50')]},
     ((235, 280), (182, 226)), {'BEFORE (original)': [nut(263.5, False)], 'AFTER (scratch fix)': [nut(260.5, True)]})
pair('F05_base_hex_pockets_before_after.png', 'F05  Power_Base bolt-head hex pockets (section z 40): pocket moved with the stud, tip-to-tip web bridged (no thin PA12 web)',
     {'BEFORE (original)': [(po, z2, '#e8c79a')], 'AFTER (scratch fix)': [(pn, z2, '#e8c79a')]}, ((230, 280), (185, 225)), {'BEFORE (original)': [], 'AFTER (scratch fix)': []})

# 2. F04 VRC spotface feather edge (z 21)
vo, vn = L(O + 'vrc/VRC_part_VRC-Body.step'), L(N + 'vrc/VRC_part_VRC-Body.step')
z = Plane(origin=(0, 0, 21))
pair('F04_VRC_spotface_feather_edge_before_after.png', 'F04  VRC body: Ø30 spotface vs R7.7 cavity corner (section z 21). Before: 0.0 mm knife edge; after: spotface carried inboard to x 35',
     {'BEFORE (original)': [(vo, z, '#c9d6e3')], 'AFTER (scratch fix)': [(vn, z, '#c9d6e3')]}, ((28, 46), (2, 24)),
     {'BEFORE (original)': [lambda ax: ax.annotate('0.0 mm feather edge', (38, 10.4), xytext=(29, 4), color='r', arrowprops=dict(arrowstyle='->', color='r'))],
      'AFTER (scratch fix)': [lambda ax: ax.text(29, 4, 'edge now ~127 deg, no sliver', color='g')]})

# 3. F02 VRC boss + holder pocket (vertical section through boss at y 9.5)
ho, hn = L(O + 'vrc/VRC_part_VRC-Board-Holder.step'), L(N + 'vrc/VRC_part_VRC-Board-Holder.step')
r3 = L(_o.environ.get('VRC_REV3_STEP','rev3work/out/VRC_part_VRC-Body.step')) if os.path.exists(_o.environ.get('VRC_REV3_STEP','rev3work/out/VRC_part_VRC-Body.step')) else vo
yz = Plane(origin=(0, 9.5, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
pair('F02_VRC_boss_plus1_and_holder_pocket_before_after.png', 'F02  VRC M6 holder boss +1.0 (top z 9.5 -> 10.5) with holder pocket deepened 1.0 (z 9.7 -> 10.7). Section y 9.5',
     {'BEFORE (original)': [(vo, yz, '#c9d6e3'), (ho, yz, '#f2d48f')], 'AFTER (scratch fix)': [(vn, yz, '#c9d6e3'), (hn, yz, '#f2d48f')]}, ((8, 34), (0, 17)),
     {'BEFORE (original)': [lambda ax: ax.text(9, 1.2, 'boss top 9.5, thread 6.5 (1.08xD);\n+1 boss alone would clash 0.8 with pocket z 9.7', fontsize=8, color='r')],
      'AFTER (scratch fix)': [lambda ax: ax.text(9, 1.2, 'boss top 10.5, pocket roof 10.7 (0.2 clear);\nthread ~7.5 (1.25xD) with M6x12', fontsize=8, color='g')]})

# 4. F01 tab slots (z 3)
z3 = Plane(origin=(0, 0, 3))
pair('F01_VRC_tab_slot_5p5_to_6p6_before_after.png', 'F01  VRC tab slot 5.5 -> 6.6 wide x 10 long (M6 ISO 273 medium) + F11 R3 tab-to-body corners (section z 3)',
     {'BEFORE (original)': [(vo, z3, '#c9d6e3')], 'AFTER (scratch fix)': [(vn, z3, '#c9d6e3')]}, ((15, 41), (22, 39)), {'BEFORE (original)': [], 'AFTER (scratch fix)': []})
co, cn = L(O + 'csb3/CSB3_part_CSB3-Body.step'), L(N + 'csb3/CSB3_part_CSB3-Body.step')
pair('F01_CSB3_tab_slot_5p5_to_6p6_before_after.png', 'F01  CSB3 tab slot 5.5 -> 6.6 x 10 + F11 corners R3 (x 10) / R1.9 (x 30, 2.0 ledge) (section z 3)',
     {'BEFORE (original)': [(co, z3, '#c9d6e3')], 'AFTER (scratch fix)': [(cn, z3, '#c9d6e3')]}, ((7, 35), (32, 49)), {'BEFORE (original)': [], 'AFTER (scratch fix)': []})

# 5. F09 CSB3 lid D-hole corner (z 52)
lo, ln = L(O + 'csb3/CSB3_part_CSB3-Lid.step'), L(N + 'csb3/CSB3_part_CSB3-Lid.step')
pair('F09_CSB3_lid_Dhole_corner_before_after.png', 'F09  CSB3 lid HD34 D-hole flat-to-arc corner: r0 -> R3 cutter radius (flat stays at y 19.91 = 41.45 across)',
     {'BEFORE (original)': [(lo, Plane(origin=(0, 0, 52)), '#c9d6e3')], 'AFTER (scratch fix)': [(ln, Plane(origin=(0, 0, 52)), '#c9d6e3')]}, ((4, 13), (16, 23)), {'BEFORE (original)': [], 'AFTER (scratch fix)': []})

# 6. F07 logic strip holes (section through strip 1 mid-thickness, YZ)
so = import_step(O + F + 'Logic_Strip_Logic_CuC110_25p4x3p2_on_edge.step').solids(); sn = import_step(N + F + 'Logic_Strip_Logic_CuC110_25p4x3p2_on_edge.step').solids()
xz = Plane(origin=(20.75, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
pair('F07_logic_strip_tap_drill_before_after.png', 'F07  LOGIC strip holes: Ø4.0 -> Ø3.3 (M4 tap drill), Ø5.0 -> Ø4.2 (M5), 0.3 edge break (section through strip 1)',
     {'BEFORE (original)': [(so[0], xz, '#d08a50')], 'AFTER (scratch fix)': [(sn[0], xz, '#d08a50')]}, ((10, 60), (4, 33)), {'BEFORE (original)': [], 'AFTER (scratch fix)': []})
