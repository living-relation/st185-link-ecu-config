import os as _o, sys as _s
_TK=_o.environ.get('HANDBUILT_CAD') or _o.path.expanduser('~/projects/handbuilt-cad')   # handbuilt-cad checkout (drawing engine, checks, renders)
for _d in ('tools','tools/checks','tools/render','drawing'): _s.path.insert(0,_o.path.join(_TK,_d))
_s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__)))
if _o.environ.get('ST185_WORK'): _o.chdir(_o.environ['ST185_WORK'])
import sys,glob,os
from build123d import *
for f in sorted(glob.glob('src/*/*.step')):
    if os.path.getsize(f)>15e6: print('SKIP big',f); continue
    try:
        s=import_step(f)
    except Exception as e: print('ERR',f,e); continue
    sol=s.solids(); bb=s.bounding_box()
    names=[c.label for c in getattr(s,'children',[])][:30]
    print(f"{f}: solids={len(sol)} bb={bb.size.X:.1f}x{bb.size.Y:.1f}x{bb.size.Z:.1f} min=({bb.min.X:.1f},{bb.min.Y:.1f},{bb.min.Z:.1f}) faces={len(s.faces())} kids={names}",flush=True)
