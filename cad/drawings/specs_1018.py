"""2026-10-18 drawing pass (Dan's sheet-1 markup of all 33 drawings, DECISIONS R184 - R197), on top of specs_1017.py.
What changes here is drawing-only (notes, tolerance block, balloons, label and step sheets); every physical change was made in the
models first (R196 / R197: #322, #324, #325). Rules applied to every sheet:
  R191 no note about anything that is not in the model (edge breaks; the edge-break line leaves the tolerance block too)
  R192 change notes (what was fixed, markup dates, R / PR numbers) live in the rev log, never in NOTES
  R195 notes are for a shop machinist: short plain steps, no engineering reasons
  R184 / R185 no "envelope model" and no pin / socket gender notes
Rev letters: the model letter from <pn>.REVLOG.md; a drawing whose model did not change takes a clerical .NN (REV below).
Claude Code, 2026-10-18."""
import specs_1017
from specs_1017 import PARTS

# the "unless otherwise specified" block without the edge-break line (R191)
TOL = ("DIMENSIONS ARE IN MILLIMETERS\nTOLERANCES:\n  X     ±0.5      X.X  ±0.2\n  X.XX  ±0.05    ANGLES ±0.5°\n"
       "SURFACE FINISH Ra 3.2 µm\nINTERPRET PER ASME Y14.5-2018")
SPOT = "SPOT FACE EVERY TAPPED HOLE ENTRY 90°, AS WIDE AS THE THREAD."
PRINTED = ["PA12, POWDER-BED PRINTED (SLS / MJF). PRINT FROM THE STEP MODEL.",
           "SIZES ON THIS SHEET ARE FOR CHECKING ONLY (OVERALL SIZE). THE 3D MODEL DEFINES EVERY OTHER FEATURE."]
COPPER_CUT = "SAW TO LENGTH, DRILL. DEBURR EVERY HOLE AND EDGE. DO NOT REMOVE THE TIN FROM THE CONTACT FACES."

# drawing rev for each drawing regenerated in this pass (cad/drawing-models.json + the rev logs, 2026-10-18)
REV = {'ST185-CSB3-101': 'C.01', 'ST185-CSB3-102': 'C.01', 'ST185-FB-101': 'W', 'ST185-FB-102': 'H', 'ST185-FB-103': 'G.01',
       'ST185-FB-104': 'E.01', 'ST185-FB-105': 'T', 'ST185-FB-106': 'H.01', 'ST185-FB-107': 'K.01', 'ST185-FB-108': 'J.01',
       'ST185-FB-109': 'G.01', 'ST185-FB-111': 'C.01', 'ST185-FB-112': 'C.01', 'ST185-FB-113': 'C.01', 'ST185-FB-114': 'B.01',
       'ST185-FB-115': 'E.01', 'ST185-FB-116': 'E.01', 'ST185-FH-101': 'G.01', 'ST185-FH-103': 'F.01', 'ST185-FH-104': 'E.01',
       'ST185-FH-105': 'D.01', 'ST185-FH-100': 'K.01', 'ST185-FB-100L': 'V', 'ST185-FB-100B': 'N.01'}

NOTES = {
 'csb3_body': ["6061-T6 ALUMINUM. STOCK 75 x 100 x 53 BILLET. QTY 1 PER CAR.",
               "O-RING GROOVE (DETAIL B) FOR AN AS568-039 NBR70 FACE SEAL. GROOVE FLOOR, GROOVE WALLS AND THE LID FACE: Ra 0.8. "
               "GROOVE CORNERS R0.13-0.38.",
               "THE BOARD SITS ON 2 CAT. 8847 L10 NYLON SUPPORTS THAT SNAP INTO THE TWO ⌀4.00 HOLES.",
               "SEAL EACH ⌀4.00 HOLE FROM BELOW: AN M8 x 1.25 x 6 ISO 4026 SET SCREW WITH THREAD SEALANT. THE SCREW TIP STOPS AT z 4.0 "
               "(THE SCREW STANDS 2.0 PROUD OF THE BOTTOM FACE).",
               "CUT THE M8 THREADS FROM BELOW WITH A THREAD MILL OR A BOTTOMING TAP. A THROUGH TAP WILL NOT PASS THE ⌀6.5 RELIEF.",
               "TAB CORNERS AT x ±30 ARE R1.9: USE A CUTTER OF R1.5 OR SMALLER.", SPOT],
 'csb3_lid': ["6061-T6 ALUMINUM. STOCK 8 x 75 x 75 PLATE; FACE BOTH SIDES TO 6.0. QTY 1 PER CAR.",
              "THE BOTTOM FACE IS THE O-RING SEALING FACE: Ra 0.8, FLAT WITHIN 0.05, NO TOOL MARKS ACROSS THE SEAL PATH.",
              "THE HD34-24-33PE CONNECTOR GOES THROUGH THE BIG HOLE; THE FLAT LINES IT UP. HOLD IT WITH PANEL NUT 112263-90 AND "
              "LOCKWASHER 112264-ZZ."],
 'fb_power_base': PRINTED + [
     "THE 14 WELLS HOLD THE COPPER C-STRAPS (ST185-FB-117): EACH STRAP'S LIPS REST ON THE LEDGE AND A SNAP HOOK CLIPS OVER THEM."],
 'fb_strip1': ["C110 COPPER, TINNED. CUT FROM 1\" x 1/8\" (25.4 x 3.2) TINNED FLAT BAR (MECCANIXITY B0CGJC2S1L). ONE 305 BAR MAKES "
               "BUS1 AND BUS2.",
               "THE HOLES TAKE PRESS-IN PEM NUTS - DO NOT TAP THEM. ⌀5.41 +0.08/-0 FOR A PEM S-M4-2ZI AT EACH M4 STUD; ⌀6.35 +0.08/-0 "
               "FOR A PEM SS-M5-2ZI AT THE M5 FEED. PRESS EACH NUT IN FROM THE STRIP FACE.",
               "THE 0.3 x 45° CHAMFERS ON THE HOLE RIMS ARE IN THE MODEL: CUT THEM AS SHOWN.",
               "THE STRIP STANDS ON ITS EDGE IN THE LOGIC BASE. " + COPPER_CUT],
 'fh101': ["6061-T6 ALUMINUM BILLET. FLANGE AND LUG ARE ONE PIECE.",
           "13 THROUGH HOLES ONLY: NOTHING ELSE CUTS INTO THE SEALING FACE.",
           "SPOT FACES: Ra 1.6, FLAT. THE INSIDE CORNER WHERE THE LUG MEETS THE FLANGE IS R3.",
           "MACHINE IN 3 SETUPS: TANK FACE, OUTSIDE FACE, THEN THE SIDE (THE ⌀6.6 HOLE)."],
 'fh103': ["6061-T6 ALUMINUM BILLET. " + SPOT,
           "EVERY EDGE HAS A 0.5 x 45° CHAMFER (IN THE MODEL). POCKET FLOOR CORNERS CAN STAY AS THE END MILL LEAVES THEM.",
           "THE SIDE FACE AT THE SADDLE LOCATES THE FH-105 TAB: 22.22 / 28.72 FROM THE 2 M4 COUNTERSINK CENTRES, +0 / -0.05.",
           "FIT THE TANK BULKHEAD NUTS BEFORE THE STRUT GOES ON."],
 'fh104': ["6061-T6 ALUMINUM BILLET. " + SPOT,
           "THE FRONT VIEW SHOWS THE BACK FACE (IT SITS ON THE STRUT): 2 M4 TAPPED HOLES, 10 DEEP, FOR ISO 4762 M4 x 14 SCREWS.",
           "THE KEY TONGUE FITS THE SLOT IN THE STRUT FOOT."],
 'fh105': ["6061-T6 ALUMINUM BILLET. " + SPOT,
           "THE BAND CHANNEL (13.2 WIDE x 1.0 DEEP) TAKES A 12.7 (1/2 IN) WORM-DRIVE BAND.",
           "2 M4 TAPPED HOLES, 8 DEEP MAX. SCREWS: ISO 10642 M4 x 12 AT 2 N·m WITH LOCTITE 243.",
           "THE TAB LOCATING FACE IS 22.22 / 28.72 FROM THE TAPPED HOLES, +0.05 / 0, SO IT SLIDES ON FH-103 WITH 0-0.10 PLAY. "
           "PUSH THE SADDLE TOWARD THE STRUT, THEN TIGHTEN.",
           "TAB ROOT R0.5 MAX. LIP ENDS R2 MAX. DEBURR 0.2 MAX."],
}
NOTES['fb_strip2'] = NOTES['fb_strip1']
for k in ('fb_power_pan', 'fb_power_cover', 'fb_retainer', 'fb_logic_base', 'fb_logic_pan', 'fb_logic_cover', 'fb_br_base', 'fb_br_cover'):
    NOTES[k] = list(PRINTED)
for k in ('fb_bar_br', 'fb_pad', 'fb_barneg', 'fb_barpos'):
    NOTES[k] = [PARTS[k]['notes'][0].replace('MATERIAL: ', ''), COPPER_CUT]

KEYS = ['csb3_body', 'csb3_lid', 'fb_power_base', 'fb_power_pan', 'fb_power_cover', 'fb_retainer', 'fb_logic_base', 'fb_logic_pan',
        'fb_logic_cover', 'fb_br_base', 'fb_br_cover', 'fb_bar_br', 'fb_pad', 'fb_barneg', 'fb_barpos', 'fb_strip1', 'fb_strip2',
        'fh101', 'fh103', 'fh104', 'fh105']
for k in KEYS:
    p = PARTS[k]
    p['notes'] = NOTES[k]
    p['tol'] = TOL
    p['rev'] = REV[p['pn']]
    p.pop('revs', None)              # the rev log beside the model is the only rev source (R152)
    if k.startswith('fh') and '(build123d)' not in p['source']:
        p['source'] += ' (build123d)'
import os as _os
_CSB3 = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'enclosures', 'csb3')
for _k in ('csb3_body', 'csb3_lid'):
    PARTS[_k]['revlog'] = _os.path.join(_CSB3, PARTS[_k]['pn'] + '.REVLOG.md')
