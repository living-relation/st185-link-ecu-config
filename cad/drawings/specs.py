SRC='C:\\\\projects\\\\active\\\\st185-link-ecu-config\\\\cad'
PARTS={}
GEN_M=["BREAK ALL SHARP EDGES 0.2-0.4 UNLESS NOTED; DO NOT BREAK O-RING GROOVE EDGES OR SEALING FACE.",
       "SPOT/CHAMFER ALL TAPPED HOLE ENTRIES 90°, ⌀ = THREAD MAJOR ⌀.",]
PARTS['vrc_body']=dict(job='st185_vrc_1015',file='src/st185_vrc_1015/VRC_part_VRC-Body.step',process='machined',
  title='VRC ENCLOSURE - BODY',pn='ST185-VRC-101',material='6061-T6 ALUMINUM',
  source=SRC+'\\\\enclosures\\\\vrc\\\\VRC_part_VRC-Body.step',
  hidden=False,
  section=dict(slot='front',origin=(0,0,0),label='A-A'),
  threads={2.5:('M3x0.5',0.5),5.0:('M6x1.0',1.0)}, thread_depth={2.5:8.0,5.0:7.5},
  hole_text={('Z',5.0):"2X ⌀5 ↧8.5\nM6x1.0-6H ↧7.5\nON 2X ⌀11 BOSS, 4.5 HIGH",('X',18.5):"⌀18.5 THRU, BOTH END WALLS\nD-FLAT 16.5 ACROSS (FLAT AT TOP)\n⌴ ⌀30 ↧3.5 ON INSIDE FACE (SEE NOTE 4)"},
  skip_radii=[2.75,9.38],
  dims=[
    ('lin','top',(-38,-18,39),(38,-18,39),'h','below'),
    ('lin','top',(38,-18,39),(38,18,39),'v','right'),
    ('lin','top',(18,25,6),(38,25,6),'h','below',{'tier':2}),
    ('lin','top',(-28,31.5,6),(28,31.5,6),'h','below',{'tier':3}),
    ('lin','top',(45,-31.5,6),(45,31.5,6),'v','right',{'tier':2}),
    ('lin','top',(45,-25,39),(45,25,39),'v','right',{'tier':3}),
    ('note','top',(30.2,-31.5+2.75,6),"4X SLOT 5.5 X 9.9 THRU",14,-30),
    ('lin','front',(-45,0,0),(-45,0,5),'v','left',{'tier':2,'text':'(5)'}),
    ('lin','front',(-38,0,5),(-38,0,39),'v','left',{'tier':3}),
    ('lin','front',(41.5,0,6),(45,0,6),'h','below',{'tier':2}),
    ('lin','right',(0,37,0),(0,37,6),'v','right'),
  ],
  details=[dict(parent='front',center=(40.6,0,38.2),radius=2.9,scale=8,label='B',place=(352,112),
     dims=[('lin',(39.68,0,39),(42.32,0,39),'h',14,'2.64 +0.10/-0'),('lin',(38,0,39),(39.68,0,39),'h',5,'1.68'),('lin',(42.32,0,37.68),(42.32,0,39),'v',14,'1.32 ±0.03')])],
  notes=["MATERIAL: 6061-T6 ALUMINUM. STOCK: 95 x 80 x 42 BILLET (FINISH ALL OVER).",
         "QTY 2 PER CAR (FRONT + REAR); BOTH IDENTICAL.",
         "O-RING GROOVE (DETAIL B) FOR AS568-039 NBR70, FACE SEAL. GROOVE FLOOR, WALLS\nAND LID FACE Ra 0.8. GROOVE CORNER R0.13-0.38.",
         "⌀30 x 3.5 SPOTFACE ON INSIDE OF EACH END WALL: BACK-COUNTERBORE THROUGH THE\nD-HOLE, OR SECOND SETUP ON THAT WALL.",
         "ENGRAVE 'IN' (+X END) / 'OUT' (-X END), 3.5 HIGH x 0.3 DEEP, BELOW CONNECTOR.",
        ]+GEN_M)

PARTS['vrc_body']['thread_depth']={5.0:7.5}
def P(key,**kw): PARTS[key]=kw
GROOVE_NOTE="O-RING GROOVE (DETAIL B) FOR AS568-039 NBR70 FACE SEAL. GROOVE FLOOR, WALLS AND LID SEALING FACE Ra 0.8. GROOVE CORNER R0.13-0.38."
P('csb3_body',job='st185_csb3_1015',file='src/st185_csb3_1015/CSB3_part_CSB3-Body.step',process='machined',
  title='CSB3 ENCLOSURE - BODY',pn='ST185-CSB3-101',material='6061-T6 ALUMINUM',
  source=SRC+'\\\\enclosures\\\\csb3\\\\CSB3_part_CSB3-Body.step',hidden=False,
  section=dict(slot='front',origin=(0,0,0),label='A-A'),
  threads={2.5:('M3x0.5',0.5)},
  hole_text={},
  boss_note={2.5:"ON 2X ⌀7 BOSS, 3.0 HIGH"},
  skip_radii=[2.75,9.38],
  dims=[
    ('lin','top',(-28,-28,50),(28,-28,50),'h','below'),
    ('lin','top',(28,-28,50),(28,28,50),'v','right'),
    ('lin','top',(10,35,6),(30,35,6),'h','below',{'tier':2}),
    ('lin','top',(-20,41.5,6),(20,41.5,6),'h','below',{'tier':3}),
    ('lin','top',(35,-41.5,6),(35,41.5,6),'v','right',{'tier':2}),
    ('lin','top',(35,-35,50),(35,35,50),'v','right',{'tier':3}),
    ('note','top',(22.2,-41.5+2.75,6),"4X SLOT 5.5 X 9.9 THRU",14,-26),
    ('lin','front',(-35,0,0),(-35,0,5),'v','left',{'tier':2,'text':'(5)'}),
    ('lin','front',(-28,0,5),(-28,0,50),'v','left',{'tier':3}),
    ('lin','front',(28,0,10),(35,0,10),'h','below',{'tier':2}),
    ('lin','right',(0,47,0),(0,47,6),'v','right'),
  ],
  details=[dict(parent='front',center=(30.6,0,49.2),radius=2.9,scale=8,label='B',place=(352,112),
     dims=[('lin',(29.68,0,50),(32.32,0,50),'h',14,'2.64 +0.10/-0'),('lin',(28,0,50),(29.68,0,50),'h',5,'1.68'),('lin',(32.32,0,48.68),(32.32,0,50),'v',14,'1.32 ±0.03')])],
  notes=["MATERIAL: 6061-T6 ALUMINUM. STOCK: 75 x 100 x 53 BILLET (FINISH ALL OVER).",
         "QTY 1 PER CAR.",GROOVE_NOTE,
         "BOSS HOLES (2X M3) LOCATE KEYSTONE 25510 STANDOFFS FOR THE CSB3 BOARD (27 x 27 PATTERN ON BOARD).",
        ]+GEN_M)
P('csb3_lid',job='st185_csb3_1015',file='src/st185_csb3_1015/CSB3_part_CSB3-Lid.step',process='machined',
  title='CSB3 ENCLOSURE - LID',pn='ST185-CSB3-102',material='6061-T6 ALUMINUM',
  source=SRC+'\\\\enclosures\\\\csb3\\\\CSB3_part_CSB3-Lid.step',hidden=True,hidden_views=['front','right'],
  section=dict(slot='front',origin=(0,0,0),label='A-A'),
  radius_text={21.54:'skip'},
  dims=[('note','top',(15.23,-15.23,6),"⌀43.08 THRU, CENTERED (HD34-24 CUTOUT)\nWITH FLAT 19.91 FROM CENTER\n⌴ ⌀54 ↧2.0 FROM BOTTOM (RELIEF)",40,-36)],
  notes=["MATERIAL: 6061-T6 ALUMINUM. STOCK: 8 x 75 x 75 PLATE (FACE BOTH SIDES TO 6.0).",
         "BOTTOM FACE IS THE O-RING SEALING FACE: Ra 0.8, FLAT WITHIN 0.05, NO TOOL MARKS ACROSS THE SEAL PATH.",
         "HD34-24-33PE RECEPTACLE MOUNTS THROUGH THE CUTOUT WITH PANEL NUT 112263-90 + LOCKWASHER 112264-ZZ; FLAT KEYS THE RECEPTACLE.",
         "BREAK ALL SHARP EDGES 0.2-0.4 EXCEPT SEALING FACE."])
P('vrc_lid',job='st185_vrc_1015',file='src/st185_vrc_1015/VRC_part_VRC-Lid.step',process='machined',
  title='VRC ENCLOSURE - LID',pn='ST185-VRC-102',material='6061-T6 ALUMINUM',
  source=SRC+'\\\\enclosures\\\\vrc\\\\VRC_part_VRC-Lid.step',hidden=True,hidden_views=['front','right'],
  notes=["MATERIAL: 6061-T6 ALUMINUM. STOCK: 8 x 95 x 55 PLATE (FACE BOTH SIDES TO 6.0).",
         "QTY 2 PER CAR.",
         "BOTTOM FACE IS THE O-RING SEALING FACE: Ra 0.8, FLAT WITHIN 0.05.",
         "BREAK ALL SHARP EDGES 0.2-0.4 EXCEPT SEALING FACE."])
P('vrc_holder',job='st185_vrc_1015',file='src/st185_vrc_1015/ST185_VRC_board_holder_PA12.step',process='printed',
  title='VRC BOARD HOLDER',pn='ST185-VRC-103',material='PA12 (SLS / MJF)',
  source=SRC+'\\\\enclosures\\\\vrc\\\\print\\\\ST185_VRC_board_holder_PA12.step',
  notes=["MATERIAL: PA12, POWDER-BED PRINTED (SLS/MJF). PRINT FILE: ST185_VRC_board_holder_PA12.3mf.",
         "DIMENSIONS ARE REFERENCE ONLY; PRINT FROM THE 3D MODEL.",
         "QTY 2 PER CAR. BOARD SITS FLUSH IN THE POCKET, HELD BY 4 SNAP TABS.",
         "2X ⌀ CSK HOLES FOR ISO 10642 M6 x 12 INTO THE BODY FLOOR BOSSES."])
P('drb_plate',job='st185_drb102_1015',file='src/st185_drb102_1015/DRB102-firewall-plate.step',process='machined',
  title='DRB102 FIREWALL PLATE',pn='ST185-DRB-101',material='6061-T6 ALUMINUM',rotate=[('X',180)],
  source=SRC+'\\\\drb102-plate\\\\DRB102-firewall-plate.step',hidden=False,
  section=dict(slot='front',origin=(0,0,0),label='A-A'),
  threads={4.2:('M5x0.8',0.8)},thread_depth={4.2:7.5},
  skip_radii=[16.7,12.0],
  radius_text={12.07:'R12.07 CUTOUT CORNER',4.32:'R4.32 KEYWAY'},
  dims=[],
  details=[dict(parent='front',center=(-79,0,6.35),radius=11,scale=2.5,label='B',place=(362,114),
     dims=[('lin',(-88.03,0,12.7),(-83.33,0,12.7),'h',6,'4.70'),('lin',(-83.33,0,10.06),(-83.33,0,12.7),'v',8,'2.64'),
           ('lin',(-72,0,6.7),(-72,0,12.7),'v',16,'6.0 WEB'),('lin',(-76,0,0),(-76,0,6.7),'v',-14,'6.7')])],
  notes=["MATERIAL: 6061-T6 ALUMINUM. STOCK: 1/2\" (12.7) PLATE x 205 x 155. TOP (AS SHOWN) = FIREWALL FACE.",
         "FIREWALL FACE GROOVE FOR AS568-261 O-RING (PARKER FACE GLAND, 0.139 CORD): 4.70 WIDE x 2.64 DEEP, INNER 166.66 x 115.0 R12, OUTER R16.7. GROOVE Ra 0.8.",
         "ENGINE FACE POCKET 152 x 104 R10, LEAVING 6.0 WEB UNDER THE CONNECTOR (TE MAX PANEL 6.35).",
         "CUTOUT 121.03 x 71.17 R12.07 (+/-0.25) PER TE DRBF-1X; KEYWAY R4.32 AT BOTTOM CENTER.",
         "CHAMFER 0.5 X 45° ON PLATE PERIMETER, POCKET RIM AND CUTOUT EDGES.",
        ]+GEN_M[1:])
BUS='\\\\busbar\\\\design-B-rev3\\\\'
for key,f,pn,t,stock in [('bus_pos','B_rev3_Bar_POS_Al6061','ST185-BUS-101','BUSBAR - POSITIVE BAR','30 x 30 SQ BAR x 265'),
                     ('bus_neg','B_rev3_Bar_NEG_Al6061','ST185-BUS-102','BUSBAR - NEGATIVE BAR','30 x 30 SQ BAR x 176'),
                     ('bus_uni','B_rev3_Bar_UNI_Al6061','ST185-BUS-103','BUSBAR - UNIVERSAL BAR','30 x 15 FLAT BAR x 105')]:
    P(key,job='st185_busbar_1015',file=f'src/st185_busbar_1015/{f}.step',process='machined',title=t,pn=pn,material='6061-T6 ALUMINUM',
      source=SRC+BUS+f+'.step',hidden=False,threads={8.0:('M8x1.25',1.25)},
      notes=[f"MATERIAL: 6061-T6 ALUMINUM. STOCK: {stock} (FINISH ALL OVER).",
             "M8 TAPPED HOLES TAKE ISO 4029 M8 x 12 SET SCREWS (CABLE CLAMP INTO ⌀13.5 BORES) OR ISO 4017 M8 STUD BOLTS.",
             "NO ANODIZE ON CONTACT FACES; CLEAN, DEBURR CABLE BORES.",
             "POCKETS/STEPS NOT DIMENSIONED HERE: MACHINE PER 3D MODEL (STEP) / CAM. DIMENSIONED FEATURES GOVERN."]+GEN_M)
P('bus_link',job='st185_busbar_1015',file='src/st185_busbar_1015/B_rev3_LinkStrap_6061_6x20_P50.step',process='machined',
  title='BUSBAR - LINK STRAP',pn='ST185-BUS-104',material='6061-T6 ALUMINUM',source=SRC+BUS+'B_rev3_LinkStrap_6061_6x20_P50.step',hidden=True,
  notes=["MATERIAL: 6061-T6 ALUMINUM. STOCK: 6 x 20 FLAT BAR x 75.","NO ANODIZE ON CONTACT FACES."]+GEN_M[:1])
for key,f,pn,t in [('bus_body','B_rev3_Body_printed_ASA','ST185-BUS-105','BUSBAR - BODY'),('bus_cover','B_rev3_Cover_printed_ASA','ST185-BUS-106','BUSBAR - COVER'),
                   ('bus_plugP','B_rev3_NotchPlug_P_printed_ASA','ST185-BUS-107','BUSBAR - NOTCH PLUG (POS)'),('bus_plugN','B_rev3_NotchPlug_N_printed_ASA','ST185-BUS-108','BUSBAR - NOTCH PLUG (NEG)')]:
    P(key,job='st185_busbar_1015',file=f'src/st185_busbar_1015/{f}.step',process='printed',title=t,pn=pn,material='ASA (FDM PRINTED)',source=SRC+BUS+f+'.step',
      notes=["MATERIAL: ASA, FDM 3D PRINTED. PRINT FROM THE STL/STEP MODEL.","DIMENSIONS ARE REFERENCE ONLY."]+(["M4 HEAT-SET INSERT HOLES FOR BRASS INSERTS M4 x 8.1."] if 'Body' in f else []))
FB='\\\\fusebox\\\\rev7\\\\'
for key,f,pn,t,note in [('fb_bar_br','BattRelay_Bar_Power_CuC110_25x6p35','ST185-FB-111','BATTRELAY BAR 25.4 x 6.35 x 36.5','CUT FROM 1\" x 1/4\" TINNED C110 FLAT BAR (MECCANIXITY B0CGJBRNJX), SAME STOCK AS POWER BAR.'),
                   ('fb_pad','Power_Pad_Out_CuC110_15x3','ST185-FB-112','OUTPUT PAD 15 x 3 x 17.5','CUT FROM 15 x 3 TINNED COPPER BAR (BOPAODAO B09Z7NBLDK). QTY 15 (14 POWER + 1 BATTRELAY).'),
                   ('fb_barneg','Power_BarNeg_CuC110_25x6p35_L105','ST185-FB-113','POWER NEG BAR 25.4 x 6.35 x 105','CUT FROM 1\" x 1/4\" TINNED C110 FLAT BAR (MECCANIXITY B0CGJBRNJX).'),
                   ('fb_barpos','Power_Bar_Power_CuC110_25x6p35_POS_bus_L226','ST185-FB-114','POWER POS BUS BAR 25.4 x 6.35 x 226','CUT FROM 1\" x 1/4\" TINNED C110 FLAT BAR (MECCANIXITY B0CGJBRNJX).')]:
    P(key,job='st185_fusebox_1015',file=f'src/st185_fusebox_1015/{f}.step',process='machined',title=t,pn=pn,material='C110 COPPER, TINNED',source=SRC+FB+f+'.step',hidden=True,
      notes=["MATERIAL: C110 COPPER, TINNED. "+note,"SAW CUT, DRILL; DEBURR ALL HOLES AND EDGES. DO NOT REMOVE TIN ON CONTACT FACES."])
for idx,(pn,t) in enumerate([('ST185-FB-115','LOGIC BUS STRIP BUS1'),('ST185-FB-116','LOGIC BUS STRIP BUS2')]):
    P(f'fb_strip{idx+1}',job='st185_fusebox_1015',file='src/st185_fusebox_1015/Logic_Strip_Logic_CuC110_25p4x3p2_on_edge.step',solid_index=idx,process='machined',title=t,pn=pn,
      material='C110 COPPER, TINNED',source=SRC+FB+'Logic_Strip_Logic_CuC110_25p4x3p2_on_edge.step',hidden=True,rotate=[('Y',90)],
      threads={4.0:('M4x0.7',0.7),5.0:('M5x0.8',0.8)},
      notes=["MATERIAL: C110 COPPER, TINNED. CUT FROM 1\" x 1/8\" (25.4 x 3.2) TINNED FLAT BAR (MECCANIXITY B0CGJC2S1L); ONE 305 BAR MAKES BUS1 + BUS2.",
             "TAPPED HOLES: M4 FOR JUMPER BOLTS, M5 FOR FEED LUG BOLT. MOUNTS ON EDGE IN THE LOGIC BASE.","DEBURR ALL HOLES AND EDGES."])
for key,f,pn,t,qn in [('fb_power_base','Power_Base_PA12_printed','ST185-FB-101','POWER BOX - BASE',''),('fb_power_pan','Power_Pan_PA12_printed','ST185-FB-102','POWER BOX - BELLY PAN',''),
                   ('fb_power_cover','Power_Cover_PA12_printed','ST185-FB-103','POWER BOX - COVER',''),('fb_retainer','ST185_R1_retainer_clip_PA12','ST185-FB-104','R1 RETAINER CLIP',''),
                   ('fb_logic_base','Logic_Base_PA12_printed','ST185-FB-105','LOGIC BOX - BASE',''),('fb_logic_pan','Logic_Pan_PA12_printed','ST185-FB-106','LOGIC BOX - BELLY PAN',''),
                   ('fb_logic_cover','Logic_Cover_PA12_printed','ST185-FB-107','LOGIC BOX - COVER',''),('fb_br_base','BattRelay_Base_PA12_printed','ST185-FB-108','BATTRELAY BOX - BASE',''),
                   ('fb_br_cover','BattRelay_Cover_PA12_printed','ST185-FB-109','BATTRELAY BOX - COVER','')]:
    P(key,job='st185_fusebox_1015',file=f'src/st185_fusebox_1015/{f}.step',process='printed',title=t,pn=pn,material='PA12 (SLS / MJF)',source=SRC+FB+f+'.step',
      complex=True,notes=["MATERIAL: PA12, POWDER-BED PRINTED (SLS/MJF). PRINT FROM THE STL/STEP MODEL.","DIMENSIONS ARE REFERENCE ONLY (OVERALL SIZE AND MAJOR HOLES); THE 3D MODEL DEFINES ALL OTHER FEATURES."])

# fuse boxes: overall dims only (Daniel)
for _k,_s in PARTS.items():
    if _s.get('job')=='st185_fusebox_1015' and _s.get('process')=='printed':
        _s['max_hole_groups']=0
        _s['notes']=[n.replace('(OVERALL SIZE AND MAJOR HOLES)','(OVERALL SIZE)') for n in _s.get('notes',[])]

# Title block (the handbuilt-cad engine defaults to a neutral "PROJECT" / "-"; st185 sets its own)
PROJECT_NAME='ST185 CELICA GT-FOUR  -  LINK ECU CONVERSION'; DRAWN_BY='SteveCAD'
for _v in list(globals().values()):
    if isinstance(_v,dict) and _v and all(isinstance(x,dict) and 'pn' in x for x in _v.values()):
        for _p in _v.values(): _p.setdefault('project',PROJECT_NAME); _p.setdefault('drawn',DRAWN_BY)
