import os as _o, sys as _s
_TK=_o.environ.get('HANDBUILT_CAD') or _o.path.expanduser('~/projects/handbuilt-cad')   # handbuilt-cad checkout (drawing engine, checks, renders)
for _d in ('tools','tools/checks','tools/render','drawing'): _s.path.insert(0,_o.path.join(_TK,_d))
_s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__)))
if _o.environ.get('ST185_WORK'): _o.chdir(_o.environ['ST185_WORK'])
"""Rebuild each assembly with the fixed parts swapped in (same placement), plus the F05 hardware move."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from build123d import *

def leaves(path):
    a = import_step(path); S = []
    def walk(n, p=''):
        lab = getattr(n, 'label', '') or ''; kids = list(getattr(n, 'children', []) or [])
        if kids:
            for c in kids: walk(c, p + '/' + lab)
        else:
            for s in n.solids(): S.append([lab, s])
    walk(a); return a.label or 'assembly', S

def swap(S, label_key, fixed_path, orig_path):
    fx = import_step(fixed_path).solids(); og = import_step(orig_path).solids()
    n = 0
    for it in S:
        if label_key not in it[0]: continue
        c = it[1].center()
        # orig solid that sits here (same frame), then its fixed twin
        j = min(range(len(og)), key=lambda k: (og[k].center() - c).length)
        if (og[j].center() - c).length > 0.05 or abs(og[j].volume - it[1].volume) > 0.01 * og[j].volume:
            raise SystemExit(f'frame mismatch for {label_key}: {og[j].center()} vs {c}')
        it[1] = fx[j]; n += 1
    return n

def build(src, out, swaps, moves=None):
    name, S = leaves(src)
    log = {}
    for key, fp, op in swaps: log[key] = swap(S, key, fp, op)
    for i, dv in (moves or {}).items():
        S[i][1] = S[i][1].translate(dv); log[f'moved #{i} {S[i][0]}'] = dv
    kids = []
    for lab, s in S:
        s.label = lab; kids.append(s)
    export_step(Compound(children=kids, label=name), out)
    print(out, len(S), log)
    return log

O, N = 'orig/', 'out/'
R = {}
ONLY = sys.argv[1:] or ['vrc', 'csb3', 'drb', 'fuse']
if 'vrc' in ONLY: R['vrc'] = build(O + 'vrc/VRC_assembly.step', N + 'vrc/VRC_assembly.step',
      [('VRC-Body', N + 'vrc/VRC_part_VRC-Body.step', O + 'vrc/VRC_part_VRC-Body.step'),
       ('VRC_board_holder', N + 'vrc/VRC_part_VRC-Board-Holder.step', O + 'vrc/VRC_part_VRC-Board-Holder.step')])
if 'csb3' in ONLY: R['csb3'] = build(O + 'csb3/CSB3_assembly.step', N + 'csb3/CSB3_assembly.step',
      [('CSB3-Body', N + 'csb3/CSB3_part_CSB3-Body.step', O + 'csb3/CSB3_part_CSB3-Body.step'),
       ('CSB3-Lid', N + 'csb3/CSB3_part_CSB3-Lid.step', O + 'csb3/CSB3_part_CSB3-Lid.step')])
if 'drb' in ONLY: R['drb'] = build(O + 'drb102/DRB102-firewall-plate-assembly.step', N + 'drb102/DRB102-firewall-plate-assembly.step',
      [('plate_6061', N + 'drb102/DRB102-firewall-plate.step', O + 'drb102/DRB102-firewall-plate.step')])
F = 'fusebox_rev7/'
parts = ['Power_BarNeg_CuC110_25x6p35_L105', 'Power_Bar_Power_CuC110_25x6p35_POS_bus_L226', 'BattRelay_Bar_Power_CuC110_25x6p35',
         'BattRelay_Pad_Out_CuC110_15x3', 'Power_Pad_Out_CuC110_15x3', 'Logic_Strip_Logic_CuC110_25p4x3p2_on_edge', 'Power_Base_PA12_printed']
B = json.load(open('logs/asm_bb.json'))
mv = {}
for b in B:   # F05: bolt, nut, PIDG lug and wire of the NEG end stud follow the hole (-3.0 in X)
    if b['l'] in ('Power_BarBolt_ISO4017_A2', 'Power_Nut_Keps_M5_M8_A2', 'Power_Lug_BusNeg_Klauke6R8_PIDG') and abs((b['mn'][0] + b['mx'][0]) / 2 - 263.5) < 0.6:
        mv[b['i']] = (-3.0, 0, 0)
print('moves', mv)  # wire 358 left in place: its exit in the cover is unchanged, the 4 mm wire bends 3 mm to the lug
if 'fuse' in ONLY: R['fuse'] = build(O + F + 'ST185_fusebox_rev7_assembly.step', N + F + 'ST185_fusebox_rev7_assembly.step',
      [(p, N + F + p + '.step', O + F + p + '.step') for p in parts], mv)
json.dump(R, open('logs/build_assemblies_%s.json' % '_'.join(ONLY), 'w'), indent=1, default=str)
