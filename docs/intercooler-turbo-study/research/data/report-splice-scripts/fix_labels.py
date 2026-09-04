import io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\projects\5sgte-intercooler-research\intercooler-report.html"
h = io.open(P, encoding="utf-8").read(); n0 = len(h)
subs = 0
def rep(old, new, note):
    global h, subs
    assert old in h, "NOT FOUND: " + note
    h = h.replace(old, new, 1); subs += 1
    print("  patched:", note)

# ---- 1. helper: nudge a label down until it clears already-placed labels ----
rep('function r2Fmt(n,d){return n.toFixed(d===undefined?0:d);}',
'''function r2Fmt(n,d){return n.toFixed(d===undefined?0:d);}

/* Keep scatter labels from sitting on top of each other. Each chart keeps its own
   list of placed label boxes; a new label is pushed down in 11 px steps until it
   clears every box already placed, then recorded. */
function r2Label(s,x,y,text,attrs,placed,halfW){
  var w = halfW || (String(text).length*5.4);
  var an = (attrs && attrs["text-anchor"]) || "start";
  var x0 = an === "end" ? x-w : x, x1 = an === "end" ? x : x+w;
  var yy = y, tries = 0;
  while(tries < 26){
    var hit = false;
    for(var i=0;i<placed.length;i++){
      var b = placed[i];
      if(x0 < b[2] && x1 > b[0] && Math.abs(yy-b[1]) < 10.5){ hit = true; break; }
    }
    if(!hit) break;
    yy += 11; tries++;
  }
  placed.push([x0,yy,x1]);
  return txt(s,x,yy,text,attrs);
}''', "r2Label helper")

# ---- 2. spool vs power scatter ----
rep('''    var an = X(p)>W-Rr-110 ? "end" : "start";
    txt(s,X(p)+(an==="start"?rad+5:-(rad+5)),Y(sp)+4,t.n.replace(" (current)",""),
        {fill:cur||rec?col:"#9fb0c4","font-size":10.2,"text-anchor":an,
         "font-weight":cur||rec?700:400});''',
'''    var an = X(p)>W-Rr-110 ? "end" : "start";
    r2Label(s,X(p)+(an==="start"?rad+5:-(rad+5)),Y(sp)+4,t.n.replace(" (current)",""),
        {fill:cur||rec?col:"#9fb0c4","font-size":10.2,"text-anchor":an,
         "font-weight":cur||rec?700:400}, placed, t.n.length*5.6);''',
    "spool/power labels")
rep('''  TD.turbos.forEach(function(t){
    var p=t.r[7200].whp, sp=t.spool;''',
'''  var placed=[];
  TD.turbos.forEach(function(t){
    var p=t.r[7200].whp, sp=t.spool;''', "spool/power placed[]")
# move the caption out of the label zone so it stops colliding
rep('''  txt(s,L+6,H-B-8,"bubble size = rotating inertia (turbine + compressor)",
      {fill:"#6f8098","font-size":9.5});''',
'''  txt(s,L+6,T+13,"bubble size = rotating inertia (turbine + compressor)",
      {fill:"#6f8098","font-size":9.5});''', "spool/power caption moved to top")

# ---- 3. inertia vs flow scatter ----
rep('''  TD.turbos.forEach(function(t){
    el(s,"line",{x1:X(t.choke),y1:Y(Math.min(yHi,t.j1)),x2:X(t.choke),y2:Y(Math.min(yHi,t.j2)),''',
'''  var placed=[];
  TD.turbos.forEach(function(t){
    el(s,"line",{x1:X(t.choke),y1:Y(Math.min(yHi,t.j1)),x2:X(t.choke),y2:Y(Math.min(yHi,t.j2)),''',
    "inertia placed[]")
rep('''    var an = X(t.choke)>W-Rr-105 ? "end" : "start";
    txt(s,X(t.choke)+(an==="start"?8:-8),Y(Math.min(yHi,t.j2))+11,
        t.n.replace(" (current)","").replace("Garrett ","").replace("Precision ","PT ").replace("Xona Rotor ",""),
        {fill:rec||cur?"#38d39f":"#9fb0c4","font-size":9.6,"text-anchor":an,
         "font-weight":rec||cur?700:400});''',
'''    var an = X(t.choke)>W-Rr-105 ? "end" : "start";
    var lab = t.n.replace(" (current)","").replace("Garrett ","").replace("Precision ","PT ").replace("Xona Rotor ","");
    r2Label(s,X(t.choke)+(an==="start"?8:-8),Y(Math.min(yHi,t.j2))+12,lab,
        {fill:cur?"#ff6b6b":(rec?"#38d39f":"#9fb0c4"),"font-size":9.6,"text-anchor":an,
         "font-weight":rec||cur?700:400}, placed, lab.length*5.3);''',
    "inertia labels")
# colour the current turbo's marker red so it matches its label and the reference line
rep('''    el(s,"circle",{cx:X(t.choke),cy:Y(Math.min(yHi,t.j2)),r:rec||cur?6:4.4,
                   fill:"#38d39f","fill-opacity":rec||cur?0.95:0.6});''',
'''    el(s,"circle",{cx:X(t.choke),cy:Y(Math.min(yHi,t.j2)),r:rec||cur?6:4.4,
                   fill:cur?"#ff6b6b":"#38d39f","fill-opacity":rec||cur?0.95:0.6});''',
    "inertia current-turbo marker colour")

# ---- 4. core trade scatter ----
rep('''  CORETRADE.forEach(function(c){''', '''  var placed=[];
  CORETRADE.forEach(function(c){''', "coretrade placed[]")
rep('''    var an = X(c.r)>W-Rr-140?"end":"start";
    txt(s,X(c.r)+(an==="start"?9:-9),Y(c.d)+4,c.n,
        {fill:col,"font-size":9.8,"text-anchor":an,"font-weight":c.base?700:400});''',
'''    var an = X(c.r)>W-Rr-150?"end":"start";
    r2Label(s,X(c.r)+(an==="start"?9:-9),Y(c.d)+4,c.n,
        {fill:col,"font-size":9.8,"text-anchor":an,"font-weight":c.base?700:400},
        placed, c.n.length*5.2);''', "coretrade labels")
# captions out of the plotted region
rep('''  txt(s,L+6,T+13,"free wins: cooler charge, no radiator cost",{fill:"#38d39f","font-size":9.8});''',
    '''  txt(s,L+6,H-B-30,"free wins: cooler charge, no radiator cost",{fill:"#38d39f","font-size":9.8});''',
    "coretrade caption 1 moved")
rep('''  txt(s,W-Rr-6,H-B-10,"trades: cooler charge, hotter radiator →",
      {fill:"#ffb347","font-size":9.8,"text-anchor":"end"});''',
'''  txt(s,W-Rr-6,H-B-14,"trades: cooler charge, hotter radiator \\u2192",
      {fill:"#ffb347","font-size":9.8,"text-anchor":"end"});''', "coretrade caption 2 moved")
rep('''  txt(s,X(11.5),Y(-11.0),"break-even",{fill:"#6f8098","font-size":9.5,"text-anchor":"end"});''',
    '''  txt(s,X(5.6),Y(-4.6),"break-even",{fill:"#6f8098","font-size":9.5,"text-anchor":"end"});''',
    "break-even label moved off the markers")

io.open(P,"w",encoding="utf-8",newline="").write(h)
print("\n%d substitutions, report %d -> %d bytes" % (subs, n0, len(h)))
