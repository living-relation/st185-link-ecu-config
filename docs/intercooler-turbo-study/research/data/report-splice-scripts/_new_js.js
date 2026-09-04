
/* ================================================================
   ROUND TWO - turbo selection, redline sensitivity, core trade
   Data block TD is emitted by make_chartdata.py.
   ================================================================ */
var R2C = ["#ff6b6b","#ffb347","#38d39f","#4ea3ff","#c58cff","#79bbff",
           "#f5a97f","#7dd3a0","#ff8f5a","#9fb0c4","#e0c060","#60d0d0"];

function r2Fmt(n,d){return n.toFixed(d===undefined?0:d);}

/* ---------- chart: the two VE curves ---------- */
function drawVE(){
  var W=780,H=340,L=54,Rr=54,T=16,B=38;
  var s=svg(W,H);
  var xLo=5000,xHi=8700,yLo=0.60,yHi=1.05,zLo=0.30,zHi=0.70;
  gridY(s,L,W,Rr,T,H,B,9,function(v){return v.toFixed(2);},yLo,yHi);
  gridX(s,L,W,Rr,T,H,B,6,function(v){return (v/1000).toFixed(1)+"k";},xLo,xHi);
  function X(r){return L+(W-Rr-L)*(r-xLo)/(xHi-xLo);}
  function Y(v){return T+(H-B-T)*(1-(v-yLo)/(yHi-yLo));}
  function YZ(v){return T+(H-B-T)*(1-(v-zLo)/(zHi-zLo));}
  var d=TD.ve, series=[["r1","#ff6b6b",2.6],["m16","#4ea3ff",2.8],
                       ["m10","#38d39f",1.8],["m20","#ffb347",1.8]];
  // shaded band between optimistic and pessimistic
  var band=[];
  for(var i=0;i<d.rpm.length;i++) band.push([X(d.rpm[i]),Y(d.m10[i])]);
  for(var i=d.rpm.length-1;i>=0;i--) band.push([X(d.rpm[i]),Y(d.m20[i])]);
  el(s,"path",{d:band.map(function(p,i){return (i?"L":"M")+p[0].toFixed(1)+" "+p[1].toFixed(1);}).join(" ")+" Z",
    fill:"#4ea3ff","fill-opacity":0.10,stroke:"none"});
  series.forEach(function(sr){
    var pts=[]; for(var i=0;i<d.rpm.length;i++) pts.push([X(d.rpm[i]),Y(d[sr[0]][i])]);
    path(s,pts,sr[1],sr[2], sr[0]=="m10"||sr[0]=="m20" ? "4 3" : null);
  });
  // Mach index on the right axis
  var zp=[]; for(var i=0;i<d.rpm.length;i++) zp.push([X(d.rpm[i]),YZ(d.Z[i])]);
  path(s,zp,"#6f8098",1.4,"2 3");
  for(var i=0;i<=5;i++){
    var y=T+(H-B-T)*i/5, v=zHi-(zHi-zLo)*i/5;
    txt(s,W-Rr+6,y+3.5,"Z "+v.toFixed(2),{fill:"#6f8098","font-size":9.5});
  }
  // Z = 0.50 knee marker
  var yk=YZ(0.50);
  el(s,"line",{x1:L,y1:yk,x2:W-Rr,y2:yk,stroke:"#6f8098","stroke-width":1,"stroke-dasharray":"6 4"});
  txt(s,L+6,yk-5,"Z = 0.50  head starts to restrict above here",{fill:"#8c9cb0","font-size":10});
  // redline markers
  [[6650,"round-1 peak"],[7200,"recommended"],[7800,"race only"]].forEach(function(m){
    var x=X(m[0]);
    el(s,"line",{x1:x,y1:T,x2:x,y2:H-B,stroke:"#38d39f","stroke-width":1,"stroke-dasharray":"3 4","stroke-opacity":0.55});
    txt(s,x+4,T+12,m[1],{fill:"#38d39f","font-size":9.5});
  });
  axes(s,L,Rr,T,B,W,H,"Engine speed, rpm","Volumetric efficiency","Taylor Mach index Z");
  mount("ch_ve",s);
}

/* ---------- chart: power vs redline, all turbos ---------- */
function drawPwrRpm(){
  var W=780,H=390,L=54,Rr=118,T=16,B=38;
  var s=svg(W,H);
  var xLo=5500,xHi=8600,yLo=350,yHi=600;
  gridY(s,L,W,Rr,T,H,B,5,function(v){return v.toFixed(0);},yLo,yHi);
  gridX(s,L,W,Rr,T,H,B,6,function(v){return (v/1000).toFixed(1)+"k";},xLo,xHi);
  function X(r){return L+(W-Rr-L)*(r-xLo)/(xHi-xLo);}
  function Y(v){return T+(H-B-T)*(1-(v-yLo)/(yHi-yLo));}
  TD.turbos.forEach(function(t,i){
    var pts=t.curve.map(function(p){return [X(p[0]),Y(Math.max(yLo,Math.min(yHi,p[1])))];});
    var cur = t.n.indexOf("7163")>=0, rec = t.n.indexOf("G25-770")>=0;
    path(s,pts,cur?"#ff6b6b":(rec?"#38d39f":R2C[i%R2C.length]), cur||rec?3.0:1.5, cur||rec?null:"3 2");
    var last=pts[pts.length-1];
    if(cur||rec) el(s,"circle",{cx:last[0],cy:last[1],r:4,fill:cur?"#ff6b6b":"#38d39f"});
  });
  // recommended redline band
  var x1=X(6650), x2=X(7200);
  el(s,"rect",{x:x1,y:T,width:x2-x1,height:H-B-T,fill:"#38d39f","fill-opacity":0.07});
  txt(s,(x1+x2)/2,T+12,"6,650 -> 7,200",{fill:"#38d39f","font-size":9.5,"text-anchor":"middle"});
  el(s,"line",{x1:X(7500),y1:T,x2:X(7500),y2:H-B,stroke:"#ffb347","stroke-width":1.4,"stroke-dasharray":"5 4"});
  txt(s,X(7500)+4,H-B-8,"7,500 mechanical ceiling",{fill:"#ffb347","font-size":9.5});
  axes(s,L,Rr,T,B,W,H,"Redline, rpm","Wheel horsepower at the compressor ceiling","");
  mount("ch_pwr_rpm",s);
  // legend
  var lg=C("lg_pwr"); if(lg){
    lg.innerHTML = TD.turbos.map(function(t,i){
      var cur=t.n.indexOf("7163")>=0, rec=t.n.indexOf("G25-770")>=0;
      var col=cur?"#ff6b6b":(rec?"#38d39f":R2C[i%R2C.length]);
      return '<span><i style="background:'+col+'"></i>'+t.n+(cur?" (yours)":(rec?" (recommended)":""))+'</span>';
    }).join("");
  }
}

/* ---------- chart: spool threshold vs peak power ---------- */
function drawSpoolPwr(){
  var W=780,H=360,L=58,Rr=26,T=18,B=42;
  var s=svg(W,H);
  var xLo=440,xHi=600,yLo=3800,yHi=6300;
  gridY(s,L,W,Rr,T,H,B,5,function(v){return (v/1000).toFixed(1)+"k";},yLo,yHi);
  gridX(s,L,W,Rr,T,H,B,6,function(v){return v.toFixed(0);},xLo,xHi);
  function X(v){return L+(W-Rr-L)*(v-xLo)/(xHi-xLo);}
  function Y(v){return T+(H-B-T)*(1-(v-yLo)/(yHi-yLo));}
  TD.turbos.forEach(function(t){
    var p=t.r[7200].whp, sp=t.spool;
    var cur=t.n.indexOf("7163")>=0, rec=t.n.indexOf("G25-770")>=0;
    var col=cur?"#ff6b6b":(rec?"#38d39f":"#4ea3ff");
    var rad=Math.max(4, Math.min(15, 5+Math.sqrt(t.j2)*5));
    el(s,"circle",{cx:X(p),cy:Y(sp),r:rad,fill:col,"fill-opacity":cur||rec?0.85:0.32,
                   stroke:col,"stroke-width":1.4});
    var an = X(p)>W-Rr-110 ? "end" : "start";
    txt(s,X(p)+(an==="start"?rad+5:-(rad+5)),Y(sp)+4,t.n.replace(" (current)",""),
        {fill:cur||rec?col:"#9fb0c4","font-size":10.2,"text-anchor":an,
         "font-weight":cur||rec?700:400});
  });
  txt(s,W-Rr-6,H-B-8,"better →",{fill:"#38d39f","font-size":11,"text-anchor":"end"});
  txt(s,L+6,H-B-8,"bubble size = rotating inertia (turbine + compressor)",
      {fill:"#6f8098","font-size":9.5});
  axes(s,L,Rr,T,B,W,H,"Peak wheel horsepower at 7,200 rpm","Spool threshold, rpm (lower is better)","");
  mount("ch_spool_pwr",s);
}

/* ---------- chart: inertia vs flow ---------- */
function drawInertiaFlow(){
  var W=780,H=340,L=58,Rr=26,T=18,B=42;
  var s=svg(W,H);
  var xLo=55,xHi=110,yLo=0,yHi=3.0;
  gridY(s,L,W,Rr,T,H,B,6,function(v){return v.toFixed(1);},yLo,yHi);
  gridX(s,L,W,Rr,T,H,B,6,function(v){return v.toFixed(0);},xLo,xHi);
  function X(v){return L+(W-Rr-L)*(v-xLo)/(xHi-xLo);}
  function Y(v){return T+(H-B-T)*(1-(v-yLo)/(yHi-yLo));}
  // reference line at J = 1.0 (the current turbo)
  el(s,"line",{x1:L,y1:Y(1.0),x2:W-Rr,y2:Y(1.0),stroke:"#ff6b6b","stroke-width":1.2,"stroke-dasharray":"5 4"});
  txt(s,W-Rr-4,Y(1.0)-5,"EFR 7163 = 1.00",{fill:"#ff6b6b","font-size":9.5,"text-anchor":"end"});
  TD.turbos.forEach(function(t){
    el(s,"line",{x1:X(t.choke),y1:Y(Math.min(yHi,t.j1)),x2:X(t.choke),y2:Y(Math.min(yHi,t.j2)),
                 stroke:"#3a4757","stroke-width":1});
    el(s,"circle",{cx:X(t.choke),cy:Y(Math.min(yHi,t.j1)),r:3.6,fill:"#4ea3ff","fill-opacity":0.75});
    var rec=t.n.indexOf("G25-770")>=0, cur=t.n.indexOf("7163")>=0;
    el(s,"circle",{cx:X(t.choke),cy:Y(Math.min(yHi,t.j2)),r:rec||cur?6:4.4,
                   fill:"#38d39f","fill-opacity":rec||cur?0.95:0.6});
    var an = X(t.choke)>W-Rr-105 ? "end" : "start";
    txt(s,X(t.choke)+(an==="start"?8:-8),Y(Math.min(yHi,t.j2))+11,
        t.n.replace(" (current)","").replace("Garrett ","").replace("Precision ","PT ").replace("Xona Rotor ",""),
        {fill:rec||cur?"#38d39f":"#9fb0c4","font-size":9.6,"text-anchor":an,
         "font-weight":rec||cur?700:400});
  });
  txt(s,L+6,T+12,"lower-right is better: light rotating mass, lots of flow",
      {fill:"#6f8098","font-size":9.8});
  axes(s,L,Rr,T,B,W,H,"Compressor choke flow, lb/min","Rotating inertia, EFR 7163 = 1.00","");
  mount("ch_inertia_flow",s);
}

/* ---------- chart: boost required vs rpm ---------- */
function drawBoostRpm(){
  var W=780,H=340,L=54,Rr=26,T=16,B=38;
  var s=svg(W,H);
  var xLo=5500,xHi=8600,yLo=20,yHi=60;
  gridY(s,L,W,Rr,T,H,B,8,function(v){return v.toFixed(0);},yLo,yHi);
  gridX(s,L,W,Rr,T,H,B,6,function(v){return (v/1000).toFixed(1)+"k";},xLo,xHi);
  function X(r){return L+(W-Rr-L)*(r-xLo)/(xHi-xLo);}
  function Y(v){return T+(H-B-T)*(1-(v-yLo)/(yHi-yLo));}
  var cols={400:"#38d39f",450:"#4ea3ff",500:"#ffb347",550:"#ff8f5a",600:"#ff6b6b"};
  Object.keys(TD.boost).forEach(function(k){
    var pts=TD.boost[k].map(function(p){return [X(p[0]),Y(Math.max(yLo,Math.min(yHi,p[1])))];});
    path(s,pts,cols[k],2.4);
    var last=pts[pts.length-1];
    txt(s,last[0]-4,last[1]-6,k+" whp",{fill:cols[k],"font-size":10,"text-anchor":"end"});
  });
  // 30 psi sensible ceiling
  el(s,"line",{x1:L,y1:Y(30),x2:W-Rr,y2:Y(30),stroke:"#9fb0c4","stroke-width":1.8,"stroke-dasharray":"7 4"});
  txt(s,L+6,Y(30)-6,"30 psi - sensible street ceiling on this bottom end",
      {fill:"#9fb0c4","font-size":10});
  el(s,"rect",{x:L,y:T,width:W-Rr-L,height:Y(42)-T,fill:"#ff6b6b","fill-opacity":0.06});
  txt(s,W-Rr-6,T+13,"above 42 psi: no candidate compressor can do it",
      {fill:"#ff8f8f","font-size":9.8,"text-anchor":"end"});
  var xr=X(7200);
  el(s,"line",{x1:xr,y1:T,x2:xr,y2:H-B,stroke:"#38d39f","stroke-width":1.3,"stroke-dasharray":"4 3"});
  txt(s,xr+4,H-B-8,"7,200 recommended",{fill:"#38d39f","font-size":9.5});
  axes(s,L,Rr,T,B,W,H,"Redline, rpm","Boost required, psi","");
  mount("ch_boost_rpm",s);
}

/* ---------- chart: core size trade ---------- */
var CORETRADE=[
 {n:"610x300x75  (24x12x3)", d:0.0,  r:0.0,  base:true},
 {n:"610x300x100 (24x12x4)", d:-7.4, r:8.2},
 {n:"610x300x115 (24x12x4.5)",d:-10.6,r:12.6},
 {n:"610x340x75 taller",     d:-2.8, r:0.9},
 {n:"685x300x75 wider",      d:-2.6, r:0.9},
 {n:"685x340x75 both",       d:-5.3, r:1.8},
 {n:"685x340x100 everything",d:-12.4,r:10.0}
];
function drawCoreTrade(){
  var W=780,H=330,L=58,Rr=26,T=18,B=42;
  var s=svg(W,H);
  var xLo=-1,xHi=14,yLo=-14,yHi=1;
  gridY(s,L,W,Rr,T,H,B,5,function(v){return v.toFixed(0);},yLo,yHi);
  gridX(s,L,W,Rr,T,H,B,6,function(v){return v.toFixed(0);},xLo,xHi);
  function X(v){return L+(W-Rr-L)*(v-xLo)/(xHi-xLo);}
  function Y(v){return T+(H-B-T)*(1-(v-yLo)/(yHi-yLo));}
  // break-even: charge gain equals radiator loss
  path(s,[[X(0),Y(0)],[X(13),Y(-13)]],"#6f8098",1.2,"5 4");
  txt(s,X(11.5),Y(-11.0),"break-even",{fill:"#6f8098","font-size":9.5,"text-anchor":"end"});
  CORETRADE.forEach(function(c){
    var free = c.r < 3;
    var col = c.base?"#9fb0c4":(free?"#38d39f":"#ffb347");
    el(s,"circle",{cx:X(c.r),cy:Y(c.d),r:c.base?7:5.5,fill:col,"fill-opacity":0.9});
    var an = X(c.r)>W-Rr-140?"end":"start";
    txt(s,X(c.r)+(an==="start"?9:-9),Y(c.d)+4,c.n,
        {fill:col,"font-size":9.8,"text-anchor":an,"font-weight":c.base?700:400});
  });
  txt(s,L+6,T+13,"free wins: cooler charge, no radiator cost",{fill:"#38d39f","font-size":9.8});
  txt(s,W-Rr-6,H-B-10,"trades: cooler charge, hotter radiator →",
      {fill:"#ffb347","font-size":9.8,"text-anchor":"end"});
  axes(s,L,Rr,T,B,W,H,"Extra heat onto the radiator, °C (worse →)",
       "Charge temperature change, °C (better ↓)","");
  mount("ch_coretrade",s);
}

/* ---------- tables ---------- */
function fillR2Tables(){
  var tb=document.querySelector("#tb_rpm tbody");
  if(tb){
    tb.innerHTML = TD.turbos.map(function(t){
      var cur=t.n.indexOf("7163")>=0, rec=t.n.indexOf("G25-770")>=0;
      var nm = t.n + (cur?' <span class="pill p-bad">yours</span>'
                        :(rec?' <span class="pill p-ok">pick</span>':""));
      var cells = TD.redlines.map(function(r){
        var d=t.r[r];
        var pill = d.lim==="PR" ? '<span class="pill p-info">PR</span>'
                                : '<span class="pill p-warn">choke</span>';
        return '<td class="num"><b>'+d.whp+'</b> whp<br><span class="note">'
               +d.b.toFixed(1)+' psi '+pill+'</span></td>';
      }).join("");
      return '<tr'+(cur||rec?' style="background:#1b222c"':'')+'><td>'+nm+'</td>'+cells
        +'<td class="num">'+(t.cross?t.cross.toLocaleString():"&gt;9,000")+'</td>'
        +'<td class="num">'+t.spool.toLocaleString()+'</td>'
        +'<td class="num">$'+t.price.toLocaleString()+'</td></tr>';
    }).join("");
  }
  var tg=document.querySelector("#tb_gain tbody");
  if(tg){
    tg.innerHTML = TD.turbos.map(function(t){
      var a=t.r[6650].whp,b=t.r[7200].whp,c=t.r[7800].whp;
      function g(x){
        var d=x-a, pc=(x/a-1)*100;
        var cls = d<=5?"p-bad":(d<20?"p-warn":"p-ok");
        return '<td class="num"><span class="pill '+cls+'">'+(d>=0?"+":"")+d
               +' whp</span> <span class="note">'+(pc>=0?"+":"")+pc.toFixed(1)+'%</span></td>';
      }
      var cur=t.n.indexOf("7163")>=0, rec=t.n.indexOf("G25-770")>=0;
      return '<tr'+(cur||rec?' style="background:#1b222c"':'')+'><td>'+t.n+'</td>'
        +'<td class="num">'+a+'</td><td class="num">'+b+'</td>'+g(b)
        +'<td class="num">'+c+'</td>'+g(c)+'</tr>';
    }).join("");
  }
}

function initRound2(){
  try{
    fillR2Tables();
    drawVE(); drawPwrRpm(); drawSpoolPwr(); drawInertiaFlow();
    drawBoostRpm(); drawCoreTrade();
  }catch(e){ if(window.console) console.error("round-two render failed:", e); }
}
