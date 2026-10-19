"""2026-10-19 drawing pass (DECISIONS R196: after the model PRs #324, #330, #331): the part drawings of specs_1019.py and the
assembly drawings of aspecs_1019.py. Run in WSL with handbuilt-cad's .venv from the repo root; the work dir holds copies of the
model STEPs (never the repo's cad/ itself):

    W=<work dir>; R=/mnt/c/projects/active/st185-link-ecu-config/cad
    mkdir -p $W/src/{st185_vrc_1017,st185_csb3_1017,st185_drb102_1017,st185_fusebox_1017,st185_vrc_1015,st185_csb3_1015,st185_drb102_1015}
    cp $R/enclosures/vrc/VRC_part_VRC-{Body,Lid}.step $R/enclosures/vrc/print/ST185_VRC_board_holder_PA12.step $W/src/st185_vrc_1017/
    cp $R/enclosures/csb3/CSB3_part_CSB3-Lid.step $W/src/st185_csb3_1017/; cp $R/drb102-plate/DRB102-firewall-plate.step $W/src/st185_drb102_1017/
    cp $R/fusebox/rev7/Power_Base_PA12_printed.step $W/src/st185_fusebox_1017/
    cp $R/enclosures/vrc/VRC_assembly.step $W/src/st185_vrc_1015/; cp $R/enclosures/csb3/CSB3_assembly.step $W/src/st185_csb3_1015/
    cp $R/drb102-plate/DRB102-firewall-plate-assembly.step $W/src/st185_drb102_1015/
    ST185_WORK=$W ~/projects/handbuilt-cad/.venv/bin/python cad/drawings/run_1019.py [<key> | asm:<key>] ...

Writes out/<job>/<PN>.pdf + <PN>.checks.json, previews/<PN>_shN.png.
Claude Code, 2026-10-19."""
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
import specs_1019  # noqa: E402
import part  # noqa: E402
# The out-of-box projection filter that lived here (LP-16 HLR artifact) is in the engine since handbuilt-cad #15 (dwg.lines_in_box).

JOB = {'vrc': 'st185_vrc_1015', 'csb3': 'st185_csb3_1015', 'drb': 'st185_drb102_1015', 'fb_power': 'st185_fusebox_1015'}
keys = sys.argv[1:] or (specs_1019.KEYS + ['asm:' + k for k in JOB])
for k in keys:
    if k.startswith('asm:'):
        import aspecs_1019
        import asm
        sp = aspecs_1019.ASM[k[4:]]()
        os.makedirs('out/' + JOB[k[4:]], exist_ok=True)
        r = asm.make_assembly(sp, 'out/%s/%s.pdf' % (JOB[k[4:]], sp['pn']), 'previews/%s' % sp['pn'])
        print('OK', k, sp['pn'], sp['rev'], 'checks ok' if r['ok'] else 'CHECKS FAIL', flush=True)
        continue
    sp = specs_1019.PARTS[k]
    os.makedirs('out/' + sp['job'], exist_ok=True)
    pdf = 'out/%s/%s.pdf' % (sp['job'], sp['pn'])
    part.make_part(sp, pdf, pdf[:-4] + '.dxf' if sp.get('dxf') else None, 'previews/%s' % sp['pn'])
    print('OK', k, sp['pn'], sp['rev'], 'checks ok' if sp['_checks']['ok'] else 'CHECKS FAIL', flush=True)
