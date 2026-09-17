/* ================================================================
   ROUND FOUR - charts and tables. Data block R4 emitted by
   make_r4_chartdata.py from unified_model_r4.py.
   Uses the same svg/el/txt/axes/path/gridX/gridY/mount helpers as r2/r3.
   ================================================================ */

function r4Num(v,d){ return (v===null||v===undefined)?"&mdash;":Number(v).toFixed(d===undefined?0:d); }
function r4Body(id){ var t=C(id); return t?t.querySelector("tbody"):null; }

/* ---------- table: rpm range ---------- */
function fillR4Rpm(){
  var b=r4Body("t-r4rpm"); if(!b) return;
  var rows=R4.rpmRange, prev=null;
  b.innerHTML = rows.map(function(r){
    var step = prev===null ? "&mdash;" : ("+"+(r.whp_mid-prev));
    prev = r.whp_mid;
    var hi = (r.rpm===7000);
    var warn = (r.rpm>=7600);
    var bg = hi ? ' style="background:rgba(56,211,159,.09)"'
                : (warn ? ' style="background:rgba(255,179,71,.07)"' : '');
    return '<tr'+bg+'><td class="num"><b>'+r.rpm.toLocaleString()+'</b>'
      + (hi?' <span class="pill p-info">stock</span>':'')+'</td>'
      +'<td class="num">'+r4Num(r.mps,1)+' m/s</td>'
      +'<td class="num">'+r4Num(r.Z,3)+'</td>'
      +'<td class="num">'+r4Num(r.ve,3)+'</td>'
      +'<td class="num">'+r4Num(r.lb,1)+' lb/min</td>'
      +'<td class="num">'+r4Num(r.choke,1)+'%</td>'
      +'<td class="num">'+r4Num(r.iat,1)+' &deg;C</td>'
      +'<td class="num"><b>'+r.whp_lo+' &ndash; '+r.whp_hi+'</b></td>'
      +'<td class="num">'+step+'</td>'
      +'<td class="note">'+(r.risk||"")+'</td></tr>';
  }).join("");
}

/* ---------- table: surge sweep ---------- */
function fillR4Surge(){
  var b=r4Body("t-r4surge"); if(!b) return;
  b.innerHTML = R4.surgeSweep.map(function(r){
    var bad = r.margin<0, marg = r.margin<3;
    var v = bad ? '<span class="pill p-bad">inside surge</span>'
          : (marg ? '<span class="pill p-warn">marginal</span>'
                  : '<span class="pill p-ok">clear</span>');
    var bg = bad ? ' style="background:rgba(255,107,107,.10)"'
           : (marg ? ' style="background:rgba(255,179,71,.08)"' : '');
    return '<tr'+bg+'><td class="num">'+r.rpm.toLocaleString()+'</td>'
      +'<td class="num">'+r4Num(r.lb,1)+' lb/min</td>'
      +'<td class="num">'+r4Num(r.surge,1)+' lb/min</td>'
      +'<td class="num">'+(r.margin>0?"+":"")+r4Num(r.margin,1)+'</td>'
      +'<td>'+v+'</td></tr>';
  }).join("");
}

/* ---------- table: community dyno ---------- */
function fillR4Dyno(){
  var b=r4Body("t-r4dyno"); if(!b) return;
  b.innerHTML = R4.community.map(function(r){
    return '<tr><td>'+r.what+'<br><span class="note">'+r.note+'</span></td>'
      +'<td class="num">'+r4Num(r.disp,1)+' L</td>'
      +'<td>'+r.fuel+'</td>'
      +'<td class="num">'+(r.boost?r.boost+' psi':'&mdash;')+'</td>'
      +'<td>'+r.drive+'</td><td class="note">'+r.dyno+'</td>'
      +'<td class="num"><b>'+r.whp+'</b></td>'
      +'<td class="num">'+r4Num(r.per_l,1)+'</td></tr>';
  }).join("")
  + '<tr style="background:rgba(56,211,159,.12)"><td><b>THIS MODEL &mdash; 5S-GTE, EFR 7163,'
  + ' E85, 30 psi, 7,500 rpm</b><br><span class="note">estimate, not a measurement. '
  + '32 &deg;C ambient, 2,100 ft, 20% AWD loss.</span></td>'
  + '<td class="num">2.19 L</td><td>E85</td><td class="num">30 psi</td><td>AWD</td>'
  + '<td class="note">none &mdash; modelled</td><td class="num"><b>'+R4.hero.whp+'</b>'
  + '<br><span class="note">band '+R4.hero.whp_lo+'&ndash;'+R4.hero.whp_hi+'</span></td>'
  + '<td class="num"><b>'+r4Num(R4.modelPerL,1)+'</b></td></tr>';
}

/* ---------- table: driveline ---------- */
function fillR4Drive(){
  var b=r4Body("t-r4drive"); if(!b) return;
  b.innerHTML = R4.driveline.band.map(function(r){
    var hi = (r.f===0.80);
    return '<tr'+(hi?' style="background:rgba(56,211,159,.09)"':'')+'>'
      +'<td class="num"><b>'+r.f.toFixed(2)+'</b></td>'
      +'<td class="num">'+r4Num(r.loss,1)+'%</td>'
      +'<td class="num"><b>'+r.whp+'</b></td>'
      +'<td>'+r.case+'</td></tr>';
  }).join("");
}

/* ---------- table: duty cycle ---------- */
function fillR4Duty(){
  var b=r4Body("t-r4duty"); if(!b) return;
  b.innerHTML = R4.duty.map(function(r){
    var heavy = r.lost_pct>40;
    return '<tr'+(heavy?' style="background:rgba(255,107,107,.07)"':' style="background:rgba(56,211,159,.07)"')+'>'
      +'<td>'+r.lab+'<br><span class="note">'+r.rpm.toLocaleString()+' rpm, '+r.boost+' psi</span></td>'
      +'<td class="num">'+r4Num(r.q_ic,1)+' kW</td>'
      +'<td class="num">'+r4Num(r.t_rad_in,1)+' &deg;C</td>'
      +'<td class="num">'+r4Num(r.q_stack,1)+' of '+r4Num(r.q_bare,1)+' kW</td>'
      +'<td class="num"><b>'+r4Num(r.lost_pct,1)+'%</b></td></tr>';
  }).join("");
}

/* ---------- table: cores ---------- */
function fillR4Core(){
  var b=r4Body("t-r4core"); if(!b) return;
  var gapFor={76:[203,254],102:[177,228],114:[165,216]};
  b.innerHTML = R4.cores.map(function(r){
    var g=gapFor[r.t]||[null,null];
    var rec = (r.k==="610x305x102");
    var alt = (r.k==="685x305x102");
    var bad = (r.k==="711x305x102");
    var v = rec ? '<span class="pill p-ok">recommended</span> if the aperture takes 610 mm'
          : alt ? '<span class="pill p-ok">better</span> if the aperture takes 685 mm'
          : bad ? '<span class="pill p-bad">not recommended</span> needs ~740 mm of aperture'
          : (r.t===76 ? 'Round-three pick. 9 &deg;C hotter charge for 7 &deg;C less onto the radiator.'
                      : (r.t===114 ? '<span class="pill p-warn">past the knee</span> 3 &deg;C for 3 &deg;C'
                                   : 'face area is cheap, depth is the trade'));
    var bg = rec ? ' style="background:rgba(56,211,159,.10)"'
           : (bad ? ' style="background:rgba(255,107,107,.07)"' : '');
    return '<tr'+bg+'><td><b>'+r.label+'</b></td>'
      +'<td class="num">'+r4Num(r.vol,1)+' L</td>'
      +'<td class="num">'+r4Num(r.vf,2)+' m/s</td>'
      +'<td class="num">'+r4Num(r.eps,3)+'</td>'
      +'<td class="num"><b>'+r4Num(r.iat,1)+' &deg;C</b><br><span class="note">'+r.iatF+' &deg;F</span></td>'
      +'<td class="num">'+r.whp_lo+' &ndash; '+r.whp_hi+'</td>'
      +'<td class="num">'+r4Num(r.t_rad_in,1)+' &deg;C</td>'
      +'<td class="num">'+(g[0]?g[0]+'&ndash;'+g[1]+' mm':'&mdash;')+'</td>'
      +'<td class="note">'+v+'</td></tr>';
  }).join("");
}

/* ---------- table: throttle body across the range ---------- */
function fillR4Tb(){
  var b=r4Body("t-r4tb"); if(!b) return;
  b.innerHTML = R4.tbRange.map(function(r){
    return '<tr><td class="num">'+r.rpm.toLocaleString()+'</td>'
      +'<td class="num">'+r.boost+' psi</td>'
      +'<td class="num">'+r4Num(r.lb,1)+' lb/min</td>'
      +'<td class="num">'+r4Num(r.v,1)+' m/s <span class="note">('+r.vfts+' ft/s)</span></td>'
      +'<td class="num">'+r4Num(r.mach,3)+'</td>'
      +'<td class="num">'+r4Num(r.dp_psi,3)+' psi</td>'
      +'<td class="num">'+r4Num(r.used,0)+'%</td></tr>';
  }).join("");
}

/* ---------- table: cold layouts ---------- */
function fillR4Cold(){
  var b=r4Body("t-r4cold"); if(!b) return;
  var rows=R4.coldLayouts.slice().sort(function(a,c){return a.box-c.box;});
  b.innerHTML = rows.map(function(r){
    var rec = r.lab.indexOf("2.50 in run")===0;
    var tight = r.lab.indexOf("2.25 in run")===0;
    var big = r.lab.indexOf("3.00 in the whole")===0;
    var bg = rec ? ' style="background:rgba(56,211,159,.10)"'
           : (big ? ' style="background:rgba(255,179,71,.07)"' : '');
    var tag = rec ? ' <span class="pill p-ok">recommended</span>'
            : (big ? ' <span class="pill p-warn">will not route</span>'
            : (tight ? ' <span class="pill p-warn">181 ft/s, 0.97 psi</span>' : ''));
    return '<tr'+bg+'><td>'+(rec?'<b>'+r.lab+'</b>':r.lab)+tag+'</td>'
      +'<td class="num">'+r.vmax+' ft/s</td>'
      +'<td class="num">'+r4Num(r.dp,3)+' psi</td>'
      +'<td class="num">'+r4Num(r.vol,2)+' L</td>'
      +'<td class="num">'+r4Num(r.sysL,2)+' L</td>'
      +'<td class="num">'+r4Num(r.sysX,2)+'&times;</td>'
      +'<td class="num">'+r.fill_ms+' ms</td>'
      +'<td class="num">'+r.box+' mm</td></tr>';
  }).join("");
}

/* ---------- table: velocity and dP at real inside diameters ---------- */
function fillR4Pipes(){
  var b=r4Body("t-r4pipes"); if(!b) return;
  b.innerHTML = R4.pipes.map(function(r){
    var rec = (r.od===2.50);
    var note = "";
    if(r.od===2.00) note=" <span class=\"note\">too small &mdash; 1.67 psi on the hot side alone</span>";
    if(r.od===3.00) note=" <span class=\"note\">lowest loss, largest to route</span>";
    return '<tr'+(rec?' style="background:rgba(56,211,159,.10)"':'')+'>'
      +'<td class="num">'+(rec?'<b>'+r.od.toFixed(2)+' in</b>':r.od.toFixed(2)+' in')+note+'</td>'
      +'<td class="num"><b>'+r4Num(r.id_mm,1)+' mm</b></td>'
      +'<td class="num">'+r.hot_fts+' ft/s <span class="note">M '+r4Num(r.hot_mach,3)+'</span></td>'
      +'<td class="num">'+r4Num(r.hot_dp,3)+' psi</td>'
      +'<td class="num">'+r.cold_fts+' ft/s <span class="note">M '+r4Num(r.cold_mach,3)+'</span></td>'
      +'<td class="num">'+r4Num(r.cold_dp,3)+' psi</td>'
      +'<td class="num">'+r4Num(r.vol_per_m,2)+' L/m</td></tr>';
  }).join("");
}

/* ---------- table: routing envelope ---------- */
function fillR4Route(){
  var b=r4Body("t-r4route"); if(!b) return;
  b.innerHTML = R4.routing.map(function(r){
    var rec = (r.od===2.50);
    return '<tr'+(rec?' style="background:rgba(56,211,159,.10)"':'')+'>'
      +'<td class="num">'+(rec?'<b>'+r.od.toFixed(2)+' in</b>':r.od.toFixed(2)+' in')+'</td>'
      +'<td class="num">'+r4Num(r.id_mm,1)+' mm</td>'
      +'<td class="num">'+r4Num(r.bare,1)+' mm</td>'
      +'<td class="num">'+r4Num(r.clamped,1)+' mm</td>'
      +'<td class="num">'+r.clr+' mm</td>'
      +'<td class="num"><b>'+r.box+' mm</b></td></tr>';
  }).join("");
}

/* ---------- table: hot layouts ---------- */
function fillR4Hot(){
  var b=r4Body("t-r4hot"); if(!b) return;
  var note={2.25:"Too fast. 0.96 psi of hot-side loss is 64% of the whole budget.",
            2.50:"Recommended. Bottom of the band, matches the compressor inlet AND the cold side, so one tube stock for the whole car.",
            2.75:"Saves 0.21 psi. Costs 0.7 L and a harder route past the turbine.",
            3.00:"Saves 0.33 psi &mdash; worth about 0.3 &deg;C. Not worth 1.5 L."};
  b.innerHTML = R4.hotLayouts.map(function(r){
    var rec = (r.od===2.50);
    var band = r.band==="in band"
      ? '<span class="pill p-ok">in band</span>'
      : '<span class="pill p-warn">'+r.band+'</span>';
    return '<tr'+(rec?' style="background:rgba(56,211,159,.10)"':'')+'>'
      +'<td class="num">'+(rec?'<b>'+r.od.toFixed(2)+' in</b>':r.od.toFixed(2)+' in')+'</td>'
      +'<td class="num">'+r.fts+' ft/s</td><td class="num">'+band+'</td>'
      +'<td class="num">'+r4Num(r.dp,3)+' psi</td>'
      +'<td class="num">'+r4Num(r.vol,2)+' L</td>'
      +'<td class="note">'+(note[r.od]||"")+'</td></tr>';
  }).join("");
}

/* ================= charts ================= */

/* 1. whp band across the rev range */
function drawR4Rpm(){
  var W=780,H=360,L=56,Rr=64,T=16,B=38, s=svg(W,H);
  var c=R4.curves, xLo=3000,xHi=8100,yLo=100,yHi=460, tLo=20,tHi=100;
  gridY(s,L,W,Rr,T,H,B,6,function(v){return v.toFixed(0);},yLo,yHi);
  gridX(s,L,W,Rr,T,H,B,it(xLo,xHi),function(v){return (v/1000).toFixed(1)+"k";},xLo,xHi);
  function X(r){return L+(W-Rr-L)*(r-xLo)/(xHi-xLo);}
  function Y(v){return T+(H-B-T)*(1-(Math.max(yLo,Math.min(yHi,v))-yLo)/(yHi-yLo));}
  function Y2(v){return T+(H-B-T)*(1-(Math.max(tLo,Math.min(tHi,v))-tLo)/(tHi-tLo));}
  /* band */
  var band=[],i;
  for(i=0;i<c.rpm.length;i++) band.push(X(c.rpm[i])+","+Y(c.b30hi[i]));
  for(i=c.rpm.length-1;i>=0;i--) band.push(X(c.rpm[i])+","+Y(c.b30lo[i]));
  el(s,"polygon",{points:band.join(" "),fill:"rgba(56,211,159,.22)",stroke:"none"});
  [["b20","#6f8098",1.8],["b25","#4ea3ff",1.8],["b34","#ffb347",1.8],["b30","#38d39f",3.0]]
    .forEach(function(k){
      var p=[]; for(var j=0;j<c.rpm.length;j++) p.push([X(c.rpm[j]),Y(c[k[0]][j])]);
      path(s,p,k[1],k[2]);
    });
  var pt=[]; for(i=0;i<c.rpm.length;i++) pt.push([X(c.rpm[i]),Y2(c.iat30[i])]);
  path(s,pt,"#c58cff",1.4,"4 3");
  /* rev-limit markers */
  [[7000,"stock 7,000"],[7500,"7,500"],[8000,"8,000"]].forEach(function(m){
    el(s,"line",{x1:X(m[0]),y1:T,x2:X(m[0]),y2:H-B,stroke:"#4a5768","stroke-width":1,
                 "stroke-dasharray":"3 4"});
    txt(s,X(m[0]),T+11,m[1],{fill:"#8fa0b4","font-size":10,"text-anchor":"middle"});
  });
  /* right axis for charge temp */
  for(i=0;i<=4;i++){
    var tv=tLo+(tHi-tLo)*i/4;
    txt(s,W-Rr+6,Y2(tv)+3.5,tv.toFixed(0),{fill:"#c58cff","font-size":10});
  }
  axes(s,L,Rr,T,B,W,H,"engine speed (rpm)","wheel horsepower (estimated)","charge temp °C");
  mount("ch_r4_rpm",s);
}

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

function drawR4All(){
  var jobs=[["fillR4Rpm",fillR4Rpm],["fillR4Surge",fillR4Surge],["fillR4Dyno",fillR4Dyno],
            ["fillR4Drive",fillR4Drive],["fillR4Duty",fillR4Duty],["fillR4Core",fillR4Core],
            ["fillR4Tb",fillR4Tb],["fillR4Cold",fillR4Cold],["fillR4Hot",fillR4Hot],
            ["fillR4Pipes",fillR4Pipes],["fillR4Route",fillR4Route],
            ["drawR4Rpm",drawR4Rpm],["drawR4Map",drawR4Map],["drawR4Dyno",drawR4Dyno],
            ["drawR4Drive",drawR4Drive],["drawR4Stack",drawR4Stack]];
  jobs.forEach(function(j){
    try{ j[1](); }catch(e){ if(window.console) console.error("r4 "+j[0]+" failed:",e); }
  });
}
try{ drawR4All(); }catch(e){ if(window.console) console.error(e); }
