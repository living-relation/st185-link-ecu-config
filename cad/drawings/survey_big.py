import os as _o, sys as _s
_TK=_o.environ.get('HANDBUILT_CAD') or _o.path.expanduser('~/projects/handbuilt-cad')   # handbuilt-cad checkout (drawing engine, checks, renders)
for _d in ('tools','tools/checks','tools/render','drawing'): _s.path.insert(0,_o.path.join(_TK,_d))
_s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__)))
if _o.environ.get('ST185_WORK'): _o.chdir(_o.environ['ST185_WORK'])
import sys
from build123d import *
for f in sys.argv[1:]:
    s=import_step(f)
    def walk(n,d=0):
        bb=n.bounding_box()
        print('  '*d+f"{n.label!r} solids={len(n.solids())} bb={bb.size.X:.0f}x{bb.size.Y:.0f}x{bb.size.Z:.0f} c=({bb.center().X:.0f},{bb.center().Y:.0f},{bb.center().Z:.0f})",flush=True)
        if d<2:
            for c in n.children: walk(c,d+1)
    print('==',f); walk(s)
