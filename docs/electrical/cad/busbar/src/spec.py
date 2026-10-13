"""ST185 glove-box combined +/- bus bar: layout spec shared by the Fusion build and the 2D drawings.

All dimensions in mm. x = along the bar, y = depth (front = -y), z = up (0 = underside of the printed base).
Claude Code, 2026-10-13.

Catalog sources (no guessed dims):
  Lugs  - Klauke tubular cable lugs, Cu tin-plated, R series (Klauke catalogue sheet "Tubular cable lugs, Cu,
          standard type"): b = tongue width, l = overall length, d4 = barrel OD, d2 = stud hole.
          6R10  50 mm2 M10  b 20  l 39  d4 14.0  d2 10.5   -> 1/0 AWG (53.5 mm2) runs H1/H2/H3/H6a/H7
          4R8   25 mm2 M8   b 16  l 32  d4 10.0  d2 8.5    -> 4 AWG (21.2 mm2) LMI-A/B, MTA-1/2 feeds
          2R8   10 mm2 M8   b 15  l 25  d4 7.0   d2 8.5    -> 8 AWG (8.4 mm2) MTA-3 feed
  Ferrule - Weidmueller H50,0/25 (1988780000): 50 mm2, contact length 25, collar dia 13 (design B set-screw ports).
  Bolts - ISO 4017 hex head, A2-70: M10 s=16 k=6.4, M8 s=13 k=5.3.
Wire gauges per connection from st185-link-ecu-config (read-only): ENGINE-ROOM-POWER-REDISTRIBUTION.md 5.1 / 8.1,
  ST185-EngineRoom-C.harness (pdb c1/c2/c8, t_gnd_id/ig = GENERIC LUG M10 50MM2),
  ST185-CabinPower.harness (t_pdb_lmi_b / mta1 / mta2 = M8 4 AWG, t_pdb_mta3 = M8 8 AWG, batt_ring = M8 4 AWG LMI-A).
"""

LUGS = {
    "6R10": dict(b=20.0, l=39.0, d4=14.0, d2=10.5, stud="M10", src="Klauke 6R10 (50 mm2, M10, Cu tin)"),
    "4R8": dict(b=16.0, l=32.0, d4=10.0, d2=8.5, stud="M8", src="Klauke 4R8 (25 mm2, M8, Cu tin)"),
    "2R8": dict(b=15.0, l=25.0, d4=7.0, d2=8.5, stud="M8", src="Klauke 2R8 (10 mm2, M8, Cu tin)"),
}
FERRULE = dict(name="Weidmueller H50,0/25", collar=13.0, length=25.0)

BOLT = {"M10": dict(s=16.0, k=6.4, hole=10.5), "M8": dict(s=13.0, k=5.3, hole=8.5)}
STD_LEN = {"M10": [25, 30, 35, 40, 45], "M8": [20, 25, 30, 35, 40]}
# stud protrusion above the land: washer + Belleville + nut + 2 threads + a lug tongue up to 6 mm
PROTRUSION_MIN = {"M10": 21.2, "M8": 18.6}
POCKET_CLEAR = 0.3     # hex pocket across flats clearance
POCKET_EXTRA = 0.6     # hex pocket depth over head height
FLOOR = 4.0            # printed base floor thickness
RIM_TOP = 8.0          # top of the printed perimeter rim / lug-channel ribs (cover skirt sits here)
GAP = 3.0              # minimum gap between installed lugs (Dan's rule)
# Lug anti-rotation pockets (Dan 2026-10-13): printed locator plate on the Al land, pockets cut THROUGH it so the
# lug sits on bare aluminium; the tongue sides are trapped by the pocket walls. Beyond the bar edge the printed body
# carries a barrel trough that fixes the wire exit direction.
POCKET = dict(T=3.0,           # locator plate thickness = pocket depth above the Al face
              clr=0.3,         # per side, tongue / ring
              trough_clr=0.5)  # per side, barrel trough
WASHER_OD = {"M10": 20.0, "M8": 16.0}   # ISO 7089 flat washer OD; the ring pocket always clears it,
                                        # so the clamp stack never bears on plastic whatever the tongue thickness


def pocket_ring(lug):
    L = LUGS[lug]
    return max(L["b"], WASHER_OD[L["stud"]]) + 2 * POCKET["clr"]


def pocket_slot(lug):
    return LUGS[lug]["b"] + 2 * POCKET["clr"]


def trough_w(lug):
    return LUGS[lug]["d4"] + 2 * POCKET["trough_clr"]


def trough_floor(lug, land):
    """Lowest point the barrel can reach (palm centred or flush on the barrel): land - d4/2, minus clearance."""
    return land - LUGS[lug]["d4"] / 2 - POCKET["trough_clr"]


def bolt_len(size, land_thk):
    k = BOLT[size]["k"]
    need = (land_thk - (k + POCKET_EXTRA)) + PROTRUSION_MIN[size]
    for L in STD_LEN[size]:
        if L >= need:
            return L
    raise ValueError("no std length")


# ---------------------------------------------------------------- Design A
# Inline poles: POS bar left, NEG bar right, printed barrier between. Two stud rows per pole;
# front row lugs exit forward (-y), rear row lugs exit rearward (+y). Stepped bar: rear land 6 mm higher.
A = dict(
    name="A",
    title="Design A - inline poles, two stepped rows, studs only",
    bars=[
        # x0, x1, y0, y1, step list: (y0, y1, top z)
        dict(pole="POS", x0=-126.0, x1=-12.0, y0=-25.0, y1=25.0,
             lands=[(-25.0, 0.0, 16.0), (0.0, 25.0, 22.0)]),
        dict(pole="NEG", x0=12.0, x1=88.0, y0=-25.0, y1=25.0,
             lands=[(-25.0, 0.0, 16.0), (0.0, 25.0, 22.0)]),
    ],
    studs=[
        # x, y, lug, exit(-1 fwd / +1 rear), pole, label
        (-112, -13, "6R10", -1, "POS", "BAT+ IN (H1, 1/0)"),
        (-112, 13, "6R10", 1, "POS", "RADLOK+ OUT (H3, 1/0)"),
        (-87, -13, "6R10", -1, "POS", "SPARE M10"),
        (-87, 13, "4R8", 1, "POS", "LMI-A IN (4 AWG)"),
        (-64, -13, "4R8", -1, "POS", "LMI-B IN (4 AWG)"),
        (-64, 13, "4R8", 1, "POS", "MTA-1 (4 AWG)"),
        (-44, -13, "4R8", -1, "POS", "MTA-2 (4 AWG)"),
        (-44, 13, "2R8", 1, "POS", "MTA-3 (8 AWG)"),
        (-24, -13, "4R8", -1, "POS", "SPARE M8"),
        (-24, 13, "4R8", 1, "POS", "SPARE M8"),
        (74, -13, "6R10", -1, "NEG", "BAT- (H2, 1/0)"),
        (74, 13, "6R10", 1, "NEG", "RADLOK- (H6a, 1/0)"),
        (49, -13, "6R10", -1, "NEG", "GND ID (H7, 1/0)"),
        (49, 13, "6R10", 1, "NEG", "GND IG (H7, 1/0)"),
        (24, -13, "6R10", -1, "NEG", "SPARE M10"),
        (24, 13, "4R8", 1, "NEG", "SPARE M8"),
    ],
    ports=[],
    body=dict(x0=-130.0, x1=92.0, y0=-48.0, y1=48.0, wall=3.0),
    barrier=dict(axis="x", at=0.0, thk=4.0),     # wall normal to x at x=0
    bosses=[(0.0, -30.0), (0.0, 30.0)],
    flanges=[dict(x0=-150.0, x1=-130.0, y0=-40.0, y1=40.0, slots=[(-140.0, -13.0), (-140.0, 13.0)]),
             dict(x0=92.0, x1=112.0, y0=-40.0, y1=40.0, slots=[(102.0, -13.0), (102.0, 13.0)])],
    holddowns=[],
    clamps=[],
    # Rev 2 (Dan 2026-10-13, A chosen): anti-rotation pockets MACHINED INTO THE ALUMINIUM (bar +3 mm, pocket floor =
    # old land height), no printed locator plates. Hold-down: 2x M4 per bar, counterbored, between stud columns on the
    # centreline, into a BLIND brass insert in a printed boss that rises into a recess in the bar underside.
    metal_pockets=True,
    bar_raise=3.0,
    bar_screws=[(-99.5, 0.0), (-34.0, 0.0), (36.5, 0.0), (61.5, 0.0)],
    section_y=13.0, section_x=-99.5,
    ribs=[(-99.5, "y"), (-75.5, "y"), (-54.0, "y"), (-34.0, "y"), (36.5, "y"), (61.5, "y")],
    ceiling=48.0,
    marks=[("POS", -69.0, 0.0), ("NEG", 50.0, 0.0)],
)

# ---------------------------------------------------------------- Design B rev 1 (as built 2026-10-13, kept unchanged)
# Parallel poles back to back: POS bar in front (everything exits forward), NEG bar behind (exits rearward),
# barrier wall along the length between them. 1/0 cables land in set-screw ports (crimped ferrule,
# 2 x M8 set screws each) in tall end blocks; 4/8 AWG on M8 studs in the thin middle (stepped bar).
B_PORT_PITCH = 21.0
B = dict(
    name="B",
    title="Design B - back-to-back poles, 1/0 set-screw ports + M8 studs",
    bars=[
        dict(pole="POS", x0=-106.5, x1=106.5, y0=-46.0, y1=-16.0,
             blocks=[(-106.5, -61.5), (82.5, 106.5)], block_top=34.0, field_top=16.0),
        dict(pole="NEG", x0=-106.5, x1=28.5, y0=16.0, y1=46.0,
             blocks=[(-106.5, -61.5), (-37.5, 28.5)], block_top=34.0, field_top=16.0),
    ],
    studs=[
        (-49.5, -31, "4R8", -1, "POS", "LMI-A IN (4 AWG)"),
        (-29.5, -31, "4R8", -1, "POS", "LMI-B IN (4 AWG)"),
        (-9.5, -31, "4R8", -1, "POS", "MTA-1 (4 AWG)"),
        (10.5, -31, "4R8", -1, "POS", "MTA-2 (4 AWG)"),
        (30.5, -31, "2R8", -1, "POS", "MTA-3 (8 AWG)"),
        (50.5, -31, "4R8", -1, "POS", "SPARE M8"),
        (70.5, -31, "4R8", -1, "POS", "SPARE M8"),
        (-49.5, 31, "4R8", 1, "NEG", "SPARE M8"),
    ],
    ports=[
        # x, face y, depth dir (+1 = bore runs +y from face), pole, label
        (-94.5, -46.0, 1, "POS", "BAT+ IN (H1, 1/0)"),
        (-73.5, -46.0, 1, "POS", "RADLOK+ OUT (H3, 1/0)"),
        (94.5, -46.0, 1, "POS", "SPARE 1/0 port"),
        (-94.5, 46.0, -1, "NEG", "BAT- (H2, 1/0)"),
        (-73.5, 46.0, -1, "NEG", "RADLOK- (H6a, 1/0)"),
        (-25.5, 46.0, -1, "NEG", "GND ID (H7, 1/0)"),
        (-4.5, 46.0, -1, "NEG", "GND IG (H7, 1/0)"),
        (16.5, 46.0, -1, "NEG", "SPARE 1/0 port"),
    ],
    port=dict(bore=13.5, depth=28.0, zc=17.0, screws=(8.0, 19.0), screw="M8", screw_len=12.0),
    body=dict(x0=-110.5, x1=110.5, y0=-60.0, y1=60.0, wall=3.0),
    barrier=dict(axis="y", at=0.0, thk=4.0),     # wall normal to y at y=0
    bosses=[(-50.0, 0.0), (50.0, 0.0)],
    flanges=[dict(x0=-130.5, x1=-110.5, y0=-45.0, y1=45.0, slots=[(-120.5, -31.0), (-120.5, 31.0)]),
             dict(x0=110.5, x1=130.5, y0=-45.0, y1=45.0, slots=[(120.5, -31.0), (120.5, 31.0)])],
    holddowns=[],
    # bar hold-down: M4 screws through locator-plate tabs into blind heat-set inserts in printed ledges beside the barrier
    clamps=[(-55.0, -10.5), (76.0, -10.5), (-55.0, 10.5), (-44.0, 10.5)],
    section_y=-31.0, section_x=-55.0,
    ribs=[(-39.5, "-y"), (-19.5, "-y"), (0.5, "-y"), (20.5, "-y"), (40.5, "-y"), (60.5, "-y")],
    ceiling=38.0,
    marks=[("POS", 0.0, -12.0), ("NEG", 60.0, 12.0)],
)


# ---------------------------------------------------------------- Design B (rev 2, 2026-10-13)
# Parallel poles back to back: POS bar in front (everything exits forward), NEG bar behind (exits rearward),
# barrier wall along the length between them. 1/0 cables land in set-screw ports (crimped ferrule, 2 x M8 set
# screws each) in tall end blocks; 4/8 AWG lugs on M8 studs in the thin field (stepped bar).
# Rev 2 (Dan): lug pockets machined in the Al (field +3 mm), 2-screw hold-down per bar into blind inserts in printed
# bosses, and a THIRD "universal" bar U in the empty space next to NEG. U is electrically separate; ONE bolted Al link
# strap ties it to NEG (strap along x through a notch in the U/NEG wall) or to POS (strap along y through a notch in the
# main barrier). Notches not in use are closed by printed plugs held down by the cover; with U floating the strap
# stows in an insulated printed slot. Only one strap exists, so POS and NEG can never be bridged by it.
B2 = dict(
    name="B_rev2",
    title="Design B rev 2 - back-to-back poles, set-screw ports, M8 studs + universal bus",
    bars=[
        dict(pole="POS", x0=-106.5, x1=131.5, y0=-46.0, y1=-16.0,
             blocks=[(-106.5, -61.5), (107.5, 131.5)], block_top=34.0, field_top=16.0),
        dict(pole="NEG", x0=-106.5, x1=54.5, y0=16.0, y1=46.0,
             blocks=[(-106.5, -61.5), (-30.5, 35.5)], block_top=34.0, field_top=16.0),
        dict(pole="UNI", x0=80.5, x1=170.5, y0=16.0, y1=46.0,
             blocks=[], block_top=34.0, field_top=16.0),
    ],
    studs=[
        (-41.5, -31, "4R8", -1, "POS", "LMI-A IN (4 AWG)"),
        (-21.5, -31, "4R8", -1, "POS", "LMI-B IN (4 AWG)"),
        (-1.5, -31, "4R8", -1, "POS", "MTA-1 (4 AWG)"),
        (18.5, -31, "4R8", -1, "POS", "MTA-2 (4 AWG)"),
        (38.5, -31, "2R8", -1, "POS", "MTA-3 (8 AWG)"),
        (58.5, -31, "4R8", -1, "POS", "SPARE M8"),
        (-40.5, 31, "4R8", 1, "NEG", "SPARE M8"),
        (118.5, 31, "4R8", 1, "UNI", "U-1 (M8)"),
        (138.5, 31, "4R8", 1, "UNI", "U-2 (M8)"),
        (158.5, 31, "4R8", 1, "UNI", "U-3 (M8)"),
    ],
    ports=[
        (-94.5, -46.0, 1, "POS", "BAT+ IN (H1, 1/0)"),
        (-73.5, -46.0, 1, "POS", "RADLOK+ OUT (H3, 1/0)"),
        (119.5, -46.0, 1, "POS", "SPARE 1/0 port"),
        (-94.5, 46.0, -1, "NEG", "BAT- (H2, 1/0)"),
        (-73.5, 46.0, -1, "NEG", "RADLOK- (H6a, 1/0)"),
        (-18.5, 46.0, -1, "NEG", "GND ID (H7, 1/0)"),
        (2.5, 46.0, -1, "NEG", "GND IG (H7, 1/0)"),
        (23.5, 46.0, -1, "NEG", "SPARE 1/0 port"),
    ],
    port=dict(bore=13.5, depth=28.0, zc=17.0, screws=(8.0, 19.0), screw="M8", screw_len=12.0),
    # link studs (M8, same hex-pocket stud as the lug studs; the strap lands on the bare Al field face)
    links=[(46.5, 25.0, "NEG", "LINK N"), (96.5, 25.0, "UNI", "LINK U"), (96.5, -25.0, "POS", "LINK P")],
    strap=dict(pitch=50.0, w=20.0, t=6.0, hole=8.5, installed=("UNI", "NEG"),
               part="6061-T6 (or 6101) link strap 6 x 20 x 70, 2 holes D8.5 at 50, ends R10, bare + anti-oxidant"),
    # barrier walls: main wall along x at y = 0; extra wall between NEG and U
    barrier=dict(axis="y", at=0.0, thk=4.0),
    xwalls=[dict(x=67.5, thk=4.0)],
    # strap notches (width 22, from z 18 to the ceiling) + removable printed plugs
    notches=[dict(wall="main", at=96.5, name="P"), dict(wall="x", at=25.0, name="N")],
    stow=dict(x0=-36.0, x1=38.0, y0=-15.0, y1=-2.0, z1=24.0, slot_w=6.6, slot_z0=6.0),
    plug_park=dict(x0=137.0, x1=167.0, y0=-36.0, y1=-24.0, z1=30.0, slot=(141.0, 163.0, -32.0, -28.0), slot_z0=12.0),
    body=dict(x0=-110.5, x1=174.5, y0=-60.0, y1=60.0, wall=3.0),
    bosses=[(-50.0, 0.0), (50.0, 0.0)],
    flanges=[dict(x0=-130.5, x1=-110.5, y0=-45.0, y1=45.0, slots=[(-120.5, -31.0), (-120.5, 31.0)]),
             dict(x0=174.5, x1=194.5, y0=-45.0, y1=45.0, slots=[(184.5, -31.0), (184.5, 31.0)])],
    holddowns=[],
    clamps=[],
    metal_pockets=True,
    bar_raise=3.0,
    bar_screws=[(-56.0, -31.0), (73.0, -31.0), (-55.0, 31.0), (46.5, 40.5), (87.0, 40.5), (108.0, 40.5)],
    extra_tags=[(155.0, -18.0, ["LINK STRAP", "U-NEG or U-POS", "ONE STRAP ONLY"])],
    sections=[("y", -31.0, "front", "studs, floor, mounting screws"),
              ("x", -56.0, "left", "hold-down: M4 screw, printed boss, blind insert"),
              ("x", 96.5, "left", "universal bus link: U link stud, notch plug in main barrier, POS link stud")],
    section_y=-31.0, section_x=-56.0,
    ribs=[],
    ceiling=41.0,
    marks=[("POS", -25.0, -12.0), ("NEG", -25.0, 12.0)],
)

# isolation hardware (catalog / standard dims)
CLAMP = dict(screw="ISO 7380 M4x10 A2", head_d=7.6, head_k=2.2, len=10.0,
             insert="M4 brass heat-set insert, 8.1 long, 5.6 hole (Ruthex RX-M4x8.1 class)", insert_len=8.1, hole=5.6,
             hole_depth=9.0, tab_w=8.6, tab_reach=5.0)
MOUNT = dict(screw="ISO 7380 M6x16 A2 + ISO 7089 washer", washer_od=12.0, washer_t=1.6, head_d=10.5, head_k=3.3,
             slot_len=12.0, slot_w=6.6)
BAR_SCREW = dict(screw="ISO 7380 M4x10 A2", cbore_d=8.0, seat_below_top=2.5, hole=4.5,
                 recess_d=10.6, recess_h=9.0, boss_d=10.0, boss_gap=0.3, insert_hole_depth=8.7)
COVER_WALL = 2.5
COVER_TOP = 3.0


GAUGE = {"6R10": "1/0", "4R8": "4AWG", "2R8": "8AWG"}
ETCH = dict(height=2.0, depth=0.6)


def _name(label):
    n = label.split(" (")[0]
    for a, b in (("RADLOK+ OUT", "RADLOK+"), (" IN", ""), ("SPARE M10", "SPARE"), ("SPARE M8", "SPARE"),
                 ("SPARE 1/0 port", "SPARE"), ("GND ", "GND ")):
        n = n.replace(a, b)
    return n


def notch(design, stud=None, port=None):
    """Cover wire-exit opening W x H (mm) for a stud or port."""
    if stud is not None:
        x, y, lug, ex, pole, label = stud
        bar = [b for b in design["bars"] if b["pole"] == pole][0]
        top = ([t for (y0, y1, t) in bar["lands"] if y0 <= y <= y1][0]) if "lands" in bar else bar["field_top"]
        return LUGS[lug]["b"] + 2, top + LUGS[lug]["d4"] + 1 - RIM_TOP
    return 22.0, design["port"]["zc"] + 11 - RIM_TOP


def etch_lines(design, stud=None, port=None):
    """3-line etched tag: terminal / gauge + stud or port bore / cover wire-exit opening."""
    w, h = notch(design, stud, port)
    if stud is not None:
        lug = stud[2]
        return [_name(stud[5]), "%s %s" % (GAUGE[lug], LUGS[lug]["stud"]), "exit %.0fx%.0f" % (w, h)]
    return [_name(port[4]), "1/0 D%.1f" % design["port"]["bore"], "exit %.0fx%.0f" % (w, h)]


def check(design):
    """Return list of (a, b, gap) lug-to-lug side gaps for studs in the same row/exit, and failures (< GAP)."""
    out = []
    st = design["studs"]
    for i in range(len(st)):
        for j in range(i + 1, len(st)):
            a, b = st[i], st[j]
            if a[1] == b[1] and a[3] == b[3]:
                gap = abs(a[0] - b[0]) - (LUGS[a[2]]["b"] + LUGS[b[2]]["b"]) / 2
                out.append((a[5], b[5], round(gap, 2)))
    return out


if __name__ == "__main__":
    for d in (A, B):
        g = check(d)
        print(d["name"], "min side gap", min(x[2] for x in g), [x for x in g if x[2] < GAP])


# ---------------------------------------------------------------- rev 3 (Dan 2026-10-13: 2 hold-down screws per bar is not
# enough and some pairs sat too close). New versions only; A rev 2 / B rev 1 / B rev 2 stay as saved.
import copy as _copy

A3 = _copy.deepcopy(A)
A3.update(
    name="A_rev3",
    title="Design A rev 3 - inline poles, two stepped rows, studs only, 7 hold-down screws",
    # POS: one screw in every column gap; NEG: both gaps + one in a 12 mm extension at the outer end
    bar_screws=[(-99.5, 0.0), (-75.5, 0.0), (-54.0, 0.0), (-34.0, 0.0), (36.5, 0.0), (61.5, 0.0), (94.0, 0.0)],
    body=dict(x0=-130.0, x1=104.0, y0=-48.0, y1=48.0, wall=3.0),
    flanges=[dict(x0=-150.0, x1=-130.0, y0=-40.0, y1=40.0, slots=[(-140.0, -13.0), (-140.0, 13.0)]),
             dict(x0=104.0, x1=124.0, y0=-40.0, y1=40.0, slots=[(114.0, -13.0), (114.0, 13.0)])],
)
A3["bars"][1]["x1"] = 100.0

B3 = _copy.deepcopy(B2)
_PITCH = 50.8            # = Bussmann AMG (MEGA-type) bolt-in fuse: M8 studs on 2.00 in (50.8 mm) centres
B3.update(
    name="B_rev3",
    title="Design B rev 3 - back-to-back poles, set-screw ports, M8 studs + universal bus, 10 hold-down screws",
    links=[(46.5, 25.0, "NEG", "LINK N"), (46.5 + _PITCH, 25.0, "UNI", "LINK U"), (46.5 + _PITCH, 25.0 - _PITCH, "POS", "LINK P")],
    strap=dict(pitch=_PITCH, w=20.0, t=6.0, hole=8.5, installed=("UNI", "NEG"),
               part="6061-T6 link strap 6 x 20 x 70.8, 2 holes D8.5 at 50.8 (= AMG/MEGA fuse pitch), ends R10"),
    fuse_option=dict(name="Bussmann AMG (MEGA-type) bolt-in fuse, 100-300 A, 32 VDC, 1 kA interrupt",
                     pitch=_PITCH, term_w=15.4, term_t=1.52, length=68.4, body_l=29.2, body_h=9.0, hole=8.6),
    notch_z0=14.8,       # deep enough for the AMG body (hangs ~3.7 mm below the terminal plane)
    notches=[dict(wall="main", at=46.5 + _PITCH, name="P"), dict(wall="x", at=25.0, name="N")],
    # relief milled in the U bar where the AMG body passes over it (U-NEG position)
    reliefs=[dict(pole="UNI", x0=80.0, x1=87.8, y0=14.0, y1=36.0, z=14.8)],
    plug_park=dict(x0=150.0, x1=180.0, y0=-42.0, y1=-28.0, z1=30.0, slot=(154.0, 176.0, -37.0, -33.0), slot_z0=12.0),
    body=dict(x0=-120.5, x1=184.5, y0=-60.0, y1=60.0, wall=3.0),
    flanges=[dict(x0=-140.5, x1=-120.5, y0=-45.0, y1=45.0, slots=[(-130.5, -31.0), (-130.5, 31.0)]),
             dict(x0=184.5, x1=204.5, y0=-45.0, y1=45.0, slots=[(194.5, -31.0), (194.5, 31.0)])],
    bar_screws=[(-110.0, -31.0), (-56.0, -31.0), (73.0, -31.0), (137.0, -31.0),     # POS 4
                (-110.0, 31.0), (-55.0, 31.0), (46.5, 40.5),                         # NEG 3
                (87.0, 40.5), (108.0, 40.5), (174.0, 31.0)],                         # U 3
    extra_tags=[(165.0, -15.0, ["LINK: strap or", "AMG fuse 50.8", "ONE ONLY"])],
    sections=[("y", -31.0, "front", "studs, floor, mounting screws"),
              ("x", -110.0, "left", "hold-down at the left end: M4 screw, printed boss, blind insert"),
              ("x", 46.5 + _PITCH, "left", "universal bus link: U link stud, notch P plug, POS link stud")],
    section_x=-110.0,
)
B3["bars"][0].update(x0=-116.5, x1=143.5, blocks=[(-116.5, -61.5), (109.5, 143.5)])
B3["bars"][1].update(x0=-116.5, blocks=[(-116.5, -61.5), (-30.5, 35.5)])
B3["bars"][2].update(x1=180.5)
B3["ports"] = [p if p[4] != "SPARE 1/0 port" or p[3] != "POS" else (121.5, p[1], p[2], p[3], p[4]) for p in B3["ports"]]
