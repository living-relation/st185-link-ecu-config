"""Pull the chart/calculator JS that round five still uses out of the round-four
file, drop everything tied to a deleted section, and write r5_script.js."""
import re

SRC = open("intercooler-report.html", encoding="utf-8").read().split("\n")

def chunk(a, b):                       # 1-indexed, inclusive
    return "\n".join(SRC[a - 1:b])

KEEP = [
    ("core physics, calculators, SVG helpers, pipe + dP charts", 4271, 4606),
    ("FPI chart",                                                4674, 4697),
    ("end tank flow diagrams",                                   4699, 4746),
    ("ducting diagram",                                          4748, 4803),
    ("control wiring",                                           4946, 4964),
]
R4DATA   = chunk(5617, 5617)
PULSE    = chunk(5220, 5261)
R4CHARTS = chunk(5879, 6075)

# drawPulse read its windows out of the round-three blob, which is gone.
PULSE = PULSE.replace("var p=R3.pulse,", "var p={win:R5.win},")
PULSE = PULSE.replace('panel(T+10,"AS BUILT:  1+2  /  3+4",\'#ff6b6b\',[1,2,3,4],',
                      'panel(T+10,"THE SUPERSEDED DIAGRAM:  1+2  /  3+4",\'#ff6b6b\',[1,2,3,4],')
PULSE = PULSE.replace('panel(T+panelH+54,"CORRECT:  1+4  /  2+3",\'#38d39f\',[1,4,2,3],',
                      'panel(T+panelH+54,"AS BUILT, AND CORRECT:  1+4  /  2+3",\'#38d39f\',[1,4,2,3],')

NEW = r"""
/* ================================================================
   ROUND FIVE - the two charts that carry the two decisions.
   ================================================================ */

/* charge pipe: what each diameter costs and buys */
function drawPipeDecision(){
  var W=780,H=340,L=58,Rr=58,T=20,B=52, s=svg(W,H);
  var d=R5.pipes, n=d.length;
  var band=(W-Rr-L)/n;
  var prLo=3.40, prHi=3.62;
  var fLo=130, fHi=210;
  function Yp(v){return T+(H-B-T)*(1-(v-prLo)/(prHi-prLo));}
  for(var i=0;i<=5;i++){
    var y=T+(H-B-T)*i/5, v=prHi-(prHi-prLo)*i/5;
    el(s,"line",{x1:L,y1:y,x2:W-Rr,y2:y,stroke:"#232c38","stroke-width":1});
    txt(s,L-6,y+3.5,v.toFixed(2),{fill:"#6f8098","font-size":10,"text-anchor":"end"});
    txt(s,W-Rr+6,y+3.5,(fHi-(fHi-fLo)*i/5).toFixed(0),{fill:"#6f8098","font-size":10});
  }
  /* the pressure-ratio ceiling */
  el(s,"line",{x1:L,y1:Yp(3.6),x2:W-Rr,y2:Yp(3.6),stroke:"#ff6b6b","stroke-width":1.8,
               "stroke-dasharray":"6 4"});
  txt(s,L+6,Yp(3.6)-6,"EFR 7163 pressure-ratio ceiling 3.60",
      {fill:"#ff6b6b","font-size":10.5,"font-weight":600});
  var fillPts=[];
  d.forEach(function(p,i){
    var cx=L+band*i+band/2;
    var bw=band*0.34;
    var y=Yp(p.pr), y0=H-B;
    var good=(p.od===2.5);
    el(s,"rect",{x:cx-bw-2,y:y,width:bw,height:y0-y,rx:2,
                 fill:good?"#38d39f":"#4ea3ff","fill-opacity":good?0.95:0.5});
    txt(s,cx-bw/2-2,y-6,p.pr.toFixed(2),
        {fill:good?"#4fe0aa":"#79bbff","font-size":10.5,"text-anchor":"middle","font-weight":600});
    fillPts.push([cx+bw/2+2, T+(H-B-T)*(1-(p.fill_ms-fLo)/(fHi-fLo))]);
    txt(s,cx,H-B+16,p.od.toFixed(2)+" in",
        {fill:good?"#4fe0aa":"#9fb0c4","font-size":11,"text-anchor":"middle",
         "font-weight":good?700:400});
    txt(s,cx,H-B+29,"ID "+p.id_mm.toFixed(1)+" mm",
        {fill:"#6f8098","font-size":9.5,"text-anchor":"middle"});
    txt(s,cx,H-B+41,"max "+p.boost_cap.toFixed(1)+" psi",
        {fill:"#8fa0b4","font-size":9.5,"text-anchor":"middle"});
  });
  path(s,fillPts,"#ffb347",2.2);
  fillPts.forEach(function(p,i){
    el(s,"circle",{cx:p[0],cy:p[1],r:4,fill:"#ffb347"});
    txt(s,p[0]+8,p[1]+3.5,d[i].fill_ms+" ms",{fill:"#ffb347","font-size":10});
  });
  axes(s,L,Rr,T,B,W,H,"charge pipe outside diameter, 0.065 in wall",
       "pressure ratio needed at 30 psi","system fill time, ms");
  mount("ch_pipe_dec",s);
}

/* core: what aperture width buys */
function drawAperture(){
  var W=780,H=340,L=58,Rr=58,T=18,B=44, s=svg(W,H);
  var d=R5.sweep.filter(function(r){return r.t===102;});
  var xLo=400,xHi=720, yLo=60,yHi=84, y2Lo=64,y2Hi=76;
  function X(v){return L+(W-Rr-L)*(v-xLo)/(xHi-xLo);}
  function Y(v){return T+(H-B-T)*(1-(v-yLo)/(yHi-yLo));}
  function Y2(v){return T+(H-B-T)*(1-(v-y2Lo)/(y2Hi-y2Lo));}
  gridY(s,L,W,Rr,T,H,B,6,function(v){return v.toFixed(0);},yLo,yHi);
  gridX(s,L,W,Rr,T,H,B,8,function(v){return v.toFixed(0);},xLo,xHi);
  for(var i=0;i<=6;i++)
    txt(s,W-Rr+6,T+(H-B-T)*i/6+3.5,(y2Hi-(y2Hi-y2Lo)*i/6).toFixed(0),
        {fill:"#6f8098","font-size":10});
  path(s,d.map(function(r){return [X(r.w),Y(r.iat)];}),"#4ea3ff",2.4);
  path(s,d.map(function(r){return [X(r.w),Y2(r.t_rad)];}),"#ffb347",2.2,"6 4");
  d.forEach(function(r){
    el(s,"circle",{cx:X(r.w),cy:Y(r.iat),r:3.2,fill:"#4ea3ff"});
  });
  /* the band that is actually plausible for a CS bumper */
  el(s,"rect",{x:X(540),y:T,width:X(660)-X(540),height:H-B-T,
               fill:"#38d39f","fill-opacity":0.07});
  txt(s,X(600),T+14,"most likely CS aperture band",
      {fill:"#4fe0aa","font-size":10,"text-anchor":"middle"});
  axes(s,L,Rr,T,B,W,H,"core width, mm  (aperture width minus 20 mm)",
       "charge temperature at the valve, °C","air arriving at the radiator, °C");
  mount("ch_aperture",s);
}

function init(){
  bindAll();
  renderCore();
  drawFpi(); drawDuct();
  tankDiag("tank_top","top"); tankDiag("tank_ctr","ctr"); tankDiag("tank_side","side");
  var jobs=[["drawPipeDecision",drawPipeDecision],["drawAperture",drawAperture],
            ["drawR4Map",drawR4Map],["drawR4Dyno",drawR4Dyno],
            ["drawR4Drive",drawR4Drive],["drawR4Stack",drawR4Stack],
            ["drawPulse",drawPulse]];
  jobs.forEach(function(j){
    try{ j[1](); }catch(e){ if(window.console) console.error(j[0]+" failed:",e); }
  });
  console.log("r5 initialised OK — mdot="+S.lbmin.toFixed(1)+" lb/min, eps="+
              S.eps.toFixed(3)+", IAT="+S.iat.toFixed(1)+" C, whp="+(S.lbmin*8.0).toFixed(0));
}
if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",init);
else init();
"""

out = []
for label, a, b in KEEP:
    out.append("/* ---- " + label + " ---- */")
    out.append(chunk(a, b))
out.append("/* ---- official BorgWarner map + community data (round four) ---- */")
out.append(R4DATA)
out.append(R4CHARTS)
out.append("/* ---- exhaust pulse timing ---- */")
out.append(PULSE)
out.append(NEW)

js = "\n\n".join(out)
open("r5_script.js", "w", encoding="utf-8").write(js)
print("wrote r5_script.js  %d bytes  %d lines" % (len(js), js.count("\n")))
for bad in ["R3.", "TD.", "R2C", "drawSoak", "drawFitPlan", "drawFitFront",
            "drawR3", "drawVE(", "drawBP", "fillR2", "initRound2", "fillR4"]:
    if bad in js:
        print("  !! still references", bad)
