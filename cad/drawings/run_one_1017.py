import os as _o, sys as _s
_TK=_o.environ.get('HANDBUILT_CAD') or _o.path.expanduser('~/projects/handbuilt-cad')   # handbuilt-cad checkout (drawing engine, checks, renders)
for _d in ('tools','tools/checks','tools/render','drawing'): _s.path.insert(0,_o.path.join(_TK,_d))
_s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__)))
if _o.environ.get('ST185_WORK'): _o.chdir(_o.environ['ST185_WORK'])
_o.makedirs('previews',exist_ok=True)
import sys, specs_1017, part
name=sys.argv[1]; sp=specs_1017.PARTS[name]
_o.makedirs('out/'+sp['job'],exist_ok=True)
pdf=f"out/{sp['job']}/{sp['pn']}.pdf"   # no rev in filenames (Dan 2026-10-17); rev is in the title block
dxf=f"out/{sp['job']}/{sp['pn']}.dxf" if sp.get('dxf') else None   # machined parts get a DXF too (cnc-part-check)
s=part.make_part(sp,pdf,dxf,f"previews/{sp['pn']}")
print('OK',name,s)
