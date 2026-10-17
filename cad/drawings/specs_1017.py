"""2026-10-17 drawing set on st185-link-ecu-config main 4744454 (PR #274 CSB3 lock-in, #275 sweep fixes, #276 harness).
Patches specs.PARTS for the current geometry and adds the fuel hanger rev 8 (build123d, Fairsolid run folder, never in the repo).
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
  "STANDOFF RETENTION (R146, #277): 6 CRUSH RIBS IN THE 8.5 AF BORE, CORNERS RELIEVED ⌀1.2, + LOCTITE 406 WICKED IN FROM BELOW. R144 COLLARS REMOVED.",
  "OPEN ITEM (OPEN-ITEMS 124): M5 x 10 LUG BOLT TORQUE INTO THE BRASS STANDOFF - TBD."]
# ---------------- fuel hanger rev 8 (build123d) ----------------
HS='C:\\\\projects\\\\active\\\\fairsolid\\\\runs\\\\fuel_hanger_billet_1014\\\\rev8\\\\'
HJ='st185_hanger_1017'
HN=["MATERIAL: 6061-T6 ALUMINUM BILLET. MODEL: build123d hanger_billet.py REV 8 (FAIRSOLID RUN FOLDER, NOT IN THE REPO).",
    "EDGE BREAKS: MODELLED WHERE build123d DID THEM (16 EDGES); BREAK ALL OTHER SHARP EDGES 0.3 (8 FAILED IN CAD, R138 NOTE)."]
def HP(key,f,pn,title,threads,notes,**kw):
    PARTS[key]=dict(job=HJ,file=src(HJ,f+'.step'),process='machined',title=title,pn=pn,material='6061-T6 ALUMINUM',source=HS+f+'.step',
                    hidden=True,threads=threads,rev='8',notes=HN+notes,**kw)
HP('hg_plate','hanger_top_plate','ST185-FH-101','FUEL HANGER - TOP PLATE',{4.2:('M5x0.8',0.8)},
   ["2X M5x0.8-6H THRU (LUG BLOCK): TAPPED THRU THE 7.8 PLATE (1.56xD, REV 8). SEAL EACH M5 SHCS WITH FUEL-RESISTANT THREAD SEALANT; SCREW TIP AT OR UNDER THE OUTSIDE FACE.",
    "OPEN ITEM (Needs Dan N6): THROUGH-TAPPED HOLES OPEN A PATH FROM THE TANK TO THE OUTSIDE FACE INSIDE THE GASKET RING - KEEP REV 8 + SEALANT, OR BACK TO REV 7 BLIND / INSERT.",
    "NEVER MACHINE THROUGH THE GASKET SEALING FACE."])
HP('hg_lug','hanger_lug_block','ST185-FH-102','FUEL HANGER - LUG BLOCK',{},["2X M5 SHCS CLEARANCE + COUNTERBORE INTO THE TOP PLATE TAPS."])
HP('hg_strut','hanger_strut','ST185-FH-103','FUEL HANGER - STRUT',{},
   ["STRUT POCKETS: FLOOR-TO-WALL EDGES ARE END-MILL FLOOR EDGES - SQUARE CUTTER CORNER OK (SWEEP C13, REV 8 SUMMARY).","FIT THE NUTS BEFORE THE STRUT (-8 NUT SOCKET GRAZE AT THE STRUT ROOT)."])
HP('hg_foot','hanger_foot','ST185-FH-104','FUEL HANGER - FOOT',{3.3:('M4x0.7',0.7)},[])
HP('hg_saddle','hanger_saddle1','ST185-FH-105','FUEL HANGER - PUMP SADDLE',{4.2:('M5x0.8',0.8)},[])
ORDER=['csb3_body','csb3_lid','vrc_holder','drb_plate','fb_power_base','fb_power_pan','fb_power_cover','fb_retainer','fb_logic_base','fb_logic_pan',
       'fb_logic_cover','fb_br_base','fb_br_cover','fb_bar_br','fb_pad','fb_barneg','fb_barpos','fb_strip1','fb_strip2']
# Fuel hanger rev 8 dropped 2026-10-17: Dan rejected the rev 8 model (N6 M5 through-hole), no FH sheets.
# ---------------- Rev letters (Dan 2026-10-17): the MODEL drives the rev letter; drawing = model letter.
# Letters A B C D E F G H J K M N P R S T ... (skip I, L, O, Q). Rev A only for brand-new models. Existing models:
# letter = count of the model's past releases in the repo history (first release = A); rev numbers are not converted.
# Clerical drawing-only revs add .01, .02 (reset on a letter bump). Register: st185 cad/DRAWING-REVS.md.
# No rev in any st185 filename (Dan 2026-10-17): PDFs / PNGs are plain <PN>.pdf / <PN>_sh1.png.
REV_LETTER={'csb3_body':('C','FIRST ISSUE. MODEL REV C (PR #274)'),
            'csb3_lid':('C','FIRST ISSUE. MODEL REV C (PR #273)'),
            'vrc_holder':('D','FIRST ISSUE. MODEL REV D (PR #273)'),
            'drb_plate':('C','FIRST ISSUE. MODEL REV C (PR #275)')}
# Fuse box rev 7 parts (Dan 2026-10-17: count each model's past releases in the repo history; rev 7 is NOT converted to G):
# releases = PRs where the part's size / volume (printed) or mass (copper) in fusebox_report.json changed, + #273 NEG bar holes, #275 LOGIC corner.
FB_REL={'fb_power_base':14,'fb_power_pan':5,'fb_power_cover':6,'fb_retainer':3,'fb_logic_base':12,'fb_logic_pan':6,'fb_logic_cover':8,
        'fb_br_base':7,'fb_br_cover':6,'fb_bar_br':3,'fb_pad':2,'fb_barneg':3,'fb_barpos':2,'fb_strip1':4,'fb_strip2':4}
SEQ='ABCDEFGHJKMNPRSTUVWXYZ'
for _k,_n in FB_REL.items(): REV_LETTER[_k]=(SEQ[_n-1],'FIRST ISSUE. MODEL REV %s (%d RELEASES)'%(SEQ[_n-1],_n))
for _k in ORDER:
    _l,_d=REV_LETTER[_k]
    PARTS[_k]['rev']=_l; PARTS[_k]['revs']=[(_l,_d,TODAY,'SC')]

# CSB3 body tab slots: the model has 6.6 x 10.0 since SteveCAD audit v3 F01 (#272), measured from the STEP 2026-10-17; specs.py still said 5.5 x 9.9
def _fix_slot(o):
    if isinstance(o,dict): return {k:_fix_slot(v) for k,v in o.items()}
    if isinstance(o,list): return [_fix_slot(v) for v in o]
    if isinstance(o,tuple): return tuple(_fix_slot(v) for v in o)
    if o=="4X SLOT 5.5 X 9.9 THRU": return "4X SLOT 6.6 X 10.0 THRU"
    return o
PARTS['csb3_body']=_fix_slot(PARTS['csb3_body'])
# CSB3 section through the (+13.5, +13.5) boss so the 4.0 / 6.5 / M8 stack shows
PARTS['csb3_body']['section']=dict(slot='front',origin=(0,13.5,0),label='A-A')

# Title block (the handbuilt-cad engine defaults to a neutral "PROJECT" / "-"; st185 sets its own)
PROJECT_NAME='ST185 CELICA GT-FOUR  -  LINK ECU CONVERSION'; DRAWN_BY='SteveCAD'
for _v in list(globals().values()):
    if isinstance(_v,dict) and _v and all(isinstance(x,dict) and 'pn' in x for x in _v.values()):
        for _p in _v.values(): _p.setdefault('project',PROJECT_NAME); _p.setdefault('drawn',DRAWN_BY)
