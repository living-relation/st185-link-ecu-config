/* ---- core physics, calculators, SVG helpers, pipe + dP charts ---- */

"use strict";
/* ============ physical constants ============ */
var R=287.05, CP=1005.0, GAM=1.40, PSI=6.89476, LBMIN=2.20462*60, CFM=2118.88;
var C=function(id){return document.getElementById(id);};
var NS="http://www.w3.org/2000/svg";
function C2K(c){return c+273.15;} function K2C(k){return k-273.15;}
function F(c){return c*9/5+32;}
function pAmb(alt){return 101.325*Math.pow(1-2.25577e-5*alt,5.25588);} // kPa

function massFlow(dispL,rpm,ve,mapKpa,iatC){
  var vdot=(dispL/1000)*(rpm/2)/60*ve;
  var rho=(mapKpa*1000)/(R*C2K(iatC));
  return vdot*rho;
}
function compOut(tinC,pr,eta){
  return K2C(C2K(tinC)*(1+(Math.pow(pr,(GAM-1)/GAM)-1)/eta));
}
function epsCF(ntu,cr){
  if(cr<=1e-6) return 1-Math.exp(-ntu);
  return 1-Math.exp((Math.pow(ntu,0.22)/cr)*(Math.exp(-cr*Math.pow(ntu,0.78))-1));
}
function coreEps(wM,hM,tM,vFace,mHot,tAmb,pAmbKpa){
  var rho=pAmbKpa*1000/(R*C2K(tAmb));
  var mc=wM*hM*vFace*rho;
  var Cc=mc*CP, Ch=mHot*CP;
  var cmin=Math.min(Cc,Ch), cmax=Math.max(Cc,Ch);
  var cr=cmin/cmax;
  var A=wM*hM*tM*900.0;
  var U=55.0*Math.sqrt(vFace/10.0);
  var ntu=U*A/cmin;
  var eHX=epsCF(ntu,cr);
  // eps from the e-NTU relation is referenced to Cmin. The CHARGE-side temperature
  // drop is Q/C_hot, so the effectiveness we actually care about is scaled by Cmin/C_hot.
  // Identical when the charge side is Cmin (normal at speed); materially lower when the
  // ambient side is starved (low face velocity / no ducting) - which is the whole point.
  var eCharge=eHX*cmin/Ch;
  return {eps:eCharge, epsHX:eHX, ntu:ntu, cr:cr, mCold:mc, cminIsCold:Cc<Ch};
}
function pipeVel(m,dIn,pKpa,tC){
  var rho=pKpa*1000/(R*C2K(tC));
  var d=dIn*0.0254, a=Math.PI*d*d/4;
  return m/(rho*a);
}
function dpPipe(m,dIn,lM,nb,pKpa,tC){
  var rho=pKpa*1000/(R*C2K(tC)), d=dIn*0.0254, a=Math.PI*d*d/4;
  var v=m/(rho*a);
  return (0.02*lM/d+nb*0.25)*0.5*rho*v*v/6894.76;
}

/* ============ shared state ============ */
var S={};
function readCore(){
  S.boost=+C("i_boost").value; S.rpm=+C("i_rpm").value; S.ve=+C("i_ve").value;
  S.tamb=+C("i_tamb").value;  S.eta=+C("i_eta").value; S.alt=+C("i_alt").value;
  S.disp=+C("i_disp").value;
  S.cw=+C("i_cw").value; S.ch=+C("i_ch").value; S.ct=+C("i_ct").value; S.vf=+C("i_vf").value;
  S.pamb=pAmb(S.alt);
  S.pman=S.pamb+S.boost*PSI;
  S.pr=S.pman/(S.pamb*0.97);
  // iterate mass flow with IAT feedback
  var iat=S.tamb+25, m=0, tc=0, e=0;
  for(var i=0;i<40;i++){
    m=massFlow(S.disp,S.rpm,S.ve,S.pman,iat);
    tc=compOut(S.tamb,S.pr,S.eta);
    var r=coreEps(S.cw/1000,S.ch/1000,S.ct/1000,S.vf,m,S.tamb,S.pamb);
    e=r.eps; S.ntu=r.ntu; S.cr=r.cr; S.mCold=r.mCold;
    S.epsHX=r.epsHX; S.cminIsCold=r.cminIsCold;
    var nt=tc-e*(tc-S.tamb);
    if(Math.abs(nt-iat)<0.02){iat=nt;break;}
    iat=nt;
  }
  S.m=m; S.tc=tc; S.eps=e; S.iat=iat;
  S.Q=m*CP*(tc-iat);
  S.rhoOut=S.pman*1000/(R*C2K(tc));
  S.cfm=m/S.rhoOut*CFM;
  S.vol=(S.cw/1000)*(S.ch/1000)*(S.ct/1000)*1000; // litres
  S.lbmin=m*LBMIN;
  S.dTrad=S.Q/(S.mCold*CP);
}
function row(k,v,cls){
  return '<div class="calcrow"><span class="k">'+k+'</span><span class="v '+(cls||"")+'">'+v+'</span></div>';
}
function renderCore(){
  readCore();
  ["boost","rpm","ve","tamb","eta","alt","disp","cw","ch","ct","vf"].forEach(function(k){
    var el=C("v_"+k), src=C("i_"+k); if(!el||!src)return;
    var val=+src.value;
    el.textContent=(k=="ve"||k=="eta")?val.toFixed(2):(k=="disp"?val.toFixed(2):
                   (k=="vf"?val.toFixed(1):val));
  });
  var cls = S.iat<50?"hi":(S.iat<70?"":"wa");
  var dpcls= S.eps>0.82?"hi":(S.eps>0.72?"":"wa");
  C("out_core").innerHTML=
    row("Site pressure", S.pamb.toFixed(1)+" kPa")+
    row("Manifold pressure (abs)", S.pman.toFixed(1)+" kPa")+
    row("Pressure ratio", S.pr.toFixed(2))+
    row("Air mass flow", S.lbmin.toFixed(1)+" lb/min &nbsp;("+S.m.toFixed(3)+" kg/s)")+
    row("Volumetric flow", S.cfm.toFixed(0)+" CFM")+
    row("Compressor outlet", S.tc.toFixed(0)+" &deg;C  /  "+F(S.tc).toFixed(0)+" &deg;F","wa")+
    row("Core volume", S.vol.toFixed(1)+" L")+
    row("NTU / C<sub>r</sub>", S.ntu.toFixed(2)+" / "+S.cr.toFixed(2))+
    row("C<sub>min</sub> side", S.cminIsCold?"AMBIENT — core is airflow-starved":"CHARGE — healthy",
        S.cminIsCold?"ba":"hi")+
    row("Charge-side effectiveness &epsilon;", S.eps.toFixed(3),dpcls)+
    row("<b>Intercooler outlet IAT</b>", S.iat.toFixed(1)+" &deg;C  /  "+F(S.iat).toFixed(0)+" &deg;F",cls)+
    row("Heat rejected Q", (S.Q/1000).toFixed(1)+" kW  ("+(S.Q*3.412).toFixed(0)+" BTU/hr)")+
    row("Air heated across core", "+"+S.dTrad.toFixed(1)+" &deg;C (what the radiator now sees)","wa")+
    row("Est. crank hp @ 10.0 hp/lb-min (E85)", (S.lbmin*10).toFixed(0)+" hp")+
    row("<b>Est. wheel hp</b> @ 0.80 AWD drivetrain", "<b>"+(S.lbmin*8.0).toFixed(0)+" whp</b>",
        S.lbmin*8.0>430?"wa":"hi")+
    row("whp band (9.5-10.5 hp/lb-min, 0.78-0.82 dt)",
        (S.lbmin*9.5*0.78).toFixed(0)+" &ndash; "+(S.lbmin*10.5*0.82).toFixed(0)+" whp")+
    row("EFR 7163 utilisation", (S.lbmin/60*100).toFixed(0)+"% of 60 lb/min",
        S.lbmin>57?"ba":(S.lbmin>50?"wa":"hi"));
  drawFace(); drawVol(); renderPipe(); renderDp();
}

/* ============ SVG helpers ============ */
function svg(w,h){var s=document.createElementNS(NS,"svg");
  s.setAttribute("viewBox","0 0 "+w+" "+h);s.setAttribute("width","100%");return s;}
function el(p,n,a){var e=document.createElementNS(NS,n);
  for(var k in a)e.setAttribute(k,a[k]);p.appendChild(e);return e;}
function txt(p,x,y,s,a){var t=el(p,"text",a||{});t.setAttribute("x",x);t.setAttribute("y",y);
  t.textContent=s;return t;}
function axes(s,L,Rr,T,B,W,H,xlab,ylab,y2lab){
  el(s,"line",{x1:L,y1:T,x2:L,y2:H-B,stroke:"#3a4757","stroke-width":1});
  el(s,"line",{x1:L,y1:H-B,x2:W-Rr,y2:H-B,stroke:"#3a4757","stroke-width":1});
  txt(s,(L+W-Rr)/2,H-6,xlab,{fill:"#6f8098","font-size":11,"text-anchor":"middle"});
  var t=txt(s,0,0,ylab,{fill:"#6f8098","font-size":11,"text-anchor":"middle"});
  t.setAttribute("transform","translate(13,"+((T+H-B)/2)+") rotate(-90)");
  if(y2lab){var t2=txt(s,0,0,y2lab,{fill:"#6f8098","font-size":11,"text-anchor":"middle"});
    t2.setAttribute("transform","translate("+(W-12)+","+((T+H-B)/2)+") rotate(90)");}
}
function path(s,pts,color,w,dash){
  var d=pts.map(function(p,i){return (i?"L":"M")+p[0].toFixed(1)+" "+p[1].toFixed(1);}).join(" ");
  var o={d:d,fill:"none",stroke:color,"stroke-width":w||2.2,"stroke-linejoin":"round"};
  if(dash)o["stroke-dasharray"]=dash;
  el(s,"path",o);
}
function gridY(s,L,W,Rr,T,H,B,n,fmt,lo,hi){
  for(var i=0;i<=n;i++){
    var y=T+(H-B-T)*i/n, v=hi-(hi-lo)*i/n;
    el(s,"line",{x1:L,y1:y,x2:W-Rr,y2:y,stroke:"#232c38","stroke-width":1});
    txt(s,L-6,y+3.5,fmt(v),{fill:"#6f8098","font-size":10,"text-anchor":"end"});
  }
}
function gridX(s,L,W,Rr,T,H,B,n,fmt,lo,hi){
  for(var i=0;i<=n;i++){
    var x=L+(W-Rr-L)*i/n, v=lo+(hi-lo)*i/n;
    el(s,"line",{x1:x,y1:T,x2:x,y2:H-B,stroke:"#232c38","stroke-width":1});
    txt(s,x,H-B+15,fmt(v),{fill:"#6f8098","font-size":10,"text-anchor":"middle"});
  }
}
function mount(id,s){var c=C(id); if(!c)return; c.innerHTML=""; c.appendChild(s);}

/* ============ chart: effectiveness vs face velocity ============ */
function drawFace(){
  var W=780,H=330,L=54,Rr=54,T=16,B=38;
  var s=svg(W,H);
  var vmax=30, epsLo=0.3, epsHi=1.0, tLo=20, tHi=140;
  gridY(s,L,W,Rr,T,H,B,7,function(v){return v.toFixed(2);},epsLo,epsHi);
  gridX(s,L,W,Rr,T,H,B,6,function(v){return v.toFixed(0);},0,vmax);
  var pe=[],pt=[];
  for(var v=1;v<=vmax;v+=0.5){
    var r=coreEps(S.cw/1000,S.ch/1000,S.ct/1000,v,S.m,S.tamb,S.pamb);
    var to=S.tc-r.eps*(S.tc-S.tamb);
    var x=L+(W-Rr-L)*v/vmax;
    pe.push([x,T+(H-B-T)*(1-(r.eps-epsLo)/(epsHi-epsLo))]);
    var ty=T+(H-B-T)*(1-(Math.max(tLo,Math.min(tHi,to))-tLo)/(tHi-tLo));
    pt.push([x,ty]);
  }
  path(s,pe,"#4ea3ff",2.4);
  path(s,pt,"#ffb347",2.4);
  // right axis for temp
  for(var i=0;i<=6;i++){
    var y=T+(H-B-T)*i/6, val=tHi-(tHi-tLo)*i/6;
    txt(s,W-Rr+6,y+3.5,val.toFixed(0)+"°",{fill:"#ffb347","font-size":10});
  }
  // operating point
  var ox=L+(W-Rr-L)*S.vf/vmax;
  var oy=T+(H-B-T)*(1-(S.eps-epsLo)/(epsHi-epsLo));
  el(s,"line",{x1:ox,y1:T,x2:ox,y2:H-B,stroke:"#38d39f","stroke-width":1.4,"stroke-dasharray":"4 3"});
  el(s,"circle",{cx:ox,cy:oy,r:5,fill:"#38d39f",stroke:"#0e1116","stroke-width":2});
  var lx=ox+11, an="start";
  if(lx>W-Rr-140){lx=ox-11;an="end";}
  el(s,"rect",{x:an==="start"?lx-4:lx-152,y:oy-31,width:156,height:20,
    fill:"#0e1116","fill-opacity":0.85,rx:4});
  txt(s,lx,oy-17,"ε = "+S.eps.toFixed(3)+"   →  "+S.iat.toFixed(0)+" °C",
      {fill:"#38d39f","font-size":11.5,"font-weight":600,"text-anchor":an});
  if(S.cminIsCold)
    txt(s,L+10,T+14,"⚠ below ~4 m/s the core is airflow-starved — ε collapses",
        {fill:"#ff6b6b","font-size":10.5});
  axes(s,L,Rr,T,B,W,H,"Core face velocity, m/s","Effectiveness ε","Outlet IAT, °C");
  mount("ch_face",s);
}

/* ============ chart: IAT vs core volume ============ */
function drawVol(){
  var W=780,H=300,L=54,Rr=24,T=16,B=38;
  var s=svg(W,H);
  var vLo=5,vHi=22,tLo=30,tHi=110;
  gridY(s,L,W,Rr,T,H,B,8,function(v){return v.toFixed(0);},tLo,tHi);
  gridX(s,L,W,Rr,T,H,B,for_n(),function(v){return v.toFixed(0);},vLo,vHi);
  function for_n(){return 6;}
  var pts=[];
  for(var vol=vLo;vol<=vHi;vol+=0.25){
    // hold height & thickness, vary width to hit target volume
    var hM=S.ch/1000,tM=S.ct/1000;
    var wM=(vol/1000)/(hM*tM);
    var r=coreEps(wM,hM,tM,S.vf,S.m,S.tamb,S.pamb);
    var to=S.tc-r.eps*(S.tc-S.tamb);
    pts.push([L+(W-Rr-L)*(vol-vLo)/(vHi-vLo),
              T+(H-B-T)*(1-(Math.max(tLo,Math.min(tHi,to))-tLo)/(tHi-tLo))]);
  }
  path(s,pts,"#ffb347",2.4);
  var rx=L+(W-Rr-L)*(13.72-vLo)/(vHi-vLo);
  el(s,"line",{x1:rx,y1:T,x2:rx,y2:H-B,stroke:"#38d39f","stroke-width":1.4,"stroke-dasharray":"4 3"});
  txt(s,rx+7,T+14,"CSF 8067 — 13.7 L",{fill:"#38d39f","font-size":11,"font-weight":600});
  // diminishing returns marker
  txt(s,L+12,T+14,"Diminishing returns →",{fill:"#6f8098","font-size":10.5});
  axes(s,L,Rr,T,B,W,H,"Core volume, litres","Outlet IAT, °C");
  mount("ch_vol",s);
}

/* ============ pipe tab ============ */
function renderPipe(){
  var tb=C("tb_pipe").getElementsByTagName("tbody")[0]; tb.innerHTML="";
  var ds=[2.0,2.25,2.5,2.75,3.0,3.25];
  ds.forEach(function(d){
    var vh=pipeVel(S.m,d,S.pman*1.03,S.tc), vc=pipeVel(S.m,d,S.pman,S.iat);
    var fh=vh*3.28084, fc=vc*3.28084;
    var dm=d*0.0254, vol=Math.PI*dm*dm/4*1000;
    var verd,cl="";
    if(fh>300){verd="Too small — excessive loss";cl="p-bad";}
    else if(fh>=200){verd="In Garrett's 200–300 ft/s band";cl="p-ok";}
    else if(fh>=140){verd="Slightly large, low loss — good street compromise";cl="p-info";}
    else if(fh>=100){verd="Oversized, adding dead volume";cl="p-warn";}
    else {verd="Far oversized";cl="p-bad";}
    var hl=(Math.abs(d-2.5)<0.01)?' style="background:#12251f"':'';
    tb.innerHTML+='<tr'+hl+'><td>'+d.toFixed(2)+' in</td>'+
      '<td class="num">'+vh.toFixed(1)+'</td><td class="num">'+fh.toFixed(0)+'</td>'+
      '<td class="num">'+vc.toFixed(1)+'</td><td class="num">'+fc.toFixed(0)+'</td>'+
      '<td class="num">'+vol.toFixed(2)+'</td>'+
      '<td><span class="pill '+cl+'">'+verd+'</span></td></tr>';
  });
  drawPipe();
}
function drawPipe(){
  var W=780,H=310,L=54,Rr=24,T=16,B=38;
  var s=svg(W,H);
  var dLo=1.75,dHi=3.5,fLo=50,fHi=400;
  gridY(s,L,W,Rr,T,H,B,7,function(v){return v.toFixed(0);},fLo,fHi);
  gridX(s,L,W,Rr,T,H,B,7,function(v){return v.toFixed(2);},dLo,dHi);
  // Garrett band 200-300
  function fy(f){return T+(H-B-T)*(1-(Math.max(fLo,Math.min(fHi,f))-fLo)/(fHi-fLo));}
  el(s,"rect",{x:L,y:fy(300),width:W-Rr-L,height:fy(200)-fy(300),fill:"#38d39f","fill-opacity":0.10});
  txt(s,W-Rr-8,fy(300)+15,"Garrett 200–300 ft/s",{fill:"#38d39f","font-size":10.5,"text-anchor":"end"});
  var ph=[],pc=[];
  for(var d=dLo;d<=dHi;d+=0.05){
    var x=L+(W-Rr-L)*(d-dLo)/(dHi-dLo);
    ph.push([x,fy(pipeVel(S.m,d,S.pman*1.03,S.tc)*3.28084)]);
    pc.push([x,fy(pipeVel(S.m,d,S.pman,S.iat)*3.28084)]);
  }
  path(s,ph,"#ff6b6b",2.4); path(s,pc,"#4ea3ff",2.4);
  var rx=L+(W-Rr-L)*(2.5-dLo)/(dHi-dLo);
  el(s,"line",{x1:rx,y1:T,x2:rx,y2:H-B,stroke:"#38d39f","stroke-width":1.4,"stroke-dasharray":"4 3"});
  txt(s,rx+7,T+14,"Recommended 2.5 in",{fill:"#38d39f","font-size":11,"font-weight":600});
  axes(s,L,Rr,T,B,W,H,"Pipe diameter, inches","Charge air velocity, ft/s");
  mount("ch_pipe",s);
}

/* ============ dP tab ============ */
function renderDp(){
  var dh=+C("i_dh").value, lh=+C("i_lh").value, nh=+C("i_nh").value;
  var dc=+C("i_dc").value, lc=+C("i_lc").value, nc=+C("i_nc").value;
  var tank=+C("i_tank").value;
  C("v_dh").textContent=dh.toFixed(2); C("v_lh").textContent=lh.toFixed(1);
  C("v_nh").textContent=nh; C("v_dc").textContent=dc.toFixed(2);
  C("v_lc").textContent=lc.toFixed(1); C("v_nc").textContent=nc;
  var pHot=dpPipe(S.m,dh,lh,nh,S.pman*1.03,S.tc);
  var pCold=dpPipe(S.m,dc,lc,nc,S.pman,S.iat);
  // core dP: quadratic scale from Treadstone C1245 (1142 CFM @ 1.5 psi), corrected
  // for this core's smaller internal flow area (thickness & width vs the reference)
  var areaRatio=(S.cw*S.ct)/(560*89);
  var core=1.5*Math.pow(S.cfm/1142,2)/Math.max(0.4,areaRatio);
  var tot=pHot+pCold+core+tank;
  var pct=100*tot/S.boost;
  // effect on PR / temp
  var pr2=(S.pman+tot*PSI)/(S.pamb*0.97);
  var tc2=compOut(S.tamb,pr2,S.eta);
  var iat2=tc2-S.eps*(tc2-S.tamb);
  function bar(v,max,col){
    return '<div class="bar"><span style="width:'+Math.min(100,100*v/max).toFixed(0)+
           '%;background:'+col+'"></span></div>';
  }
  var mx=Math.max(0.6,tot);
  C("out_dp").innerHTML=
    row("Hot pipe ("+dh.toFixed(2)+" in, "+lh.toFixed(1)+" m, "+nh+" bends)",pHot.toFixed(3)+" psi")+
    bar(pHot,mx,"#ff6b6b")+
    row("Core ("+S.cw+"×"+S.ch+"×"+S.ct+" mm)",core.toFixed(3)+" psi")+
    bar(core,mx,"#4ea3ff")+
    row("End tanks",tank.toFixed(3)+" psi")+bar(tank,mx,"#ffb347")+
    row("Cold pipe ("+dc.toFixed(2)+" in, "+lc.toFixed(1)+" m, "+nc+" bends)",pCold.toFixed(3)+" psi")+
    bar(pCold,mx,"#38d39f")+
    '<div style="height:10px"></div>'+
    row("<b>TOTAL &Delta;P</b>",tot.toFixed(2)+" psi",tot<1.5?"hi":(tot<2.5?"wa":"ba"))+
    row("As % of boost",pct.toFixed(1)+" %",pct<7?"hi":(pct<12?"wa":"ba"))+
    row("Required PR rises to",pr2.toFixed(3))+
    row("Compressor outlet penalty","+"+(tc2-S.tc).toFixed(1)+" &deg;C")+
    row("Post-cooler IAT penalty","+"+(iat2-S.iat).toFixed(2)+" &deg;C","hi")+
    '<p class="note" style="margin-top:10px">Target is &le; 1.5 psi. Note how small the IAT penalty '+
    'is even at high &Delta;P — the real cost is compressor map position and shaft speed, not heat.</p>';
  drawDp();
}
function drawDp(){
  var W=780,H=300,L=54,Rr=24,T=16,B=38;
  var s=svg(W,H);
  var qLo=0,qHi=900,dLo=0,dHi=2.0;
  gridY(s,L,W,Rr,T,H,B,8,function(v){return v.toFixed(2);},dLo,dHi);
  gridX(s,L,W,Rr,T,H,B,6,function(v){return v.toFixed(0);},qLo,qHi);
  function px(q){return L+(W-Rr-L)*(q-qLo)/(qHi-qLo);}
  function py(d){return T+(H-B-T)*(1-(Math.max(dLo,Math.min(dHi,d))-dLo)/(dHi-dLo));}
  function curve(k,col,dash){
    var p=[]; for(var q=0;q<=qHi;q+=15) p.push([px(q),py(k*q*q)]);
    path(s,p,col,2.3,dash);
  }
  curve(1.5/(1142*1142)*1.25,"#4ea3ff");                 // B&P 3 in
  curve(1.5/(1142*1142)*1.10,"#38d39f");                 // tube&fin 3 in (~12% lower)
  curve(1.5/(1142*1142)*0.82,"#ffb347");                 // B&P 4.5 in (more area)
  var ux=px(S.cfm);
  el(s,"line",{x1:ux,y1:T,x2:ux,y2:H-B,stroke:"#ff6b6b","stroke-width":1.4,"stroke-dasharray":"4 3"});
  txt(s,ux+7,T+14,"Your peak flow "+S.cfm.toFixed(0)+" CFM",{fill:"#ff6b6b","font-size":11,"font-weight":600});
  txt(s,ux+7,T+29,"← all cores are trivially unrestrictive here",{fill:"#6f8098","font-size":10.5});
  axes(s,L,Rr,T,B,W,H,"Charge air flow, CFM","Core ΔP, psi");
  mount("ch_dp",s);
}

/* ---- FPI chart ---- */

/* ============ FPI chart ============ */
function drawFpi(){
  var W=780,H=300,L=54,Rr=24,T=16,B=38;
  var s=svg(W,H);
  var fLo=8,fHi=24,yLo=0.4,yHi=1.7;
  gridY(s,L,W,Rr,T,H,B,6,function(v){return v.toFixed(2);},yLo,yHi);
  gridX(s,L,W,Rr,T,H,B,8,function(v){return v.toFixed(0);},fLo,fHi);
  function px(f){return L+(W-Rr-L)*(f-fLo)/(fHi-fLo);}
  function py(y){return T+(H-B-T)*(1-(Math.max(yLo,Math.min(yHi,y))-yLo)/(yHi-yLo));}
  var pq=[],pd=[],pr=[];
  for(var f=fLo;f<=fHi;f+=0.25){
    var q=Math.pow(f/16,0.55), d=Math.pow(f/16,1.05);
    pq.push([px(f),py(q)]); pd.push([px(f),py(d)]); pr.push([px(f),py(q/d)]);
  }
  path(s,pq,"#38d39f",2.4); path(s,pd,"#ff6b6b",2.4); path(s,pr,"#4ea3ff",2.4,"5 4");
  // recommended band 14-16
  el(s,"rect",{x:px(14),y:T,width:px(16)-px(14),height:H-B-T,fill:"#38d39f","fill-opacity":0.10});
  txt(s,px(15),T+14,"14–16 FPI",{fill:"#38d39f","font-size":11,"font-weight":600,"text-anchor":"middle"});
  txt(s,px(15),T+27,"recommended",{fill:"#38d39f","font-size":9.5,"text-anchor":"middle"});
  el(s,"line",{x1:px(12),y1:T,x2:px(12),y2:H-B,stroke:"#6f8098","stroke-width":1.2,"stroke-dasharray":"3 4"});
  txt(s,px(12)-6,H-B-8,"Q/ΔP peak ≈12",{fill:"#9fb0c4","font-size":10,"text-anchor":"end"});
  axes(s,L,Rr,T,B,W,H,"Fins per inch (external)","Relative, normalised to 16 FPI = 1.0");
  mount("ch_fpi",s);
}

/* ---- end tank flow diagrams ---- */

/* ============ end tank flow-distribution diagrams ============ */
function tankDiag(id,mode){
  var W=300,H=170;
  var s=svg(W,H);
  var cx=70,cy=28,cw=170,chh=112;   // core rect
  el(s,"rect",{x:cx,y:cy,width:cw,height:chh,fill:"#151a22",stroke:"#3a4757","stroke-width":1.2,rx:2});
  var nT=9, flows=[];
  for(var i=0;i<nT;i++){
    var f;
    if(mode=="top")  f=0.25+1.25*Math.pow(i/(nT-1),1.6);
    if(mode=="ctr")  f=0.35+1.10*Math.exp(-Math.pow((i-(nT-1)/2)/1.6,2));
    if(mode=="side") f=0.92+0.16*Math.sin(i*1.1);
    flows.push(f);
  }
  var mx=Math.max.apply(null,flows);
  for(var i=0;i<nT;i++){
    var y=cy+6+(chh-12)*i/(nT-1);
    var f=flows[i]/mx;
    var col = f>0.8?"#38d39f":(f>0.55?"#ffb347":"#ff6b6b");
    el(s,"line",{x1:cx+4,y1:y,x2:cx+cw-4,y2:y,stroke:col,"stroke-width":1+4.5*f,
                 "stroke-opacity":0.85,"stroke-linecap":"round"});
  }
  // tanks
  if(mode=="top"){
    el(s,"path",{d:"M"+cx+" "+cy+" L"+(cx+cw)+" "+cy+" L"+(cx+cw)+" "+(cy-16)+" L"+cx+" "+(cy-16)+" Z",
      fill:"#212936",stroke:"#3a4757"});
    el(s,"line",{x1:cx+22,y1:cy-30,x2:cx+22,y2:cy-16,stroke:"#4ea3ff","stroke-width":7,"stroke-linecap":"round"});
    txt(s,cx+22,cy-36,"IN",{fill:"#4ea3ff","font-size":10,"text-anchor":"middle"});
  } else if(mode=="ctr"){
    el(s,"path",{d:"M"+cx+" "+cy+" L"+cx+" "+(cy+chh)+" L"+(cx-24)+" "+(cy+chh)+" L"+(cx-24)+" "+cy+" Z",
      fill:"#212936",stroke:"#3a4757"});
    el(s,"line",{x1:cx-46,y1:cy+chh/2,x2:cx-24,y2:cy+chh/2,stroke:"#4ea3ff","stroke-width":8,"stroke-linecap":"round"});
    txt(s,cx-46,cy+chh/2-11,"IN",{fill:"#4ea3ff","font-size":10,"text-anchor":"middle"});
  } else {
    el(s,"path",{d:"M"+cx+" "+cy+" L"+cx+" "+(cy+chh)+" L"+(cx-30)+" "+(cy+chh)+" L"+(cx-12)+" "+cy+" Z",
      fill:"#16302a",stroke:"#38d39f"});
    el(s,"line",{x1:cx-52,y1:cy+chh-10,x2:cx-30,y2:cy+chh-10,stroke:"#38d39f","stroke-width":8,"stroke-linecap":"round"});
    txt(s,cx-40,cy+chh+13,"IN",{fill:"#38d39f","font-size":10,"text-anchor":"middle"});
    el(s,"path",{d:"M"+(cx+cw)+" "+cy+" L"+(cx+cw)+" "+(cy+chh)+" L"+(cx+cw+12)+" "+(cy+chh)+" L"+(cx+cw+30)+" "+cy+" Z",
      fill:"#16302a",stroke:"#38d39f"});
    el(s,"line",{x1:cx+cw+30,y1:cy+8,x2:cx+cw+52,y2:cy+8,stroke:"#38d39f","stroke-width":8,"stroke-linecap":"round"});
    txt(s,cx+cw+40,cy-2,"OUT",{fill:"#38d39f","font-size":10,"text-anchor":"middle"});
    el(s,"line",{x1:cx-21,y1:cy+chh-4,x2:cx-6,y2:cy+22,stroke:"#9fb0c4","stroke-width":1.6,"stroke-dasharray":"3 2"});
    txt(s,cx-2,cy+18,"vane",{fill:"#9fb0c4","font-size":8.5});
  }
  txt(s,cx+cw/2,cy+chh+22,"tube flow: thicker = more",{fill:"#6f8098","font-size":9.5,"text-anchor":"middle"});
  mount(id,s);
}

/* ---- ducting diagram ---- */

/* ============ ducting diagram ============ */
function drawDuct(){
  var W=780,H=290;
  var s=svg(W,H);
  var g=el(s,"g",{});
  // core
  el(g,"rect",{x:470,y:60,width:52,height:170,fill:"#1c2836",stroke:"#4ea3ff","stroke-width":2});
  for(var i=0;i<11;i++)
    el(g,"line",{x1:470,y1:64+16*i,x2:522,y2:64+16*i,stroke:"#2c3542","stroke-width":1});
  txt(g,496,252,"CORE 610 × 300 × 75",{fill:"#4ea3ff","font-size":11,"text-anchor":"middle","font-weight":600});
  // duct walls
  el(g,"path",{d:"M180 105 L470 60",stroke:"#38d39f","stroke-width":2.5,fill:"none"});
  el(g,"path",{d:"M180 185 L470 230",stroke:"#38d39f","stroke-width":2.5,fill:"none"});
  el(g,"line",{x1:180,y1:105,x2:180,y2:185,stroke:"#38d39f","stroke-width":3});
  // seals
  [[470,60],[470,230]].forEach(function(p){
    el(g,"circle",{cx:p[0],cy:p[1],r:5,fill:"none",stroke:"#ffb347","stroke-width":2});
  });
  txt(g,540,54,"SEAL all 4 edges",{fill:"#ffb347","font-size":11,"font-weight":600});
  el(g,"line",{x1:536,y1:50,x2:478,y2:60,stroke:"#ffb347","stroke-width":1,"stroke-dasharray":"3 2"});
  // splitter vane
  el(g,"path",{d:"M300 145 L470 145",stroke:"#9fb0c4","stroke-width":1.6,"stroke-dasharray":"5 3"});
  txt(g,330,139,"splitter vane (if length-limited)",{fill:"#9fb0c4","font-size":10});
  // arrowhead helper (explicit polygons — no marker dependency)
  function arrow(x1,y,x2,col,w){
    el(g,"line",{x1:x1,y1:y,x2:x2-7,y2:y,stroke:col,"stroke-width":w||1.8});
    el(g,"path",{d:"M"+(x2-7)+" "+(y-4)+" L"+x2+" "+y+" L"+(x2-7)+" "+(y+4)+" Z",fill:col});
  }
  // ram air arrows
  for(var i=0;i<5;i++) arrow(84,110+18*i,166,"#4ea3ff");
  txt(g,84,96,"RAM AIR",{fill:"#4ea3ff","font-size":11,"font-weight":600});
  // mouth dimension
  el(g,"line",{x1:170,y1:105,x2:170,y2:185,stroke:"#ffb347","stroke-width":1});
  el(g,"line",{x1:165,y1:105,x2:175,y2:105,stroke:"#ffb347"});
  el(g,"line",{x1:165,y1:185,x2:175,y2:185,stroke:"#ffb347"});
  txt(g,84,206,"MOUTH — 50–70% of core face area",{fill:"#ffb347","font-size":10});
  // core height dimension
  el(g,"line",{x1:534,y1:60,x2:534,y2:230,stroke:"#4ea3ff","stroke-width":1});
  el(g,"line",{x1:529,y1:60,x2:539,y2:60,stroke:"#4ea3ff"});
  el(g,"line",{x1:529,y1:230,x2:539,y2:230,stroke:"#4ea3ff"});
  txt(g,542,55,"300 mm core height",{fill:"#4ea3ff","font-size":10});
  // angle callout
  el(g,"path",{d:"M236 92 A 62 62 0 0 1 248 80",fill:"none",stroke:"#ff6b6b","stroke-width":1.4});
  el(g,"line",{x1:180,y1:105,x2:460,y2:105,stroke:"#3a4757","stroke-width":1,"stroke-dasharray":"4 3"});
  txt(g,256,88,"≤ 7° per wall  (≤ 14° total included)",{fill:"#ff6b6b","font-size":11,"font-weight":600});
  txt(g,256,101,"beyond ~15° total the flow separates and you lose pressure recovery",
      {fill:"#6f8098","font-size":9.5});
  // exit
  arrow(540,148,606,"#ffb347");
  txt(g,614,144,"heated air → condenser → radiator",{fill:"#ffb347","font-size":10.5});
  txt(g,614,158,"MUST have an exit path from the bay",{fill:"#ff6b6b","font-size":10});
  txt(g,20,24,"DUCT GEOMETRY — plan view",{fill:"#e6edf5","font-size":12.5,"font-weight":600});
  txt(g,20,272,"Sealing all four edges is worth more than any core upgrade in this report.",
      {fill:"#38d39f","font-size":11,"font-weight":600});
  mount("duct_svg",s);
}

/* ---- control wiring ---- */

/* ============ wiring ============ */
function bindAll(){
  ["boost","rpm","ve","tamb","eta","alt","disp","cw","ch","ct","vf"].forEach(function(k){
    var e=C("i_"+k); if(e) e.addEventListener("input",renderCore);
  });
  ["dh","lh","nh","dc","lc","nc","tank"].forEach(function(k){
    var e=C("i_"+k); if(e) e.addEventListener("input",renderDp);
  });
  var btns=document.querySelectorAll(".tabbar button");
  Array.prototype.forEach.call(btns,function(b){
    b.addEventListener("click",function(){
      Array.prototype.forEach.call(btns,function(x){x.classList.remove("on");});
      Array.prototype.forEach.call(document.querySelectorAll(".tabpane"),function(p){p.classList.remove("on");});
      b.classList.add("on");
      var p=C(b.dataset.tab); if(p) p.classList.add("on");
      renderCore();
    });
  });
}

/* ---- official BorgWarner map + community data (round four) ---- */

var R4={"const":{"disp":2188.8,"pamb":93.87,"tamb":32.0,"hp":10.0,"dt_lo":0.78,"dt":0.8,"dt_hi":0.83,"rodratio":1.516,"rpm_stock":7000.0,"rpm_max":8000.0,"tb_bore":74.5,"plenum_flange":76.2},"hero":{"rpm":7500,"boost":30,"lb":51.4,"whp":411,"whp_lo":401,"whp_hi":427,"crank":514,"iat":69.6,"pr":3.42,"tc":214,"eps":0.793,"choke":85.7},"rpmRange":[{"rpm":6600,"mps":20.0,"Z":0.463,"ve":0.967,"lb":47.69,"iat":65.1,"whp_lo":372,"whp_mid":382,"whp_hi":396,"cfm":61.7,"choke":79.5,"risk":""},{"rpm":6800,"mps":20.6,"Z":0.476,"ve":0.965,"lb":48.85,"iat":66.5,"whp_lo":381,"whp_mid":391,"whp_hi":405,"cfm":63.4,"choke":81.4,"risk":""},{"rpm":7000,"mps":21.2,"Z":0.489,"ve":0.963,"lb":49.98,"iat":67.9,"whp_lo":390,"whp_mid":400,"whp_hi":415,"cfm":65.2,"choke":83.3,"risk":"stock redline. Nothing is stressed. Stock valve springs fine."},{"rpm":7200,"mps":21.8,"Z":0.502,"ve":0.958,"lb":50.95,"iat":69.1,"whp_lo":397,"whp_mid":408,"whp_hi":423,"cfm":66.7,"choke":84.9,"risk":"+200 rpm. Within stock spring capability. No parts needed."},{"rpm":7400,"mps":22.4,"Z":0.516,"ve":0.939,"lb":51.27,"iat":69.5,"whp_lo":400,"whp_mid":410,"whp_hi":426,"cfm":67.1,"choke":85.4,"risk":"approaching reported stock spring float (7,500-7,600)."},{"rpm":7500,"mps":22.8,"Z":0.523,"ve":0.929,"lb":51.4,"iat":69.6,"whp_lo":401,"whp_mid":411,"whp_hi":427,"cfm":67.3,"choke":85.7,"risk":"outer limit on stock springs. Fit upgraded springs to be safe."},{"rpm":7600,"mps":23.1,"Z":0.53,"ve":0.92,"lb":51.51,"iat":69.8,"whp_lo":402,"whp_mid":412,"whp_hi":428,"cfm":67.5,"choke":85.9,"risk":"upgraded valve springs REQUIRED. Service interval shortens."},{"rpm":7800,"mps":23.7,"Z":0.543,"ve":0.9,"lb":51.7,"iat":70.0,"whp_lo":403,"whp_mid":414,"whp_hi":429,"cfm":67.8,"choke":86.2,"risk":"race territory. 23.7 m/s piston speed on a 1.52 rod ratio."},{"rpm":8000,"mps":24.3,"Z":0.557,"ve":0.88,"lb":51.82,"iat":70.1,"whp_lo":404,"whp_mid":415,"whp_hi":430,"cfm":68.0,"choke":86.4,"risk":"24.3 m/s. Buys 4 whp over 7,500. Bearing and rod life is the cost."}],"ladder":[{"rpm":7000,"boost":20,"pr":2.66,"lb":40.49,"choke":67.5,"iat":50.4,"whp_lo":316,"whp":324,"whp_hi":336,"eta_off":0.701},{"rpm":7000,"boost":25,"pr":3.04,"lb":45.44,"choke":75.7,"iat":58.9,"whp_lo":354,"whp":364,"whp_hi":377,"eta_off":0.7},{"rpm":7000,"boost":28,"pr":3.26,"lb":48.2,"choke":80.3,"iat":64.2,"whp_lo":376,"whp":386,"whp_hi":400,"eta_off":0.698},{"rpm":7000,"boost":30,"pr":3.42,"lb":49.98,"choke":83.3,"iat":67.9,"whp_lo":390,"whp":400,"whp_hi":415,"eta_off":0.696},{"rpm":7000,"boost":32,"pr":3.57,"lb":51.71,"choke":86.2,"iat":71.6,"whp_lo":403,"whp":414,"whp_hi":429,"eta_off":0.694},{"rpm":7000,"boost":34,"pr":3.72,"lb":53.39,"choke":89.0,"iat":75.3,"whp_lo":416,"whp":427,"whp_hi":443,"eta_off":0.691},{"rpm":7500,"boost":20,"pr":2.66,"lb":41.09,"choke":68.5,"iat":51.0,"whp_lo":321,"whp":329,"whp_hi":341,"eta_off":0.7},{"rpm":7500,"boost":25,"pr":3.04,"lb":46.37,"choke":77.3,"iat":59.9,"whp_lo":362,"whp":371,"whp_hi":385,"eta_off":0.698},{"rpm":7500,"boost":28,"pr":3.26,"lb":49.42,"choke":82.4,"iat":65.7,"whp_lo":385,"whp":395,"whp_hi":410,"eta_off":0.695},{"rpm":7500,"boost":30,"pr":3.42,"lb":51.4,"choke":85.7,"iat":69.6,"whp_lo":401,"whp":411,"whp_hi":427,"eta_off":0.693},{"rpm":7500,"boost":32,"pr":3.57,"lb":53.34,"choke":88.9,"iat":73.6,"whp_lo":416,"whp":427,"whp_hi":443,"eta_off":0.69},{"rpm":7500,"boost":34,"pr":3.72,"lb":55.25,"choke":92.1,"iat":77.7,"whp_lo":431,"whp":442,"whp_hi":459,"eta_off":0.687},{"rpm":8000,"boost":20,"pr":2.66,"lb":41.35,"choke":68.9,"iat":51.3,"whp_lo":323,"whp":331,"whp_hi":343,"eta_off":0.7},{"rpm":8000,"boost":25,"pr":3.04,"lb":46.71,"choke":77.9,"iat":60.3,"whp_lo":364,"whp":374,"whp_hi":388,"eta_off":0.697},{"rpm":8000,"boost":28,"pr":3.26,"lb":49.81,"choke":83.0,"iat":66.1,"whp_lo":388,"whp":398,"whp_hi":413,"eta_off":0.694},{"rpm":8000,"boost":30,"pr":3.42,"lb":51.82,"choke":86.4,"iat":70.1,"whp_lo":404,"whp":415,"whp_hi":430,"eta_off":0.692},{"rpm":8000,"boost":32,"pr":3.57,"lb":53.8,"choke":89.7,"iat":74.2,"whp_lo":420,"whp":430,"whp_hi":447,"eta_off":0.689},{"rpm":8000,"boost":34,"pr":3.72,"lb":55.74,"choke":92.9,"iat":78.3,"whp_lo":435,"whp":446,"whp_hi":463,"eta_off":0.686}],"cores":[{"k":"610x305x76","label":"610 x 305 x 76 (24x12x3)","vol":14.1,"vf":7.81,"eps":0.742,"iat":78.8,"iatF":174,"whp":404,"whp_lo":394,"whp_hi":419,"dTrad_raw":33.1,"dt_ic":28.0,"dt_cond":3.2,"t_rad_in":63.3,"head":41.7,"head_pct":57.1,"mass":4.2,"w":610.0,"h":305.0,"t":76.0,"depth_need":111},{"k":"610x305x102","label":"610 x 305 x 102 (24x12x4)","vol":19.0,"vf":6.84,"eps":0.793,"iat":69.6,"iatF":157,"whp":411,"whp_lo":401,"whp_hi":427,"dTrad_raw":41.1,"dt_ic":34.8,"dt_cond":3.7,"t_rad_in":70.5,"head":34.5,"head_pct":47.2,"mass":5.7,"w":610.0,"h":305.0,"t":102.0,"depth_need":137},{"k":"610x305x114","label":"610 x 305 x 114 (24x12x4.5)","vol":21.2,"vf":6.51,"eps":0.81,"iat":66.6,"iatF":152,"whp":414,"whp_lo":403,"whp_hi":429,"dTrad_raw":44.3,"dt_ic":37.6,"dt_cond":3.9,"t_rad_in":73.5,"head":31.5,"head_pct":43.2,"mass":6.4,"w":610.0,"h":305.0,"t":114.0,"depth_need":149},{"k":"685x305x76","label":"685 x 305 x 76 (27x12x3)","vol":15.9,"vf":6.95,"eps":0.758,"iat":76.0,"iatF":169,"whp":406,"whp_lo":396,"whp_hi":421,"dTrad_raw":34.0,"dt_ic":28.8,"dt_cond":3.2,"t_rad_in":64.0,"head":41.0,"head_pct":56.1,"mass":4.8,"w":685.0,"h":305.0,"t":76.0,"depth_need":111},{"k":"685x305x102","label":"685 x 305 x 102 (27x12x4)","vol":21.3,"vf":6.09,"eps":0.807,"iat":67.1,"iatF":153,"whp":413,"whp_lo":403,"whp_hi":429,"dTrad_raw":42.0,"dt_ic":35.6,"dt_cond":3.7,"t_rad_in":71.3,"head":33.7,"head_pct":46.2,"mass":6.4,"w":685.0,"h":305.0,"t":102.0,"depth_need":137},{"k":"685x340x102","label":"685 x 340 x 102 (27x13.4x4)","vol":23.8,"vf":5.47,"eps":0.819,"iat":64.9,"iatF":149,"whp":415,"whp_lo":405,"whp_hi":431,"dTrad_raw":42.8,"dt_ic":36.3,"dt_cond":3.7,"t_rad_in":72.0,"head":33.0,"head_pct":45.2,"mass":7.1,"w":685.0,"h":340.0,"t":102.0,"depth_need":137},{"k":"711x305x102","label":"711 x 305 x 102 (28x12x4) - the ESTIMATE","vol":22.1,"vf":5.87,"eps":0.811,"iat":66.4,"iatF":151,"whp":414,"whp_lo":403,"whp_hi":429,"dTrad_raw":42.3,"dt_ic":35.8,"dt_cond":3.7,"t_rad_in":71.5,"head":33.5,"head_pct":45.9,"mass":6.6,"w":711.0,"h":305.0,"t":102.0,"depth_need":137}],"pipes":[{"od":2.0,"id_mm":47.5,"hot_fts":323,"hot_dp":1.666,"hot_mach":0.223,"cold_fts":233,"cold_dp":1.619,"cold_mach":0.192,"vol_per_m":1.77,"sysL":11.02,"sysX":5.03,"fill_ms":151},{"od":2.25,"id_mm":53.8,"hot_fts":252,"hot_dp":0.957,"hot_mach":0.173,"cold_fts":181,"cold_dp":0.929,"cold_mach":0.149,"vol_per_m":2.28,"sysL":12.33,"sysX":5.64,"fill_ms":168},{"od":2.5,"id_mm":60.2,"hot_fts":201,"hot_dp":0.586,"hot_mach":0.139,"cold_fts":145,"cold_dp":0.569,"cold_mach":0.119,"vol_per_m":2.85,"sysL":13.81,"sysX":6.31,"fill_ms":188},{"od":2.75,"id_mm":66.5,"hot_fts":165,"hot_dp":0.378,"hot_mach":0.113,"cold_fts":119,"cold_dp":0.367,"cold_mach":0.098,"vol_per_m":3.48,"sysL":15.46,"sysX":7.06,"fill_ms":210},{"od":3.0,"id_mm":72.9,"hot_fts":137,"hot_dp":0.255,"hot_mach":0.095,"cold_fts":99,"cold_dp":0.247,"cold_mach":0.081,"vol_per_m":4.17,"sysL":17.27,"sysX":7.89,"fill_ms":234}],"tb":{"bore":74.5,"adapter":76.2,"plenum":76.2,"plate":[109.0,105.0],"v":28.9,"vfts":95,"mach":0.078,"dp_psi":0.0467,"dp_pa":322.0,"cap_lbmin":198,"cap_hp":1980,"step_in_k":0.01853,"step_in_pa":21.8,"step_out_k":0.00195,"step_out_pa":2.5,"step_psi":0.00353,"step_pct":0.24},"tbRange":[{"rpm":7000,"boost":30,"lb":49.98,"v":28.0,"vfts":92,"mach":0.076,"dp_psi":0.0439,"used":25.2},{"rpm":7000,"boost":34,"lb":53.39,"v":28.0,"vfts":92,"mach":0.075,"dp_psi":0.047,"used":24.9},{"rpm":7500,"boost":30,"lb":51.4,"v":28.9,"vfts":95,"mach":0.078,"dp_psi":0.0467,"used":26.0},{"rpm":7500,"boost":34,"lb":55.25,"v":29.1,"vfts":96,"mach":0.078,"dp_psi":0.0506,"used":25.9},{"rpm":8000,"boost":30,"lb":51.82,"v":29.2,"vfts":96,"mach":0.079,"dp_psi":0.0475,"used":26.2},{"rpm":8000,"boost":34,"lb":55.74,"v":29.5,"vfts":97,"mach":0.078,"dp_psi":0.0516,"used":26.1}],"coldLayouts":[{"lab":"2.50 in run, welded cone to 3.00 last 150 mm","vmax":145,"dp":0.591,"vol":4.47,"sysL":14.01,"sysX":6.4,"fill_ms":191,"box":127},{"lab":"2.75 in run, welded cone to 3.00 last 150 mm","vmax":119,"dp":0.376,"vol":5.32,"sysL":14.87,"sysX":6.79,"fill_ms":203,"box":140},{"lab":"3.00 in the whole 1.5 m","vmax":99,"dp":0.247,"vol":6.26,"sysL":15.8,"sysX":7.22,"fill_ms":216,"box":152},{"lab":"2.25 in run, welded cone to 3.00 last 150 mm","vmax":181,"dp":0.971,"vol":3.7,"sysL":13.24,"sysX":6.05,"fill_ms":180,"box":114}],"coldTransitions":{"cone":0.0352,"sudden":0.0443,"cone_pa":242.5,"sudden_pa":305.7},"routing":[{"od":2.25,"id_mm":53.8,"bare":57.1,"clamped":75.1,"clr":86,"box":114},{"od":2.5,"id_mm":60.2,"bare":63.5,"clamped":81.5,"clr":95,"box":127},{"od":2.75,"id_mm":66.5,"bare":69.8,"clamped":87.8,"clr":105,"box":140},{"od":3.0,"id_mm":72.9,"bare":76.2,"clamped":94.2,"clr":114,"box":152}],"routingDeltaBox":25,"hotLayouts":[{"od":2.25,"fts":252,"band":"in band","dp":0.957,"vol":2.51},{"od":2.5,"fts":201,"band":"in band","dp":0.586,"vol":3.13},{"od":2.75,"fts":165,"band":"below band","dp":0.378,"vol":3.83},{"od":3.0,"fts":137,"band":"below band","dp":0.255,"vol":4.59}],"budget":{"rows":[["hot pipe, 2.50 in, 1.1 m, 3 bends",0.586],["intercooler core, 610x305x102",0.18],["end tanks, fabricated tapered, 2.50 in ports",0.35],["cold pipe, 2.50 in, 1.35 m, 4 bends",0.547],["welded 2.50 -> 3.00 cone + 150 mm of 3.00",0.044],["throttle body, 74.5 mm at WOT",0.047],["the two 1.7 mm steps at the throttle",0.004]],"total":1.757,"pct":5.9,"sysL":14.01,"sysX":6.4,"fill_ms":191,"vs3in":{"dp3":1.413,"dpr":0.0261,"dtc":1.34,"diat":0.28,"dwhp":0.1}},"stack":[{"t":76,"gap_lo":203,"gap_hi":254,"after_lo":183,"after_hi":234},{"t":102,"gap_lo":177,"gap_hi":228,"after_lo":157,"after_hi":208},{"t":114,"gap_lo":165,"gap_hi":216,"after_lo":145,"after_hi":196}],"duty":[{"lab":"sustained WOT climb, 100 km/h","rpm":7000,"boost":30.0,"q_ic":55.4,"t_rad_in":70.0,"q_bare":28.5,"q_stack":12.6,"lost_pct":55.8},{"lab":"part throttle recovery, 100 km/h","rpm":3000,"boost":5.0,"q_ic":4.2,"t_rad_in":38.3,"q_bare":28.5,"q_stack":25.9,"lost_pct":9.2},{"lab":"cruise, no boost, 100 km/h","rpm":2500,"boost":0.0,"q_ic":0.8,"t_rad_in":36.2,"q_bare":28.5,"q_stack":26.7,"lost_pct":6.2}],"driveline":{"band":[{"f":0.78,"loss":22.0,"whp":401,"case":"worst credible AWD loss, plate LSD dragging"},{"f":0.8,"loss":20.0,"whp":411,"case":"round three baseline, unchanged by the upgrades"},{"f":0.81,"loss":19.0,"whp":416,"case":"rebuilt trans + 1-pc CF shaft, helical LSD"},{"f":0.83,"loss":17.0,"whp":427,"case":"best credible; needs a coast-down to justify"}],"dyno_gain":2.6,"lb":51.4},"community":[{"what":"Ford Focus ST 2.0 EcoBoost, EFR 7163, E85 (ZZP)","disp":2.0,"whp":480,"fuel":"E85","boost":null,"drive":"FWD","dyno":"not stated","lb_implied":null,"note":"vendor claim reported on focusst.org; boost not stated","per_l":240.0},{"what":"Evo 9 2.3 built, EFR 7163, E85, 36 psi (Driven Fab)","disp":2.3,"whp":593,"fuel":"E85","boost":36,"drive":"AWD","dyno":"Dynojet","note":"ran out of injector before running out of turbo; Dynojet AWD","per_l":257.8},{"what":"Mazda BP 1.8, EFR 7163, E85","disp":1.8,"whp":450,"fuel":"E85","boost":null,"drive":"RWD","dyno":"not stated","note":"miataturbo.net, reported as routine rather than a peak","per_l":250.0},{"what":"3S-GTE, EFR 7163, E85, 25 psi","disp":2.0,"whp":402,"fuel":"E85","boost":25,"drive":"not stated","dyno":"Mainline (steady state)","note":"300 kW at the wheels; the closest single comparable to this build","per_l":201.0},{"what":"3S-GTE Gen 3 in AE86, 20 psi, 93 octane","disp":2.0,"whp":402,"fuel":"93","boost":20,"drive":"RWD","dyno":"not stated","note":"pump fuel, RWD - shows what the head and cams support","per_l":201.0},{"what":"ST185 3S-GTE, .50 turbo, 14 psi, 91 octane (EricGT4)","disp":2.0,"whp":337,"fuel":"91","boost":14,"drive":"AWD","dyno":"Dynojet","note":"same chassis and drivetrain as this car - the best AWD-loss anchor","per_l":168.5},{"what":"Stock ST185 3S-GTE","disp":2.0,"whp":190,"fuel":"91","boost":9,"drive":"AWD","dyno":"Dynojet","note":"against a 225 PS JDM crank rating - implies ~15%, but JDM ratings of that era are not measured to a comparable standard","per_l":95.0},{"what":"5S-GTE high compression, Precision 6262 (mr2man)","disp":2.2,"whp":700,"fuel":"E85/race","boost":null,"drive":"RWD","dyno":"not stated","note":"same displacement class - shows the block is not the ceiling","per_l":318.2}],"officialPoints":[{"rpm":7000,"boost":30,"lb":49.98,"pr":3.416,"eta_model":0.706,"eta_official":0.696,"surge":20.9,"choke":60.0,"surge_margin":29.1,"choke_margin":10.0},{"rpm":7500,"boost":30,"lb":51.4,"pr":3.416,"eta_model":0.706,"eta_official":0.693,"surge":20.9,"choke":60.0,"surge_margin":30.5,"choke_margin":8.6},{"rpm":7500,"boost":32,"lb":53.34,"pr":3.568,"eta_model":0.706,"eta_official":0.69,"surge":23.2,"choke":58.4,"surge_margin":30.1,"choke_margin":5.0},{"rpm":7500,"boost":34,"lb":55.25,"pr":3.719,"eta_model":0.706,"eta_official":0.687,"surge":25.5,"choke":57.2,"surge_margin":29.7,"choke_margin":1.9},{"rpm":8000,"boost":30,"lb":51.82,"pr":3.416,"eta_model":0.706,"eta_official":0.692,"surge":20.9,"choke":60.0,"surge_margin":31.0,"choke_margin":8.2}],"officialSolved":[{"rpm":7000,"eta":0.696,"tc":216,"iat":68.3,"whp":399,"whp_lo":389,"whp_hi":414,"lb":49.91,"d_whp":-1,"d_iat":0.4},{"rpm":7200,"eta":0.694,"tc":217,"iat":69.7,"whp":407,"whp_lo":397,"whp_hi":422,"lb":50.9,"d_whp":0,"d_iat":0.6},{"rpm":7500,"eta":0.693,"tc":217,"iat":70.3,"whp":411,"whp_lo":400,"whp_hi":426,"lb":51.34,"d_whp":0,"d_iat":0.6},{"rpm":8000,"eta":0.692,"tc":217,"iat":70.8,"whp":414,"whp_lo":404,"whp_hi":430,"lb":51.76,"d_whp":-1,"d_iat":0.7}],"surgeSweep":[{"rpm":2500,"lb":18.91,"pr":3.42,"surge":20.9,"margin":-1.9},{"rpm":2750,"lb":20.89,"pr":3.42,"surge":20.9,"margin":0.0},{"rpm":3000,"lb":22.85,"pr":3.42,"surge":20.9,"margin":2.0},{"rpm":3250,"lb":24.79,"pr":3.42,"surge":20.9,"margin":3.9},{"rpm":3500,"lb":26.71,"pr":3.42,"surge":20.9,"margin":5.9},{"rpm":3750,"lb":28.59,"pr":3.42,"surge":20.9,"margin":7.7},{"rpm":4000,"lb":30.45,"pr":3.42,"surge":20.9,"margin":9.6},{"rpm":4250,"lb":32.27,"pr":3.42,"surge":20.9,"margin":11.4},{"rpm":4500,"lb":34.06,"pr":3.42,"surge":20.9,"margin":13.2},{"rpm":4750,"lb":35.82,"pr":3.42,"surge":20.9,"margin":15.0},{"rpm":5000,"lb":37.54,"pr":3.42,"surge":20.9,"margin":16.7}],"radPenalty":{"d_rad_in":7.2,"pct_head":9.9,"shadow_pct":84,"entrain":1.18},"etaRms":0.021,"pairing":[{"lab":"AS BUILT / CORRECT   1+4 / 2+3","vals":[-96.0,-96.0]},{"lab":"the superseded diagram 1+2 / 3+4","vals":[84.0,84.0]}],"windows":{"1":[135.0,399.0],"2":[675.0,219.0],"3":[315.0,579.0],"4":[495.0,39.0]},"bp":[{"emap":1.0,"ve":0.96,"lb":52.81,"whp":423},{"emap":1.3,"ve":0.945,"lb":52.11,"whp":417},{"emap":1.6,"ve":0.929,"lb":51.4,"whp":411},{"emap":1.9,"ve":0.914,"lb":50.69,"whp":406},{"emap":2.2,"ve":0.899,"lb":49.98,"whp":400}],"modelPerL":187.9,"rad":{"part":"Mishimoto MMRAD-CEL-89","overall_mm":[714,439,64.5],"core_mm":[699,318,51.8],"rows":2,"port_in":1.25},"curves":{"rpm":[3000,3050,3100,3150,3200,3250,3300,3350,3400,3450,3500,3550,3600,3650,3700,3750,3800,3850,3900,3950,4000,4050,4100,4150,4200,4250,4300,4350,4400,4450,4500,4550,4600,4650,4700,4750,4800,4850,4900,4950,5000,5050,5100,5150,5200,5250,5300,5350,5400,5450,5500,5550,5600,5650,5700,5750,5800,5850,5900,5950,6000,6050,6100,6150,6200,6250,6300,6350,6400,6450,6500,6550,6600,6650,6700,6750,6800,6850,6900,6950,7000,7050,7100,7150,7200,7250,7300,7350,7400,7450,7500,7550,7600,7650,7700,7750,7800,7850,7900,7950,8000,8050],"b20":[142.5,145.0,147.5,150.0,152.6,155.1,157.6,160.1,162.6,165.1,167.6,170.1,172.6,175.1,177.6,180.1,182.5,185.0,187.5,189.9,192.4,194.8,197.3,199.7,202.1,204.6,207.0,209.4,211.8,214.2,216.6,219.0,221.3,223.7,226.1,228.4,230.7,233.1,235.4,237.7,240.0,242.3,244.6,246.9,249.2,251.5,253.7,256.0,258.2,260.5,262.7,264.9,267.1,269.3,271.5,273.7,275.8,278.0,280.1,282.3,284.4,286.5,288.6,290.7,292.8,294.9,296.9,299.0,301.0,303.1,305.1,307.1,309.1,311.1,313.0,315.0,317.0,318.9,320.8,322.8,323.9,324.5,325.1,325.6,326.1,326.6,327.1,327.6,328.0,328.4,328.7,329.1,329.4,329.6,329.9,330.1,330.3,330.5,330.6,330.7,330.8,330.9],"b25":[162.9,165.8,168.6,171.4,174.3,177.1,179.9,182.7,185.5,188.3,191.1,193.9,196.7,199.4,202.2,204.9,207.7,210.4,213.2,215.9,218.6,221.3,224.0,226.7,229.4,232.1,234.7,237.4,240.1,242.7,245.3,247.9,250.6,253.2,255.8,258.3,260.9,263.5,266.0,268.6,271.1,273.6,276.2,278.7,281.2,283.6,286.1,288.6,291.0,293.5,295.9,298.3,300.7,303.1,305.5,307.9,310.3,312.6,315.0,317.3,319.6,321.9,324.2,326.5,328.8,331.1,333.3,335.6,337.8,340.0,342.2,344.4,346.6,348.7,350.9,353.0,355.2,357.3,359.4,361.5,363.5,365.6,366.7,367.3,367.9,368.5,369.1,369.6,370.1,370.6,371.0,371.4,371.8,372.1,372.4,372.7,373.0,373.2,373.4,373.6,373.7,373.8],"b30":[182.8,185.9,189.0,192.2,195.3,198.3,201.4,204.5,207.6,210.6,213.7,216.7,219.7,222.7,225.7,228.7,231.7,234.7,237.7,240.6,243.6,246.5,249.5,252.4,255.3,258.2,261.1,263.9,266.8,269.7,272.5,275.3,278.2,281.0,283.8,286.6,289.3,292.1,294.9,297.6,300.4,303.1,305.8,308.5,311.2,313.8,316.5,319.2,321.8,324.4,327.1,329.7,332.3,334.8,337.4,340.0,342.5,345.1,347.6,350.1,352.6,355.1,357.5,360.0,362.4,364.9,367.3,369.7,372.1,374.5,376.9,379.2,381.6,383.9,386.2,388.5,390.8,393.1,395.3,397.6,399.8,402.0,404.2,406.4,407.6,408.3,408.9,409.6,410.1,410.7,411.2,411.7,412.1,412.5,412.9,413.3,413.6,413.9,414.2,414.4,414.6,414.7],"b32":[190.6,193.8,197.0,200.2,203.4,206.6,209.8,213.0,216.1,219.3,222.4,225.5,228.7,231.8,234.9,238.0,241.0,244.1,247.1,250.2,253.2,256.3,259.3,262.3,265.3,268.2,271.2,274.2,277.1,280.0,283.0,285.9,288.8,291.7,294.5,297.4,300.3,303.1,305.9,308.8,311.6,314.4,317.1,319.9,322.7,325.4,328.2,330.9,333.6,336.3,339.0,341.7,344.3,347.0,349.6,352.2,354.9,357.5,360.0,362.6,365.2,367.7,370.3,372.8,375.3,377.8,380.3,382.8,385.2,387.7,390.1,392.5,394.9,397.3,399.7,402.0,404.4,406.7,409.0,411.4,413.6,415.9,418.2,420.4,422.7,423.7,424.3,425.0,425.6,426.2,426.7,427.2,427.7,428.2,428.6,429.0,429.3,429.6,429.9,430.2,430.4,430.6],"b34":[198.2,201.6,204.9,208.2,211.5,214.7,218.0,221.3,224.5,227.8,231.0,234.2,237.4,240.6,243.8,247.0,250.1,253.3,256.4,259.5,262.7,265.8,268.9,271.9,275.0,278.1,281.1,284.1,287.2,290.2,293.2,296.2,299.1,302.1,305.1,308.0,310.9,313.8,316.7,319.6,322.5,325.4,328.2,331.1,333.9,336.7,339.5,342.3,345.1,347.9,350.6,353.4,356.1,358.8,361.5,364.2,366.9,369.6,372.2,374.8,377.5,380.1,382.7,385.3,387.8,390.4,393.0,395.5,398.0,400.5,403.0,405.5,407.9,410.4,412.8,415.3,417.7,420.1,422.4,424.8,427.1,429.5,431.8,434.1,436.4,438.7,439.5,440.1,440.8,441.4,442.0,442.5,443.0,443.5,444.0,444.4,444.7,445.1,445.4,445.7,445.9,446.1],"b30lo":[178.2,181.3,184.3,187.3,190.4,193.4,196.4,199.4,202.4,205.3,208.3,211.3,214.2,217.2,220.1,223.0,225.9,228.8,231.7,234.6,237.5,240.4,243.2,246.1,248.9,251.7,254.5,257.3,260.1,262.9,265.7,268.5,271.2,274.0,276.7,279.4,282.1,284.8,287.5,290.2,292.8,295.5,298.1,300.8,303.4,306.0,308.6,311.2,313.8,316.3,318.9,321.4,324.0,326.5,329.0,331.5,334.0,336.4,338.9,341.3,343.8,346.2,348.6,351.0,353.4,355.8,358.1,360.5,362.8,365.1,367.4,369.7,372.0,374.3,376.5,378.8,381.0,383.2,385.4,387.6,389.8,392.0,394.1,396.3,397.4,398.1,398.7,399.3,399.9,400.4,400.9,401.4,401.8,402.2,402.6,402.9,403.3,403.5,403.8,404.0,404.2,404.4],"b30hi":[189.7,192.9,196.1,199.4,202.6,205.8,209.0,212.2,215.3,218.5,221.7,224.8,228.0,231.1,234.2,237.3,240.4,243.5,246.6,249.7,252.7,255.8,258.8,261.8,264.9,267.9,270.9,273.8,276.8,279.8,282.7,285.7,288.6,291.5,294.4,297.3,300.2,303.1,305.9,308.8,311.6,314.4,317.3,320.1,322.8,325.6,328.4,331.1,333.9,336.6,339.3,342.0,344.7,347.4,350.1,352.7,355.4,358.0,360.6,363.2,365.8,368.4,370.9,373.5,376.0,378.6,381.1,383.6,386.1,388.5,391.0,393.4,395.9,398.3,400.7,403.1,405.4,407.8,410.1,412.5,414.8,417.1,419.4,421.7,422.9,423.6,424.3,424.9,425.5,426.1,426.6,427.1,427.6,428.0,428.4,428.8,429.1,429.4,429.7,429.9,430.1,430.3],"iat30":[36.6,36.9,37.2,37.5,37.9,38.2,38.6,38.9,39.3,39.6,40.0,40.4,40.7,41.1,41.5,41.9,42.3,42.7,43.1,43.5,43.9,44.3,44.7,45.2,45.6,46.0,46.4,46.8,47.3,47.7,48.1,48.5,49.0,49.4,49.8,50.2,50.7,51.1,51.5,51.9,52.4,52.8,53.2,53.6,54.1,54.5,54.9,55.3,55.7,56.1,56.5,57.0,57.4,57.8,58.2,58.6,59.0,59.4,59.8,60.2,60.6,61.0,61.3,61.7,62.1,62.5,62.9,63.2,63.6,64.0,64.4,64.7,65.1,65.4,65.8,66.2,66.5,66.9,67.2,67.6,67.9,68.2,68.6,68.9,69.1,69.2,69.3,69.4,69.5,69.5,69.6,69.7,69.8,69.8,69.9,69.9,70.0,70.0,70.1,70.1,70.1,70.2],"lb30":[22.85,23.24,23.63,24.02,24.41,24.79,25.18,25.56,25.94,26.33,26.71,27.09,27.47,27.84,28.22,28.59,28.97,29.34,29.71,30.08,30.45,30.82,31.18,31.55,31.91,32.27,32.63,32.99,33.35,33.71,34.06,34.42,34.77,35.12,35.47,35.82,36.17,36.51,36.86,37.2,37.54,37.88,38.22,38.56,38.9,39.23,39.56,39.9,40.23,40.56,40.88,41.21,41.53,41.86,42.18,42.5,42.81,43.13,43.45,43.76,44.07,44.38,44.69,45.0,45.31,45.61,45.91,46.21,46.51,46.81,47.11,47.4,47.69,47.99,48.27,48.56,48.85,49.13,49.42,49.7,49.98,50.25,50.53,50.8,50.95,51.04,51.12,51.19,51.27,51.33,51.4,51.46,51.51,51.57,51.62,51.66,51.7,51.74,51.77,51.8,51.82,51.84],"ve30":[0.9335,0.9348,0.9361,0.9373,0.9385,0.9397,0.9409,0.9421,0.9432,0.9443,0.9454,0.9464,0.9475,0.9485,0.9495,0.9504,0.9514,0.9523,0.9532,0.9541,0.9549,0.9557,0.9565,0.9573,0.9581,0.9588,0.9595,0.9602,0.9609,0.9615,0.9621,0.9627,0.9633,0.9638,0.9644,0.9649,0.9653,0.9658,0.9662,0.9666,0.967,0.9674,0.9677,0.968,0.9683,0.9686,0.9688,0.9691,0.9693,0.9694,0.9696,0.9697,0.9698,0.9699,0.97,0.97,0.97,0.97,0.97,0.9699,0.9698,0.9697,0.9696,0.9694,0.9693,0.9691,0.9688,0.9686,0.9683,0.968,0.9677,0.9674,0.967,0.9666,0.9662,0.9658,0.9653,0.9649,0.9644,0.9638,0.9633,0.9627,0.9621,0.9615,0.9582,0.9535,0.9487,0.9439,0.9391,0.9342,0.9294,0.9245,0.9196,0.9147,0.9098,0.9048,0.8998,0.8948,0.8898,0.8848,0.8798,0.8747]},"map":{"surge":[[5.3,1.1],[9.1,2.0],[11.2,2.4],[16.2,3.0],[20.6,3.4],[26.8,3.8],[32.3,4.0]],"choke":[[58.0,1.4],[62.2,2.2],[61.5,2.6],[60.5,3.0],[60.0,3.42],[58.0,3.6],[56.6,3.8],[53.3,4.0]],"prAxis":[1.0,4.2],"flowAxis":[0,65],"speedLines":[44,84,111,132,150],"contours":[0.58,0.6,0.62,0.64,0.66,0.68,0.7,0.72,0.74],"labels":[[11.3,2.01,0.58],[54.2,2.21,0.58],[11.3,2.21,0.6],[56.9,2.71,0.6],[14.4,2.41,0.62],[57.7,2.92,0.62],[29.0,2.86,0.64],[57.7,3.14,0.64],[35.6,3.14,0.66],[43.6,3.5,0.68],[50.7,3.74,0.7],[45.8,3.37,0.72],[43.6,2.92,0.74]],"peak":0.74,"peakAt":[44.0,3.0],"topPr":4.1,"pdf":"efr-7163-f.pdf","rms":0.021,"compInd":57,"compOd":71,"gridF":[4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48,50,52,54,56,58,60,62,64,66],"gridP":[1.0,1.1,1.2,1.3,1.4,1.5,1.6,1.7,1.8,1.9,2.0,2.1,2.2,2.3,2.4,2.5,2.6,2.7,2.8,2.9,3.0,3.1,3.2,3.3,3.4,3.5,3.6,3.7,3.8,3.9,4.0,4.1,4.2],"grid":[[0.6268,0.6401,0.6512,0.6602,0.6671,0.6718,0.6744,0.6748,0.6731,0.6693,0.6633,0.6552,0.645,0.6326,0.618,0.6014,0.5826,0.5617,0.5386,0.5134,0.486,0.4565,0.4249,0.3912,0.3553,0.35,0.35,0.35,0.35,0.35,0.35,0.35],[0.6209,0.6355,0.6479,0.6582,0.6664,0.6724,0.6763,0.678,0.6777,0.6751,0.6705,0.6637,0.6547,0.6437,0.6304,0.6151,0.5976,0.578,0.5562,0.5323,0.5063,0.4781,0.4478,0.4153,0.3808,0.35,0.35,0.35,0.35,0.35,0.35,0.35],[0.614,0.6299,0.6436,0.6552,0.6647,0.672,0.6772,0.6803,0.6812,0.68,0.6766,0.6711,0.6635,0.6537,0.6418,0.6278,0.6116,0.5933,0.5728,0.5503,0.5255,0.4987,0.4697,0.4385,0.4052,0.3698,0.35,0.35,0.35,0.35,0.35,0.35],[0.6061,0.6233,0.6383,0.6512,0.662,0.6706,0.6771,0.6815,0.6837,0.6838,0.6818,0.6776,0.6713,0.6628,0.6522,0.6395,0.6246,0.6076,0.5885,0.5672,0.5438,0.5182,0.4905,0.4607,0.4287,0.3946,0.3584,0.35,0.35,0.35,0.35,0.35],[0.5971,0.6156,0.632,0.6462,0.6583,0.6683,0.6761,0.6818,0.6853,0.6867,0.686,0.6831,0.6781,0.6709,0.6616,0.6502,0.6366,0.6209,0.6031,0.5831,0.561,0.5368,0.5104,0.4819,0.4512,0.4184,0.3835,0.35,0.35,0.35,0.35,0.35],[0.5872,0.607,0.6247,0.6402,0.6536,0.6649,0.674,0.681,0.6858,0.6885,0.6891,0.6875,0.6838,0.678,0.67,0.6599,0.6477,0.6333,0.6167,0.5981,0.5773,0.5543,0.5293,0.502,0.4727,0.4412,0.4076,0.3718,0.35,0.35,0.35,0.35],[0.5763,0.5974,0.6164,0.6332,0.6479,0.6605,0.6709,0.6792,0.6854,0.6894,0.6913,0.691,0.6886,0.6841,0.6774,0.6686,0.6577,0.6446,0.6294,0.612,0.5925,0.5709,0.5471,0.5212,0.4932,0.463,0.4307,0.3962,0.3596,0.35,0.35,0.35],[0.5644,0.5868,0.6071,0.6252,0.6412,0.6551,0.6669,0.6765,0.6839,0.6893,0.6924,0.6935,0.6924,0.6892,0.6838,0.6763,0.6667,0.6549,0.641,0.625,0.6068,0.5865,0.564,0.5394,0.5127,0.4838,0.4528,0.4196,0.3844,0.35,0.35,0.35],[0.5515,0.5752,0.5968,0.6162,0.6336,0.6487,0.6618,0.6727,0.6815,0.6881,0.6926,0.695,0.6952,0.6933,0.6892,0.683,0.6747,0.6642,0.6516,0.6369,0.62,0.601,0.5799,0.5566,0.5312,0.5036,0.4739,0.4421,0.4081,0.372,0.35,0.35],[0.5375,0.5626,0.5855,0.6062,0.6249,0.6414,0.6557,0.6679,0.678,0.686,0.6918,0.6954,0.697,0.6964,0.6936,0.6887,0.6817,0.6726,0.6613,0.6479,0.6323,0.6146,0.5947,0.5728,0.5486,0.5224,0.494,0.4635,0.4308,0.396,0.3591,0.35],[0.5226,0.549,0.5732,0.5953,0.6152,0.633,0.6487,0.6622,0.6736,0.6828,0.6899,0.6949,0.6978,0.6985,0.697,0.6935,0.6877,0.6799,0.6699,0.6578,0.6435,0.6271,0.6086,0.5879,0.5651,0.5402,0.5131,0.4839,0.4525,0.419,0.3834,0.35],[0.5067,0.5344,0.5599,0.5833,0.6045,0.6236,0.6406,0.6554,0.6681,0.6787,0.6871,0.6934,0.6975,0.6996,0.6994,0.6972,0.6928,0.6862,0.6776,0.6667,0.6538,0.6387,0.6215,0.6021,0.5806,0.557,0.5312,0.5033,0.4732,0.4411,0.4067,0.3703],[0.4898,0.5187,0.5456,0.5703,0.5928,0.6132,0.6315,0.6477,0.6617,0.6735,0.6833,0.6909,0.6963,0.6997,0.7008,0.6999,0.6968,0.6916,0.6842,0.6747,0.6631,0.6493,0.6334,0.6153,0.5951,0.5728,0.5483,0.5217,0.493,0.4621,0.4291,0.3939],[0.4719,0.5021,0.5303,0.5563,0.5801,0.6019,0.6215,0.6389,0.6542,0.6674,0.6785,0.6874,0.6941,0.6988,0.7012,0.7016,0.6998,0.6959,0.6898,0.6816,0.6713,0.6588,0.6442,0.6275,0.6086,0.5876,0.5644,0.5391,0.5117,0.4821,0.4504,0.4166],[0.4529,0.4845,0.514,0.5413,0.5665,0.5895,0.6104,0.6292,0.6458,0.6603,0.6726,0.6828,0.6909,0.6968,0.7006,0.7023,0.7018,0.6992,0.6945,0.6876,0.6786,0.6674,0.6541,0.6387,0.6211,0.6014,0.5795,0.5556,0.5294,0.5012,0.4708,0.4382],[0.433,0.4659,0.4967,0.5253,0.5518,0.5761,0.5983,0.6184,0.6363,0.6521,0.6658,0.6773,0.6867,0.6939,0.6991,0.702,0.7029,0.7016,0.6981,0.6925,0.6848,0.675,0.663,0.6489,0.6326,0.6142,0.5937,0.571,0.5462,0.5192,0.4901,0.4589],[0.4121,0.4463,0.4784,0.5083,0.5361,0.5618,0.5853,0.6067,0.6259,0.643,0.658,0.6708,0.6815,0.69,0.6965,0.7007,0.7029,0.7029,0.7008,0.6965,0.6901,0.6815,0.6709,0.658,0.6431,0.626,0.6068,0.5854,0.5619,0.5362,0.5085,0.4786],[0.3902,0.4257,0.4591,0.4903,0.5194,0.5464,0.5712,0.5939,0.6145,0.6329,0.6491,0.6633,0.6753,0.6851,0.6929,0.6985,0.7019,0.7032,0.7024,0.6994,0.6943,0.6871,0.6777,0.6662,0.6526,0.6368,0.6189,0.5988,0.5766,0.5523,0.5258,0.4972],[0.3673,0.4041,0.4388,0.4713,0.5017,0.53,0.5562,0.5801,0.602,0.6217,0.6393,0.6548,0.6681,0.6792,0.6883,0.6952,0.6999,0.7026,0.7031,0.7014,0.6976,0.6917,0.6836,0.6734,0.6611,0.6466,0.63,0.6112,0.5904,0.5673,0.5422,0.5149],[0.35,0.3815,0.4175,0.4514,0.4831,0.5127,0.5401,0.5654,0.5886,0.6096,0.6285,0.6452,0.6599,0.6723,0.6827,0.6909,0.697,0.7009,0.7027,0.7024,0.6999,0.6953,0.6885,0.6796,0.6686,0.6554,0.6401,0.6227,0.6031,0.5814,0.5575,0.5315],[0.35,0.3579,0.3952,0.4304,0.4634,0.4943,0.523,0.5496,0.5741,0.5965,0.6167,0.6347,0.6507,0.6645,0.6761,0.6856,0.693,0.6982,0.7013,0.7023,0.7011,0.6978,0.6924,0.6848,0.6751,0.6632,0.6492,0.6331,0.6148,0.5944,0.5719,0.5472],[0.35,0.35,0.3719,0.4084,0.4427,0.4749,0.505,0.5329,0.5587,0.5823,0.6038,0.6232,0.6405,0.6556,0.6685,0.6793,0.688,0.6946,0.699,0.7013,0.7014,0.6994,0.6953,0.689,0.6806,0.67,0.6573,0.6425,0.6256,0.6065,0.5852,0.5618],[0.35,0.35,0.35,0.3854,0.421,0.4546,0.4859,0.5152,0.5422,0.5672,0.59,0.6107,0.6293,0.6457,0.6599,0.6721,0.6821,0.6899,0.6956,0.6992,0.7007,0.7,0.6971,0.6922,0.6851,0.6758,0.6645,0.6509,0.6353,0.6175,0.5976,0.5755],[0.35,0.35,0.35,0.3614,0.3984,0.4332,0.4659,0.4964,0.5248,0.5511,0.5752,0.5972,0.617,0.6348,0.6503,0.6638,0.6751,0.6843,0.6913,0.6962,0.6989,0.6996,0.698,0.6944,0.6886,0.6806,0.6706,0.6584,0.644,0.6275,0.6089,0.5882],[0.35,0.35,0.35,0.35,0.3747,0.4108,0.4448,0.4767,0.5064,0.5339,0.5594,0.5827,0.6038,0.6229,0.6398,0.6545,0.6671,0.6776,0.6859,0.6921,0.6962,0.6981,0.6979,0.6956,0.6911,0.6845,0.6757,0.6648,0.6518,0.6366,0.6193,0.5998],[0.35,0.35,0.35,0.35,0.35,0.3875,0.4228,0.4559,0.4869,0.5158,0.5426,0.5672,0.5896,0.61,0.6282,0.6442,0.6582,0.6699,0.6796,0.6871,0.6925,0.6957,0.6968,0.6958,0.6926,0.6873,0.6798,0.6702,0.6585,0.6446,0.6286,0.6105],[0.35,0.35,0.35,0.35,0.35,0.3631,0.3997,0.4342,0.4665,0.4967,0.5247,0.5507,0.5744,0.5961,0.6156,0.633,0.6482,0.6613,0.6722,0.6811,0.6877,0.6923,0.6947,0.695,0.6931,0.6891,0.6829,0.6747,0.6642,0.6517,0.637,0.6202],[0.35,0.35,0.35,0.35,0.35,0.35,0.3757,0.4114,0.4451,0.4766,0.5059,0.5332,0.5582,0.5812,0.602,0.6207,0.6372,0.6516,0.6639,0.674,0.682,0.6879,0.6916,0.6932,0.6926,0.6899,0.6851,0.6781,0.669,0.6577,0.6444,0.6288],[0.35,0.35,0.35,0.35,0.35,0.35,0.3506,0.3877,0.4226,0.4554,0.4861,0.5147,0.541,0.5653,0.5874,0.6074,0.6253,0.641,0.6545,0.666,0.6753,0.6824,0.6875,0.6904,0.6911,0.6897,0.6862,0.6805,0.6727,0.6628,0.6507,0.6365],[0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.3629,0.3992,0.4333,0.4653,0.4951,0.5229,0.5484,0.5719,0.5931,0.6123,0.6293,0.6442,0.6569,0.6676,0.676,0.6824,0.6866,0.6886,0.6885,0.6863,0.682,0.6755,0.6668,0.6561,0.6432],[0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.3748,0.4102,0.4435,0.4746,0.5037,0.5305,0.5553,0.5779,0.5983,0.6167,0.6329,0.6469,0.6588,0.6686,0.6762,0.6818,0.6851,0.6863,0.6854,0.6824,0.6772,0.6699,0.6604,0.6488],[0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.3861,0.4207,0.4531,0.4835,0.5116,0.5377,0.5616,0.5834,0.603,0.6205,0.6359,0.6491,0.6602,0.6691,0.676,0.6806,0.6832,0.6836,0.6818,0.678,0.6719,0.6638,0.6535],[0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.361,0.3969,0.4306,0.4623,0.4918,0.5191,0.5443,0.5674,0.5884,0.6072,0.6238,0.6384,0.6508,0.661,0.6692,0.6751,0.679,0.6807,0.6803,0.6777,0.673,0.6662,0.6572]],"locus30":[[2500,18.91,3.416],[2600,19.7,3.416],[2700,20.49,3.416],[2800,21.28,3.416],[2900,22.07,3.416],[3000,22.85,3.416],[3100,23.63,3.416],[3200,24.41,3.416],[3300,25.18,3.416],[3400,25.94,3.416],[3500,26.71,3.416],[3600,27.47,3.416],[3700,28.22,3.416],[3800,28.97,3.416],[3900,29.71,3.416],[4000,30.45,3.416],[4100,31.18,3.416],[4200,31.91,3.416],[4300,32.63,3.416],[4400,33.35,3.416],[4500,34.06,3.416],[4600,34.77,3.416],[4700,35.47,3.416],[4800,36.17,3.416],[4900,36.86,3.416],[5000,37.54,3.416],[5100,38.22,3.416],[5200,38.9,3.416],[5300,39.56,3.416],[5400,40.23,3.416],[5500,40.88,3.416],[5600,41.53,3.416],[5700,42.18,3.416],[5800,42.81,3.416],[5900,43.45,3.416],[6000,44.07,3.416],[6100,44.69,3.416],[6200,45.31,3.416],[6300,45.91,3.416],[6400,46.51,3.416],[6500,47.11,3.416],[6600,47.69,3.416],[6700,48.27,3.416],[6800,48.85,3.416],[6900,49.42,3.416],[7000,49.98,3.416],[7100,50.53,3.416],[7200,50.95,3.416],[7300,51.12,3.416],[7400,51.27,3.416],[7500,51.4,3.416],[7600,51.51,3.416],[7700,51.62,3.416],[7800,51.7,3.416],[7900,51.77,3.416],[8000,51.82,3.416]],"surgeSafeBoost":[[2000,0.0],[2250,0.0],[2500,0.0],[2750,0.0],[3000,23.5],[3250,29.5],[3500,30.0],[3750,30.0],[4000,30.0],[4250,30.0],[4500,30.0],[4750,30.0],[5000,30.0],[5250,30.0],[5500,30.0],[5750,30.0],[6000,30.0],[6250,30.0],[6500,30.0],[6750,30.0],[7000,30.0],[7250,30.0],[7500,30.0],[7750,30.0],[8000,30.0]]},"pack":{"radOverall":[714,439,64.5],"radCore":[699,318,51.8],"radPart":"Mishimoto MMRAD-CEL-89","radRows":2,"condThick":20.0,"gapLo":203.0,"gapHi":254.0,"icW":610,"icH":305}};

/* 2. official compressor map */
function drawR4Map(){
  var W=780,H=440,L=58,Rr=26,T=16,B=40, s=svg(W,H);
  var m=R4.map, fLo=0,fHi=65,pLo=1.0,pHi=4.4;
  function X(f){return L+(W-Rr-L)*(f-fLo)/(fHi-fLo);}
  function Y(p){return T+(H-B-T)*(1-(p-pLo)/(pHi-pLo));}
  /* efficiency shading */
  function col(e){
    if(e>=0.72) return "rgba(56,211,159,.55)";
    if(e>=0.70) return "rgba(56,211,159,.40)";
    if(e>=0.68) return "rgba(120,205,150,.32)";
    if(e>=0.66) return "rgba(190,205,120,.28)";
    if(e>=0.64) return "rgba(255,196,110,.26)";
    if(e>=0.62) return "rgba(255,168,100,.22)";
    if(e>=0.60) return "rgba(255,140,100,.18)";
    return "rgba(255,110,110,.13)";
  }
  function surgeAt(p){
    var a=m.surge; if(p<=a[0][1])return a[0][0];
    for(var i=0;i<a.length-1;i++) if(p>=a[i][1]&&p<=a[i+1][1])
      return a[i][0]+(p-a[i][1])/(a[i+1][1]-a[i][1])*(a[i+1][0]-a[i][0]);
    return a[a.length-1][0];
  }
  function chokeAt(p){
    var a=m.choke; if(p<=a[0][1])return a[0][0];
    for(var i=0;i<a.length-1;i++) if(p>=a[i][1]&&p<=a[i+1][1])
      return a[i][0]+(p-a[i][1])/(a[i+1][1]-a[i][1])*(a[i+1][0]-a[i][0]);
    return a[a.length-1][0];
  }
  var gf=m.gridF, gp=m.gridP;
  for(var iy=0;iy<gp.length-1;iy++){
    var p=gp[iy]; if(p<1.2||p>m.topPr) continue;
    var s0=surgeAt(p), c0=chokeAt(p);
    for(var ix=0;ix<gf.length-1;ix++){
      var f=gf[ix]; if(f<s0||f>c0) continue;
      var x0=X(f), x1=X(Math.min(gf[ix+1],c0)), y0=Y(gp[iy+1]), y1=Y(p);
      el(s,"rect",{x:x0,y:y0,width:Math.max(0.6,x1-x0),height:Math.max(0.6,y1-y0),
                   fill:col(m.grid[iy][ix]),stroke:"none"});
    }
  }
  gridY(s,L,W,Rr,T,H,B,I_PR(),function(v){return v.toFixed(1);},pLo,pHi);
  gridX(s,L,W,Rr,T,H,B,13,function(v){return v.toFixed(0);},fLo,fHi);
  /* surge + choke */
  path(s,m.surge.map(function(q){return [X(q[0]),Y(q[1])];}),"#ff6b6b",2.4);
  path(s,m.choke.map(function(q){return [X(q[0]),Y(q[1])];}),"#4ea3ff",2.4);
  txt(s,X(m.surge[m.surge.length-1][0])-4,Y(m.surge[m.surge.length-1][1])-6,"surge",
      {fill:"#ff6b6b","font-size":10,"text-anchor":"end"});
  txt(s,X(m.choke[m.choke.length-1][0])+5,Y(m.choke[m.choke.length-1][1])-4,"choke",
      {fill:"#4ea3ff","font-size":10});
  /* printed contour labels, as evidence */
  m.labels.forEach(function(q){
    el(s,"circle",{cx:X(q[0]),cy:Y(q[1]),r:2,fill:"#9fb0c4"});
    txt(s,X(q[0])+4,Y(q[1])-3,q[2].toFixed(2),{fill:"#9fb0c4","font-size":8.5});
  });
  /* peak island marker */
  el(s,"circle",{cx:X(m.peakAt[0]),cy:Y(m.peakAt[1]),r:4.5,fill:"none",
                 stroke:"#38d39f","stroke-width":1.6});
  txt(s,X(m.peakAt[0])+8,Y(m.peakAt[1])+3,"0.74 island",
      {fill:"#38d39f","font-size":10});
  /* operating locus */
  path(s,m.locus30.map(function(q){return [X(q[1]),Y(q[2])];}),"#38d39f",3.0);
  m.locus30.forEach(function(q){
    if(q[0]%1000!==0) return;
    el(s,"circle",{cx:X(q[1]),cy:Y(q[2]),r:2.6,fill:"#38d39f"});
    txt(s,X(q[1]),Y(q[2])+13,(q[0]/1000).toFixed(0)+"k",
        {fill:"#8fa0b4","font-size":9,"text-anchor":"middle"});
  });
  /* design point */
  var dp=R4.hero;
  el(s,"circle",{cx:X(dp.lb),cy:Y(dp.pr),r:5.5,fill:"#ffb347",stroke:"#12161c","stroke-width":1.5});
  txt(s,X(dp.lb)-8,Y(dp.pr)-9,"7,500 rpm / 30 psi",
      {fill:"#ffb347","font-size":10,"text-anchor":"end"});
  axes(s,L,Rr,T,B,W,H,"compressor flow (lb/min)","pressure ratio");
  mount("ch_r4_map",s);
}
function I_PR(){ return 17; }

/* 3. community dyno bars */
function drawR4Dyno(){
  var W=780,H=330,L=250,Rr=30,T=14,B=38, s=svg(W,H);
  var rows=R4.community.slice().sort(function(a,b){return a.per_l-b.per_l;});
  var maxv=330;
  var n=rows.length+1, band=(H-B-T)/n;
  function X(v){return L+(W-Rr-L)*v/maxv;}
  for(var i=0;i<=6;i++){
    var gx=L+(W-Rr-L)*i/6;
    el(s,"line",{x1:gx,y1:T,x2:gx,y2:H-B,stroke:"#232c38","stroke-width":1});
    txt(s,gx,H-B+15,(maxv*i/6).toFixed(0),{fill:"#6f8098","font-size":10,"text-anchor":"middle"});
  }
  rows.forEach(function(r,i){
    var y=T+band*i+band*0.18, h=band*0.60;
    el(s,"rect",{x:L,y:y,width:Math.max(1,X(r.per_l)-L),height:h,fill:"#4ea3ff",rx:2});
    txt(s,L-8,y+h*0.72,r.what.length>40?r.what.slice(0,39)+"…":r.what,
        {fill:"#9fb0c4","font-size":9.5,"text-anchor":"end"});
    txt(s,X(r.per_l)+5,y+h*0.75,r.per_l.toFixed(0)+"  ("+r.whp+" whp)",
        {fill:"#cfe0f2","font-size":9.5});
  });
  /* model bar with band */
  var y=T+band*rows.length+band*0.18, h=band*0.60;
  var lo=R4.hero.whp_lo/2.1888, hi=R4.hero.whp_hi/2.1888;
  el(s,"rect",{x:X(lo),y:y-3,width:Math.max(1,X(hi)-X(lo)),height:h+6,
               fill:"rgba(56,211,159,.30)",rx:2});
  el(s,"rect",{x:L,y:y,width:Math.max(1,X(R4.modelPerL)-L),height:h,fill:"#38d39f",rx:2});
  txt(s,L-8,y+h*0.72,"THIS MODEL — estimate, no dyno",
      {fill:"#38d39f","font-size":9.5,"text-anchor":"end","font-weight":"700"});
  txt(s,X(hi)+5,y+h*0.75,R4.modelPerL.toFixed(0)+"  ("+R4.hero.whp_lo+"–"+R4.hero.whp_hi+" whp)",
      {fill:"#4fe0aa","font-size":9.5});
  axes(s,L,Rr,T,B,W,H,"wheel horsepower per litre","");
  mount("ch_r4_dyno",s);
}

/* 4. driveline band */
function drawR4Drive(){
  var W=780,H=250,L=120,Rr=120,T=16,B=38, s=svg(W,H);
  var rows=R4.driveline.band, lo=380,hi=440;
  var band=(H-B-T)/rows.length;
  function X(v){return L+(W-Rr-L)*(v-lo)/(hi-lo);}
  for(var i=0;i<=6;i++){
    var gx=L+(W-Rr-L)*i/6, gv=lo+(hi-lo)*i/6;
    el(s,"line",{x1:gx,y1:T,x2:gx,y2:H-B,stroke:"#232c38","stroke-width":1});
    txt(s,gx,H-B+15,gv.toFixed(0),{fill:"#6f8098","font-size":10,"text-anchor":"middle"});
  }
  rows.forEach(function(r,i){
    var y=T+band*i+band*0.20, h=band*0.55;
    var isBase=(r.f===0.80);
    el(s,"rect",{x:L,y:y,width:Math.max(1,X(r.whp)-L),height:h,
                 fill:isBase?"#38d39f":"#4ea3ff",rx:2});
    txt(s,L-8,y+h*0.72,"factor "+r.f.toFixed(2)+"  ("+r.loss.toFixed(0)+"% loss)",
        {fill:isBase?"#4fe0aa":"#9fb0c4","font-size":10.5,"text-anchor":"end"});
    txt(s,X(r.whp)+6,y+h*0.75,r.whp+" whp",{fill:"#cfe0f2","font-size":10.5});
  });
  axes(s,L,Rr,T,B,W,H,"wheel horsepower at 7,500 rpm / 30 psi (51.4 lb/min in every bar)","");
  mount("ch_r4_drive",s);
}

/* 5. packaging stack, side view to scale */
function drawR4Stack(){
  var W=780,H=300, s=svg(W,H);
  var p=R4.pack;
  var core=102, gapLo=p.gapLo-(core-76), gapHi=p.gapHi-(core-76);
  var duct=40, bumper=14, cond=p.condThick, rad=p.radOverall[2];
  var total=bumper+duct+core+gapHi+cond+rad+30;
  var sc=(W-140)/total, ox=80, oy=70, ht=140;
  function box(x,w,fill,stroke,lab,sub){
    el(s,"rect",{x:ox+x*sc,y:oy,width:Math.max(1.5,w*sc),height:ht,
                 fill:fill,stroke:stroke,"stroke-width":1.4,rx:2});
    if(lab){
      var t=txt(s,0,0,lab,{fill:stroke,"font-size":10.5,"text-anchor":"middle"});
      t.setAttribute("transform","translate("+(ox+(x+w/2)*sc)+","+(oy+ht/2)+") rotate(-90)");
    }
    if(sub) txt(s,ox+(x+w/2)*sc,oy+ht+16,sub,
                {fill:"#8fa0b4","font-size":9.5,"text-anchor":"middle"});
  }
  var x=0;
  box(x,bumper,"#2a3240","#8fa0b4","bumper","skin"); x+=bumper;
  box(x,duct,"rgba(78,163,255,.16)","#4ea3ff","SEALED DUCT",duct+" mm"); x+=duct;
  box(x,core,"rgba(56,211,159,.22)","#38d39f","INTERCOOLER",core+" mm core"); x+=core;
  var gx=x;
  box(x,gapHi,"rgba(255,255,255,.03)","#4a5768","","clear air"); x+=gapHi;
  box(x,cond,"rgba(197,140,255,.18)","#c58cff","A/C COND",cond+" mm"); x+=cond;
  box(x,rad,"rgba(255,179,71,.18)","#ffb347","RADIATOR",p.radPart.split(" ")[1]+"  "+rad+" mm");
  x+=rad;
  el(s,"line",{x1:ox+x*sc,y1:oy-6,x2:ox+x*sc,y2:oy+ht+6,stroke:"#8fa0b4",
               "stroke-width":1.2,"stroke-dasharray":"3 3"});
  txt(s,ox+x*sc+6,oy+14,"fender support",{fill:"#8fa0b4","font-size":9.5});
  txt(s,ox+x*sc+6,oy+27,"engine side →",{fill:"#6f8098","font-size":9});
  /* the measured gap dimension */
  var y0=oy-22;
  el(s,"line",{x1:ox+gx*sc,y1:y0,x2:ox+(gx+gapHi)*sc,y2:y0,stroke:"#38d39f","stroke-width":1.4});
  el(s,"line",{x1:ox+gx*sc,y1:y0-5,x2:ox+gx*sc,y2:y0+5,stroke:"#38d39f","stroke-width":1.4});
  el(s,"line",{x1:ox+(gx+gapHi)*sc,y1:y0-5,x2:ox+(gx+gapHi)*sc,y2:y0+5,stroke:"#38d39f","stroke-width":1.4});
  txt(s,ox+(gx+gapHi/2)*sc,y0-8,
      gapLo.toFixed(0)+"–"+gapHi.toFixed(0)+" mm clear behind a "+core+" mm core",
      {fill:"#38d39f","font-size":10.5,"text-anchor":"middle"});
  /* airflow arrow */
  el(s,"line",{x1:ox-40,y1:oy+ht/2,x2:ox-8,y2:oy+ht/2,stroke:"#4ea3ff","stroke-width":2});
  el(s,"polygon",{points:(ox-8)+","+(oy+ht/2)+" "+(ox-16)+","+(oy+ht/2-4)+" "+(ox-16)+","+(oy+ht/2+4),
                  fill:"#4ea3ff"});
  txt(s,ox-44,oy+ht/2+4,"air",{fill:"#4ea3ff","font-size":10,"text-anchor":"end"});
  /* temperature ladder */
  var ty=oy+ht+42;
  txt(s,ox,ty,"air temperature along the stack at 30 psi, 32 °C ambient:",
      {fill:"#9fb0c4","font-size":10.5});
  var c102=null;
  R4.cores.forEach(function(cc){ if(cc.k==="610x305x102") c102=cc; });
  if(c102){
    txt(s,ox,ty+18,"32 °C ambient  →  intercooler adds "+c102.dt_ic.toFixed(0)
        +" °C after mixing over the gap  →  condenser adds "+c102.dt_cond.toFixed(0)
        +" °C  →  radiator sees "+c102.t_rad_in.toFixed(0)+" °C",
        {fill:"#cfe0f2","font-size":11});
    txt(s,ox,ty+35,"radiator core "+p.radCore[0]+" × "+p.radCore[1]+" × "
        +p.radCore[2]+" mm, "+p.radRows+" row  —  intercooler face shadows "
        +R4.radPenalty.shadow_pct+"% of it",
        {fill:"#8fa0b4","font-size":10});
  }
  mount("ch_r4_stack",s);
}

/* ---- exhaust pulse timing ---- */

/* ---------- 7. exhaust pulse timing ---------- */
function drawPulse(){
  var W=780,H=444,L=52,Rr=126,T=26,B=58, s=svg(W,H);
  var p={win:R5.win}, COL={1:"#4ea3ff",2:"#38d39f",3:"#ff6b6b",4:"#ffb347"};
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
  panel(T+10,"THE SUPERSEDED DIAGRAM:  1+2  /  3+4",'#ff6b6b',[1,2,3,4],
        [["Scroll A","#ff6b6b","84° OVERLAP"],["Scroll B","#ff6b6b","84° OVERLAP"]]);
  panel(T+panelH+54,"AS BUILT, AND CORRECT:  1+4  /  2+3",'#38d39f',[1,4,2,3],
        [["Scroll A","#38d39f","96° clear gap"],["Scroll B","#38d39f","96° clear gap"]]);
  txt(s,(L+W-Rr)/2,H-6,"Crank angle, degrees — one full 720° four-stroke cycle",
      {fill:"#6f8098","font-size":11,"text-anchor":"middle"});
  mount("ch_pulse",s);
}


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
