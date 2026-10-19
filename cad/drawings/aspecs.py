import numpy as np
from build123d import *
from asm import load_children
import hw
SRC='C:\\\\projects\\\\active\\\\st185-link-ecu-config\\\\cad'
import os
B_REV=os.environ.get('DWG_REV')=='B'
CAD=os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))      # the repo cad/ folder (rev logs, R152)
REV7=os.path.join(CAD,'fusebox','rev7')
def vrc():
    ch=load_children('src/st185_vrc_1015/VRC_assembly.step')
    g=lambda k:[s for n,v in ch.items() if n.startswith(k) for s in v]
    lid=[hw.csk_screw(sx*41.1,sy*21.1,45,3,12,6.9) for sx in(-1,1) for sy in(-1,1)]
    tab=[hw.pan_screw(sx*28,sy*31.5,6,6,30,12,4.6) for sx in(-1,1) for sy in(-1,1)]
    hb=g('VRC_board_holder'); hz=Compound(hb).bounding_box().max.Z
    # holder v2 (R126 / R131): 2 x M6 x 14 into the floor bosses at (23.2, 9.5) / (-18.2, -9.5) - measured from VRC_part_VRC-Body.step (2026-10-18)
    hsc=[hw.csk_screw(x,y,hz,6,14,12) for x,y in ((23.2,9.5),(-18.2,-9.5))]
    items=[
     dict(item=1,qty=1,pn='ST185-VRC-101',desc='VRC ENCLOSURE BODY',mat='6061-T6 AL, MACHINED',shapes=g('VRC-Body')),
     dict(item=2,qty=1,pn='ST185-VRC-102',desc='VRC ENCLOSURE LID',mat='6061-T6 AL, MACHINED',shapes=g('VRC-Lid')),
     dict(item=3,qty=1,pn='ST185-VRC-103',desc='BOARD HOLDER',mat='PA12, 3D PRINTED (SLS/MJF)',shapes=hb),
     dict(item=4,qty=1,pn='OpenLogicEFI NCV1124 RevB3',desc='DUAL VR CONDITIONER MODULE',mat='PURCHASED',shapes=g('OpenLogicEFI')),
     dict(item=5,qty=2,pn='CNLINKO LP-16-C05SX-02-101',desc='LP-16 MALE PANEL SOCKET, REAR NUT (IN + OUT)',mat='PURCHASED',shapes=g('LP16-IN')+g('LP16-OUT')),
     dict(item=6,qty=1,pn='PARKER N0674-70 2-039',desc='O-RING AS568-039 (69.57 ID x 1.78), LID FACE SEAL',mat='NBR 70',shapes=g('ORING')),
     dict(item=7,qty=4,pn='ISO 10642 M3 x 12',desc='LID SCREW, COUNTERSUNK SOCKET HEAD',mat='A2 STAINLESS',shapes=lid),
     dict(item=8,qty=2,pn='LEMU 2990806014',desc='HOLDER SCREW ISO 10642 M6 x 14, CSK TX30',mat='A2 STAINLESS',shapes=hsc),
    ]
    if not B_REV:
        items.append(dict(item=9,qty=4,pn='ESSENTRA 50M060100P030',desc='TAB SCREW M6 x 1.0 x 30 PAN HEAD (BOX MOUNTS ON NYLON)',mat='NYLON 6/6',shapes=tab))
    stages=[[
      dict(no=1,title='BOARD + HOLDER INTO BODY',base=[1],move=[(3,(0,0,30)),(4,(0,0,42)),(8,(0,0,58))]),
      dict(no=2,title='LP-16 SOCKETS INTO END WALLS',base=[1,3,4],move=[(5,(0,0,0))],xmove=True),
      dict(no=3,title='O-RING, LID, LID SCREWS',base=[1,3,4,5],move=[(6,(0,0,18)),(2,(0,0,34)),(7,(0,0,52))]),
    ]]
    if not B_REV: stages[0].append(dict(no=4,title='MOUNT TO BRACKET (TAB SCREWS)',base=[1,2,3,4,5,6,7],move=[(9,(0,0,28))]))
    else: stages[0][2]['ctx']=True
    # stage 2: IN moves +X, OUT -X : split item 5 shapes by side
    s5=items[4]['shapes']
    stages[0][1]['move']=[]
    stages[0][1]['custom']=[(5,s,(40 if s.center().X>0 else -40,0,0)) for s in s5]
    return dict(context=tab if B_REV else [],open_hide=[2,6,7],title='VRC ENCLOSURE - ASSEMBLY',pn='ST185-VRC-100',items=items,stage_sheets=stages,
      source=SRC+'\\\\enclosures\\\\vrc\\\\VRC_assembly.step',revlog=os.path.join(CAD,'enclosures','vrc','ST185-VRC-100.REVLOG.md'),
      notes=['QTY 2 ASSEMBLIES PER CAR (FRONT + REAR).','TORQUE M3 LID SCREWS EVENLY, CRISS-CROSS; LID CLOSES METAL-TO-METAL ON RIM.','LP-16 REAR NUT: 1.0 N·m.'])
ASM={'vrc':vrc}

def csb3():
    ch=load_children('src/st185_csb3_1015/CSB3_assembly.step')
    g=lambda k:[s for n,v in ch.items() if n.startswith(k) for s in v]
    lid=[hw.csk_screw(sx*31.1,sy*31.1,56,3,12,6.9) for sx in(-1,1) for sy in(-1,1)]
    # the 4 nylon M6 tab screws are not part of the assembly (Dan, markup 2026-10-18: he may not use them; R197)
    items=[
     dict(item=1,qty=1,pn='ST185-CSB3-101',desc='CSB3 ENCLOSURE BODY',mat='6061-T6 AL, MACHINED',shapes=g('CSB3-Body')),
     dict(item=2,qty=1,pn='ST185-CSB3-102',desc='CSB3 ENCLOSURE LID',mat='6061-T6 AL, MACHINED',shapes=g('CSB3-Lid')),
     dict(item=3,qty=1,pn='ECUMASTER CSB3',desc='CAN SWITCH BOARD (CUSTOMER SUPPLIED)',mat='PURCHASED',shapes=g('ECUMaster')),
     dict(item=4,qty=1,pn='TE HD34-24-33PE',desc='HD30 FLANGE RECEPTACLE 33P',mat='PURCHASED',shapes=g('HD34')),
     dict(item=5,qty=1,pn='TE 112263-90',desc='PANEL NUT SIZE 24 (FOR ITEM 4)',mat='PURCHASED'),
     dict(item=6,qty=1,pn='TE 112264-ZZ',desc='LOCKWASHER SIZE 24 (FOR ITEM 4)',mat='PURCHASED'),
     dict(item=7,qty=26,pn='TE 0460-202-2031',desc='SIZE 20 SOLID PIN (IN ITEM 4)',mat='PURCHASED'),
     dict(item=8,qty=2,pn='CAT. 8847 L=10',desc='PCB SUPPORT, NYLON LOCK-IN, L 10 (R133)',mat='NYLON',shapes=g('Lock-in')),
     dict(item=9,qty=2,pn='ISO 4026 M8 x 6',desc='FLOOR SEAL SET SCREW, FLAT POINT (R133)',mat='A2 STAINLESS',shapes=g('Set_screws')),
     dict(item=10,qty=1,pn='PARKER N0674-70 2-039',desc='O-RING AS568-039, LID FACE SEAL',mat='NBR 70',shapes=g('ORING')),
     dict(item=11,qty=4,pn='ISO 10642 M3 x 12',desc='LID SCREW, CSK SOCKET HEAD',mat='A2 STAINLESS',shapes=lid),
     dict(item=12,qty=1,pn='TE HD36-24-33SE',desc='HD30 PLUG 33S (HARNESS SIDE)',mat='PURCHASED'),
     dict(item=13,qty=26,pn='TE 0462-201-2031',desc='SIZE 20 SOLID SOCKET (IN ITEM 12)',mat='PURCHASED'),
     dict(item=14,qty=7,pn='TE 0413-204-2005',desc='SIZE 20 SEALING PLUG, UNUSED CAVITIES',mat='PURCHASED'),
    ]
    stages=[[
      dict(no=1,title='SET SCREWS FROM BELOW, LOCK-IN SUPPORTS, CSB3 BOARD',base=[1],move=[(9,(0,0,-22)),(8,(0,0,22)),(3,(0,0,40))]),
      dict(no=2,title='HD34 RECEPTACLE INTO LID',base=[2],move=[(4,(0,0,55))],note='SECURE WITH PANEL NUT (5) + LOCKWASHER (6) FROM UNDERSIDE (NOT SHOWN)'),
      dict(no=3,title='O-RING, LID, LID SCREWS',base=[1,3,8,9],move=[(10,(0,0,22)),(2,(0,0,45)),(4,(0,0,45)),(11,(0,0,75))]),
    ]]
    return dict(open_hide=[2,4,10,11],title='CSB3 ENCLOSURE - ASSEMBLY',pn='ST185-CSB3-100',items=items,stage_sheets=stages,
      source=SRC+'\\\\enclosures\\\\csb3\\\\CSB3_assembly.step',revlog=os.path.join(CAD,'enclosures','csb3','ST185-CSB3-100.REVLOG.md'),
      notes=['ITEMS MARKED (NOT SHOWN) ARE NOT IN THE 3D MODEL.','TORQUE M3 LID SCREWS EVENLY, CRISS-CROSS; LID CLOSES METAL-TO-METAL ON RIM.','PINS (7) ON BOX SIDE; SOCKETS (14) ON HARNESS SO LIVE 12V IS SHROUDED.'])

def busbar():
    ch=load_children('src/st185_busbar_1015/B_rev3_ASSEMBLY.step')
    g=lambda k:[s for n,v in ch.items() if n.startswith(k) for s in v]
    items=[
     dict(item=1,qty=1,pn='ST185-BUS-105',desc='BUSBAR BODY',mat='ASA, 3D PRINTED',shapes=g('Body_printed')),
     dict(item=2,qty=1,pn='ST185-BUS-106',desc='BUSBAR COVER',mat='ASA, 3D PRINTED',shapes=g('Cover_printed')),
     dict(item=3,qty=1,pn='ST185-BUS-101',desc='POSITIVE BAR',mat='6061-T6 AL, MACHINED',shapes=g('Bar_POS')),
     dict(item=4,qty=1,pn='ST185-BUS-102',desc='NEGATIVE BAR',mat='6061-T6 AL, MACHINED',shapes=g('Bar_NEG')),
     dict(item=5,qty=1,pn='ST185-BUS-103',desc='UNIVERSAL BAR',mat='6061-T6 AL, MACHINED',shapes=g('Bar_UNI')),
     dict(item=6,qty=1,pn='ST185-BUS-104',desc='LINK STRAP 6 x 20, 50 PITCH',mat='6061-T6 AL, MACHINED',shapes=g('LinkStrap')),
     dict(item=7,qty=1,pn='ST185-BUS-107',desc='NOTCH PLUG, POS',mat='ASA, 3D PRINTED',shapes=g('NotchPlug_P')),
     dict(item=8,qty=1,pn='ST185-BUS-108',desc='NOTCH PLUG, NEG',mat='ASA, 3D PRINTED',shapes=g('NotchPlug_N')),
     dict(item=9,qty=10,pn='ISO 4017 M8 x 25',desc='HEX BOLT (LUG STUD)',mat='A2-70 STAINLESS',shapes=g('Bolt_ISO4017_M8x25')),
     dict(item=10,qty=3,pn='ISO 4017 M8 x 30',desc='HEX BOLT (LINK / UNI STUD)',mat='A2-70 STAINLESS',shapes=g('Bolt_ISO4017_M8x30')),
     dict(item=11,qty=16,pn='ISO 4029 M8 x 12',desc='SET SCREW, CUP POINT (CABLE CLAMP)',mat='A2 STAINLESS',shapes=g('SetScrew')),
     dict(item=12,qty=10,pn='ISO 7380 M4 x 10',desc='BUTTON HEAD SCREW (BAR HOLD-DOWN)',mat='A2 STAINLESS',shapes=g('BarScrew')),
     dict(item=13,qty=10,pn='M4 x 8.1 HEAT-SET',desc='HEAT-SET INSERT M4, 8.1 LONG',mat='BRASS',shapes=g('HeatSetInsert')),
     dict(item=14,qty=4,pn='ISO 7380 M6 x 16',desc='MOUNT SCREW (REFERENCE, TO VEHICLE)',mat='A2 STAINLESS',shapes=g('REF_MountScrew')),
    ]
    stages=[[
      dict(no=1,title='HEAT-SET INSERTS INTO BODY',base=[1],move=[(13,(0,0,25))]),
      dict(no=2,title='STUD BOLTS, BARS, LINK STRAP, HOLD-DOWN SCREWS',base=[1,13],move=[(9,(0,0,40)),(10,(0,0,40)),(3,(0,0,40)),(4,(0,0,40)),(5,(0,0,40)),(6,(0,0,58)),(12,(0,0,80))]),
      dict(no=3,title='CABLE SET SCREWS + NOTCH PLUGS',base=[1,3,4,5,6,9,10,12,13],move=[(11,(0,0,30)),(7,(0,0,40)),(8,(0,0,40))]),
      dict(no=4,title='COVER + MOUNTING',base=[1,3,4,5,6,7,8,9,10,11,12,13],move=[(2,(0,0,50)),(14,(0,0,-30))]),
    ]]
    return dict(open_hide=[2],open_label='TRIMETRIC - COVER REMOVED',title='BUSBAR B REV3 - ASSEMBLY',pn='ST185-BUS-100',items=items,stage_sheets=stages,
      source=SRC+'\\\\busbar\\\\design-B-rev3\\\\B_rev3_ASSEMBLY.step',
      notes=['LUG STUDS: M8 LUGS (KLAUKE 4R8 / 2R8) PER B_rev3_report.json, NOT IN THIS BOM.','MOUNT SCREWS (14) SHOWN FOR REFERENCE; LENGTH TO SUIT VEHICLE.'])

def drb():
    ch=load_children('src/st185_drb102_1015/DRB102-firewall-plate-assembly.step')
    g=lambda k:[s for n,v in ch.items() if n.startswith(k) for s in v]
    items=[
     dict(item=1,qty=1,pn='ST185-DRB-101',desc='DRB102 FIREWALL PLATE',mat='6061-T6 AL, MACHINED',shapes=g('plate_6061')),
     dict(item=2,qty=1,pn='TE DRB12-102PAE-L018',desc='DEUTSCH DRB RECEPTACLE, 102 WAY, CABIN SIDE',mat='PURCHASED',shapes=g('TE_DRB12')),
     dict(item=3,qty=1,pn='TE DRBF-1A',desc='DRB INTERFACE FLANGE',mat='PURCHASED',shapes=g('TE_DRBF')),
     dict(item=4,qty=1,pn='TE DRB16-102SAE-L018',desc='DEUTSCH DRB PLUG, 102 WAY, ENGINE HARNESS',mat='PURCHASED',shapes=g('TE_DRB16')),
     dict(item=5,qty=4,pn='#10-14 PLASTITE 48',desc='FLANGE SCREW, PAN HEAD, THREAD-FORMING (HEADS SHOWN)',mat='PURCHASED',shapes=g('te_screw_heads')),
     dict(item=6,qty=1,pn='AS568-261',desc='O-RING, FIREWALL FACE SEAL (0.139 CORD)',mat='NBR 70',shapes=g('oring')),
    ]
    stages=[[
      dict(no=1,title='O-RING INTO FIREWALL-FACE GROOVE',base=[1],move=[(6,(0,0,-30))]),
      dict(no=2,title='RECEPTACLE + FLANGE FROM FIREWALL SIDE, SCREWS FROM ENGINE SIDE',base=[1,6],move=[(3,(0,0,-60)),(2,(0,0,-60)),(5,(0,0,40))]),
      dict(no=3,title='PLUG FROM ENGINE SIDE',base=[1,2,3,5,6],move=[(4,(0,0,60))]),
    ]]
    return dict(title='DRB102 FIREWALL PLATE - ASSEMBLY',pn='ST185-DRB-100',items=items,stage_sheets=stages,
      source=SRC+'\\\\drb102-plate\\\\DRB102-firewall-plate-assembly.step',iso='iso2',revlog=os.path.join(CAD,'drb102-plate','ST185-DRB-100.REVLOG.md'),
      notes=['PLATE FASTENS TO THE FIREWALL WITH 10X M5 SCREWS INTO THE TAPPED HOLES (SCREWS NOT IN SOURCE BOM).','FIREWALL (1 mm REFERENCE) AND SOCKET KEEP-OUT NOT SHOWN.','CONNECTOR BODIES ARE ENVELOPE MODELS.'])
ASM.update(csb3=csb3,busbar=busbar,drb=drb)

import csv, re
def _short(t,n=46):
    t=re.sub(r'\s+',' ',t).strip()
    if len(t)<=n: return t.upper()
    for sep in [' (',', ',' - ',': ']:
        i=t.find(sep,18)
        if 0<i<=n: return t[:i].upper()
    return (t[:n-1]+'…').upper()
def _mat(r):
    g=r['group']; d=(r['item']+' '+r['description']).lower()
    w=lambda *ks: any(re.search(r'\b%s\b'%re.escape(k),d) for k in ks)      # whole words: "plug" is not a "lug", "130 A, 2" is not "A2"
    if g=='Printed': return 'PA12, 3D PRINTED'
    if g=='Copper': return 'C110 Cu, TINNED'
    if g in ('Relay','Relays','Fuses','Terminals','Jumpers') and not w('lug','bolt','washer'): return 'PURCHASED'
    if w('a4','316'): return 'A4 STAINLESS'
    if w('a2','stainless'): return 'A2 STAINLESS'
    if w('brass'): return 'BRASS'
    if w('zinc','steel'): return 'STEEL, ZINC'
    if w('copper','lug'): return 'Cu, TINNED'
    return 'PURCHASED'
_FB=None
def fb_children():
    global _FB
    if _FB is None: _FB=load_children('src/st185_fusebox_1015/ST185_fusebox_rev7_assembly.step')
    return _FB
def fusebox(box):
    ch=fb_children()
    g=lambda *ks:[s for n,v in ch.items() if any(n.startswith(k) for k in ks) for s in v]
    rows=list(csv.DictReader(open(f'src/csv/fusebox-parts-{box.lower()}.csv',encoding='utf-8-sig')))
    M=MAP[box]
    items=[];n=0
    for r in rows:
        q=int(float(r['qty_need'] or 0))
        if q==0 and r['group']!='Copper': continue
        n+=1
        it=dict(item=n,qty=q if q else 1,pn=r['part_number'][:30],desc=_short(r['item']),mat=_mat(r))
        if r['item'].startswith('OPTIONAL'): it['desc']=('M3 HEAT-SET INSERT' if 'insert' in r['item'].lower() else 'M3 x 10 CAP SCREW')+' (OPTIONAL COVER BACKUP)'
        for key,(labels,pn,desc) in M.items():
            if key.lower() in (r['item']+'|'+r['part_number']).lower():
                if labels=='same': it['desc']=it['desc'][:40]+' (SEE NOTE 2)'
                elif labels: it['shapes']=g(*labels)
                if pn: it['pn']=pn
                if desc: it['desc']=desc
                break
        items.append(it)
    return items
# 2026-10-18 buildability review: maps follow the rev 7 parts lists (POWER: cad/fusebox/rev7/fusebox-parts-power.csv, R155 C-straps;
# LOGIC / BATTRELAY: cad/fusebox/). Keys are matched in order against "item|part number" - a longer key goes before a key it contains.
MAP={
 'POWER':{'Power Base':(['Power_Base'],'ST185-FB-101',None),'Power Pan':(['Power_Pan'],'ST185-FB-102',None),'Power Cover':(['Power_Cover'],'ST185-FB-103',None),
   'Retainer clip':(['Power_Retainer'],'ST185-FB-104','R1 RETAINER CLIP'),'POS bus bar':(['Power_Bar_Power','Power_BarNeg'],'ST185-FB-113/-114','POS BUS BAR L226 + NEG BAR L105'),
   'Output C-straps':(['Power_Strap_Out'],'ST185-FB-117','OUTPUT C-STRAP 15 x 3 (14 FROM 1 BAR)'),'FHS-M5-12':(['Power_Stud_PEM'],None,None),
   'Top-nut holder':(['Power_NutHolder'],'ST185-FB-118','C-STRAP TOP-NUT HOLDER, PA12 (1 PER STRAP)'),'RS 527-268':(['Power_Nut_DIN934'],None,'HEX NUT M5 DIN 934, TOP NUT IN ITS HOLDER'),
   'AMI-30':(['Power_Fuse_AMI_orange'],None,None),'AMI-40':(['Power_Fuse_AMI_ltgreen'],None,None),'AMI-50':(['Power_Fuse_AMI_red'],None,None),'AMI-60':(['Power_Fuse_AMI_yellow'],None,None),
   'ATM-10':(['Power_Fuse_ATM'],None,None),'1-1414687-0':(['Power_Relay_TE_PowerB'],None,None),'1-1414147-0':(['Power_Relay_TE_F7'],None,'MAXI ISO F7 RELAY 680 OHM (k_efi/k_str/k_fan)'),
   '1-1393304-0':('same',None,None),'280756-4':(['Power_Terminal_TE_280756'],None,None),'280755-4':(['Power_Terminal_TE_280755'],None,None),
   '87a receptacle':('same',None,None),'42281-1':(['Power_Terminal_TE_42281'],None,None),'62998-2':(['Power_Terminal_TE_62998'],None,None),
   '1-968851-1':(['Power_Terminal_TE_1-968851'],None,None),'1-968849-1':(['Power_Terminal_TE_1-968849'],None,None),
   'Klauke 2R5':(['Power_Lug_Klauke'],None,None),'Klauke 6R8':(['Power_Lug_BusPos','Power_Lug_BusNeg'],None,None),
   'RS 287-3921':(['Power_EarBolt'],None,'HEX BOLT M5 x 10, EAR (DOWN INTO THE TOP NUT)'),'RS 263-2205':(['Power_BarBolt'],None,'HEX BOLT M5 x 16 / M8 x 25, BAR STUDS'),
   'RS 190-276':('same',None,None),'RS 264-6432':(['Power_Nut_Keps','Power_LugNut'],None,'KEPS NUT M5 (BAR STUDS + LUG STUDS) / HEX NUT M8'),'RS 530-769':('same',None,None),
   'EFC 10S00056':(['Power_Limiter'],None,None)},
 'LOGIC':{'Logic Base':(['Logic_Base'],'ST185-FB-105',None),'Logic Pan':(['Logic_Pan'],'ST185-FB-106',None),'Logic Cover':(['Logic_Cover'],'ST185-FB-107',None),
   'Logic strips':(['Logic_Strip'],'ST185-FB-115/-116','LOGIC BUS STRIPS BUS1 + BUS2'),'S-M4-2ZI':(['Logic_Nut_PEM_S-M4'],None,None),'SS-M5-2ZI':(['Logic_Nut_PEM_SS-M5'],None,None),
   'ATM-20':(['Logic_Fuse_ATM_20A'],None,None),'ATM-2':(['Logic_Fuse_ATM_2A'],None,None),'ATM-5':(['Logic_Fuse_ATM_5A'],None,None),
   'ATM-7':(['Logic_Fuse_ATM_7p5A'],None,None),'ATM-10':(['Logic_Fuse_ATM_10A'],None,None),'ATM-15':(['Logic_Fuse_ATM_15A'],None,None),
   '4-1904124-2':(['Logic_Relay'],None,'MICRO RELAY (ALL 7 POSITIONS)'),'4-1904124-3':('same',None,None),'5-1393292-8':('same',None,None),'6-1419137-4':('same',None,None),
   '280919-2':(['Logic_Terminal_TE_280919'],None,None),'42281-1':(['Logic_Terminal_TE_42281'],None,None),
   '1-968849-1':(['Logic_Terminal_TE_1-968849'],None,None),'1-968851-1':(['Logic_Terminal_TE_1-968851'],None,None),
   '320554':(['Logic_Lug_TE_PIDG'],None,None),'53941-1':('same',None,None),'M22759/16-14':(['Logic_Wire_jumper'],None,None),
   'M22759/16-16':('same',None,None),'M22759/16-18':('same',None,None),'M22759/16-20':('same',None,None),
   'RS 287-3915':(['Logic_LugBolt_M4'],None,None),'RS 231-0691':(['Logic_Washer'],None,None),'Klauke 2R5':(['Logic_Lug_Klauke'],None,None),
   'RS 287-3921':(['Logic_LugBolt_M5'],None,None),'EFC 10S00056':(['Logic_Limiter'],None,None)},
 'BATTRELAY':{'BattRelay Base':(['BattRelay_Base'],'ST185-FB-108',None),'BattRelay Cover':(['BattRelay_Cover'],'ST185-FB-109',None),
   'Bar 25.4':(['BattRelay_Bar'],'ST185-FB-111',None),'Pad 25.4':(['BattRelay_Pad'],'ST185-FB-112',None),'1416010-1':(['BattRelay_Relay'],None,None),
   '282080-1':(['BattRelay_CoilPlug'],None,None),'AMI-40':(['BattRelay_Fuse'],None,None),'Klauke 1R6':(['BattRelay_Lug_Klauke'],None,'RING LUG 6 mm², M6 / 10 mm² M5 (4 LUGS)'),
   'Klauke 2R5':('same',None,None),'RS 190-169':(['BattRelay_FlangeBolt'],None,None),'RS 527-274':(['BattRelay_Nut'],None,'HEX NUT M6 / KEPS M5 (ALL NUTS)'),
   'RS 264-6432':('same',None,None),'RS 263-2205':(['BattRelay_BarBolt'],None,'HEX BOLT M5 x 16 / M5 x 12 / M6 FEED STUD'),'RS 484-0098':('same',None,None),
   'EFC 10S00056':(['BattRelay_Limiter'],None,'COMPRESSION LIMITERS (ALL 4)'),'EFC 10S00052':('same',None,None)},
}
def _stages(items,plan):
    num=lambda key:[it['item'] for it in items if key.lower() in (it['desc']+'|'+it['pn']).lower() and it.get('shapes')]
    out=[];placed=[]
    for no,(title,moves) in enumerate(plan,1):
        mv=[]
        for key,vec in moves:
            for i in num(key):
                if i not in [m for m,_ in mv]: mv.append((i,vec))
        out.append(dict(no=no,title=title,base=list(placed),move=mv))
        placed+= [i for i,_ in mv]
    return out
TERM_NOTES=['TERMINALS GO UP FROM UNDER THE DECK, CONTACT BOX FIRST, UNTIL THE LANCE CLICKS; PULL THE WIRE BACK LIGHTLY TO CHECK (TE 114-2025 3.6, 114-20021 3.7).',
            'DO NOT TIE THE HARNESS CLOSER THAN 38 mm TO THE DECK UNDERSIDE, AND DO NOT DRESS WIRES SHARPLY TO ONE SIDE (TE 114-20021 3.7 C).']
def fb_power():
    items=fusebox('POWER')
    ch=fb_children(); n=max(i['item'] for i in items)
    # N37 (2026-10-19): the M5 x 10 row of the parts list is the ear bolt now (the lug end is an FHS stud with a Keps nut)
    plan=[('LIMITERS; BAR BOLTS FROM BELOW',[('EFC',(0,0,-25)),('263-2205',(0,0,-30))]),
          ('BARS; C-STRAPS STRAIGHT DOWN (NOTE 4)',[('ST185-FB-113',(0,0,40)),('ST185-FB-117',(0,0,45)),('FHS-M5',(0,0,45)),('TOP-NUT HOLDER',(0,0,45)),('527-268',(0,0,45))]),
          ('TERMINALS, R1 CLIP, LUGS UNDER THE STRAPS',[('280756',(0,0,-30)),('280755',(0,0,-30)),('42281',(0,0,-30)),('62998',(0,0,-30)),
            ('968851',(0,0,-30)),('968849',(0,0,-30)),('ST185-FB-104',(0,0,-40)),('2R5',(0,0,-40))]),
          ('FUSES, EAR BOLTS, NUTS, LUGS, RELAYS',[('AMI-',(0,0,40)),('ATM',(0,0,40)),('EAR (DOWN',(0,0,60)),('264-6432',(0,0,60)),('6R8',(0,0,45)),('RELAY',(0,0,50))]),
          ('BELLY PAN + COVER',[('ST185-FB-102',(0,0,-50)),('ST185-FB-103',(0,0,70))])]
    st=_stages(items,plan)
    base=[it['item'] for it in items if it['pn']=='ST185-FB-101']
    for s in st: s['base']=base+s['base']
    return dict(title='POWER FUSE BOX - ASSEMBLY',pn='ST185-FB-100P',items=items,stage_sheets=[st],bom_h=1.6,bom_cols=(8,8,40,74,30),
      source=SRC+FB+'ST185_fusebox_rev7_assembly.step',open_hide=[i['item'] for i in items if i['pn'] in ('ST185-FB-103',)],open_label='TRIMETRIC - COVER REMOVED',
      revlog=os.path.join(REV7,'ST185-FB-100P.REVLOG.md'),
      notes=['OVERALL DIMENSIONS ONLY (REFERENCE). ITEMS MARKED (NOT SHOWN) ARE NOT MODELED; WIRES/HARNESS OMITTED FOR CLARITY.',
             'RELAY / FASTENER ITEMS THAT SHARE ONE MODEL BODY ARE BALLOONED ON THE FIRST ITEM OF THE GROUP.',
             'M5 BOLTS AND NUTS 4 N·m MAX (AMI SHEET). C-STRAP: STUD PRESSED AND TOP NUT + HOLDER IN BEFORE INSTALL, SEE FB-117.',
             'C-STRAPS GO STRAIGHT DOWN INTO THEIR WELLS: THE LIPS PUSH THE SNAP HOOKS OUT (40 DEG LEAD-IN) AND THE HOOKS SNAP BACK OVER THE LIP ENDS (R181).']+TERM_NOTES)
def fb_logic():
    items=fusebox('LOGIC')
    plan=[('LIMITERS; STRIPS SLID IN FROM THE REAR',[('EFC',(0,0,-25)),('ST185-FB-115',(0,60,0)),('S-M4',(0,60,0)),('SS-M5',(0,60,0))]),
          ('TERMINALS UP INTO THE CAVITIES',[('280919',(0,0,-30)),('42281',(0,0,-30)),('968849',(0,0,-30)),('968851',(0,0,-30))]),
          ('FEED LUGS (NOTE 3) + JUMPERS',[('2R5',(0,0,-35)),('287-3921',(0,0,-45)),('320554',(0,0,-30)),('M22759',(0,0,-30)),('231-0691',(0,0,-40)),('287-3915',(0,0,-50))]),
          ('FUSES + RELAYS',[('ATM',(0,0,45)),('RELAY',(0,0,55))]),
          ('BELLY PAN + COVER',[('ST185-FB-106',(0,0,-50)),('ST185-FB-107',(0,0,70))])]
    st=_stages(items,plan); base=[it['item'] for it in items if it['pn']=='ST185-FB-105']
    for s in st: s['base']=base+s['base']
    return dict(title='LOGIC FUSE BOX - ASSEMBLY',pn='ST185-FB-100L',items=items,stage_sheets=[st],bom_h=1.6,bom_cols=(8,8,40,74,30),
      source=SRC+FB+'ST185_fusebox_rev7_assembly.step',open_hide=[i['item'] for i in items if i['pn'] in ('ST185-FB-107',)],open_label='TRIMETRIC - COVER REMOVED',
      revlog=os.path.join(REV7,'ST185-FB-100L.REVLOG.md'),
      notes=['OVERALL DIMENSIONS ONLY (REFERENCE). ITEMS MARKED (NOT SHOWN) ARE NOT MODELED; WIRES/HARNESS OMITTED FOR CLARITY.',
             'RELAY / LUG / WIRE ITEMS THAT SHARE ONE MODEL BODY ARE BALLOONED ON THE FIRST ITEM OF THE GROUP (ALL 7 MICRO RELAYS SHARE ONE ENVELOPE).',
             'THE M5 x 10 FEED BOLT TIP RUNS 1.7 INTO THE SPINE: IT IS THE LENGTHWISE LOCK OF EACH STRIP - USE x 10, NOT SHORTER.']+TERM_NOTES)
def fb_br():
    items=fusebox('BATTRELAY')
    plan=[('LIMITERS, FLANGE BOLTS, HCR150 RELAY',[('LIMITER',(0,0,-25)),('190-169',(0,0,-30)),('1416010',(0,0,50))]),
          ('BAR, PAD, FUSE, STUDS, NUTS, LUGS',[('ST185-FB-111',(0,0,40)),('ST185-FB-112',(0,0,40)),('263-2205',(0,0,-25)),('AMI-40',(0,0,55)),('527-274',(0,0,70)),('1R6',(0,0,85)),('282080',(0,-30,0))]),
          ('COVER',[('ST185-FB-109',(0,0,70))])]
    st=_stages(items,plan); base=[it['item'] for it in items if it['pn']=='ST185-FB-108']
    for s in st: s['base']=base+s['base']
    return dict(title='BATT RELAY BOX - ASSEMBLY',pn='ST185-FB-100B',items=items,stage_sheets=[st],bom_h=1.9,bom_cols=(8,8,40,74,30),
      revlog=os.path.join(REV7,'ST185-FB-100B.REVLOG.md'),
      source=SRC+FB+'ST185_fusebox_rev7_assembly.step',open_hide=[i['item'] for i in items if i['pn'] in ('ST185-FB-109',)],open_label='TRIMETRIC - COVER REMOVED',
      notes=['OVERALL DIMENSIONS ONLY (REFERENCE). ITEMS MARKED (NOT SHOWN) ARE NOT MODELED; WIRES OMITTED FOR CLARITY.',
             'LUG / NUT / BOLT / LIMITER ITEMS THAT SHARE ONE MODEL BODY ARE BALLOONED ON THE FIRST ITEM OF THE GROUP.',
             'BAR AND PAD: PUSH DOWN PAST THE STANDING SNAP HOOKS (R157); BOTH ARE THEN BOLTED.'])
FB='\\\\fusebox\\\\rev7\\\\'
ASM.update(fb_power=fb_power,fb_logic=fb_logic,fb_br=fb_br)

def fuel_hanger():
    """ST185-FH-100 fuel hanger assembly (option B holder, approved B9, Dan 2026-10-17). Parts from cad/fuel-hanger
    (fuel_hanger.py + build_holder.py), copied into src/st185_fuelhanger_1017 by run_1017.sh. Rev log: ST185-FH-100.REVLOG.md."""
    J='src/st185_fuelhanger_1017/'
    one=lambda f:list(import_step(J+f).solids())
    sc=one('ref_screws_M4.step'); zc=sorted(s.center().Z for s in sc); zmid=(zc[0]+zc[-1])/2
    sad_sc=[s for s in sc if s.center().Z<zmid]; foot_sc=[s for s in sc if s.center().Z>=zmid]
    FHD=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'fuel-hanger')
    items=[
     dict(item=1,qty=1,pn='ST185-FH-101',desc='FUEL HANGER - FLANGE (INTEGRAL LUG)',mat='6061-T6 AL, MACHINED',shapes=one('fuel-hanger-flange.step')),
     dict(item=2,qty=1,pn='ST185-FH-103',desc='FUEL HANGER - STRUT',mat='6061-T6 AL, MACHINED',shapes=one('fuel-hanger-strut.step')),
     dict(item=3,qty=1,pn='ST185-FH-104',desc='FUEL HANGER - FOOT',mat='6061-T6 AL, MACHINED',shapes=one('fuel-hanger-foot.step')),
     dict(item=4,qty=1,pn='ST185-FH-105',desc='FUEL HANGER - PUMP SADDLE',mat='6061-T6 AL, MACHINED',shapes=one('fuel-hanger-saddle.step')),
     dict(item=5,qty=2,pn='ISO 10642 M4 x 12',desc='SADDLE SCREW, CSK SOCKET HEAD',mat='A2 STAINLESS',shapes=sad_sc),
     dict(item=6,qty=2,pn='ISO 4762 M4 x 14',desc='FOOT SCREW, SOCKET HEAD CAP',mat='A2 STAINLESS',shapes=foot_sc),
     dict(item=7,qty=1,pn='SAE #24 WORM-DRIVE',desc='BAND CLAMP, 12.7 (1/2 IN) BAND',mat='STAINLESS, PURCHASED',shapes=one('ref_band_clamp_worm_drive.step')),
     dict(item=8,qty=1,pn='WALBRO F90000295',desc='FUEL PUMP (CUSTOMER SUPPLIED)',mat='PURCHASED',shapes=one('fuel-hanger-pump_f90000295.step')),
     dict(item=9,qty=2,pn='M6 BOLT + NYLOC NUT',desc='STRUT TO LUG, LENGTH TO SUIT',mat='A2 STAINLESS'),
    ]
    for it in items: it['shapes']=[s.rotate(Axis.X,180) for s in it.get('shapes',[])] or None   # installed: flange on top
    for it in items:
        if it['shapes'] is None: it.pop('shapes')
    return dict(title='FUEL HANGER - ASSEMBLY',pn='ST185-FH-100',items=items,revlog=os.path.join(FHD,'ST185-FH-100.REVLOG.md'),
      file=J+'fuel-hanger-assembly.step',source='st185-link-ecu-config\\cad\\fuel-hanger\\fuel-hanger-assembly.step',
      project='ST185 CELICA GT-FOUR  -  LINK ECU CONVERSION',drawn='SteveCAD',
      notes=['MADE-WITH: build123d (cad/fuel-hanger). SHOWN AS INSTALLED. OVERALL DIMS ONLY (REF). FITTINGS PER FH-101, NOT SHOWN.',
             'ORDER: BULKHEAD NUTS, THEN STRUT TO FLANGE LUG (ITEM 9); FOOT (ITEM 3) WITH 2X ITEM 6 + MEDIUM THREADLOCKER; PUMP INTO THE FOOT.',
             'SADDLE (ITEM 4): PUSH TOWARD THE STRUT SO THE TAB BEARS ON THE STRUT SIDE FACE, THEN 2X ITEM 5 AT 2 N·m + LOCTITE 243. BAND CLAMP (ITEM 7) IN THE SADDLE CHANNEL.',
             '2 G HAND CHECK, PUMP MASS 0.6 kg ASSUMED: SADDLE HELD BY M4 PRELOAD FRICTION, SF 38 ALONG THE STRUT (NO KEY).'])
ASM.update(fuel_hanger=fuel_hanger)

# Title block (the handbuilt-cad engine defaults to a neutral "PROJECT" / "-"; st185 sets its own)
PROJECT_NAME='ST185 CELICA GT-FOUR  -  LINK ECU CONVERSION'; DRAWN_BY='SteveCAD'
for _v in list(globals().values()):
    if isinstance(_v,dict) and _v and all(isinstance(x,dict) and 'pn' in x for x in _v.values()):
        for _p in _v.values(): _p.setdefault('project',PROJECT_NAME); _p.setdefault('drawn',DRAWN_BY)
def _titled(f):          # ASM holds functions: put the st185 title block on what they return
    def g():
        d=f(); d.setdefault('project',PROJECT_NAME); d.setdefault('drawn',DRAWN_BY); return d
    return g
ASM={k:_titled(f) for k,f in ASM.items()}
