"""2026-10-17 drawing set on st185-link-ecu-config main 4744454 (PR #274 CSB3 lock-in, #275 sweep fixes, #276 harness).
Patches specs.PARTS for the current geometry and adds the fuel hanger FH-101..105 from cad/fuel-hanger (build123d; was fairsolid rev 8).
Rules (Dan): STEP only; edge breaks modelled where the CAD does it cleanly, else a drawing note (R138); tapped holes = tap drill + thread
from the model; one of several identical features dimensioned with (xN); no repeated dims."""
import copy, specs
from specs import PARTS, GEN_M, SRC, GROOVE_NOTE
TODAY='2026-10-17'
J='st185_1017'
def src(job,f): return f'src/{job}/{f}'
NOTE_BREAK_BILLET="EDGE BREAKS ARE NOT MODELLED ON THIS PART (R138): BREAK ALL SHARP EDGES 0.2-0.4 UNLESS NOTED; DO NOT BREAK O-RING GROOVE EDGES OR SEALING FACE."
# ---------------- CSB3 body (Fusion v4, R133) ----------------
b=PARTS['csb3_body']; b.update(job='st185_csb3_1017',file=src('st185_csb3_1017','CSB3_part_CSB3-Body.step'),rev='C',
  revs=[('B','REV B ISSUE (SteveCAD audit v3)','2026-10-15','SC'),('C','R133 LOCK-IN SUPPORTS + M8 SEAL HOLES (#274)',TODAY,'SC')])
b['threads']={2.5:('M3x0.5',0.5),6.8:('M8x1.25',1.25)}
b['thread_depth']={6.8:4.32}
b.pop('boss_note',None)
b['hole_text']={('Z',4.0):"⌀4.00 THRU 1.57 BOSS TOP (CAT. 8847 SNAP-IN)\nFROM BOTTOM: ⌀6.8 ↧4.32, M8x1.25-6H ↧4.32\nTHREAD MILL OR BOTTOMING TAP FROM BELOW\n⌀6.5 RELIEF TO z 6.43 (PLATE UNDERSIDE)\nON ⌀10 BOSS, 3.0 HIGH"}
b['notes']=["6061-T6. STOCK 75 x 100 x 53 BILLET. QTY 1 PER CAR.", GROOVE_NOTE,
  "BOARD ON 2X CAT. 8847 L10 NYLON LOCK-IN SUPPORTS IN THE ⌀4.00 HOLES; BOARD UNDERSIDE z 18.0 (R133).",
  "SEAL: 2X M8x1.25x6 ISO 4026 SET SCREW + THREAD SEALANT, TIP z 4.0 MAX, 2.0 PROUD. SEAL ONLY - 1.5xD RULE N/A (R133).",
  "M8: THREAD MILL OR BOTTOMING TAP FROM BELOW (THROUGH TAP CANNOT PASS ⌀6.5 RELIEF).",
  "TAB CORNERS R1.9 AT x ±30: CUTTER r <= 1.5 (F11).",
  "EDGE BREAKS NOT MODELLED (R138): BREAK SHARP EDGES 0.2-0.4 EXCEPT O-RING GROOVE / SEAL FACE. SPOT TAPPED ENTRIES 90°."]
_unused=[
  "BOARD ON 2X CAT. 8847 L = 10.0 METRIC NYLON LOCK-IN SUPPORTS (R133): CHASSIS END SNAPS INTO THE ⌀4.00 HOLE THROUGH THE 1.57 BOSS TOP; BOARD UNDERSIDE AT z 18.0.",
  "SEAL EACH FLOOR HOLE WITH AN M8x1.25x6 ISO 4026 / DIN 913 SET SCREW (A2 PREFERRED) + THREAD SEALANT; TIP AT z 4.0 (NEVER PAST 4.32), 2.0 PROUD OF BOTTOM FACE. SEAL ONLY - THE 1.5xD THREAD RULE DOES NOT APPLY (R133).",
  "M8 THREAD: THREAD MILL OR BOTTOMING TAP FROM BELOW - A THROUGH TAP CANNOT PASS THE ⌀6.5 RELIEF.",
  NOTE_BREAK_BILLET, GEN_M[1]]
PARTS['csb3_lid'].update(job='st185_csb3_1017',file=src('st185_csb3_1017','CSB3_part_CSB3-Lid.step'),rev='C',
  revs=[('C','REISSUE WITH BODY REV C (LID UNCHANGED)',TODAY,'SC')])
# ---------------- VRC board holder (printed, no drawing yet) ----------------
h=PARTS['vrc_holder']; h.update(job='st185_vrc_1017',file=src('st185_vrc_1017','ST185_VRC_board_holder_PA12.step'),rev='A')
h['notes']=[n.replace('M6 x 12','M6 x 14 (LEMU 2990806014, 9.0 THREAD = 1.5xD)') for n in h['notes']]
# ---------------- VRC body + lid (Fusion ST185-VRC-Enclosure after #273; first engine drawings 2026-10-17, R150-R152) ----------------
# Geometry measured from the STEP 2026-10-17: bosses D11 z 5.0-12.5, drill D5.0 from z 1.0 (11.5 deep, 1.0 floor left); lid M3 tap drill
# D2.53 x 9.5; tab slots 6.6 wide, arc centres 10 apart; groove 2.646 x 1.32. Lid: 90 x 50 x 6, 4 x D3.4.
import os as _os0
_VRCDIR=_os0.path.join(_os0.path.dirname(_os0.path.dirname(_os0.path.abspath(__file__))),'enclosures','vrc')
vb=PARTS['vrc_body']; vb.update(job='st185_vrc_1017',file=src('st185_vrc_1017','VRC_part_VRC-Body.step'),revlog=_os0.path.join(_VRCDIR,'ST185-VRC-101.REVLOG.md'))
vb['thread_depth']={2.5:8.0,5.0:10.0}
vb['hole_text']={('Z',5.0):"2X ⌀5.0 ↧11.5 (1.0 FLOOR LEFT, NOT THRU)\nM6x1.0-6H ↧10.0, TAP AT FIT\nON 2X ⌀11 BOSS, 7.5 HIGH (TOP z 12.5)",
                 ('X',18.5):"⌀18.5 THRU, BOTH END WALLS\nD-FLAT 16.5 ACROSS (FLAT AT TOP)\n⌴ ⌀30 ↧3.5 ON INSIDE FACE (SEE NOTE 3)"}
vb['notes']=["6061-T6. STOCK 95 x 80 x 42 BILLET. QTY 2 PER CAR (FRONT + REAR), IDENTICAL.",
  "O-RING GROOVE (DETAIL B): AS568-039 NBR70 FACE SEAL. GROOVE + LID FACE Ra 0.8, GROOVE CORNER R0.13-0.38.",
  "⌀30 x 3.5 SPOTFACE INSIDE EACH END WALL: BACK-COUNTERBORE THROUGH THE D-HOLE OR A 2ND SETUP.",
  "BOSSES: M6 x 14 ISO 10642 ENGAGES 9.0 (1.5xD, R131). TAB CORNERS R3; FLOOR CORNERS SQUARE OK.",
  "ENGRAVE IN (+X) / OUT (-X): ARIAL BLACK 4.0 HIGH, 0.3 DEEP, UPRIGHT FROM OUTSIDE.",
  "EDGE BREAKS NOT MODELLED (R138): BREAK SHARP EDGES 0.2-0.4 EXCEPT GROOVE / SEAL FACE. SPOT TAPPED ENTRIES 90°."]
vl=PARTS['vrc_lid']; vl.update(job='st185_vrc_1017',file=src('st185_vrc_1017','VRC_part_VRC-Lid.step'),revlog=_os0.path.join(_VRCDIR,'ST185-VRC-102.REVLOG.md'),hidden=False)
vl.pop('hidden_views',None)
vl['hole_text']={('Z',3.4):"4X ⌀3.4 THRU\n⌵ ⌀6.9 X 90° (ISO 10642 M3)"}
vl['notes']=["MATERIAL: 6061-T6 ALUMINUM. STOCK: 8 x 95 x 55 PLATE (FACE BOTH SIDES TO 6.0). QTY 2 PER CAR.",
  "BOTTOM FACE IS THE O-RING SEALING FACE (AS568-039 IN THE BODY RIM, ST185-VRC-101): Ra 0.8, FLAT WITHIN 0.05, NO TOOL MARKS ACROSS THE SEAL PATH. LID CLOSES METAL-TO-METAL ON THE RIM.",
  "EDGE BREAKS NOT MODELLED (R138): BREAK SHARP EDGES 0.2-0.4 EXCEPT THE SEALING FACE."]
# ---------------- DRB102 plate (CadQuery, #275: M5 tapped through, chamfers kept) ----------------
d=PARTS['drb_plate']; d.update(job='st185_drb102_1017',file=src('st185_drb102_1017','DRB102-firewall-plate.step'),rev='C',
  revs=[('B','REV B ISSUE','2026-10-15','SC'),('C','M5 TAPPED THRU (#275), GROOVE 4.75',TODAY,'SC')])
d['threads']={4.2:('M5x0.8',0.8)}; d.pop('thread_depth',None)
d['skip_radii']=[16.75,12.0]
d['details'][0]['dims']=[('lin',(-88.08,0,12.7),(-83.33,0,12.7),'h',6,'4.75'),('lin',(-83.33,0,10.06),(-83.33,0,12.7),'v',8,'2.64'),
           ('lin',(-72,0,6.7),(-72,0,12.7),'v',16,'6.0 WEB'),('lin',(-76,0,0),(-76,0,6.7),'v',-14,'6.7')]
_x=("FIREWALL FACE GROOVE FOR AS568-261 O-RING (PARKER FACE GLAND, 0.139 CORD): 4.75 WIDE x 2.64 DEEP, INNER 166.70 x 115.0 R12, OUTER R16.75 (1.0 % STRETCH, OPEN-10). GROOVE Ra 0.8.")
d['notes']=["6061-T6, 1/2\" (12.7) PLATE x 205 x 155. TOP (AS SHOWN) = FIREWALL FACE.",
  "FIREWALL FACE GROOVE FOR AS568-261 (PARKER FACE GLAND): 4.75 x 2.64 DEEP, INNER 166.66 x 115.0 R12, OUTER R16.75 (OPEN-10). Ra 0.8.",
  "ENGINE FACE POCKET 152 x 104 R10, 6.0 WEB UNDER CONNECTOR. CUTOUT 121.03 x 71.17 R12.07 ±0.25 PER TE DRBF-1X, KEYWAY R4.32.",
  "0.5 x 45° CHAMFERS (PERIMETER, POCKET RIM, CUTOUT, TE HOLES) ARE MODELLED (R138) - MACHINE PER MODEL.",
  "10X M5 A2 FIREWALL SCREWS: LENGTH = SHEET (+ WASHER) + 7.5..12.7 THREAD, TIP AT/UNDER ENGINE FACE. THREAD SEALANT ON EACH."]
_unused2=["0.5 X 45° CHAMFERS ON PLATE PERIMETER, POCKET RIM, CUTOUT AND TE HOLES ARE MODELLED (R138: MODELLED WHERE THE CAD DOES IT CLEANLY) - MACHINE PER MODEL.",
             "10X M5 FIREWALL SCREWS, A2: TAPPED THRU THE 12.7 PLATE; LENGTH = FIREWALL SHEET (+ WASHER) + 7.5 TO 12.7 OF THREAD (>= 1.5xD), TIP AT OR UNDER THE ENGINE FACE (e.g. M5 x 12 ON A 1 mm SHEET). THREAD SEALANT ON EACH SCREW - HOLES ARE OUTSIDE THE O-RING AND NO LONGER BLIND."]
# ---------------- fuse box rev 7 (Fusion, re-exported 2026-10-17 00:42 with #275) ----------------
for k,s in PARTS.items():
    if s.get('job')=='st185_fusebox_1015':
        s['job']='st185_fusebox_1017'; s['file']=s['file'].replace('st185_fusebox_1015','st185_fusebox_1017'); s['rev']='A'
PARTS['fb_retainer']['file']=src('st185_fusebox_1017','Power_Retainer_R1_PA12_printed.step')
for k in ('fb_strip1','fb_strip2'):
    s=PARTS[k]; s['threads']={}
    s['notes']=[s['notes'][0],
      "HOLES ARE PEM MOUNTING HOLES, NEVER TAPPED (R129): ⌀5.41 +0.08/-0 FOR PEM S-M4-2ZI AT EACH M4 STUD, ⌀6.35 +0.08/-0 FOR PEM SS-M5-2ZI AT THE M5 FEED. PRESS NUTS IN FROM THE STRIP FACE.",
      "0.3 x 45° EDGE BREAK IS MODELLED (THE ⌀6.01 / ⌀6.95 RIMS) - R138 / R76.","MOUNTS ON EDGE IN THE LOGIC BASE. DEBURR ALL HOLES AND EDGES."]
PARTS['fb_power_base']['notes']=PARTS['fb_power_base']['notes']+[
  "VERIFIED 2026-10-17: R145 SLITS FILLED (NO GAP < 0.5, S6).",
  "OUTPUTS (R155, N14 = B): 14 WELLS FOR THE COPPER C-STRAPS (ST185-FB-117); THE LIPS REST ON THE LEDGE (DOWN STOP), A SNAP HOOK REACHES OVER "
  "THE LIPS (UP STOP) - OUT ROW: THE FREED SKIRT, IN ROW: AN ARM CUT FREE IN THE DECK. NO STANDOFFS, CRUSH RIBS OR ADHESIVE (R146 SUPERSEDED)."]
# N14 = B (R155): the POWER outputs are copper C-straps (ST185-FB-117, run_fb117.py); the output pad drawing is the battery block pad only
_p=PARTS['fb_pad']
_p['file']=src('st185_fusebox_1017','BattRelay_Pad_Out_CuC110_15x3.step')
_p['source']=_p['source'].replace('Power_Pad_Out_CuC110_15x3','BattRelay_Pad_Out_CuC110_15x3')
_p['title']='OUTPUT PAD 15 x 3 x 17.5 (BATTERY RELAY BLOCK)'
_p['notes']=[n.replace('QTY 15 (14 POWER + 1 BATTRELAY).','QTY 1 (BATTERY RELAY BLOCK; THE POWER BOX OUTPUTS ARE THE C-STRAPS ST185-FB-117 SINCE R155).') for n in _p['notes']]
# Dan's markup 2026-10-17 (23-06): the battery block pad grows to the bar width - 25.4 x 3.2 x 15.5 from the 1" x 1/8" strip stock (the spare
# second bar of the LOGIC strip pair), two printed snap tabs hold it (R157); the drawings that change with the markup: run_markup_1017.py
_p['file']=src('st185_fusebox_1017','BattRelay_Pad_Out_CuC110_25p4x3p2.step')
_p['source']=_p['source'].replace('BattRelay_Pad_Out_CuC110_15x3','BattRelay_Pad_Out_CuC110_25p4x3p2')
_p['title']='BATTERY BLOCK PAD 25.4 x 3.2 x 15.5'
_p['notes']=["MATERIAL: C110 COPPER, TINNED. CUT FROM 1\" x 1/8\" (25.4 x 3.2) TINNED FLAT BAR (MECCANIXITY B0CGJC2S1L, THE SPARE BAR OF THE LOGIC STRIP PAIR). QTY 1.",
             "SAW CUT, DRILL; DEBURR ALL HOLES AND EDGES. DO NOT REMOVE TIN ON CONTACT FACES."]
PARTS['fb_power_base']['notes']=PARTS['fb_power_base']['notes']+[
  "MARKUP 2026-10-17 (R157 - R160): EVERY HOLD-DOWN HOOK BEARS ON THE COPPER (0 GAP); LUG POCKETS (WALLS + RAISED FLOOR) WHERE EVERY BUS LUG LEAVES "
  "THE COPPER; RIBS BETWEEN THE STRAP STATIONS UNDER THE DECK; NEG FRONT WALL; ROOT FILLETS ON THE STANDING WALLS; 7 COVER CATCHES."]
for _k in ('fb_strip1','fb_strip2'):
    PARTS[_k]['notes']=PARTS[_k]['notes']+["MARKUP 2026-10-17: SPARE STUD POSITIONS DELETED; STUDS ON A 9.35 PITCH (BUS1 10, BUS2 9)."]
# ---------------- fuel hanger (build123d, cad/fuel-hanger; option B holder approved B9, Dan 2026-10-17) ----------------
# Replaces the fairsolid rev 8 entries (Dan rejected rev 8). Models: fuel_hanger.py (FH-101 flange) and build_holder.py
# (FH-103 strut, FH-104 foot, FH-105 saddle, assembly). Rev log rows come from cad/fuel-hanger/<PN>.REVLOG.md (R152).
import os as _os, math as _m
_FHDIR=_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),'fuel-hanger')
HJ='st185_fuelhanger_1017'
HS='st185-link-ecu-config\\cad\\fuel-hanger\\'
HN="6061-T6 BILLET. MADE-WITH: build123d (cad/fuel-hanger/%s). REV = RELEASE COUNT (cad/DRAWING-REVS.md). SPOT TAPPED ENTRIES 90°."
PUMP="PUMP MASS 0.6 kg ASSUMED (WALBRO F90000295, 2 G HAND CHECK)."
def HP(key,f,pn,title,threads,notes,src_py='build_holder.py',**kw):
    PARTS[key]=dict(job=HJ,file=src(HJ,f),process='machined',title=title,pn=pn,material='6061-T6 ALUMINUM',source=HS+f,
                    hidden=False,threads=threads,revlog=_os.path.join(_FHDIR,pn+'.REVLOG.md'),dxf=True,
                    notes=[HN%src_py]+notes,**kw)
HP('fh101','fuel-hanger-flange.step','ST185-FH-101','FUEL HANGER - FLANGE (INTEGRAL LUG)',{},
   ["ONE BILLET: FLANGE + LUG (REPLACES FH-101 REV F + FH-102 REV A). NO M5 SCREWS, NO DOWELS. 13 THRU-HOLES ONLY; NOTHING ELSE BREAKS THE SEALING FACE.",
    "SPOT FACES Ra 1.6 FLAT. UPRIGHT-TO-BASE R3. OPS: TANK FACE, OUTSIDE FACE, SIDE (⌀6.6).",
    "EDGES NOT MODELLED (R138): BREAK SHARP EDGES 0.2-0.4; SEAL FACE / SPOT RIMS 0.3 MAX."],
   src_py='fuel_hanger.py', rev='G.01',
   hole_text={("Z", 5.8): "2X ⌀5.79 THRU (STUD)\n⌴⌀16 ↧0.4 BOTH SIDES",
              ("Z", 14.7): "⌀14.68 THRU (-6 AN)\n⌴⌀24 ↧0.4 BOTH SIDES",
              ("Z", 19.4): "⌀19.45 THRU (-8 AN)\n⌴⌀30 ↧0.4 BOTH SIDES",
              ("Z", 5.5): "9X ⌀5.5 THRU\n⌴⌀12 ↧2.8 OUTSIDE (RIM 5.0)"})
HP('fh103','fuel-hanger-strut.step','ST185-FH-103','FUEL HANGER - STRUT',{4.2:('M5x0.8',0.8)},
   ["ALL EDGES 0.5 x 45° CHAMFER, UNIFORM (MODELLED). POCKET FLOOR CORNERS: END-MILL OK.",
    "+u SIDE FACE AT THE SADDLE (FH-105 TAB LOCATING FACE): 22.22 / 28.72 FROM THE 2X M4 CSK CENTRES 0/-0.05.",
    "REV F: SADDLE KEY SLOT REMOVED, FOOT KEY SLOT KEPT. FIT THE BULKHEAD NUTS BEFORE THE STRUT.", PUMP],
   # the engine reads only one cone per hole (the 0.5 chamfer), so the 2 saddle countersinks are called out by hand
   hole_text={(_a,4.5):"4X ⌀4.5 THRU, ⌵⌀5.5 X 90° (0.5 CHAMFER)\n2X AT THE SADDLE (171.2 / 181.2): ⌵⌀8.4 X 90°\nBACK FACE, ISO 10642 M4 FLUSH" for _a in ('X','Y','Z')})
_N=None
try:
    import sys as _sys; _sys.path.insert(0,_FHDIR); import fuel_hanger as _fh; _N=_fh.N
except Exception as _e: print('fuel_hanger import for the foot view failed:',_e)
_FOOT_ROT=[('Z',90.0-_m.degrees(_m.atan2(_N[1],_N[0])))] if _N else None   # back face (strut side, 2X M4 taps) toward the FRONT view
HP('fh104','fuel-hanger-foot.step','ST185-FH-104','FUEL HANGER - FOOT',{3.3:('M4x0.7',0.7)},
   ["FRONT VIEW = BACK FACE ON THE STRUT: 2X M4 TAP 10 FOR ISO 4762 M4 x 14; KEY TONGUE SITS IN THE STRUT FOOT SLOT.",
    "R0.8 TOP-EDGE FILLETS MODELLED; 3 SKIPPED ON THE STRUT SIDE OF THE FLOOR TOP: BREAK THOSE 0.3-0.5. OTHER EDGES 0.2-0.4.", PUMP],
   **({'rotate':_FOOT_ROT} if _FOOT_ROT else {}))
HP('fh105','fuel-hanger-saddle.step','ST185-FH-105','FUEL HANGER - PUMP SADDLE',{3.3:('M4x0.7',0.7)},
   ["BAND CHANNEL 13.2 x 1.0 DEEP FITS A 12.7 (1/2 IN) WORM-DRIVE BAND.",
    "2X M4 TAP 8 MAX DEPTH. ISO 10642 M4 x 12: 2 N·m + LOCTITE 243.",
    "TAB LOCATING FACE 22.22 / 28.72 FROM THE TAPPED HOLES +0.05/0: SLIP FIT 0-0.10 ON FH-103. PUSH SADDLE TOWARD STRUT, THEN TORQUE.",
    "TAB ROOT R0.5 MAX. LIP ENDS R2 MAX. DEBURR 0.2 MAX.", PUMP])
FH_ORDER=['fh101','fh103','fh104','fh105']
ORDER=['csb3_body','csb3_lid','vrc_body','vrc_lid','vrc_holder','drb_plate','fb_power_base','fb_power_pan','fb_power_cover','fb_retainer','fb_logic_base','fb_logic_pan',
       'fb_logic_cover','fb_br_base','fb_br_cover','fb_bar_br','fb_pad','fb_barneg','fb_barpos','fb_strip1','fb_strip2']
# Fuel hanger rev 8 dropped 2026-10-17 (Dan rejected it); the fuel hanger sheets are FH_ORDER above, from cad/fuel-hanger.
# ---------------- Rev letters (Dan 2026-10-17): the MODEL drives the rev letter; drawing = model letter.
# Letters A B C D E F G H J K M N P R S T ... (skip I, L, O, Q). Rev A only for brand-new models. Existing models:
# letter = count of the model's past releases in the repo history (first release = A); rev numbers are not converted.
# Clerical drawing-only revs add .01, .02 (reset on a letter bump). Register: st185 cad/DRAWING-REVS.md.
# No rev in any st185 filename (Dan 2026-10-17): PDFs / PNGs are plain <PN>.pdf / <PN>_sh1.png.
REV_LETTER={'csb3_body':('C','FIRST ISSUE. MODEL REV C (PR #274)'),
            'csb3_lid':('C','FIRST ISSUE. MODEL REV C (PR #273)'),
            'vrc_holder':('D','FIRST ISSUE. MODEL REV D (PR #273)'),
            'vrc_body':('D','FIRST ENGINE DRAWING. MODEL REV D (PR #273)'),
            'vrc_lid':('A','FIRST ENGINE DRAWING. MODEL REV A (PR #139)'),
            'drb_plate':('C','FIRST ISSUE. MODEL REV C (PR #275)')}
# Fuse box rev 7 parts (Dan 2026-10-17: count each model's past releases in the repo history; rev 7 is NOT converted to G):
# releases = PRs where the part's size / volume (printed) or mass (copper) in fusebox_report.json changed, + #273 NEG bar holes, #275 LOGIC corner.
FB_REL={'fb_power_base':18,'fb_power_pan':7,'fb_power_cover':7,'fb_retainer':5,'fb_logic_base':15,'fb_logic_pan':8,'fb_logic_cover':10,
        'fb_br_base':9,'fb_br_cover':7,'fb_bar_br':3,'fb_pad':3,'fb_barneg':3,'fb_barpos':2,'fb_strip1':5,'fb_strip2':5}   # + Dan's markup 2026-10-17; + fit audit / N21 2026-10-18
SEQ='ABCDEFGHJKMNPRSTUVWXYZ'
for _k,_n in FB_REL.items(): REV_LETTER[_k]=(SEQ[_n-1],'FIRST ISSUE. MODEL REV %s (%d RELEASES)'%(SEQ[_n-1],_n))
# REV_LETTER['fb_pad'] was ('B.01', clerical, N14 = B); Dan's markup 2026-10-17 changed the pad model (25.4 x 3.2): rev C from the release count
for _k in ORDER:
    _l,_d=REV_LETTER[_k]
    PARTS[_k]['rev']=_l; PARTS[_k]['revs']=[(_l,_d,TODAY,'SC')]
# N14 = B (R155, 2026-10-17): the fuse box drawings read the full rev history from <part no>.REVLOG.md beside the model in cad/fusebox/rev7
_REV7=_os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),'..','fusebox','rev7'))
for _k in ORDER:
    if _k.startswith('fb_') and _os.path.exists(_os.path.join(_REV7,PARTS[_k]['pn']+'.REVLOG.md')):
        PARTS[_k]['revlog']=_os.path.join(_REV7,PARTS[_k]['pn']+'.REVLOG.md')

# CSB3 body tab slots: the model has 6.6 x 10.0 since SteveCAD audit v3 F01 (#272), measured from the STEP 2026-10-17; specs.py still said 5.5 x 9.9
def _fix_slot(o):
    if isinstance(o,dict): return {k:_fix_slot(v) for k,v in o.items()}
    if isinstance(o,list): return [_fix_slot(v) for v in o]
    if isinstance(o,tuple): return tuple(_fix_slot(v) for v in o)
    if o=="4X SLOT 5.5 X 9.9 THRU": return "4X SLOT 6.6 X 10.0 THRU"
    return o
PARTS['csb3_body']=_fix_slot(PARTS['csb3_body'])
PARTS['vrc_body']=_fix_slot(PARTS['vrc_body'])   # VRC slots are 6.6 x 10 too (F01, #272)
# CSB3 section through the (+13.5, +13.5) boss so the 4.0 / 6.5 / M8 stack shows
PARTS['csb3_body']['section']=dict(slot='front',origin=(0,13.5,0),label='A-A')

# Title block (the handbuilt-cad engine defaults to a neutral "PROJECT" / "-"; st185 sets its own)
PROJECT_NAME='ST185 CELICA GT-FOUR  -  LINK ECU CONVERSION'; DRAWN_BY='SteveCAD'
for _v in list(globals().values()):
    if isinstance(_v,dict) and _v and all(isinstance(x,dict) and 'pn' in x for x in _v.values()):
        for _p in _v.values(): _p.setdefault('project',PROJECT_NAME); _p.setdefault('drawn',DRAWN_BY)
