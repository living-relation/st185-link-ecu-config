"""R150 (Dan 2026-10-17: "Minimum thickness for walls is for critical or structural features, and doesn't apply to everything. If
something is questionable or unclear, it should be flagged for change or approval."): sorts every R127 spot (a wall <= 1.95 mm, W, or a
feature attached by < 3 mm, A) that cad/check_printed_walls.py finds into one of three classes:
  structural      the R73 / R127 minimums apply - check_printed_solid.py S4 / S5 FAIL on it
  non-structural  a named feature that carries no load, seals nothing and holds nothing - FLAGGED for Dan (reported, never failed)
  questionable    the map cannot place it - FLAGGED for Dan too, never silently passed
Critical / structural (R150): load-bearing walls, outer skins behind pockets, mounting / clip / retention features, walls between separate
circuits' terminals, anything sealing. The feature map below is the smallest one that covers that for the printed fuse box parts:
  1. FEATURES  named boxes (world mm) per part, first match wins. Today: the spots Dan marked on 2026-10-15 (R127 M1 - M6, the old
               MARKED list of check_printed_solid.py) and the whole R1 retainer clip - all structural. A spot Dan approves as
               non-structural gets a 'non-structural' box here (with his words), or a named exemption in spec.WALL_EXEMPT.
  2. A spots   an attachment under 3 mm is a mounting / clip / retention question by definition: structural.
  3. base rules (Power / Logic / BattRelay bases, from the build report and the part outline wall_check.json records):
               below the deck underside (legs, feet, the solid block under the POWER deck) = load-bearing; outside the deck outline
               (mount ears, end tabs) = mounting; within OUTER_BAND of the outline = the outer skin behind the pockets (R127 amendment);
               within TERMINAL_BAND of a terminal hole = a wall between separate circuits' terminals (R94 / R120).
  4. shells    (covers, pans): within OUTER_BAND of the part's own x / y extent = its side wall (skirt, catch band) - structural.
Anything else is questionable. None of the printed parts seals anything today (the covers are vented); a sealing face added later gets
a structural box in FEATURES.
Claude Code / Grok Bot, 2026-10-17.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec as S  # noqa: E402

STRUCTURAL, NON_STRUCTURAL, QUESTIONABLE = 'structural', 'non-structural', 'questionable'
FLAGGED = (NON_STRUCTURAL, QUESTIONABLE)
OUTER_BAND = S.OUTER_MIN + 1.5   # mm: 3.0 + 1.5 - the 4.3 base skirt / rim and the 2.5 cover / pan side walls sit inside it
TERMINAL_BAND = 3.0    # mm round a terminal hole footprint: the wall between it and its neighbour (R73 2.0 + 1.0 for the section step)
BOX_OF = (('Power_', 'POWER'), ('Logic_', 'LOGIC'), ('BattRelay_', 'BATTRELAY'))
PLACE = S.PLACE       # world (x, y) of each box's local origin - the STLs and the report boxes are in world mm
WHOLE = (-1e3, 1e3, -1e3, 1e3, -1e3, 1e3)
# (class, why, (x0, x1, y0, y1, z0, z1)) per part; the R127 spots Dan marked 2026-10-15 (closeup_c2) stay structural and must stay clear
FEATURES = {
    'Power_Base_PA12_printed': [
        (STRUCTURAL, 'R127 M1 / M5: R1 cavity group under the deck (Dan-marked)', (191.0, 225.0, 30.0, 56.0, 26.0, 38.5)),
        (STRUCTURAL, 'R127 M4: R1 bend saddle (Dan-marked)', (218.0, 236.0, 36.0, 50.0, 10.0, 32.0)),
        (STRUCTURAL, 'R127 M6: R2 bend saddle (Dan-marked)', (188.0, 206.0, 54.0, 68.0, 10.0, 32.0)),
    ],
    'Power_Retainer_R1_PA12_printed': [
        (STRUCTURAL, 'R127 M2 / R123: R1 retainer clip - a retention feature (Dan-marked)', WHOLE),
    ],
}
MARKED = {k: [b for (c, why, b) in v if 'Dan-marked' in why] for k, v in FEATURES.items()}   # check_printed_solid.py S4: must stay clear


def box_of(part):
    return next((b for (p, b) in BOX_OF if part.startswith(p)), None)


def _hit(a, b):
    """Boxes (x0, x1, y0, y1, z0, z1) overlap or touch."""
    return all(b[2 * d] <= a[2 * d + 1] and a[2 * d] <= b[2 * d + 1] for d in range(3))


def _near(a, b, r):
    """Box a comes within r of box b in plan (x, y)."""
    return all(b[2 * d] - r <= a[2 * d + 1] and a[2 * d] <= b[2 * d + 1] + r for d in range(2))


def terminal_boxes(report, box):
    """Plan footprints (x0, x1, y0, y1) of every terminal hole of a box, world mm."""
    sx, sy = PLACE.get(box, (0.0, 0.0))
    return [(h['x'] + sx - h['sx'] / 2, h['x'] + sx + h['sx'] / 2, h['y'] + sy - h['sy'] / 2, h['y'] + sy + h['sy'] / 2)
            for h in (report.get('terminal_holes') or {}).get(box, [])]


def classify(part, at, kind, info=None, report=None, features=None):
    """(class, why) of one spot. at = (x0, x1, y0, y1, z0, z1) world mm; kind 'W' (wall) or 'A' (attachment); info = the part's
    wall_check.json entry (its 'outline' / 'bounds'); report = fusebox_report.json; features = FEATURES (tests pass their own)."""
    info, report = info or {}, report or {}
    for (c, why, b) in (FEATURES if features is None else features).get(part, []):
        if _hit(at, b):
            return c, why
    if kind == 'A':
        return STRUCTURAL, 'attached by < 3 mm: a mounting / clip / retention feature (R127 A)'
    box = box_of(part)
    if '_Base_' in part:
        zd = ((report.get('boxes_mm') or {}).get(box) or {}).get('z_d')
        if zd is not None and at[4] < zd - 0.5:
            return STRUCTURAL, 'below the deck underside (z %.1f): legs / feet / block under the deck - load-bearing' % zd
        ol = info.get('outline')
        if ol:
            if at[0] < ol[0] or at[1] > ol[1] or at[2] < ol[2] or at[3] > ol[3]:
                return STRUCTURAL, 'outside the deck outline: mount ear / foot / end tab - mounting'
            if min(at[0] - ol[0], ol[1] - at[1], at[2] - ol[2], ol[3] - at[3]) <= OUTER_BAND:
                return STRUCTURAL, 'within %.1f of the outline: outer skin behind the pockets (R127 amendment)' % OUTER_BAND
        for t in terminal_boxes(report, box):
            if _near(at, t, TERMINAL_BAND):
                return STRUCTURAL, 'within %.1f of a terminal hole: wall between separate circuits\' terminals' % TERMINAL_BAND
        if not ol:
            return QUESTIONABLE, 'no deck outline recorded in wall_check.json - re-run cad/check_printed_walls.py to place it'
        return QUESTIONABLE, 'base, inside the deck, away from the skin and the terminals (rib / guide / web?) - Dan to change or approve'
    bd = info.get('bounds')
    if bd:
        if min(at[0] - bd[0], bd[1] - at[1], at[2] - bd[2], bd[3] - at[3]) <= OUTER_BAND:
            return STRUCTURAL, 'within %.1f of the part edge: shell side wall / skirt' % OUTER_BAND
        return QUESTIONABLE, 'shell face away from its side walls (cover top / pan floor) - Dan to change or approve'
    return QUESTIONABLE, 'no part bounds recorded in wall_check.json - re-run cad/check_printed_walls.py to place it'


def classify_part(part, info, report=None, features=None):
    """[(kind, item, class, why)] for every W and A spot of one wall_check.json part entry."""
    out = []
    for k, key in (('W', 'walls'), ('A', 'attach')):
        for x in info.get(key) or []:
            c, why = classify(part, x['at'], k, info, report, features)
            out.append((k, x, c, why))
    return out


def flag_lines(parts, report=None, features=None):
    """Human-readable flag list (R150): one line per non-structural / questionable spot, for Dan to change or approve."""
    lines = []
    for part in sorted(parts):
        for (k, x, c, why) in classify_part(part, parts[part], report, features):
            if c in FLAGGED:
                lines.append('%s  %s  %s at x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f  [%s] %s' % (
                    c.upper(), part, 'wall <= 1.95' if k == 'W' else x.get('kind', 'attachment < 3'), *x['at'], c, why))
    return lines


def write_flags_md(path, parts, report=None):
    """cad/fusebox/rev7/WALL-FLAGS.md: the flag list Dan reads (written by check_printed_walls.py, checked by check_printed_solid.py)."""
    ls = flag_lines(parts, report)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# Printed fuse box walls - flagged for Dan (R150)\n\n')
        f.write('Generated by `cad/check_printed_walls.py` from `wall_check.json` - do not hand-edit. Minimum wall (R73 / R127) applies to\n'
                'critical or structural features only (DECISIONS R150); those still fail `check_printed_solid.py` S4 / S5. The spots below\n'
                'are thin but not placed as structural: **change or approve** each one (approve = a non-structural box in\n'
                '`cad/fusebox/src/wall_classes.py` FEATURES or a named exemption in `spec.WALL_EXEMPT`, with your words).\n\n')
        f.write('Flagged: %d\n\n' % len(ls))
        f.write(''.join('- %s\n' % l for l in ls) if ls else '- none\n')
    return ls
