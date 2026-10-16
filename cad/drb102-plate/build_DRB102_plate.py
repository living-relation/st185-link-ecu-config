import cadquery as cq, math, json, os, sys
# Run (WSL, any venv with cadquery): python build_DRB102_plate.py [out_dir]   (default /tmp/w)
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/w'
os.makedirs(OUT, exist_ok=True)
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
# ---------------- TE (source) dims, mm ----------------
TE = dict(   # TE's own figures; the holes we cut are below (HOLE_D)
 cut_w=121.03, cut_h=71.17, cut_r=12.07,      # DRBF-1X sh2 recommended panel cutout (+/-0.25)
 key_r=4.32,                                  # keyway notch R.170, bottom centre
 hole_x=128.65, hole_y=79.50, hole_d=6.35,    # 4x dia .250 on 5.065 x 3.130
 panel_max=6.35,                              # thickness .250 max
 fl_w=148.41, fl_h=98.55, fl_r=9.53, fl_d=46.56,  # flange envelope (5.843 x 3.880, R.375, 1.833 deep)
 rec_w=125.76, rec_h=75.34, rec_d=58.19, rec_r=15.24,  # DRB12-102PXE-L018
 plg_w=125.76, plg_h=75.34, plg_d=45.16, plg_r=15.24,  # DRB16-102SXE-L018
)
# ---------------- design dims ----------------
T=12.70          # 1/2" 6061-T6 plate
WEB=6.00         # web under the connector (<= TE 6.35 max)
PL_W, PL_H, PL_R = 201.0, 150.0, 10.0
PK_W, PK_H, PK_R = 152.0, 104.0, 10.0      # engine-face pocket
FW_W, FW_H, FW_R = 155.0, 105.0, 12.0      # firewall cutout
G_D, G_W = 2.64, 4.75                       # Parker face gland 0.139 cord: L .101-.107; G 4.75 (OPEN-10, 2026-10-16: was 4.70 -> 4.69 measured,
                                            # under Parker 4.72-4.85; widened OUTWARD only - the inner wall, which sets the AS568-261 stretch, stays)
G_IR = 12.0; G_IB = 57.5                     # inner corner R, inner half-height
# size inner half-width so groove inner perimeter = 1.01 * pi * ID(AS568-261 = 6.734")
ID261=6.734*25.4
per_target=1.01*math.pi*ID261
G_IA=(per_target+(8-2*math.pi)*G_IR)/4 - G_IB
G_OA, G_OB, G_OR = G_IA+G_W, G_IB+G_W, G_IR+G_W
TAP_X, TAP_Y = 93.5, 67.5
TAP_D, TAP_DRILL, TAP_THR = 4.2, 10.0, 7.5   # F08 (rev2): M5 tap drill 4.2 x 10 + 118 deg point, thread 7.5 = 1.5 x D (2 x D would break through)
HOLE_D = 6.6     # D1 (Dan): DRBF-1A flange M6 holes, ISO 273 medium clearance (TE shows 6.35)
SCREW_NOTE = 'Firewall screws: M5 x 8 max, A2, qty 10, no part number (D5, F16): thread depth 7.5, a longer screw bottoms out.'
taps=[(sx*TAP_X,sy*TAP_Y) for sx in (-1,1) for sy in (-1,1)]+[(sx*31.0,sy*TAP_Y) for sx in (-1,1) for sy in (-1,1)]+[(-TAP_X,0),(TAP_X,0)]

def rrect(w,h,r,d,z0=0):
    return cq.Workplane("XY").workplane(offset=z0).rect(w,h).extrude(d).edges("|Z").fillet(r)

# plate blank with 0.5 chamfers on perimeter
plate=rrect(PL_W,PL_H,PL_R,T).faces(">Z or <Z").edges().chamfer(0.5)
tools={}
tools['pocket']=rrect(PK_W,PK_H,PK_R,T-WEB+1,WEB)
cut=rrect(TE['cut_w'],TE['cut_h'],TE['cut_r'],T+2,-1)
cut=cut.union(cq.Workplane("XY").workplane(offset=-1).center(0,-TE['cut_h']/2).circle(TE['key_r']).extrude(T+2))
tools['cutout']=cut
teh=cq.Workplane("XY").workplane(offset=-1).pushPoints([(sx*TE['hole_x']/2,sy*TE['hole_y']/2) for sx in(-1,1) for sy in(-1,1)]).circle(HOLE_D/2).extrude(T+2)
tools['te_holes']=teh
groove=rrect(2*G_OA,2*G_OB,G_OR,G_D+1,-1).cut(rrect(2*G_IA,2*G_IB,G_IR,G_D+3,-2))
tools['groove']=groove
# blind tapped holes from firewall face (z=0), tap drill + 118deg point
cone_h=(TAP_D/2)/math.tan(math.radians(59))
tp=None
for (x,y) in taps:
    s=cq.Solid.makeCylinder(TAP_D/2,TAP_DRILL+1,cq.Vector(x,y,-1)).fuse(cq.Solid.makeCone(TAP_D/2,0,cone_h,cq.Vector(x,y,TAP_DRILL)))
    tp=s if tp is None else tp.fuse(s)
tools['taps']=cq.Workplane().add(tp)
p=plate
for k in ['pocket','cutout','te_holes','groove','taps']:
    p=p.cut(tools[k])
# 0.5 chamfers: pocket rim (z=T), cutout edges at z=0 and z=WEB, TE hole edges
def chamf(p,box):
    try:
        return p.edges(cq.selectors.BoxSelector(*box)).chamfer(0.5),True
    except Exception as e:
        print('chamfer fail',box,e); return p,False
p,_=chamf(p,((-PK_W/2-1,-PK_H/2-1,T-0.01),(PK_W/2+1,PK_H/2+1,T+0.01)))
p,_=chamf(p,((-TE['cut_w']/2-0.5,-TE['cut_h']/2-TE['key_r']-0.5,WEB-0.01),(TE['cut_w']/2+0.5,TE['cut_h']/2+0.5,WEB+0.01)))
p,_=chamf(p,((-TE['cut_w']/2-0.5,-TE['cut_h']/2-TE['key_r']-0.5,-0.01),(TE['cut_w']/2+0.5,TE['cut_h']/2+0.5,0.01)))
plate_s=p.val()
print('plate valid',plate_s.isValid(),'solids',len(p.solids().vals()),'vol cm3',round(plate_s.Volume()/1000,1),'mass kg',round(plate_s.Volume()/1e6*2.70,3))
cq.exporters.export(p,os.path.join(OUT,'DRB102-firewall-plate.step'))

# ---------- envelopes ----------
env={}
env['plug_DRB16']=rrect(TE['plg_w'],TE['plg_h'],TE['plg_r'],TE['plg_d'],WEB)
env['socket_keepout']=cq.Workplane("XY").workplane(offset=WEB+TE['plg_d']).circle(12.5).extrude(150)
env['flange_DRBF1A']=rrect(TE['fl_w'],TE['fl_h'],TE['fl_r'],TE['fl_d'],-TE['fl_d'])
env['recept_DRB12']=rrect(TE['rec_w'],TE['rec_h'],TE['rec_r'],TE['rec_d'],-TE['rec_d'])
env['te_screw_heads']=cq.Workplane("XY").workplane(offset=WEB).pushPoints([(sx*TE['hole_x']/2,sy*TE['hole_y']/2) for sx in(-1,1) for sy in(-1,1)]).circle(4.75).extrude(3.6)
fw=cq.Workplane("XY").workplane(offset=-1.0).rect(280,220).extrude(1.0).cut(rrect(FW_W,FW_H,FW_R,4,-2))
fw=fw.cut(cq.Workplane("XY").workplane(offset=-2).pushPoints(taps).circle(2.75).extrude(4))
env['firewall_ref_1mm']=fw
# O-ring (free cross-section) swept along groove centreline
try:
    cl=cq.Workplane("XY").rect(2*(G_IA+G_W/2),2*(G_IB+G_W/2)).val()
    cl=cq.Wire.assembleEdges(cq.Workplane().add(cq.Face.makeFromWires(cl)).edges().vals())
    path=cq.Workplane("XY").add(cq.Workplane("XY").rect(2*(G_IA+G_W/2),2*(G_IB+G_W/2)).extrude(1).edges("|Z").fillet(G_IR+G_W/2).faces("<Z").wires().val())
    w=path.val()
    st=w.startPoint(); tg=w.tangentAt(0)
    prof=cq.Workplane(cq.Plane(origin=(st.x,st.y,G_D-3.53/2+0.0),xDir=(0,0,1),normal=tg)).circle(3.53/2)
    oring=prof.sweep(cq.Workplane().add(w),transition='round')
    env['oring_AS568_261']=oring
except Exception as e: print('oring fail',e)

res={}
for k,v in env.items():
    try:
        vol=plate_s.intersect(v.val()).Volume()
    except Exception: vol=float('nan')
    res[k]=round(vol,3)
print('interference vol with plate (mm3):',res)
# plug vs te screw heads
print('plug∩heads',round(env['plug_DRB16'].val().intersect(env['te_screw_heads'].val()).Volume(),3))
def dist(a,b):
    d=BRepExtrema_DistShapeShape(a.wrapped,b.wrapped); d.Perform(); return d.Value()
print('plug to pocket wall (lateral clearance, mm):',round(dist(env['plug_DRB16'].val(), plate_s),2))
print('screw heads to plate walls:',round(dist(env['te_screw_heads'].val(),rrect(PK_W+40,PK_H+40,10,T,0).cut(rrect(PK_W,PK_H,PK_R,T,0)).val()),2))
print('flange to firewall hole:',round(dist(env['flange_DRBF1A'].val(),fw.val()),2))

asm=cq.Assembly(name='DRB102_firewall_assy')
asm.add(p,name='plate_6061',color=cq.Color(0.75,0.77,0.8))
cols={'plug_DRB16':(0.2,0.2,0.2),'socket_keepout':(1,0.6,0),'flange_DRBF1A':(0.1,0.1,0.1),'recept_DRB12':(0.3,0.3,0.35),'te_screw_heads':(0.6,0.6,0.1),'firewall_ref_1mm':(0.5,0.6,0.5),'oring_AS568_261':(0.9,0.4,0.1)}
for k,v in env.items(): asm.add(v,name=k,color=cq.Color(*cols[k]))
asm.save(os.path.join(OUT,'DRB102-firewall-plate-assembly.step'))
# OPEN-10 stretch check (AS568-261: ID 6.734 in, W 0.139 in): the ring sits on the groove's INNER wall, whose perimeter is set above
per_in = 2*(2*(G_IA-G_IR)+2*(G_IB-G_IR)) + 2*math.pi*G_IR
stretch = per_in/(math.pi*ID261) - 1
print('O-ring stretch on the inner wall: %.2f %% (target 1-3 %%); groove width %.2f, depth %.2f, squeeze %.0f %%' % (100*stretch, G_W, G_D, 100*(3.53-G_D)/3.53))
json.dump(dict(G_IA=G_IA,G_IB=G_IB,G_IR=G_IR,G_OA=G_OA,G_OB=G_OB,G_OR=G_OR,G_W=G_W,per_in=per_target/25.4,stretch_pct=round(100*stretch,2),
               hole_d=HOLE_D,tap=[TAP_D,TAP_DRILL,TAP_THR],screws=SCREW_NOTE,taps=taps),open(os.path.join(OUT,'params.json'),'w'),indent=1)
print(json.load(open(os.path.join(OUT,'params.json'))))
