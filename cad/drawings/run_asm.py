import os as _o, sys as _s
_TK=_o.environ.get('HANDBUILT_CAD') or _o.path.expanduser('~/projects/handbuilt-cad')   # handbuilt-cad checkout (drawing engine, checks, renders)
for _d in ('tools','tools/checks','tools/render','drawing'): _s.path.insert(0,_o.path.join(_TK,_d))
_s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__)))
if _o.environ.get('ST185_WORK'): _o.chdir(_o.environ['ST185_WORK'])
_o.makedirs('previews',exist_ok=True)
import sys,os
pass
import aspecs, asm
k=sys.argv[1]; sp=aspecs.ASM[k]()
job={'vrc':'st185_vrc_1015','csb3':'st185_csb3_1015','busbar':'st185_busbar_1015','drb':'st185_drb102_1015'}.get(k,'st185_fusebox_1015')
os.makedirs('out/'+job,exist_ok=True)
asm.make_assembly(sp,f"out/{job}/{sp['pn']}.pdf",f"previews/{sp['pn']}")
print('OK',k)
