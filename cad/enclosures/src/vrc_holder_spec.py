"""VRC board holder (OPEN-ITEMS row 97, Dan K7 = A: "no extra room though ... just make it fit the enclosure with room
for the wires") - every number the Fusion build (build_vrc_holder.py) and its checks use, in mm, enclosure axes
(box floor top z = 5, cavity x +-38 / y +-18 / to the lid at z = 39; IN socket on +x, OUT on -x).

Board: OpenLogicEFI Dual VR Conditioner NCV1124 RevB3, `Duel VR.kicad_pcb` (github.com/OpenLogicEFI/Hardware,
Modules/VR Conditioner NCV1124/RevB3): Edge.Cuts 24.13 x 24.10, corner R 0.71, 1.6 thick; DIP-8 footprint J3 at
(169.4138, 97.9366) rot 180 on a board centred at (165.100, 93.815) -> the pin positions below. SMD on top only.
The pin header itself is not in the maker's files: a standard 2.54 mm male header is assumed (2.54 plastic under the
board, 5.96 pin below it, 1.44 tail above the top), so 8.5 mm of pin hangs below the board.

Wires inside the box: M22759/16-20 (the 20 AWG wire of ST185-WheelSpeed-Front / -Rear), OD 1.57
(cad/fusebox/src/spec.py OD table). Bend: 3 x OD inside radius where the wire is held (FAA AC 43.13-1B 11-96, the
same rule as the fuse box wiring, wiring_sim.r_sup) -> 5.5 mm on the centre line.
Claude Code, 2026-10-15.
"""
import math

# ---------- enclosure (read from Fusion ST185-VRC-Enclosure v1, VRC-Body)
FLOOR_Z, LID_Z = 5.0, 39.0
CAV_X, CAV_Y, CAV_R = 38.0, 18.0, 7.7
BOSS_XY, BOSS_TOP, BOSS_D = (14.0, 12.0), 8.0, 7.0      # 4 bosses, M3 tapped 4.5 deep
LP16_REAR_X, LP16_AXIS_Z, LP16_REAR_R = 28.9, 21.0, 9.0  # rear envelope ends at x = +-28.9 (cups included), D18 about z 21

# ---------- board (KiCad RevB3)
PCB_X, PCB_Y, PCB_T, PCB_R = 24.13, 24.10, 1.6, 0.71
PIN_X = {1: 4.3138, 2: 4.3138, 3: 4.3138, 4: 4.3138, 5: -3.3062, 6: -3.3062, 7: -3.3062, 8: -3.3062}
PIN_Y = {1: -4.1217, 2: -1.5817, 3: 0.9583, 4: 3.4983, 5: 3.4983, 6: 0.9583, 7: -1.5817, 8: -4.1217}
PIN_NET = {1: 'VR1-', 2: 'VR1+', 3: 'VR2+', 4: 'VR2-', 5: 'VDD', 6: 'GND', 7: 'VR2OUT', 8: 'VR1OUT'}
PIN_SQ, HDR_PLASTIC, PIN_BELOW, PIN_TAIL = 0.64, 2.54, 8.5, 1.44
SO8 = dict(x0=-1.13 - 0.0, x1=4.02, y0=6.14, y1=11.05, h=1.75)   # IC1 body (pad rows at X -1.13 / 4.02, Y 6.69-10.50)

# ---------- holder (printed; PA12 powder bed like the fuse boxes, R73: walls >= 2.0, no closed cavity)
FIT = 0.25            # board-to-pocket gap per side: the normal printed fit, no extra room (K7)
WALL = 2.0            # R73 minimum wall
LEDGE = 1.0           # board sits on a 1 mm ledge round its edge (bottom side is bare except the header)
TIP_GAP = 0.5         # pin tip to the well floor
PLATE_T = 2.0         # under the screw heads: M3 x 6 nylon -> 4.0 of thread in the 4.5 deep boss
WELL_Z = 13.0         # well floor: puts the wire joints (Z_JOINT) under the LP-16 cups' height band
Z_BOARD = WELL_Z + TIP_GAP + PIN_BELOW          # board underside (22.0)
Z_TOP = Z_BOARD + PCB_T                         # board top = tub top (23.6)
PLATE = dict(w=2 * (BOSS_XY[0] + BOSS_D / 2), h=2 * (BOSS_XY[1] + BOSS_D / 2), r=BOSS_D / 2)   # 35 x 31, covers the bosses
POCKET = (PCB_X + 2 * FIT, PCB_Y + 2 * FIT, PCB_R + FIT)
WELL = (POCKET[0] - 2 * LEDGE, POCKET[1] - 2 * LEDGE, 0.5)
TUB = (POCKET[0] + 2 * WALL, POCKET[1] + 2 * WALL, POCKET[2] + WALL)
SCREW_HOLE, HEAD_ACCESS = 3.4, 6.6              # Wurth 97790603111 M3 x 6 nylon pan head (DIN 7985 head about 5.6)
Z_JOINT = WELL_Z + 2.0                          # wire centre line where it meets the pin (exposed pin is z 13.5-19.46)
SLOT_Y = (min(PIN_Y.values()) - 1.6, max(PIN_Y.values()) + 1.6)   # wire exits in the +-x walls
SLOT_Z = (WELL_Z, Z_BOARD - LEDGE)
SNAP_X = (-9.5, -3.5)  # two snap arms on the +-y walls, clear of IC1 (+y edge) - no top parts within 1.2 mm of the edge here
SNAP_SLIT, SNAP_Z0, LIP_IN, LIP_H, LIP_GAP = 0.6, 15.5, 0.7, 0.8, 0.1

# ---------- wires
OD = 1.57
R_BEND = 3 * OD + OD / 2          # 5.5 centre line
CUP_R = 4.0   # assumed: the 5 solder cups on a 8 mm circle, cup 1 on top, numbered clockwise seen from inside the box
DRAIN_Y = -(CAV_Y + TUB[1] / 2) / 2   # drain jumper (IN 3 -> OUT 5) runs beside the holder, halfway to the wall

# LP-16 cup -> module pin (S8 / S16 pin maps; NCV1124 nets: VR1 = left wheel, VR2 = right)
IN_MAP = {1: 2, 2: 1, 4: 3, 5: 4}      # ABS+ L -> VR1+, ABS- L -> VR1-, ABS+ R -> VR2+, ABS- R -> VR2-
OUT_MAP = {1: 5, 2: 6, 3: 8, 4: 7}     # +5V -> VDD, Gnd -> GND, L out -> VR1OUT, R out -> VR2OUT
# The OUT map crosses over (cups 1 / 2 and 3 / 4 land on pins in the other order), so two OUT wires meet their pin
# higher up (the exposed pin runs to z 19.46): the best of the 3-level search in the PR, 0.39 mm between wires.
JOINT_Z = {('OUT', 1): 18.2, ('OUT', 4): 18.2}


def cup(side, k):
    """side +1 = IN (+x), -1 = OUT (-x). Seen from inside, 'right' is -y for IN and +y for OUT."""
    a = math.radians(72 * (k - 1))
    u, v = CUP_R * math.sin(a), CUP_R * math.cos(a)
    return (side * (LP16_REAR_X - 0.3), -side * u, LP16_AXIS_Z + v)


def wires():
    """name -> (polyline, side). Cup -> 6.6 straight (cup + heat shrink) -> into the wall slot -> to the pin side."""
    out = {}
    for side, cmap, tag in ((1, IN_MAP, 'IN'), (-1, OUT_MAP, 'OUT')):
        for k, p in cmap.items():
            c = cup(side, k)
            zj = JOINT_Z.get((tag, k), Z_JOINT - 0.4)
            end = (PIN_X[p] + side * (PIN_SQ / 2 + OD / 2 + 0.05), PIN_Y[p], zj)
            pts = [c, (side * 22.0, c[1], c[2]), (side * (TUB[0] / 2 + 2.2), PIN_Y[p], zj), end]
            out['%s%d-pin%d' % (tag, k, p)] = pts
    a, b = cup(1, 3), cup(-1, 5)
    out['drain IN3-OUT5'] = [a, (22.0, a[1], a[2]), (17.0, DRAIN_Y, LP16_AXIS_Z), (-17.0, DRAIN_Y, LP16_AXIS_Z),
                             (-22.0, b[1], b[2]), b]
    return out


def _sub(a, b): return tuple(x - y for x, y in zip(a, b))
def _add(a, b): return tuple(x + y for x, y in zip(a, b))
def _mul(a, k): return tuple(x * k for x in a)
def _dot(a, b): return sum(x * y for x, y in zip(a, b))
def _ln(a): return math.sqrt(_dot(a, a))
def _nrm(a): return _mul(a, 1 / _ln(a))


def smooth(pts, R=R_BEND, n=10):
    """Polyline -> points with a circular fillet of centre radius R at every corner. Returns (points, problems)."""
    probs, res = [], [pts[0]]
    tl = []
    for i in range(1, len(pts) - 1):
        d0, d1 = _nrm(_sub(pts[i], pts[i - 1])), _nrm(_sub(pts[i + 1], pts[i]))
        th = math.acos(max(-1, min(1, _dot(d0, d1))))
        tl.append((th, R * math.tan(th / 2)))
    for i in range(len(pts) - 1):
        L = _ln(_sub(pts[i + 1], pts[i]))
        need = (tl[i - 1][1] if i > 0 else 0) + (tl[i][1] if i < len(tl) else 0)
        if need > L + 1e-6:
            probs.append('segment %d: %.2f long, bends need %.2f' % (i, L, need))
    for i in range(1, len(pts) - 1):
        th, t = tl[i - 1]
        d0, d1 = _nrm(_sub(pts[i], pts[i - 1])), _nrm(_sub(pts[i + 1], pts[i]))
        a, b = _sub(pts[i], _mul(d0, t)), _add(pts[i], _mul(d1, t))
        if th < 1e-4:
            res += [pts[i]]; continue
        # quadratic-to-circular: sample the arc between a and b around the fillet centre
        bis = _nrm(_sub(d1, d0))
        cen = _add(pts[i], _mul(bis, R / math.cos(th / 2)))
        va, vb = _sub(a, cen), _sub(b, cen)
        for j in range(n + 1):
            s = j / n
            w0, w1 = math.sin((1 - s) * th) / math.sin(th), math.sin(s * th) / math.sin(th)
            res.append(_add(cen, _add(_mul(va, w0), _mul(vb, w1))))
    res.append(pts[-1])
    return res, probs


def seg_dist(p1, q1, p2, q2):
    """Minimum distance between two 3D segments."""
    d1, d2, r = _sub(q1, p1), _sub(q2, p2), _sub(p1, p2)
    a, e, f = _dot(d1, d1), _dot(d2, d2), _dot(d2, r)
    c, b = _dot(d1, r), _dot(d1, d2)
    den = a * e - b * b
    s = max(0, min(1, (b * f - c * e) / den)) if den > 1e-12 else 0
    t = (b * s + f) / e
    if t < 0: t, s = 0, max(0, min(1, -c / a))
    elif t > 1: t, s = 1, max(0, min(1, (b - c) / a))
    return _ln(_sub(_add(p1, _mul(d1, s)), _add(p2, _mul(d2, t))))


def wire_report():
    """Bend fit per wire + the closest approach between every pair of wires (centre lines)."""
    W = {k: smooth(v) for k, v in wires().items()}
    rows, worst = [], (99, '')
    names = list(W)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            pa, pb = W[a][0], W[b][0]
            d = min(seg_dist(pa[m], pa[m + 1], pb[n], pb[n + 1]) for m in range(len(pa) - 1) for n in range(len(pb) - 1))
            if d - OD < worst[0]:
                worst = (d - OD, '%s / %s' % (a, b))
    for k, (pts, probs) in W.items():
        L = sum(_ln(_sub(pts[m + 1], pts[m])) for m in range(len(pts) - 1))
        rows.append((k, round(L, 1), probs))
    return rows, worst


if __name__ == '__main__':
    print('board underside z %.2f, top %.2f; tub %.2f x %.2f; pocket %.2f x %.2f; plate %.1f x %.1f'
          % (Z_BOARD, Z_TOP, TUB[0], TUB[1], POCKET[0], POCKET[1], PLATE['w'], PLATE['h']))
    rows, worst = wire_report()
    for r in rows:
        print(r)
    print('closest wire pair: gap %.2f mm (%s)' % worst)
