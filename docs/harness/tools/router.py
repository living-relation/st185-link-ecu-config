"""Orthogonal schematic router for harness.design docs (Dan's format rules 2026-11-01)."""
import itertools, random, collections
G=30
class Box:
    def __init__(s,id,x,y,w,h): s.id,s.x,s.y,s.w,s.h=id,x,y,w,h
    def hit_h(s,y,x1,x2):   # horizontal line at drawn y (stored+15)
        a,b=min(x1,x2),max(x1,x2); return s.y<y<s.y+s.h and a<s.x+s.w and b>s.x
    def hit_v(s,x,y1,y2):
        a,b=min(y1,y2),max(y1,y2); return s.x<x<s.x+s.w and a<s.y+s.h and b>s.y
class Router:
    def __init__(s): s.boxes={}; s.vsegs=[]; s.hsegs=[]
    def box(s,id,x,y,w,h): s.boxes[id]=Box(id,x,y,w,h)
    def free(s,pts,ends,net=None):
        # pts: drawn polyline; ends: box ids allowed
        for (x1,y1),(x2,y2) in zip(pts,pts[1:]):
            for b in s.boxes.values():
                if b.id in ends: continue
                if y1==y2 and b.hit_h(y1,x1,x2): return False
                if x1==x2 and b.hit_v(x1,y1,y2): return False
            if x1==x2:
                for (vx,a,c,nn) in s.vsegs:
                    if net is not None and nn==net: continue
                    if vx==x1 and min(y1,y2)<max(a,c)+8 and max(y1,y2)>min(a,c)-8: return False
            if y1==y2:
                for (hy,a,c,nn) in s.hsegs:
                    if net is not None and nn==net: continue
                    if hy==y1 and min(x1,x2)<max(a,c)-1 and max(x1,x2)>min(a,c)+1: return False
        return True
    def commit(s,pts,net=None):
        for (x1,y1),(x2,y2) in zip(pts,pts[1:]):
            if x1==x2 and y1!=y2: s.vsegs.append((x1,y1,y2,net))
            if y1==y2 and x1!=x2: s.hsegs.append((y1,x1,x2,net))
    def route(s,P,Q,ends,lanes,net=None):
        """P=(x_out,yrow) left end, Q=(x_in,yrow) right end, drawn coords. lanes: candidate drawn x list in preference order.
        returns list of drawn bend points (empty = straight) or None"""
        (xa,ya),(xb,yb)=P,Q
        if ya==yb:
            pts=[P,Q]
            if s.free(pts,ends,net): s.commit(pts,net); return []
        for x in lanes:
            if not (min(xa,xb)<x<max(xa,xb)): continue
            pts=[P,(x,ya),(x,yb),Q]
            if s.free(pts,ends,net): s.commit(pts,net); return [(x,ya),(x,yb)]
        return None
def crossings(order, segs, x0, step):
    """segs: id -> (y_src, y_dst) for conductors leaving a left column at y_src, jogging at its lane, going right at y_dst.
    order: list of ids left->right. count crossings."""
    xs={c:x0+i*step for i,c in enumerate(order)}; n=0
    for i,j in itertools.combinations(order,2):
        (a1,b1),(a2,b2)=segs[i],segs[j]
        xi,xj=xs[i],xs[j]
        if xi>xj: i,j,a1,b1,a2,b2,xi,xj=j,i,a2,b2,a1,b1,xj,xi
        # i is left lane. i's dst horizontal (from xi rightwards) crosses j's vertical
        if min(a2,b2)<b1<max(a2,b2): n+=1
        # j's src horizontal (from left edge to xj) crosses i's vertical
        if min(a1,b1)<a2<max(a1,b1): n+=1
        if a2==b1: n+=1000      # j's source row is i's destination row and j's lane is right of i: overlap
    return n
def order_groups(groups, segs, x0, step, iters=4000, seed=1):
    """groups: list of lists of conductor ids (kept together). returns flattened order minimising crossings."""
    rnd=random.Random(seed)
    def inner(g):   # within a group: down-going -> upper source further right; up-going -> lower source further right
        down=[c for c in g if segs[c][1]>=segs[c][0]]; up=[c for c in g if segs[c][1]<segs[c][0]]
        return sorted(up,key=lambda c:-segs[c][0])+sorted(down,key=lambda c:-segs[c][0]) if False else \
               sorted(g,key=lambda c:(segs[c][1]-segs[c][0]>=0, -segs[c][0] if segs[c][1]>=segs[c][0] else segs[c][0]))
    gs=[inner(g) for g in groups]
    # initial: sort groups by mean destination y
    gs.sort(key=lambda g: sum(segs[c][1] for c in g)/len(g))
    flat=lambda L:[c for g in L for c in g]
    best=crossings(flat(gs),segs,x0,step)
    for _ in range(iters):
        i,j=rnd.randrange(len(gs)),rnd.randrange(len(gs))
        if i==j: continue
        t=gs[:]; g=t.pop(i); t.insert(j,g)
        c=crossings(flat(t),segs,x0,step)
        if c<=best: gs,best=t,c
    return flat(gs),best
