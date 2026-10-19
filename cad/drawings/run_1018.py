"""2026-10-18 drawing pass (DECISIONS R184 - R197): regenerate the drawings whose models are merged, from specs_1018.py / aspecs_1018.py.
Run in WSL with handbuilt-cad's .venv, from the repo root (work dir as run_1017.sh: src/<job>/ holds the model STEPs, src/csv the parts lists):

    ST185_WORK=<work dir> ~/projects/handbuilt-cad/.venv/bin/python cad/drawings/run_1018.py [<key> ...]

Keys: the part keys of specs_1018.KEYS and asm:<key> of aspecs_1018.ASM. Writes out/<job>/<PN>.pdf + <PN>.checks.json, previews/<PN>_shN.png.
Held for Dan (Dispatch 2026-10-18): DRB-100 / -101, CSB3-100, VRC-100 .. -103, FB-117, FB-100P.
Claude Code, 2026-10-18."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_TK = os.environ.get('HANDBUILT_CAD') or os.path.expanduser('~/projects/handbuilt-cad')
for _d in ('tools', 'tools/checks', 'tools/render', 'drawing'):
    sys.path.insert(0, os.path.join(_TK, _d))
sys.path.insert(0, HERE)
if os.environ.get('ST185_WORK'):
    os.chdir(os.environ['ST185_WORK'])
os.makedirs('previews', exist_ok=True)
import specs_1018  # noqa: E402
import part  # noqa: E402

JOB = {'fuel_hanger': 'st185_fuelhanger_1017', 'fb_logic': 'st185_fusebox_1017', 'fb_br': 'st185_fusebox_1017'}
keys = sys.argv[1:] or (specs_1018.KEYS + ['asm:fuel_hanger', 'asm:fb_logic', 'asm:fb_br'])
for k in keys:
    if k.startswith('asm:'):
        import aspecs_1018
        import asm
        sp = aspecs_1018.ASM[k[4:]]()
        os.makedirs('out/' + JOB[k[4:]], exist_ok=True)
        r = asm.make_assembly(sp, 'out/%s/%s.pdf' % (JOB[k[4:]], sp['pn']), 'previews/%s' % sp['pn'])
        print('OK', k, sp['pn'], sp['rev'], 'checks ok' if r['ok'] else 'CHECKS FAIL', flush=True)
        continue
    sp = specs_1018.PARTS[k]
    os.makedirs('out/' + sp['job'], exist_ok=True)
    pdf = 'out/%s/%s.pdf' % (sp['job'], sp['pn'])
    part.make_part(sp, pdf, pdf[:-4] + '.dxf' if sp.get('dxf') else None, 'previews/%s' % sp['pn'])
    print('OK', k, sp['pn'], sp['rev'], 'checks ok' if sp['_checks']['ok'] else 'CHECKS FAIL', flush=True)
