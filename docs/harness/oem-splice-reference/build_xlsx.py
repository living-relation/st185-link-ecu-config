"""Build st185-oem-splice-reference.xlsx from MASTER-wirelist.csv + the highlighted images in img/.
Run make_images.py first, then: python build_xlsx.py
"""
import csv, os, math
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XImg
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from PIL import Image as PImg

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, 'img')
MASTER = os.path.join(HERE, '..', 'MASTER-wirelist.csv')
rows = {r['wire_id']: r for r in csv.DictReader(open(MASTER, encoding='utf-8'))}

# (sheet, connector label, pin, wire_id, oem_id in master, skipped-device flag)
SP = []
def add(sheet, conn, oem_id, items, flag=''):
    for it in items:
        pin, wid = it[0], it[1]
        fl = it[2] if len(it) > 2 else flag
        SP.append((sheet, conn, oem_id, pin, wid, fl))

CRU = 'VERIFY: pin numbers from 1990 EWD p.118 - wire colour matches 1993 Mitchell Fig.12 but 1993 stalk pin numbers NOT confirmed (no cruise page in the repo 1993 EWD)'
S1 = 'J-B1 (1H 1I 1F)'
add(S1, 'J/B No.1 plug 1H (8 pin, left kick)', 'JB1', [('2', 'w_pmu_dome'), ('4', 'w_turn_f7'), ('5', 'w_wip_b', 'wiper (skipped device)'), ('6', 'w_clr'), ('7', 'w_ign'), ('7', 'w_ig2_in'), ('8', 'w_turn_f8')])
add(S1, 'J/B No.1 plug 1I (1 pin)', 'JB1', [('1', 'w_pdb_jb1')])
add(S1, 'J/B No.1 plug 1F (14 pin, dark gray)', 'JB1', [('1', 'w_rl_tail'), ('2', 'w_rl_turn_r'), ('3', 'w_rl_turn_l')])
S2 = 'IE1'
add(S2, 'IE1 (20 pin, blue, left kick)', 'IE1', [
    ('3', 'w_pmu_rtr', 'retract relay feed (retract motors skipped)'), ('10', 'w_pdb_am1'), ('12', 'w_haz_cp'), ('17', 'w_pdb_am2'), ('19', 'w_horn_85_cp'),
    ('2', 'w_head_coil_cp', 'headlights (skipped)'), ('11', 'w_hl_high', 'headlights (skipped)'), ('18', 'w_hl_low', 'headlights (skipped)'),
    ('6', 'w_wip_park', 'wiper (skipped)'), ('13', 'w_wip_lo', 'wiper (skipped)'), ('20', 'w_wip_hi', 'wiper (skipped)'),
    ('7', 'w_rtr_r3_4', 'retract (skipped)'), ('8', 'w_rtr_r3_2', 'retract (skipped)'), ('9', 'w_rtr_close', 'retract (skipped)'),
    ('14', 'w_rtr_r2_4', 'retract (skipped)'), ('15', 'w_rtr_r2_2', 'retract (skipped)'), ('16', 'w_rtr_open', 'retract (skipped)')])
S3 = 'IG2 (under ECU)'
add(S3, 'IG2 (20 pin, dark gray, under engine ECU)', 'IG2', [('15', 'w_ig_ks_in'), ('16', 'w_alt_l_c')])
S4 = 'J-B3 R-B2 R-B4'
add(S4, 'J/B No.3 plug 3B (16 pin, behind cluster)', 'JB3', [('9', 'w_rev_gauge_cp')])
add(S4, 'R/B No.2 power main relay (left kick)', 'RB2', [('2', 'w_pwr_86_cp'), ('1', 'w_rb2'), ('2', 'w_rb2_wl', 'VERIFY: pin 2 already has the L-Y coil lead; W-L may be on the 30A fuse terminal 2')])
add(S4, 'R/B No.4 starter relay (M/T) (right kick)', 'RB4', [('1', 'w_start_in_cp')])
add(S4, 'R/B No.4 heater relay (right kick)', 'RB4', [('1', 'w_htr_85_cp'), ('3', 'w_htr_86_cp')])
S5 = 'Cluster plugs'
add(S5, 'Cluster plug C13 (B) [master calls it C11]', 'C11', [('2', 'w_tl_a'), ('11', 'w_tr_a'), ('12', 'w_hb_a')])
add(S5, 'Cluster plug C14 (C) [master calls it C12]', 'C12', [('9', 'w_ig_tap'), ('8', 'w_chg_k'), ('1', 'w_pk_k')])
S6 = 'Cruise Clutch Stop'
add(S6, 'Cruise stalk C16 (1993) [master: C14 = 1990 code]', 'Cruise', [('5', 'w_an2', CRU), ('15', 'w_sw2', CRU), ('17', 'w_cru_gnd', CRU)])
add(S6, 'Clutch start switch C11 (1993)', 'C11', [('1', 'w_sw5')])
add(S6, 'Stop light switch S9 (1993)', 'S9', [('1', 'w_sw6'), ('1', 'w_rl_stop')])
S7 = 'A-C amp + Blower'
add(S7, 'Blower motor B4', 'B4', [('2', 'w_rb4_cp')])
add(S7, 'A/C amplifier A15 (1993 manual A/C) [master: A18 = 1990/92 code]', 'A18', [('11', 'w_ac_kill'), ('13', 'w_ac_psw_sw', 'A5 pressure switch (skipped)')])
S8 = 'Rear lamps'
add(S8, 'LH rear lamp R11 (socket pigtail)', 'R11', [('1', 'w_rl_stop_r11_c1'), ('2', 'w_rl_tail_r11_c2'), ('3', 'w_rl_tail_r11_c3'), ('4', 'w_rl_rev_r11_c4'), ('5', 'w_rl_gnd_r11_c5'), ('6', 'w_rl_turn_l')])
add(S8, 'RH rear lamp R12 (socket pigtail)', 'R12', [('1', 'w_rl_stop_r12_c1'), ('2', 'w_rl_tail_r12_c2'), ('3', 'w_rl_tail_r12_c3'), ('4', 'w_rl_rev_r12_c4'), ('5', 'w_rl_gnd_r12_c5'), ('6', 'w_rl_turn_r')])
add(S8, 'Licence light L1 (socket pigtail)', 'L1', [('1', 'w_rl_tail_l1_c1'), ('2', 'w_rl_gnd_l1_c2')])
add(S8, 'High-mount stop light H6', 'H6', [('A-1', 'w_rl_stop_h6_c1'), ('A-2', 'w_rl_gnd_h6_c2')])
S9 = 'F7 F8 (replace)'
add(S9, 'LH front turn/clearance F7', 'F7', [('1', 'w_clr_f7'), ('2', 'w_f7_gnd'), ('3', 'w_turn_f7')])
add(S9, 'RH front turn/clearance F8', 'F8', [('1', 'w_clr_f8'), ('2', 'w_f8_gnd'), ('3', 'w_turn_f8')])

def first_method(m):
    parts = [p.strip() for p in m.split(' / ')]
    for p in parts:
        if not p.startswith('new-wire run terminated'):
            return p
    return parts[0]

def oem_colour(c):
    return c.split(' / ')[0].replace(' (factory wiring; new wire here)', '').strip()

def other_end(r, oem_id):
    if r['from_id'] == oem_id or r['from_id'].startswith(oem_id):
        return (r['to_id'], r['to_pin'], r['to_name'])
    return (r['from_id'], r['from_pin'], r['from_name'])

PAGE = {'w_ac_kill': '1993 EWD p.223 (manual A/C, A15 pin 11)', 'w_ac_psw_sw': '1993 EWD p.222 (manual A/C, A15 pin 13)', 'w_rb4_cp': '1993 EWD p.223 (manual A/C, B4 pin 2)',
        'w_an2': '1990 EWD p.118 (C14)', 'w_sw2': '1990 EWD p.118 (C14)', 'w_cru_gnd': '1990 EWD p.118 (C14)'}
def oem_page(r):
    return PAGE.get(r['wire_id'], r['oem_ewd_page'].split(' / ')[0])

HEAD = ['Pin', 'OEM wire colour (EWD)', 'New wire AWG', 'New wire colour', 'Signal / what it does', 'Goes to (new harness end)', 'Splice method', 'EWD page', 'wire_id', 'Flag']
table = {}
for (sheet, conn, oem_id, pin, wid, flag) in SP:
    r = rows[wid]
    oe = other_end(r, oem_id)
    desc = r['from_desc'] or r['to_desc']
    table.setdefault(sheet, []).append([conn, pin, oem_colour(r['oem_wire_colour']), r['gauge_awg'], r['colour'], desc,
                                        '%s pin %s %s' % (oe[0], oe[1], ('(' + oe[2] + ')') if oe[2] else '') if oe[1] else oe[0],
                                        first_method(r['oem_method']), oem_page(r), wid, flag])

wb = Workbook()
thin = Side(style='thin', color='BBBBBB')
BORD = Border(left=thin, right=thin, top=thin, bottom=thin)
HFILL = PatternFill('solid', fgColor='1F3864')
SKIP = PatternFill('solid', fgColor='FFE9CC')
WARN = PatternFill('solid', fgColor='FFF2A8')
WRAP = Alignment(wrap_text=True, vertical='top')
WIDTHS = [30, 6, 14, 8, 10, 32, 34, 44, 14, 22, 36]

def put_header(ws, r0, cols):
    for i, h in enumerate(cols):
        c = ws.cell(row=r0, column=i + 1, value=h)
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = HFILL
        c.alignment = Alignment(wrap_text=True, vertical='center')
        c.border = BORD

def put_rows(ws, r0, data):
    for j, row in enumerate(data):
        for i, v in enumerate(row):
            c = ws.cell(row=r0 + j, column=i + 1, value=v)
            c.alignment = WRAP
            c.border = BORD
            if 'VERIFY' in str(row[-1]):
                c.fill = WARN
            elif 'skipped' in str(row[-1]):
                c.fill = SKIP

def add_img(ws, fname, row, maxw=900):
    p = os.path.join(IMG, fname)
    if not os.path.exists(p):
        ws.cell(row=row, column=1, value='(missing image %s)' % fname)
        return row + 2
    w, h = PImg.open(p).size
    sc = min(1.0, maxw / w)
    im = XImg(p)
    im.width, im.height = int(w * sc), int(h * sc)
    ws.add_image(im, 'A%d' % row)
    return row + int(math.ceil(im.height / 20.0)) + 2

# ---------------- README ----------------
ws = wb.active
ws.title = 'READ ME'
ws.column_dimensions['A'].width = 130
lines = [
    ('ST185 OEM splice reference - cabin / dash / cowl / junction-block plugs', 'title'),
    ('Built from MASTER-wirelist.csv (pins, AWG, signals) + the extracted EWD pages in st185-celica-repair-manual. One tab per connector group; each tab has the pin table, then the pictures.', ''),
    ('How to read the pictures: RED circle = a pin you splice into. ORANGE circle = pin used only by a device you told me to skip (headlights, wiper/washer, retract motors). BLUE circle = alternate / cruise item or approximate location.', ''),
    ('Two-letter wire colours are Toyota codes: first letter = base colour, second = stripe (G-B = green with black stripe). B black, W white, R red, G green, L blue, Y yellow, BR brown, O orange, LG light green, P pink, V violet, GR gray.', ''),
    ('AWG and "new wire colour" columns are the NEW harness wire from the master. The EWD does not give the factory wire gauge.', ''),
    ('Only the J/B, R/B and joint plugs (J-B1, IE1, IG2, J-B3/R-B2/R-B4) have real pin-face drawings in the EWD. The part plugs (cluster, cruise stalk, clutch switch, stop switch, blower) are NOT drawn as faces anywhere in the repo - for those the picture is the EWD schematic with the pin circled. Only the A/C amplifier has a face drawing (Mitchell Fig.5, 18 pin).', ''),
    ('J/B and joint-plug drawings are from the 1993 EWD.', ''),
    ('', ''),
    ('YOUR CAR IS A 1993, SO THE 1993 EWD IS THE PRIMARY BOOK. Where the master uses another book\'s code:', 'title'),
    ('Cluster: master "C11" = 1993 plug C13 (B); master "C12" = 1993 plug C14 (C). The pins and colours were read from 1993 p.206-207, so only the label differs.', ''),
    ('Cruise stalk: master "C14" (1990 code) = C16 in the 1993 book. The 1993 EWD in the repo has no cruise page, so pins 5 / 15 / 17 come from the 1990 book; colours match the 1993 Mitchell diagram. Confirm pin numbers on the car.', ''),
    ('A/C amplifier: master "A18" (1990/92 code) = A15 in the 1993 book. Pin 11 (G-Y) and pin 13 (Y-R) both check out on 1993 p.222-223 (manual A/C). Blower B4 pin 2 checks out on p.223.', ''),
    ('Stop light switch S9 and clutch start switch C11 are 1993 codes and match the master.', ''),
    ('', ''),
    ('SKIPPED per your instructions: headlights H1/H2, wiper F9, washer W1, retract motors R2/R3, compressor clutch A4, pressure switch A5, and all Group A engine-bay plugs. Their IE1 / 1H / A18 tap pins are still listed in orange so you can see what shares the plug.', ''),
]
for i, (t, kind) in enumerate(lines, 1):
    c = ws.cell(row=i, column=1, value=t)
    c.alignment = Alignment(wrap_text=True, vertical='top')
    if kind == 'title':
        c.font = Font(bold=True, size=13)

# ---------------- Splice list ----------------
ws = wb.create_sheet('Splice list')
cols = ['Connector'] + HEAD + ['Tab']
put_header(ws, 1, ['Connector'] + HEAD[:-1] + ['Flag', 'Tab'])
r = 2
for (sheet, conn, oem_id, pin, wid, flag) in SP:
    row = [x for x in table[sheet] if x[9] == wid and x[1] == pin and x[0] == conn][0]
    for i, v in enumerate(row + [sheet]):
        c = ws.cell(row=r, column=i + 1, value=v)
        c.alignment = WRAP
        c.border = BORD
        if 'VERIFY' in str(row[-1]):
            c.fill = WARN
        elif 'skipped' in str(row[-1]):
            c.fill = SKIP
    r += 1
for i, w in enumerate(WIDTHS + [20], 1):
    ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = 'C2'
ws.auto_filter.ref = 'A1:%s%d' % (get_column_letter(12), r - 1)

# ---------------- connector tabs ----------------
IMGS = {
    S1: [('loc_relay_blocks.png', 700), ('jb1_1H.png', 1000), ('jb1_1I.png', 800), ('jb1_1F.png', 1000)],
    S2: [('loc_relay_blocks.png', 700), ('ie1.png', 1000)],
    S3: [('loc_relay_blocks.png', 700), ('ig2.png', 1100)],
    S4: [('loc_relay_blocks.png', 700), ('jb3_3B_jb_side.png', 600), ('jb3_3B_cowl_side.png', 600), ('rb2.png', 800), ('rb4.png', 800)],
    S5: [('loc_dash_1993.png', 830), ('sch_cluster_1.png', 1000), ('sch_cluster_2.png', 700)],
    S6: [('loc_dash_1993.png', 830), ('loc_dash_1993_b.png', 840), ('sch_cruise_1990.png', 450), ('sch_start_1993.png', 800), ('sch_stop_1993.png', 560)],
    S7: [('loc_dash_1993.png', 830), ('acamp_face.png', 700), ('sch_ac_223.png', 900), ('sch_ac_222.png', 900)],
    S8: [('loc_rear_lamps.png', 840), ('sch_stop_1993.png', 560)],
    S9: [],
}
NOTES = {
    S1: 'J/B No.1 sits behind the left kick panel (see location picture). Plug 1H mates to the engine-room main wire, 1I to the same, 1F to the floor wire (dark gray). In each picture the LEFT drawing is shown with its label, the other half is the mating half; both halves are circled so you can work from whichever side you can reach.',
    S2: 'IE1 joins the engine-room main wire and the cowl wire at the left kick panel. Both mating halves are shown; the pin numbers match between halves. Check wire colours on the car to tell which half is the cowl side.',
    S3: 'IG2 joins the engine wire and the cowl wire under the engine ECU (see location picture - ECU is at the bottom of the relay-block page).',
    S4: 'J/B3 is behind the combination meter. R/B2 is on the left kick panel, R/B4 (with R/B3) on the right kick panel. The master calls the R/B pins "terminal 1/2/3" of the relay socket. W-L lead on R/B2: the master puts it on pin 2, but pin 2 is the L-Y coil lead - verify on the car (orange circle = 30A fuse pin 2).',
    S5: 'Cluster plugs are labelled A/B/C on the back of the meter. The 1993 book codes them C12 (A), C13 (B), C14 (C); the master calls the B plug C11 and the C plug C12. No pin-face drawing for these exists in the repo - the picture is the EWD schematic with the tapped pins circled.',
    S6: 'No pin-face drawings for these plugs in the repo. The 1993 EWD in the repo has no cruise page, so the stalk pins (5 / 15 / 17, 1993 plug C16) come from the 1990 book (C14). Wire colours W / Y-B / BR match the 1993 Mitchell cruise diagram, but check the pin numbers on the car. Clutch switch C11 and stop switch S9 are straight from the 1993 EWD.',
    S7: 'Only the A/C amplifier has a pin-face drawing (Mitchell Fig.5, 18 pin, pins 11 and 13 circled). Blower motor B4: no plug-face drawing found. Pin 2 = the B (blower +) lead per 1993 EWD p.223. A15 pin 11 (G-Y, from the engine ECU) is on p.223 and pin 13 (Y-R) on p.222 of the 1993 manual-A/C pages, so both master pins check out against the 1993 book.',
    S8: 'Factory bulb sockets are kept (R117): solder flying leads to the socket pigtails. Pin numbers are the lamp-side pins from the EWD.',
    S9: 'F7 / F8: master replaces the plug (new wire run terminated at a new socket). Candidate part 81735-12180 (see Buy list tab) - pin count not confirmed, compare to the old socket.',
}
for sheet in [S1, S2, S3, S4, S5, S6, S7, S8, S9]:
    ws = wb.create_sheet(sheet)
    ws.cell(row=1, column=1, value=sheet).font = Font(bold=True, size=14)
    c = ws.cell(row=2, column=1, value=NOTES[sheet])
    c.alignment = WRAP
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=10)
    ws.row_dimensions[2].height = 75
    put_header(ws, 4, ['Connector'] + HEAD)
    put_rows(ws, 5, table[sheet])
    for i, w in enumerate(WIDTHS, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    rr = 5 + len(table[sheet]) + 2
    for (fn, mw) in IMGS[sheet]:
        rr = add_img(ws, fn, rr, mw)

# ---------------- Buy list ----------------
ws = wb.create_sheet('Buy list')
put_header(ws, 1, ['What', 'Qty', 'Toyota PN', 'Status', 'Cheapest source found', 'URL', 'Note'])
buy = [
    ['F7 / F8 front turn + clearance lamp socket-and-wire', 2, '81735-12180 (candidate)', 'Candidate only - listed for Celica 1986-93 incl. All-Trac; pin count not stated', 'ToyotaPartsDeal $23.79 each ($47.58)',
     'https://www.toyotapartsdeal.com/oem/toyota~socket~and~wire~clearance~lamp~81735-12180.html', 'Compare pin count / colours with the old 3-wire socket before ordering'],
    ['All cabin / dash / cowl / J-B items (J-B1, IE1, IG2, J-B3, R-B2, R-B4, cluster, cruise, clutch, stop, blower, A/C amp, rear lamp sockets)', '-', 'none', 'Splice onto the factory leads - no connector to buy',
     'Butt splices / solder sleeves / ATUM heat-shrink from the project BOM', '', 'Per master oem_method; factory sockets and plugs stay in the car. If you later want unplug-able taps, tell me - then the mating halves of IE1 / IG2 need to be sourced.'],
]
put_rows(ws, 2, buy)
for i, w in enumerate([48, 6, 24, 44, 36, 70, 60], 1):
    ws.column_dimensions[get_column_letter(i)].width = w

out = os.path.join(HERE, 'st185-oem-splice-reference.xlsx')
wb.save(out)
print('saved', out, 'splice rows', len(SP))
