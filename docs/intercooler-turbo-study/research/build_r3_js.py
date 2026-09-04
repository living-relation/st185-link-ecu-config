# -*- coding: utf-8 -*-
"""Add the round-three data block, the eight new charts, and correct the
calculator defaults + open-questions list."""
import os, io, json

HERE = "/sessions/amazing-blissful-bell/mnt/projects/5sgte-intercooler-research"
REPORT = os.path.join(HERE, "intercooler-report.html")
html = io.open(REPORT, encoding="utf-8").read()
r3js = io.open(os.path.join(HERE, "data", "chartdata_r3.js"), encoding="utf-8").read()
orig = len(html)

def must(old, new, n=1, label=""):
    global html
    c = html.count(old)
    assert c == n, "PATCH FAIL [%s]: found %d expected %d\n%r" % (label, c, n, old[:140])
    html = html.replace(old, new)

# ====================================================================
# A. calculator defaults -> the round-three design point
# ====================================================================
cal = [
 ('<label class="ctl">Boost, psi gauge <span class="rowval" id="v_boost">25.0</span></label>\n'
  '<input type="range" id="i_boost" min="5" max="40" step="0.5" value="25">',
  '<label class="ctl">Boost, psi gauge <span class="rowval" id="v_boost">30.0</span></label>\n'
  '<input type="range" id="i_boost" min="5" max="40" step="0.5" value="30">', "boost"),
 ('<label class="ctl">Engine speed, rpm <span class="rowval" id="v_rpm">7000</span></label>\n'
  '<input type="range" id="i_rpm" min="2000" max="8500" step="100" value="7000">',
  '<label class="ctl">Engine speed, rpm <span class="rowval" id="v_rpm">7500</span></label>\n'
  '<input type="range" id="i_rpm" min="2000" max="8500" step="100" value="7500">', "rpm"),
 ('<label class="ctl">Volumetric efficiency <span class="rowval" id="v_ve">0.95</span></label>\n'
  '<input type="range" id="i_ve" min="0.60" max="1.10" step="0.01" value="0.95">',
  '<label class="ctl">Volumetric efficiency <span class="rowval" id="v_ve">0.94</span></label>\n'
  '<input type="range" id="i_ve" min="0.60" max="1.10" step="0.01" value="0.94">', "ve"),
 ('<label class="ctl">Compressor isentropic efficiency <span class="rowval" id="v_eta">0.74</span></label>\n'
  '<input type="range" id="i_eta" min="0.50" max="0.82" step="0.01" value="0.74">',
  '<label class="ctl">Compressor isentropic efficiency <span class="rowval" id="v_eta">0.71</span></label>\n'
  '<input type="range" id="i_eta" min="0.50" max="0.82" step="0.01" value="0.71">', "eta"),
 ('<label class="ctl">Displacement, L <span class="rowval" id="v_disp">2.20</span></label>\n'
  '<input type="range" id="i_disp" min="1.6" max="3.0" step="0.05" value="2.2">',
  '<label class="ctl">Displacement, L <span class="rowval" id="v_disp">2.19</span></label>\n'
  '<input type="range" id="i_disp" min="1.6" max="3.0" step="0.01" value="2.19">', "disp"),
 ('<label class="ctl">Core height, mm <span class="rowval" id="v_ch">300</span></label>\n'
  '<input type="range" id="i_ch" min="150" max="400" step="5" value="300">',
  '<label class="ctl">Core height, mm <span class="rowval" id="v_ch">305</span></label>\n'
  '<input type="range" id="i_ch" min="150" max="400" step="5" value="305">', "ch"),
 ('<label class="ctl">Core thickness, mm <span class="rowval" id="v_ct">75</span></label>\n'
  '<input type="range" id="i_ct" min="40" max="150" step="5" value="75">',
  '<label class="ctl">Core thickness, mm <span class="rowval" id="v_ct">102</span></label>\n'
  '<input type="range" id="i_ct" min="40" max="150" step="2" value="102">', "ct"),
 ('<label class="ctl">Core face velocity, m/s <span class="rowval" id="v_vf">12</span></label>\n'
  '<input type="range" id="i_vf" min="2" max="30" step="0.5" value="12">',
  '<label class="ctl">Core face velocity, m/s <span class="rowval" id="v_vf">6.8</span></label>\n'
  '<input type="range" id="i_vf" min="2" max="30" step="0.1" value="6.8">', "vf"),
]
for a, b, l in cal: must(a, b, label="cal " + l)

# power readout rows in the core calculator
must('    row("Est. crank hp @ 10 hp/lb-min", (S.lbmin*10).toFixed(0)+" hp")+',
     '    row("Est. crank hp @ 10.0 hp/lb-min (E85)", (S.lbmin*10).toFixed(0)+" hp")+\n'
     '    row("<b>Est. wheel hp</b> @ 0.80 AWD drivetrain", "<b>"+(S.lbmin*8.0).toFixed(0)+" whp</b>",\n'
     '        S.lbmin*8.0>430?"wa":"hi")+\n'
     '    row("whp band (9.5-10.5 hp/lb-min, 0.78-0.82 dt)",\n'
     '        (S.lbmin*9.5*0.78).toFixed(0)+" &ndash; "+(S.lbmin*10.5*0.82).toFixed(0)+" whp")+',
     label="whp rows")

# ====================================================================
# B. data block + chart code
# ====================================================================
CHARTS = r'''

/* ================================================================
   ROUND THREE - reconciliation charts. Data block R3 emitted by
   make_r3_chartdata.py from unified_model.py.
   ================================================================ */
''' + r3js + r'''

function r3Axes(s,L,Rr,T,B,W,H,xl,yl,y2){ axes(s,L,Rr,T,B,W,H,xl,yl,y2); }

/* ---------- 1. three models, power vs rpm ---------- */
function drawR3Power(){
  var W=780,H=350,L=56,Rr=120,T=16,B=38, s=svg(W,H);
  var d=R3.power, xLo=3500,xHi=8200,yLo=100,yHi=600;
  gridY(s,L,W,Rr,T,H,B,5,function(v){return v.toFixed(0);},yLo,yHi);
  gridX(s,L,W,Rr,T,H,B,it(xLo,xHi),function(v){return (v/1000).toFixed(1)+"k";},xLo,xHi);
  function X(r){return L+(W-Rr-L)*(r-xLo)/(xHi-xLo);}
  function Y(v){return T+(H-B-T)*(1-(Math.max(yLo,Math.min(yHi,v))-yLo)/(yHi-yLo));}
  [["prior","#ff6b6b",2.6],["report","#ffb347",2.6],["unified","#38d39f",3.2]].forEach(function(k){
    var p=[]; for(var i=0;i<d.rpm.length;i++) p.push([X(d.rpm[i]),Y(d[k[0]][i])]);
    path(s,p,k[1],k[2]);
    var last=p[p.length-1];
    el(s,"circle",{cx:last[0],cy:last[1],r:3.5,fill:k[1]});
  });
  var i75=d.rpm.indexOf(7500);
  [["prior","542 whp  prior research","#ff6b6b"],["report","441 whp  report round 2","#ffb347"],
   ["unified","404 whp  round three","#38d39f"]].forEach(function(k){
    txt(s,X(7500)+8,Y(d[k[0]][i75])+3.5,k[1],{fill:k[2],"font-size":10.5});
  });
  el(s,"line",{x1:X(7500),y1:T,x2:X(7500),y2:H-B,stroke:"#6f8098","stroke-width":1,"stroke-dasharray":"4 4"});
  txt(s,X(7500)-5,H-B-6,"7,500 rpm",{fill:"#6f8098","font-size":9.5,"text-anchor":"end"});
  r3Axes(s,L,Rr,T,B,W,H,"Engine speed, rpm","Wheel horsepower at 30 psi","");
  mount("ch_r3_power",s);
}
function it(a,b){return Math.min(8,Math.round((b-a)/500));}

/* ---------- 2. EFR 7163 boost ladder ---------- */
function drawR3Ladder(){
  var W=780,H=340,L=56,Rr=56,T=18,B=42, s=svg(W,H);
  var d=R3.ladder, yLo=280,yHi=460, y2Lo=40,y2Hi=100;
  gridY(s,L,W,Rr,T,H,B,6,function(v){return v.toFixed(0);},yLo,yHi);
  var xLo=19,xHi=35;
  gridX(s,L,W,Rr,T,H,B,8,function(v){return v.toFixed(0);},xLo,xHi);
  function X(v){return L+(W-Rr-L)*(v-xLo)/(xHi-xLo);}
  function Y(v){return T+(H-B-T)*(1-(v-yLo)/(yHi-yLo));}
  function Y2(v){return T+(H-B-T)*(1-(v-y2Lo)/(y2Hi-y2Lo));}
  // PR ceiling marker at 32.6 psi
  var xc=X(32.6);
  el(s,"rect",{x:xc,y:T,width:(W-Rr)-xc,height:H-B-T,fill:"#ff6b6b","fill-opacity":0.10});
  el(s,"line",{x1:xc,y1:T,x2:xc,y2:H-B,stroke:"#ff6b6b","stroke-width":2});
  txt(s,xc-5,T+13,"PR ceiling 3.6",{fill:"#ff6b6b","font-size":10,"text-anchor":"end"});
  var pw=[],pt=[],pc=[];
  d.forEach(function(r){
    pw.push([X(r.boost),Y(r.whp)]);
    pt.push([X(r.boost),Y2(r.iat)]);
    pc.push([X(r.boost),Y2(r.choke)]);
  });
  path(s,pc,"#4ea3ff",2.0,"4 3"); path(s,pt,"#ffb347",2.2); path(s,pw,"#38d39f",3.2);
  d.forEach(function(r){
    el(s,"circle",{cx:X(r.boost),cy:Y(r.whp),r:r.boost==30?5:3.2,
      fill:r.boost==30?"#38d39f":"#2a3442",stroke:"#38d39f","stroke-width":2});
    if(r.boost==30||r.boost==25||r.boost==34)
      txt(s,X(r.boost),Y(r.whp)-11,r.whp+" whp",{fill:"#38d39f","font-size":10.5,"text-anchor":"middle"});
  });
  for(var i=0;i<=6;i++){
    var y=T+(H-B-T)*i/6, v=y2Hi-(y2Hi-y2Lo)*i/6;
    txt(s,W-Rr+6,y+3.5,v.toFixed(0),{fill:"#6f8098","font-size":9.5});
  }
  r3Axes(s,L,Rr,T,B,W,H,"Boost, psi gauge","Wheel horsepower","Charge temp °C  /  % of choke");
  mount("ch_r3_ladder",s);
}

/* ---------- 3. constant sensitivity heat grid ---------- */
function drawR3Sens(){
  var W=780,H=300,L=120,Rr=140,T=44,B=44, s=svg(W,H);
  var g=R3.sens.grid, dts=R3.sens.dts;
  var cw=(W-Rr-L)/dts.length, chh=(H-B-T)/g.length;
  var lo=1e9,hi=-1e9;
  g.forEach(function(r){for(var i=1;i<r.length;i++){lo=Math.min(lo,r[i]);hi=Math.max(hi,r[i]);}});
  g.forEach(function(r,ri){
    for(var i=0;i<dts.length;i++){
      var v=r[i+1], f=(v-lo)/(hi-lo);
      var x=L+i*cw, y=T+ri*chh;
      var col="rgb("+Math.round(56+199*f)+","+Math.round(211-100*f)+","+Math.round(159-80*f)+")";
      el(s,"rect",{x:x+1.5,y:y+1.5,width:cw-3,height:chh-3,fill:col,"fill-opacity":0.30,
                   stroke:col,"stroke-width":1,rx:3});
      var pick=(r[0]==10.0&&dts[i]==0.80), prior=(r[0]==11.0&&dts[i]==0.85);
      if(pick){el(s,"rect",{x:x+1.5,y:y+1.5,width:cw-3,height:chh-3,fill:"none",
                            stroke:"#38d39f","stroke-width":2.6,rx:3});}
      if(prior){el(s,"rect",{x:x+1.5,y:y+1.5,width:cw-3,height:chh-3,fill:"none",
                            stroke:"#ff6b6b","stroke-width":2.2,"stroke-dasharray":"4 3",rx:3});}
      txt(s,x+cw/2,y+chh/2+5,String(v),{fill:pick?"#7dffcb":"#e6edf5","font-size":pick?15:13,
          "text-anchor":"middle","font-weight":pick?700:500});
    }
    txt(s,L-10,T+ri*chh+chh/2+4,r[0].toFixed(1),{fill:"#9fb0c4","font-size":11.5,"text-anchor":"end"});
  });
  dts.forEach(function(dt,i){
    txt(s,L+i*cw+cw/2,T-12,dt.toFixed(2),{fill:"#9fb0c4","font-size":11.5,"text-anchor":"middle"});
  });
  txt(s,L+(W-Rr-L)/2,T-30,"Drivetrain factor  (1.00 = no loss)",
      {fill:"#6f8098","font-size":11,"text-anchor":"middle"});
  var yl=txt(s,0,0,"Crank hp per lb/min",{fill:"#6f8098","font-size":11,"text-anchor":"middle"});
  yl.setAttribute("transform","translate(22,"+(T+(H-B-T)/2)+") rotate(-90)");
  txt(s,W-Rr+14,T+18,"■ resolved",{fill:"#38d39f","font-size":11});
  txt(s,W-Rr+14,T+36,"10.0 × 0.80",{fill:"#8c9cb0","font-size":10});
  txt(s,W-Rr+14,T+58,"□ prior research",{fill:"#ff6b6b","font-size":11});
  txt(s,W-Rr+14,T+76,"11.0 × 0.85",{fill:"#8c9cb0","font-size":10});
  txt(s,W-Rr+14,T+104,"this report,",{fill:"#ffb347","font-size":10});
  txt(s,W-Rr+14,T+118,"round two: 10.0 × 0.82",{fill:"#ffb347","font-size":10});
  txt(s,W-Rr+14,H-B-16,"All cells: "+R3.sens.lb.toFixed(1)+" lb/min",{fill:"#6f8098","font-size":10});
  txt(s,W-Rr+14,H-B-2,"Identical physics.",{fill:"#6f8098","font-size":10});
  mount("ch_r3_sens",s);
}

/* ---------- 4. VE curves ---------- */
function drawR3VE(){
  var W=780,H=350,L=56,Rr=56,T=16,B=38, s=svg(W,H);
  var d=R3.ve, xLo=4500,xHi=8200,yLo=0.60,yHi=1.10,zLo=0.30,zHi=0.70;
  gridY(s,L,W,Rr,T,H,B,10,function(v){return v.toFixed(2);},yLo,yHi);
  gridX(s,L,W,Rr,T,H,B,7,function(v){return (v/1000).toFixed(1)+"k";},xLo,xHi);
  function X(r){return L+(W-Rr-L)*(r-xLo)/(xHi-xLo);}
  function Y(v){return T+(H-B-T)*(1-(Math.max(yLo,Math.min(yHi,v))-yLo)/(yHi-yLo));}
  function YZ(v){return T+(H-B-T)*(1-(v-zLo)/(zHi-zLo));}
  var zp=[]; for(var i=0;i<d.rpm.length;i++) zp.push([X(d.rpm[i]),YZ(d.Z[i])]);
  path(s,zp,"#c58cff",1.3,"2 3");
  [["r1","#6f8098",2.0,"5 4"],["prior","#ff6b6b",2.4,null],
   ["report","#ffb347",2.4,null],["unified","#38d39f",3.2,null]].forEach(function(k){
    var p=[]; for(var i=0;i<d.rpm.length;i++) p.push([X(d.rpm[i]),Y(d[k[0]][i])]);
    path(s,p,k[1],k[2],k[3]);
  });
  var i75=d.rpm.indexOf(7500);
  [["prior","0.870","#ff6b6b"],["report","0.943","#ffb347"],["unified","0.938","#38d39f"]].forEach(function(k,n){
    el(s,"circle",{cx:X(7500),cy:Y(d[k[0]][i75]),r:3.6,fill:k[2]});
  });
  for(var i=0;i<=5;i++){
    var y=T+(H-B-T)*i/5, v=zHi-(zHi-zLo)*i/5;
    txt(s,W-Rr+6,y+3.5,"Z "+v.toFixed(2),{fill:"#c58cff","font-size":9.5});
  }
  var yk=YZ(0.50);
  el(s,"line",{x1:L,y1:yk,x2:W-Rr,y2:yk,stroke:"#c58cff","stroke-width":1,"stroke-dasharray":"6 4","stroke-opacity":.6});
  txt(s,L+6,yk-5,"Z = 0.50  head begins to restrict above here",{fill:"#c58cff","font-size":9.5});
  [[7200,"7,200 recommended"],[7500,"7,500 outer limit"]].forEach(function(m){
    var x=X(m[0]);
    el(s,"line",{x1:x,y1:T,x2:x,y2:H-B,stroke:"#38d39f","stroke-width":1,"stroke-dasharray":"3 4","stroke-opacity":.5});
    txt(s,x+4,T+12,m[1],{fill:"#38d39f","font-size":9.5});
  });
  r3Axes(s,L,Rr,T,B,W,H,"Engine speed, rpm","Volumetric efficiency","Taylor Mach index Z");
  mount("ch_r3_ve",s);
}

/* ---------- 5. turbo comparison ---------- */
function drawR3Turbo(){
  var t=R3.turbos, W=780,H=30+t.length*38+46,L=150,Rr=104,T=34,B=42, s=svg(W,H);
  var xLo=380,xHi=500, sLo=3200,sHi=5800;
  gridX(s,L,W,Rr,T,H,B,6,function(v){return v.toFixed(0);},xLo,xHi);
  function X(v){return L+(W-Rr-L)*(Math.max(xLo,Math.min(xHi,v))-xLo)/(xHi-xLo);}
  var bh=26, gap=38;
  t.forEach(function(r,i){
    var y=T+i*gap;
    var col = r.ghost?"#ff6b6b":(r.n.indexOf("7163")>=0?"#38d39f":"#4a5568");
    el(s,"rect",{x:L,y:y,width:X(r.whpmax)-L,height:bh,fill:"#4ea3ff","fill-opacity":0.22,rx:2});
    el(s,"rect",{x:L,y:y,width:X(r.whp30)-L,height:bh,fill:"#38d39f","fill-opacity":r.ghost?0.18:0.55,rx:2});
    if(r.n.indexOf("7163")>=0)
      el(s,"rect",{x:L-2,y:y-2,width:X(r.whpmax)-L+4,height:bh+4,fill:"none",stroke:"#38d39f","stroke-width":2,rx:3});
    txt(s,L-8,y+17,r.n,{fill:r.ghost?"#ff8f8f":"#e6edf5","font-size":11.5,"text-anchor":"end",
        "font-weight":r.n.indexOf("7163")>=0?700:400});
    txt(s,X(r.whp30)-6,y+17,String(r.whp30),{fill:"#0d1117","font-size":11,"text-anchor":"end","font-weight":700});
    txt(s,X(r.whpmax)+5,y+17,r.whpmax+" @ "+r.boostmax+" psi",{fill:"#7fb6e8","font-size":10});
    // spool marker on the right rail
    var sx=W-Rr+16+(80)*(r.spool-sLo)/(sHi-sLo);
    el(s,"circle",{cx:sx,cy:y+bh/2,r:4,fill:"#ffb347","fill-opacity":r.ghost?0.3:0.9});
    if(r.ghost) txt(s,X(r.whp30)/1+8,y+17,"",{});
  });
  txt(s,W-Rr+16,T-10,"spool →",{fill:"#ffb347","font-size":10});
  txt(s,W-Rr+16,H-B+15,"3.2k",{fill:"#ffb347","font-size":9});
  txt(s,W-Rr+96,H-B+15,"5.8k",{fill:"#ffb347","font-size":9,"text-anchor":"end"});
  el(s,"line",{x1:L,y1:T-16,x2:L,y2:H-B,stroke:"#3a4757","stroke-width":1});
  el(s,"line",{x1:L,y1:H-B,x2:W-Rr,y2:H-B,stroke:"#3a4757","stroke-width":1});
  txt(s,(L+W-Rr)/2,H-6,"Wheel horsepower",{fill:"#6f8098","font-size":11,"text-anchor":"middle"});
  txt(s,L,T-16,"solid = at 30 psi (what you drive)   pale = at that turbo's own ceiling",
      {fill:"#6f8098","font-size":10});
  mount("ch_r3_turbo",s);
}

/* ---------- 6. core trade ---------- */
function drawR3Core(){
  var W=780,H=360,L=62,Rr=40,T=22,B=46, s=svg(W,H);
  var c=R3.cores, xLo=30,xHi=48, yLo=60,yHi=82;
  gridY(s,L,W,Rr,T,H,B,5,function(v){return v.toFixed(0);},yLo,yHi);
  gridX(s,L,W,Rr,T,H,B,6,function(v){return v.toFixed(0);},xLo,xHi);
  function X(v){return L+(W-Rr-L)*(v-xLo)/(xHi-xLo);}
  function Y(v){return T+(H-B-T)*(1-(v-yLo)/(yHi-yLo));}
  var placed=[];
  c.forEach(function(r){
    var pick=(r.w==610&&r.t==102), wide=(r.w==711), base=(r.w==610&&r.t==76);
    var col=pick?"#38d39f":(wide?"#ff6b6b":(base?"#ffb347":"#7fb6e8"));
    el(s,"circle",{cx:X(r.dTrad),cy:Y(r.iat),r:pick?9:6,fill:col,
      "fill-opacity":pick?0.95:0.6,stroke:col,"stroke-width":2});
    r3Label(s,X(r.dTrad)+11,Y(r.iat)+4,r.w+"×"+r.h+"×"+r.t,
      {fill:col,"font-size":11,"font-weight":pick?700:400},placed,86);
  });
  var pk=c.filter(function(r){return r.w==610&&r.t==102;})[0];
  var bs=c.filter(function(r){return r.w==610&&r.t==76;})[0];
  el(s,"line",{x1:X(bs.dTrad),y1:Y(bs.iat),x2:X(pk.dTrad),y2:Y(pk.iat),
    stroke:"#38d39f","stroke-width":1.6,"stroke-dasharray":"4 3"});
  txt(s,L+8,T+14,"↓ cooler charge is better",{fill:"#4fe0aa","font-size":10.5});
  txt(s,W-Rr-8,H-B-8,"hotter radiator air is worse →",{fill:"#ff8f8f","font-size":10.5,"text-anchor":"end"});
  r3Axes(s,L,Rr,T,B,W,H,"Extra heat onto the radiator inlet, °C",
         "Charge temperature at the valve, °C","");
  mount("ch_r3_core",s);
}

/* ---------- 7. exhaust pulse timing ---------- */
function drawPulse(){
  var W=780,H=420,L=52,Rr=126,T=26,B=40, s=svg(W,H);
  var p=R3.pulse, COL={1:"#4ea3ff",2:"#38d39f",3:"#ff6b6b",4:"#ffb347"};
  function X(d){return L+(W-Rr-L)*d/720;}
  var panelH=(H-B-T-34)/2;
  function panel(y0,title,titleCol,order,note){
    txt(s,L,y0-8,title,{fill:titleCol,"font-size":12,"font-weight":700});
    el(s,"rect",{x:L,y:y0,width:W-Rr-L,height:panelH,
      fill:titleCol,"fill-opacity":0.05,stroke:"#232c38","stroke-width":1});
    for(var g=0;g<=8;g++){
      var x=X(g*90);
      el(s,"line",{x1:x,y1:y0,x2:x,y2:y0+panelH,stroke:"#232c38","stroke-width":1});
      txt(s,x,y0+panelH+13,String(g*90),{fill:"#6f8098","font-size":9,"text-anchor":"middle"});
    }
    var rh=panelH/4;
    order.forEach(function(cy,i){
      var yy=y0+i*rh+rh*0.22, hh=rh*0.56;
      txt(s,L-7,yy+hh/2+4,"Cyl "+cy,{fill:"#9fb0c4","font-size":10.5,"text-anchor":"end"});
      p.win[cy].forEach(function(sg){
        el(s,"rect",{x:X(sg[0]),y:yy,width:X(sg[1])-X(sg[0]),height:hh,
          fill:COL[cy],"fill-opacity":0.82,rx:2});
      });
    });
    // scroll brackets
    note.forEach(function(n,i){
      var yA=y0+(i*2)*rh+rh*0.22, yB=y0+(i*2+1)*rh+rh*0.78;
      var bx=W-Rr+8;
      el(s,"path",{d:"M"+bx+" "+yA+" L"+(bx+6)+" "+yA+" L"+(bx+6)+" "+yB+" L"+bx+" "+yB,
        fill:"none",stroke:n[1],"stroke-width":1.6});
      txt(s,bx+11,(yA+yB)/2-4,n[0],{fill:n[1],"font-size":10,"font-weight":600});
      txt(s,bx+11,(yA+yB)/2+9,n[2],{fill:n[1],"font-size":9.5});
    });
  }
  panel(T+10,"AS BUILT:  1+2  /  3+4",'#ff6b6b',[1,2,3,4],
        [["Scroll A","#ff6b6b","84° OVERLAP"],["Scroll B","#ff6b6b","84° OVERLAP"]]);
  panel(T+panelH+52,"CORRECT:  1+4  /  2+3",'#38d39f',[1,4,2,3],
        [["Scroll A","#38d39f","96° clear gap"],["Scroll B","#38d39f","96° clear gap"]]);
  txt(s,(L+W-Rr)/2,H-6,"Crank angle, degrees — one full 720° four-stroke cycle",
      {fill:"#6f8098","font-size":11,"text-anchor":"middle"});
  mount("ch_pulse",s);
}

/* ---------- 8. backpressure vs power ---------- */
function drawBP(){
  var W=780,H=310,L=58,Rr=58,T=18,B=42, s=svg(W,H);
  var d=R3.bp, xLo=1.0,xHi=2.5, yLo=380,yHi=420;
  gridY(s,L,W,Rr,T,H,B,4,function(v){return v.toFixed(0);},yLo,yHi);
  gridX(s,L,W,Rr,T,H,B,6,function(v){return v.toFixed(1);},xLo,xHi);
  function X(v){return L+(W-Rr-L)*(v-xLo)/(xHi-xLo);}
  function Y(v){return T+(H-B-T)*(1-(Math.max(yLo,Math.min(yHi,v))-yLo)/(yHi-yLo));}
  var p=d.map(function(r){return [X(r[0]),Y(r[2])];});
  path(s,p,"#38d39f",3.0);
  function marker(x,col,lab,sub){
    var r=null; for(var i=0;i<d.length;i++) if(Math.abs(d[i][0]-x)<0.03) r=d[i];
    if(!r) return;
    el(s,"line",{x1:X(x),y1:T,x2:X(x),y2:H-B,stroke:col,"stroke-width":1.6,"stroke-dasharray":"4 3"});
    el(s,"circle",{cx:X(x),cy:Y(r[2]),r:6,fill:col});
    txt(s,X(x),T+13,lab,{fill:col,"font-size":10.5,"text-anchor":"middle","font-weight":600});
    txt(s,X(x),T+27,sub+"  →  "+r[2]+" whp",{fill:col,"font-size":10,"text-anchor":"middle"});
  }
  marker(1.6,"#4ea3ff","correct pairing","EMAP/IMAP 1.6");
  marker(2.0,"#ff6b6b","as built","EMAP/IMAP ~2.0");
  var a=null,b=null;
  for(var i=0;i<d.length;i++){ if(Math.abs(d[i][0]-1.6)<0.03)a=d[i]; if(Math.abs(d[i][0]-2.0)<0.03)b=d[i]; }
  if(a&&b){
    el(s,"rect",{x:X(1.6),y:Y(a[2]),width:X(2.0)-X(1.6),height:Y(b[2])-Y(a[2]),
      fill:"#ff6b6b","fill-opacity":0.14});
    txt(s,(X(1.6)+X(2.0))/2,Y(b[2])+18,(b[2]-a[2])+" whp",
      {fill:"#ff8f8f","font-size":12,"text-anchor":"middle","font-weight":700});
  }
  r3Axes(s,L,Rr,T,B,W,H,"Exhaust manifold pressure ÷ intake manifold pressure",
         "Wheel horsepower at 7,500 rpm, 30 psi","");
  mount("ch_bp",s);
}

/* ---------- 9. spool comparison ---------- */
function drawSpoolPair(){
  var W=780,H=310,L=56,Rr=56,T=18,B=42, s=svg(W,H);
  var d=R3.spool, xLo=2000,xHi=6000, yLo=0,yHi=32;
  gridY(s,L,W,Rr,T,H,B,4,function(v){return v.toFixed(0);},yLo,yHi);
  gridX(s,L,W,Rr,T,H,B,8,function(v){return (v/1000).toFixed(1)+"k";},xLo,xHi);
  function X(r){return L+(W-Rr-L)*(r-xLo)/(xHi-xLo);}
  function Y(v){return T+(H-B-T)*(1-(v-yLo)/(yHi-yLo));}
  var pr=[],pw=[];
  for(var i=0;i<d.rpm.length;i++){ pr.push([X(d.rpm[i]),Y(d.right[i])]); pw.push([X(d.rpm[i]),Y(d.wrong[i])]); }
  var band=pr.concat(pw.slice().reverse());
  el(s,"path",{d:band.map(function(p,i){return (i?"L":"M")+p[0].toFixed(1)+" "+p[1].toFixed(1);}).join(" ")+" Z",
    fill:"#ff6b6b","fill-opacity":0.13,stroke:"none"});
  path(s,pw,"#ff6b6b",2.8); path(s,pr,"#38d39f",3.0);
  var i35=d.rpm.indexOf(3500);
  el(s,"line",{x1:X(3500),y1:Y(d.wrong[i35]),x2:X(3500),y2:Y(d.right[i35]),
    stroke:"#e6edf5","stroke-width":1.6});
  txt(s,X(3500)+8,(Y(d.wrong[i35])+Y(d.right[i35]))/2,
    (d.right[i35]-d.wrong[i35]).toFixed(1)+" psi at 3,500 rpm",{fill:"#e6edf5","font-size":11,"font-weight":600});
  r3Axes(s,L,Rr,T,B,W,H,"Engine speed, rpm","Boost, psi gauge","");
  mount("ch_spoolpair",s);
}

function drawR3All(){
  try{
    drawR3Power(); drawR3Ladder(); drawR3Sens(); drawR3VE();
    drawR3Turbo(); drawR3Core(); drawPulse(); drawBP(); drawSpoolPair();
  }catch(e){ console.error("round-three charts failed:",e); }
}
'''

must('/* ==== round-two data ==== */', CHARTS + '\n/* ==== round-two data ==== */',
     label="charts block")

# call them from init
must('  drawFitPlan(); drawFitFront();',
     '  drawFitPlan(); drawFitFront();\n  drawR3All();', label="init call")

must('console.log("Intercooler report initialised OK — mdot="+S.lbmin.toFixed(1)+\n'
     '              " lb/min, eps="+S.eps.toFixed(3)+", IAT="+S.iat.toFixed(1)+" C");',
     'console.log("Intercooler report r3 initialised OK — mdot="+S.lbmin.toFixed(1)+\n'
     '              " lb/min, eps="+S.eps.toFixed(3)+", IAT="+S.iat.toFixed(1)+" C, whp="+\n'
     '              (S.lbmin*8.0).toFixed(0));',
     label="console log")

io.open(REPORT, "w", encoding="utf-8").write(html)
print("js injected: %d -> %d bytes (+%d)" % (orig, len(html), len(html)-orig))
