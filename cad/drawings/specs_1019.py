"""2026-10-19 drawing pass: the part drawings the 2026-10-18 pass left (DECISIONS R196: drawings after the model PRs), on top of
specs_1018.py. Models first: #324 (VRC body E), #330 (FB-101 X), #331 (CSB3 lid D, real connector models). Rules as specs_1018:
R191 / R192 / R195 notes (plain machinist steps, no change notes, nothing about what is not in the model), the tolerance block
without the edge-break line. Rev letters: the model letter from <pn>.REVLOG.md; no model change = clerical .NN (REV below).
Claude Code, 2026-10-19."""
import specs_1018
from specs_1017 import PARTS
from specs_1018 import TOL, SPOT, PRINTED

REV = {'ST185-VRC-101': 'F', 'ST185-VRC-102': 'B', 'ST185-VRC-103': 'D.01', 'ST185-DRB-101': 'C.01', 'ST185-CSB3-102': 'E',
       'ST185-FB-101': 'X'}

NOTES = {
 'vrc_body': PRINTED + ["QTY 2 PER CAR, BOTH THE SAME.",
              "O-RING GROOVE (DETAIL B) FOR AN AS568-039 NBR70 FACE SEAL. GROOVE CORNERS R0.13-0.38.",
              "4 CORNER BORES ⌀3.99 x 8 DEEP, ON ⌀10 BOSSES, AXES AT (±42.5, ±22.5), FOR SPIROL 150419 HEAT-SET INSERTS.",
              "2 FLOOR BOSSES: ⌀5.0 DRILL, M6 x 1.0, FOR LEMU 2990806014.",
              "ENGRAVE IN (+X END) AND OUT (-X END): ARIAL BLACK 4.0 HIGH, 0.3 DEEP."],
 'vrc_lid': PRINTED + ["QTY 2 PER CAR.",
             "4 HOLES ⌀3.45, 90° COUNTERSINK TO ⌀7, AXES AT (±42.5, ±22.5), FOR ACCU SSK-M3-12-A2.",
             "THE BOTTOM FACE IS THE O-RING SEALING FACE. THE LID SITS ON THE BODY RIM."],
 'vrc_holder': PRINTED + ["QTY 2 PER CAR. THE BOARD SITS FLUSH IN THE POCKET, HELD BY 4 SNAP TABS.",
                          "2 COUNTERSUNK HOLES FOR M6 x 14 ISO 10642 SCREWS (LEMU 2990806014) INTO THE BODY FLOOR BOSSES."],
 'drb_plate': ["6061-T6 ALUMINUM, 1/2 IN (12.7) PLATE x 205 x 155. THE TOP AS SHOWN IS THE FIREWALL FACE.",
               "FIREWALL FACE GROOVE FOR AN AS568-261 O-RING: 4.75 WIDE x 2.64 DEEP, INSIDE 166.66 x 115.0 R12, OUTSIDE R16.75. "
               "GROOVE Ra 0.8.",
               "ENGINE FACE POCKET 152 x 104 R10 LEAVES A 6.0 WEB UNDER THE CONNECTOR. CUTOUT 121.03 x 71.17 R12.07 ±0.25 WITH THE "
               "R4.32 KEY NOTCH (TE DRBF-1X).",
               "THE 0.5 x 45° CHAMFERS (PERIMETER, POCKET RIM, CUTOUT, FLANGE HOLES) ARE IN THE MODEL: CUT THEM AS SHOWN.",
               "THE 10 M5 HOLES ARE TAPPED RIGHT THROUGH. FIREWALL SCREWS: M5 A2, SHEET (+ WASHER) + 7.5 TO 12.7 LONG, TIP AT OR UNDER "
               "THE ENGINE FACE, THREAD SEALANT ON EACH."],
 'csb3_lid': PRINTED + ["QTY 1 PER CAR.",
     "4 HOLES ⌀3.45, 90° COUNTERSINK TO ⌀7, AXES AT (±32.5, ±32.5), FOR ACCU SSK-M3-12-A2.",
     "THE BOTTOM FACE IS THE O-RING SEALING FACE. THE LID SITS ON THE BODY RIM.",
     "THE HD34-24-33PE CONNECTOR GOES THROUGH THE BIG HOLE. THE FLAT LINES IT UP.",
     "THE FIRST 0.2 OF THE BIG HOLE ABOVE THE ⌀54 SEAT IS FULL ROUND ⌀43.08 (NO FLAT), SO THE CONNECTOR'S ROUND COLLAR SEATS."],
 'fb_power_base': specs_1018.NOTES['fb_power_base'],
}

KEYS = ['vrc_body', 'vrc_lid', 'vrc_holder', 'drb_plate', 'csb3_lid', 'fb_power_base']
for k in KEYS:
    p = PARTS[k]
    p['notes'] = NOTES[k]
    p['tol'] = TOL
    p['rev'] = REV[p['pn']]
    p.pop('revs', None)              # the rev log beside the model is the only rev source (R152)

# the D-hole callouts follow the models: VRC body E (double-D), CSB3 lid D (round relief at the seat)
PARTS['vrc_body']['hole_text'][('X', 18.5)] = "⌀18.5 THRU, BOTH END WALLS\n2 FLATS 16.5 APART (TOP + BOTTOM)\n⌴ ⌀30 ↧3.5 ON INSIDE FACE"
PARTS['csb3_lid']['dims'] = []
PARTS['csb3_lid']['hole_text'] = {('Z', 43.1): "⌀43.08 THRU (HD34-24 CUTOUT)\nFLAT 19.91 FROM CENTER, FROM 0.2 ABOVE THE SEAT\n"
                                                  "⌴ ⌀54 ↧8.0 FROM BOTTOM (SEAT)"}
import os as _os
_C = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
PARTS['drb_plate']['revlog'] = _os.path.join(_C, 'drb102-plate', 'ST185-DRB-101.REVLOG.md')
PARTS['vrc_holder']['revlog'] = _os.path.join(_C, 'enclosures', 'vrc', 'ST185-VRC-103.REVLOG.md')

# D5 a1 (Dan 2026-11-08) plus PA12 MJF (Dan 2026-11-09): the four box parts are printed, not machined.
for _k in ('csb3_body', 'csb3_lid', 'vrc_body', 'vrc_lid'):
    PARTS[_k]['process'] = 'printed'
    PARTS[_k]['material'] = 'PA12 (MJF)'
PARTS['csb3_body']['rev'] = 'D'
PARTS['csb3_body']['notes'] = PRINTED + [
    "QTY 1 PER CAR.",
    "O-RING GROOVE (DETAIL B) FOR AN AS568-039 NBR70 FACE SEAL. GROOVE CORNERS R0.13-0.38.",
    "4 CORNER BORES ⌀3.99 x 8 DEEP, ON ⌀10 BOSSES, AXES AT (±32.5, ±32.5), FOR SPIROL 150419 HEAT-SET INSERTS.",
    "THE BOARD SITS ON 2 CAT. 8847 L10 NYLON SUPPORTS THAT SNAP INTO THE TWO ⌀4.00 HOLES.",
    "EACH FLOOR HOLE TAKES AN ACCU SSF-M8-6-A2 SET SCREW FROM BELOW. THE TIP STOPS AT z 4.0. THIS IS NOT A WATER SEAL.",
]
PARTS['csb3_body']['hole_text'].pop(('Z', 4.0), None)
PARTS['csb3_body']['threads'].pop(2.5, None)

# ---- C-strap set (Dispatch 2026-10-19, after #330 / R199): the new top-nut holder drawing. Number: the next FB number after -117
# (the C-strap itself took -117 rather than the never-used -110, N14 = B), so ST185-FB-118.
PARTS['fb_nut_holder'] = dict(
    job='st185_fusebox_1017', file='src/st185_fusebox_1017/Power_NutHolder_PA12_printed.step', process='printed',
    title='POWER BOX - C-STRAP TOP-NUT HOLDER', pn='ST185-FB-118', material='PA12 (SLS / MJF)',
    source='C:\\projects\\active\\st185-link-ecu-config\\cad\\fusebox\\rev7\\Power_NutHolder_PA12_printed.step',
    max_hole_groups=0, tol=TOL, rev='A', revlog=_os.path.join(_C, 'fusebox', 'rev7', 'ST185-FB-118.REVLOG.md'),
    project=PARTS['fb_power_base']['project'],
    notes=PRINTED + ["QTY 14 PER CAR (ONE IN EVERY C-STRAP, ST185-FB-117).",
                     "PUSH A DIN 934 M5 NUT (RS 527-268) INTO THE HEX POCKET, FLATS LINED UP WITH THE POCKET. "
                     "THEN SLIDE THE HOLDER INTO THE OPEN SIDE OF THE C UNTIL IT SITS ON BOTH LEGS AND THE WEB."])
KEYS.append('fb_nut_holder')
