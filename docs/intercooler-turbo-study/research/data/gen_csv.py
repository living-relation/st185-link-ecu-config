import math, csv, os
R=287.05; CP=1005.0; GAM=1.4
def C2K(c): return c+273.15
P=101325.0*(1-2.25577e-5*640.0)**5.25588
def eps_cf(n,cr):
    if cr<=1e-6: return 1-math.exp(-n)
    return 1-math.exp((n**0.22/cr)*(math.exp(-cr*n**0.78)-1))

TAMB=32.0; BOOST=25.0; RPM=7000; VE=0.95; ETA=0.74; D=2.2
PM=P/1000+BOOST*6.89476
PR=PM/(P/1000*0.97)
Tc=C2K(TAMB)*(1+(PR**((GAM-1)/GAM)-1)/ETA)-273.15

def solve(W,H,T,v):
    iat=60.0
    for _ in range(80):
        m=D/1000*(RPM/2)/60*VE*(PM*1000)/(R*C2K(iat))
        rho=P/(R*C2K(TAMB)); mc=W*H*v*rho
        Cc=mc*CP; Ch=m*CP; cmin=min(Cc,Ch); cr=cmin/max(Cc,Ch)
        A=W*H*T*900.0; U=55.0*(v/10)**0.5
        e=eps_cf(U*A/cmin,cr)*cmin/Ch
        n=Tc-e*(Tc-TAMB)
        if abs(n-iat)<0.005: iat=n; break
        iat=n
    return m,e,iat

OUT=r"C:\projects\5sgte-intercooler-research\model-data.csv"
rows=[]
rows.append(["SECTION","Effectiveness and outlet IAT vs core face velocity (CSF 8067, 610x300x75)"])
rows.append(["face_velocity_ms","road_speed_mph_approx","effectiveness","outlet_IAT_C","outlet_IAT_F"])
for v in [2,3,4,5,6,8,10,12,14,16,18,20,22,25,28,30]:
    m,e,iat=solve(0.610,0.300,0.075,v)
    rows.append([v, round(v*2.237/0.30,0), round(e,4), round(iat,1), round(iat*9/5+32,0)])

rows.append([])
rows.append(["SECTION","Outlet IAT vs core volume (300 mm high, 75 mm thick, 12 m/s face)"])
rows.append(["core_width_mm","core_volume_L","effectiveness","outlet_IAT_C","outlet_IAT_F","note"])
for W in [350,400,450,500,550,610,650,700]:
    m,e,iat=solve(W/1000,0.300,0.075,12.0)
    note = "RECOMMENDED - CSF 8067" if W==610 else ("CSF 8056" if W==505 else "")
    rows.append([W, round(W/1000*0.300*0.075*1000,2), round(e,4), round(iat,1),
                 round(iat*9/5+32,0), note])

rows.append([])
rows.append(["SECTION","Charge pipe velocity at design point (45.7 lb/min)"])
rows.append(["pipe_OD_in","hot_ms","hot_fts","cold_ms","cold_fts","volume_L_per_m","verdict"])
m,e,iat=solve(0.610,0.300,0.075,12.0)
for d in [2.0,2.25,2.5,2.75,3.0,3.25]:
    def v(pk,t):
        rho=pk*1000/(R*C2K(t)); dm=d*0.0254
        return m/(rho*math.pi*dm*dm/4)
    vh=v(PM*1.03,Tc); vc=v(PM,iat); fh=vh*3.28084
    verd=("Too small" if fh>300 else "Garrett band" if fh>=200 else
          "Good street compromise" if fh>=140 else "Oversized" if fh>=100 else "Far oversized")
    dm=d*0.0254
    rows.append([d, round(vh,1), round(fh,0), round(vc,1), round(vc*3.28084,0),
                 round(math.pi*dm*dm/4*1000,3),
                 ("RECOMMENDED - "+verd) if abs(d-2.5)<0.01 else verd])

rows.append([])
rows.append(["SECTION","Off-design operating points (eps = 0.85)"])
rows.append(["condition","boost_psi","rpm","ambient_C","mass_flow_lbmin","PR",
             "compressor_out_C","IC_outlet_C","IC_outlet_F","heat_kW"])
for lab,b,rp,ta,et in [("street cruise-to-pass",15,5000,25,0.76),
                       ("DESIGN POINT",25,7000,32,0.74),
                       ("worst case hot day",28,7500,35,0.72),
                       ("cool day track",22,6500,15,0.76)]:
    pm=P/1000+b*6.89476; pr=pm/(P/1000*0.97)
    tc=C2K(ta)*(1+(pr**((GAM-1)/GAM)-1)/et)-273.15
    mm=D/1000*(rp/2)/60*0.95*(pm*1000)/(R*C2K(ta+20))
    to=tc-0.85*(tc-ta)
    rows.append([lab,b,rp,ta,round(mm*2.20462*60,1),round(pr,2),round(tc,0),
                 round(to,0),round(to*9/5+32,0),round(mm*CP*(tc-to)/1000,1)])

rows.append([])
rows.append(["SECTION","Thermal mass / heat soak"])
rows.append(["core","volume_L","mass_kg","thermal_capacity_kJ_per_K","time_constant_s_low_airflow"])
for name,W,H,T,dens,ua in [("CSF 8067 bar&plate 610x300x75",.610,.300,.075,2.05,880),
                            ("CSF 8047 bar&plate 560x300x90",.560,.300,.090,2.05,880),
                            ("tube&fin equivalent 610x300x75",.610,.300,.075,1.35,1060),
                            ("small OEM-size core",.400,.250,.060,1.50,470)]:
    vol=W*H*T; mkg=vol*1000*dens; Cth=mkg*900
    rows.append([name, round(vol*1000,2), round(mkg,1), round(Cth/1000,2), round(Cth/ua,1)])

rows.append([])
rows.append(["SECTION","FPI trade-off (normalised to 16 FPI = 1.0)"])
rows.append(["FPI","heat_transfer_rel","air_side_dP_rel","Q_per_dP","note"])
for f in [10,12,14,16,18,20,22,24]:
    q=(f/16)**0.55; dp=(f/16)**1.05
    note = "Q/dP peak" if f==12 else ("RECOMMENDED BAND" if f in (14,16) else "")
    rows.append([f, round(q,3), round(dp,3), round(q/dp,3), note])

with open(OUT,"w",newline="",encoding="utf-8") as fh:
    csv.writer(fh).writerows(rows)
print("wrote", OUT, os.path.getsize(OUT), "bytes,", len(rows), "rows")
