import os as _o, sys as _s
_TK=_o.environ.get('HANDBUILT_CAD') or _o.path.expanduser('~/projects/handbuilt-cad')   # handbuilt-cad checkout (drawing engine, checks, renders)
for _d in ('tools','tools/checks','tools/render','drawing'): _s.path.insert(0,_o.path.join(_TK,_d))
_s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__)))
if _o.environ.get('ST185_WORK'): _o.chdir(_o.environ['ST185_WORK'])
import sys,json
from build123d import *
a=import_step(sys.argv[1]); S=[]
def walk(n,path=''):
    lab=getattr(n,'label','') or ''; kids=list(getattr(n,'children',[]) or [])
    if kids:
        for c in kids: walk(c,path+'/'+lab)
    else:
        for s in n.solids(): S.append((path+'/'+lab,s))
walk(a)
out=[]
for i,(l,s) in enumerate(S):
    b=s.bounding_box(); out.append(dict(i=i,l=l.split('/')[-1],v=round(s.volume,2),mn=[round(t,2) for t in b.min],mx=[round(t,2) for t in b.max]))
json.dump(out,open(sys.argv[2],'w'))
print(len(out))
