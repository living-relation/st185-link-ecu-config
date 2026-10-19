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
BOSS_XY, BOSS_TOP, BOSS_D = (14.0, 12.0), 8.0, 7.0      # HISTORY ONLY (unused): the 4 v1 M3 floor bosses, removed by R126 - read from Fusion
# ST185-VRC-Enclosure v11 (SteveCAD sweep C10, 2026-10-17): VRC-Body has no bosses at (+-14, +-12); its tapped holes are the 2 M6 holder bosses
# (BOSS2_D below: D11 z 5.0 - 12.5, D5.0 tap drill z 1.0 - 12.5) and the 4 lid screw holes (D2.53 tap drill, z 29.5 - 38.74)
LP16_REAR_X, LP16_AXIS_Z, LP16_REAR_R = 28.9, 21.0, 9.0  # rear envelope ends at x = +-28.9 (cups included), D18 about z 21

# ---------- board (KiCad RevB3)
PCB_X, PCB_Y, PCB_T, PCB_R = 24.13, 24.10, 1.6, 0.71
PIN_X = {1: 4.3138, 2: 4.3138, 3: 4.3138, 4: 4.3138, 5: -3.3062, 6: -3.3062, 7: -3.3062, 8: -3.3062}
PIN_Y = {1: -4.1217, 2: -1.5817, 3: 0.9583, 4: 3.4983, 5: 3.4983, 6: 0.9583, 7: -1.5817, 8: -4.1217}
PIN_NET = {1: 'VR1-', 2: 'VR1+', 3: 'VR2+', 4: 'VR2-', 5: 'VDD', 6: 'GND', 7: 'VR2OUT', 8: 'VR1OUT'}
PIN_SQ, HDR_PLASTIC, PIN_BELOW, PIN_TAIL = 0.64, 2.54, 8.5, 1.44
SO8 = dict(x0=-1.13 - 0.0, x1=4.02, y0=6.14, y1=11.05, h=1.75)   # IC1 body (pad rows at X -1.13 / 4.02, Y 6.69-10.50)

# ---------- holder v2 (Dan M9, 2026-10-15, DECISIONS R126 - supersedes the v1 tub / ledge / pin well / wire slots / M3 plate):
# "Redesign to be simpler. wires soldered from top of pcb. extrude solid block. cut square recess for the pcb with little tabs to hold
# it down. add a couple counter sink socket head cap screw holes in the corners of the block to attach it to the enclosure. edit
# enclosure to have 2 corresponding screw bosses that can be drilled out and tapped for 6mm screws later"
# One extruded PA12 block on the box floor. Wires solder on the TOP of the board, so no header is fitted and nothing hangs under it
# (two shallow reliefs under the pin rows take the solder tips). PA12 powder bed (R73: walls >= 2.0 except the named snap tabs).
FIT = 0.4             # board to pocket, per side
WALL = 2.0            # R73 minimum wall
Z_TOP = 17.5          # board top, flush with the block top; N4 (Dan 2026-10-16, OPEN-6 = A): the holder 2.5 higher (was 15.0), 21.5 mm to the lid for soldering
Z_BOARD = Z_TOP - PCB_T                         # pocket floor / board underside (13.4)
POCKET = (PCB_X + 2 * FIT, PCB_Y + 2 * FIT, PCB_R + FIT)
# block outline (x, y): +-28.85 x +-17.6, the x ends notched back to +-28.4 for |y| < 7.0, where the LP-16 rear envelope (x >= 28.9,
# a D18 cylinder about z 21: |y| < 6.7 at z 15) and its cups sit; block corners stay inside the cavity's R7.7 corners
BLOCK = dict(x=28.85, y=17.6, x_notch=28.4, y_notch=8.8, z0=FLOOR_Z, z1=Z_TOP)   # N4: notch |y| 7.0 -> 8.8: at the new top (z 17.5) the D18 rear is 8.29 wide (+0.4 FIT + margin)
RELIEF = dict(w=2.6, l=11.0, d=1.5)             # under each pin row: solder tips of the top-soldered wires (blind)
# N4: with the block 2.5 higher its top (z 17.5) is level with the two lowest LP-16 solder cups (z 17.76) - the leads from cups 3 / 4 and the
# drain leave the cup straight in toward the board, so each block end gets a lead relief back down to the old top: |x| >= x0, |y| <= y,
# down to z (2.0 under those leads; outside the M6 head seat - the countersink rim reaches it only beyond the head's 5.67 radius)
LEAD_RELIEF = dict(x0=18.5, y_lo=-6.5, y_cup=3.6, clr=0.45, z=15.0)


def lead_relief():
    """Outline (x, y) of the lead relief at the +x (IN) end; the -x end is its point mirror (x, y) -> (-x, -y), like the screws. From
    the end face it is y_lo .. y_cup (round the cup 3 / 4 leads; wider on -y for the drain), then its countersink-side edge follows the
    cup 4 lead in to x 21.7 (lead y + OD / 2 + clr), so >= 1.95 of PA12 stays between it and the M6 countersink."""
    LR = LEAD_RELIEF
    yt = max(TURN_Y[('IN', 4)], -TURN_Y[('OUT', 4)]) + OD / 2 + LR['clr']
    xe = BLOCK['x'] + 1.0
    return [(xe, LR['y_lo']), (xe, LR['y_cup']), (LP16_REAR_X - 0.3, LR['y_cup']), (21.7, yt), (LR['x0'], yt), (LR['x0'], LR['y_lo'])]
# 4 snap tabs at the pocket's +-y edges (clear of IC1, which reaches y 11.05 at x -1.1..4.0): a 1.0 arm freed by a slot behind it
# and two slits at its ends, a 0.6 lip with a lead-in over the board edge
TABS_X = ((-9.5, -4.5), (4.5, 9.5))
TAB_T, TAB_GAP, TAB_SLIT, TAB_Z0 = 1.0, 1.0, 0.6, 8.0
LIP_IN, LIP_H, LIP_GAP = 0.6, 0.8, 0.1
# 2 x M6 countersunk socket head cap screws, opposite corners: ISO 10642 A2 M6 x 12, RS PRO 266-8419
# (https://int.rsdelivers.com/product/rs-pro/rs-pro-plain-stainless-steel-hex-socket-screw-hex/2668419); head dk <= 12.0, 90 deg
SCREWS = ((20.7, 9.5), (-20.7, -9.5))
SCREW_PN, SCREW_LEN = 'Lemu 2990806014 (M6 x 14, ISO 10642 / DIN 7991, A2, TX30)', 14.0   # N4: M6 x 12 hex (RS 266-8419) -> M6 x 14 - no hex-socket A2 M6 x 14 listing found
CLEAR, CSK_D = 6.6, 12.2                         # clearance hole, countersink diameter at the block top (90 deg)
CSK_DEPTH = (CSK_D - CLEAR) / 2                  # 2.8
# enclosure: 2 bosses on the floor under the screws (6061-T6), the block sits over them in recesses
BOSS2_D, BOSS2_H = 11.0, 7.5                    # boss top z 12.5; M6 major 6.0 -> 2.5 wall. History: 4.5 (R126) -> 5.5 (F02, +1) -> 7.5 (N4)
PILOT_D, PILOT_DEPTH = 5.0, 11.5                # M6 x 1.0 tap drill, from the boss top down to z 1.0 (1.0 of floor left, sealed)
TAP = 'M6x1.0-6H, 10.0 full thread'
# N4 (Dan 2026-10-16, OPEN-6 = A: "raise the VRC bosses and the holder 2.5 mm (full 1.5 x D thread, thicker ring)"): the holder goes up 2.5
# (Z_TOP 17.5) and the boss top to z 12.5 (+2.0 on F02's 10.5) so BOTH asks hold with a stocked screw: an M6 x 14 flush at z 17.5 engages
# 14 - (17.5 - 12.5) = 9.0 = 1.5 x D, its tip at z 3.5 inside the full thread; the ring between the recess roof (z 12.7) and the countersink
# bottom (z 14.7) is 2.0 (R73; was 1.5). Raising both by 2.5 would have kept 7.5 of thread and the 1.5 ring.
RECESS_D, RECESS_H = BOSS2_D + 2 * FIT, BOSS2_H + 0.2
# a screw of SCREW_LEN with its head flush engages (Z_TOP - SCREW_LEN) .. boss top = 9.0 mm of thread (1.5 x D; 7.5 after F02, 6.5 before)

# ---------- wires
OD = 1.57
R_BEND = 3 * OD + OD / 2          # 5.5 centre line
CUP_R = 4.0   # assumed: the 5 solder cups on a 8 mm circle, cup 1 on top, numbered clockwise seen from inside the box
DRAIN_Y = -13.0   # drain jumper (IN 3 -> OUT 5) runs over the block (top z 15) at the LP-16 axis height, clear of the board pads

# LP-16 cup -> module pin (S8 / S16 pin maps; NCV1124 nets: VR1 = left wheel, VR2 = right)
IN_MAP = {1: 2, 2: 1, 4: 3, 5: 4}      # ABS+ L -> VR1+, ABS- L -> VR1-, ABS+ R -> VR2+, ABS- R -> VR2-
OUT_MAP = {1: 5, 2: 6, 3: 8, 4: 7}     # +5V -> VDD, Gnd -> GND, L out -> VR1OUT, R out -> VR2OUT
# The OUT map crosses over (cups 1 / 2 and 3 / 4 land on pins in the other order), so two OUT wires meet their pin
# higher up (the exposed pin runs to z 19.46): the best of the 3-level search in the PR, 0.39 mm between wires.
JOINT_Z = {}   # v1 only: wires met the pins under the board
# v2: height above the board top where each lead turns down onto its pad. The OUT map crosses over, so OUT 1 / OUT 3 pass over the
# other two: best of a 4-level search per side - 0.94 mm between wires, the 2.54 pad pitch allows 0.97
# N4: the lead from cup 4 (IN +y, OUT -y: the side of that end's M6 countersink) runs its 6.6+ straight (cup + heat shrink) in toward the
# middle, to y 0 at x 21.7, so its lead relief stays >= 1.95 from the countersink
TURN_Y = {('IN', 4): 0.0, ('OUT', 4): 0.0}
APPROACH = {('OUT', 1): 14.0, ('OUT', 3): 20.0,
            ('IN', 4): 10.5, ('OUT', 4): 10.5}   # N4: cups 3 / 4 now drop longer onto their pads (a straight end >= 0.5 before the pad)   # N4: the board 2.5 higher, so the leads from the lowest cups (4) need a longer drop for their 3 x OD bends


def cup(side, k):
    """side +1 = IN (+x), -1 = OUT (-x). Seen from inside, 'right' is -y for IN and +y for OUT."""
    a = math.radians(72 * (k - 1))
    u, v = CUP_R * math.sin(a), CUP_R * math.cos(a)
    return (side * (LP16_REAR_X - 0.3), -side * u, LP16_AXIS_Z + v)


def wires():
    """name -> polyline. v2 (R126): cup -> 6.6 straight (cup + heat shrink) -> over the block top -> down onto the board's top pad at
    its pin (soldered from the top, no header)."""
    out = {}
    for side, cmap, tag in ((1, IN_MAP, 'IN'), (-1, OUT_MAP, 'OUT')):
        for k, p in cmap.items():
            c = cup(side, k)
            h = APPROACH.get((tag, k), 8.5)
            pts = [c, (side * 21.7, TURN_Y.get((tag, k), c[1]), c[2]), (PIN_X[p], PIN_Y[p], Z_TOP + h), (PIN_X[p], PIN_Y[p], Z_TOP + 0.3)]
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
    print('board underside z %.2f, top %.2f; block +-%.2f x +-%.2f; pocket %.2f x %.2f; screws %s'
          % (Z_BOARD, Z_TOP, BLOCK['x'], BLOCK['y'], POCKET[0], POCKET[1], SCREWS))
    rows, worst = wire_report()
    for r in rows:
        print(r)
    print('closest wire pair: gap %.2f mm (%s)' % worst)
