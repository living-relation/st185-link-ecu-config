import os as _o, sys as _s
_TK=_o.environ.get('HANDBUILT_CAD') or _o.path.expanduser('~/projects/handbuilt-cad')   # handbuilt-cad checkout (drawing engine, checks, renders)
for _d in ('tools','tools/checks','tools/render','drawing'): _s.path.insert(0,_o.path.join(_TK,_d))
_s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__)))
if _o.environ.get('ST185_WORK'): _o.chdir(_o.environ['ST185_WORK'])
import sys,os
os.environ['DWG_REV']='B'
pass
kind,k=sys.argv[1],sys.argv[2]
A=('A','INITIAL RELEASE','2026-10-15','DG')
os.makedirs('previews_B',exist_ok=True)
if kind=='part':
    import specs,part
    sp=dict(specs.PARTS[k]); job=sp['job']
    sp['rev']='B'; sp['revs']=[A,('B','DETAIL LEADER ADDED, DETAIL MOVED','2026-10-15','DG')]
    os.makedirs('out_B/'+job,exist_ok=True)
    pdf=f"out_B/{job}/{sp['pn']}_B.pdf"; dxf=f"out_B/{job}/{sp['pn']}_B.dxf" if sp['process']=='machined' else None
    part.make_part(sp,pdf,dxf,f"previews_B/{sp['pn']}_B")
else:
    import aspecs,asm
    sp=aspecs.ASM[k](); job={'vrc':'st185_vrc_1015'}[k]
    sp['rev']='B'; sp['revs']=[A,('B','NYLON TAB SCREWS OFF BOM, RENUMBERED','2026-10-15','DG')]
    os.makedirs('out_B/'+job,exist_ok=True)
    asm.make_assembly(sp,f"out_B/{job}/{sp['pn']}_B.pdf",f"previews_B/{sp['pn']}_B")
print('OK',k)
