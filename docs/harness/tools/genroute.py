"""Generic orthogonal router for a harness.design doc JSON (schematic view). Keeps node positions; rewrites
wire / core / shield layout points. Dan's rules 2026-11-01."""
import json, sys, collections
from router import Router, order_groups
def run(d, mid=None, step=30):
    R=Router(); node={}; anc={}
    W=lambda n: n.get('width',150)
    for c in d['connectors']:
        p=c['schematicPosition']; h=30+30*len(c['cavities']); R.box(c['id'],p['x'],p['y'],W(c),h); node[c['id']]=('conn',c)
    for t in d.get('terminals',[]):
        p=t['schematicPosition']; R.box(t['id'],p['x'],p['y'],W(t),30); node[t['id']]=('term',t)
    for s in d.get('splices',[])+d.get('resistors',[])+d.get('diodes',[]):
        p=s['schematicPosition']; R.box(s['id'],p['x'],p['y'],30,30); node[s['id']]=('pt',s)
    for c in d.get('cables',[]):
        p=c['schematicPosition']; n=len(c['cores'])+(1 if 'shield' in c else 0); R.box(c['id'],p['x'],p['y'],60,30+30*n); node[c['id']]=('cab',c)
    xs=[n[1]['schematicPosition']['x'] for n in node.values() if n[0] in('conn','term')]
    if mid is None: mid=(min(xs)+max(xs))/2
    def anchor(e):
        k,n=node[e['id']]; p=n['schematicPosition']
        if k=='conn':
            i=[cv['id'] for cv in n['cavities']].index(e['handle']); y=p['y']+30*(i+1)+15
            return (p['x']+W(n) if p['x']<mid else p['x'], y, 'R' if p['x']<mid else 'L')
        if k=='term': return (p['x']+W(n) if p['x']<mid else p['x'], p['y']+15, 'R' if p['x']<mid else 'L')
        h=e['handle']
        if h in('Left','PIN1') and n['id'].startswith(('r','d')): return (p['x'],p['y']+15,'L')
        if h in('Right','PIN2') and n['id'].startswith(('r','d')): return (p['x']+30,p['y']+15,'R')
        return (p['x']+15,p['y']+15,'C')
    segs=[]
    def net_of(*es):
        for e in es:
            if e and node[e['id']][0]=='pt' and e['handle']=='Splice': return e['id']
        return None
    for w in d['wires']:
        a,b=anchor(w['source']),anchor(w['target'])
        L,Q=(b,a) if a[0]>b[0] else (a,b)
        segs.append(dict(k=('w',w['id']),P=L[:2],Q=Q[:2],ends={w['source']['id'],w['target']['id']},net=net_of(w['source'],w['target']),flip=a[0]>b[0]))
    for c in d.get('cables',[]):
        p=c['schematicPosition']; seq=c['cores']+([c['shield']] if 'shield' in c else [])
        for i,co in enumerate(seq):
            yc=p['y']+30*(i+1)+15
            for side in ('source','target'):
                e=co.get(side)
                if not e: continue
                q=anchor(e)
                if q[0]<p['x']: segs.append(dict(k=('c',c['id'],co['id'],side),P=q[:2],Q=(p['x'],yc),ends={e['id'],c['id']},net=net_of(e),left=True))
                else: segs.append(dict(k=('c',c['id'],co['id'],side),P=(p['x']+60,yc),Q=q[:2],ends={e['id'],c['id']},net=net_of(e),left=False))
    allx=sorted({b.x for b in R.boxes.values()}|{b.x+b.w for b in R.boxes.values()})
    lo,hi=min(allx),max(allx)
    LANES=[x for x in range(int(lo)-int(lo)%30+15,int(hi),step) if not any(b.x-10<x<b.x+b.w+10 for b in R.boxes.values() if b.h>30*3)]
    res={}
    for s in segs:   # straights first
        if s['P'][1]==s['Q'][1] and R.route(s['P'],s['Q'],s['ends'],[],s['net'])==[]: res[s['k']]=[]
    # bundle by the left node: order lanes per left node to cut crossings
    byleft=collections.defaultdict(list)
    for s in segs:
        if s['k'] in res: continue
        byleft[round(s['P'][0])].append(s)
    netlane=collections.defaultdict(list)
    for x0 in sorted(byleft):
        ss=byleft[x0]
        cand=[x for x in LANES if x>x0]
        grp=collections.defaultdict(list)
        for s in ss: grp[tuple(sorted(s['ends']))].append(s['k'])
        sy={s['k']:(s['P'][1],s['Q'][1]) for s in ss}
        order,_=order_groups(list(grp.values()),sy,cand[0] if cand else 0,step,iters=3000)
        by={s['k']:s for s in ss}; ptr=0
        for k in order:
            s=by[k]; ok=None
            pref=netlane[s['net']] if s['net'] else []
            for x in pref+[x for x in cand[ptr:] if x<s['Q'][0]]:
                r_=R.route(s['P'],s['Q'],s['ends'],[x],s['net'])
                if r_ is not None:
                    ok=r_
                    if x not in pref: ptr=cand.index(x)+1
                    break
            if ok is None:
                ok=R.route(s['P'],s['Q'],s['ends'],[x for x in cand if x<s['Q'][0]],s['net'])
            if ok and s['net']: netlane[s['net']].append(ok[0][0])
            res[k]=ok
    for k,v in list(res.items()):    # Z fallback
        if v is not None: continue
        s=next(t for t in segs if t['k']==k); P,Q=s['P'],s['Q']; done=False
        if P[0]==Q[0]:
            # both ends on the left column: run down the outside (left) of the column
            ex=[b for b in R.boxes.values() if b.id in s['ends']]
            lx=min(b.x for b in ex)
            P2,Q2=(lx,P[1]),(lx,Q[1])
            for x in range(int(lx)-30,int(lx)-600,-30):
                pts=[P2,(x,P[1]),(x,Q[1]),Q2]
                if R.free(pts,s['ends'],s['net']): R.commit(pts,s['net']); res[k]=pts[1:-1]; done=True; break
            if done: continue
            for x in list(range(int(P[0])+15,int(P[0])+2300,15)):
                pts=[P,(x,P[1]),(x,Q[1]),Q]
                if R.free(pts,s['ends'],s['net']): R.commit(pts,s['net']); res[k]=pts[1:-1]; done=True; break
            if done: continue
        for ym in [Q[1]+dd for dd in (30,-30,60,-60,90,-90,120,-120,150,-150)]:
            for x1 in [x for x in LANES if P[0]<x<Q[0]][::-1]:
                for x2 in [x for x in LANES if x1<x<Q[0]]:
                    pts=[P,(x1,P[1]),(x1,ym),(x2,ym),(x2,Q[1]),Q]
                    if R.free(pts,s['ends'],s['net']): R.commit(pts,s['net']); res[k]=pts[1:-1]; done=True; break
                if done: break
            if done: break
    return R,segs,res
def apply(d,segs,res,tag='r'):
    ST=lambda p:{'x':p[0]-15,'y':p[1]-15}
    bad=[]
    def lp(pre,pts): return [{'id':'%s_%s%d'%(pre,tag,i),'schematicPosition':ST(p)} for i,p in enumerate(pts)] or None
    W={w['id']:w for w in d['wires']}
    for s in segs:
        r=res.get(s['k'])
        if r is None: bad.append(s['k'])
        if s['k'][0]=='w':
            w=W[s['k'][1]]; pts=(r or [])[::-1] if s['flip'] else (r or [])
            v=lp(w['id'],pts)
            if v: w['layoutPoints']=v
            else: w.pop('layoutPoints',None)
        else:
            _,cid,coid,side=s['k']
            c=next(c for c in d['cables'] if c['id']==cid)
            co=next(x for x in c['cores']+([c['shield']] if 'shield' in c else []) if x['id']==coid)
            key=side+'LayoutPoints'
            pts=(r or [])
            pts=pts[::-1] if s['left'] else pts
            if not s['left'] and s['Q'][0]-s['P'][0] < 240: pts=[]   # cable right beside its device: let the app draw it
            v=lp(coid+side[0],pts)
            if v: co[key]=v
            else: co.pop(key,None)
    return bad


if __name__ == '__main__':
    # python docs/harness/tools/genroute.py <doc.json> <out.json>   (a harness.design document JSON, schematic view)
    src, dst = sys.argv[1:3]
    d = json.load(open(src))
    R, segs, res = run(d)
    print('unrouted', apply(d, segs, res))
    json.dump(d, open(dst, 'w'))
