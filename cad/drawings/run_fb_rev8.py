"""Fuse box rev 8 drawing pass (Dan A15 b 2026-11-12, A33 a 2026-11-13; DECISIONS "Fuse box rev 8", R196): the part drawings
ST185-FB-101 / -102 / -103 / -105 / -106 / -107 / -109 and the assemblies ST185-FB-100P / -100L / -100B, from the rev 8 STEPs
(cad/fusebox/rev8, models folder st185_fusebox_1101 revC). Part specs: the specs_1019 chain (notes, tolerance block); assemblies:
aspecs.py (MAP, rev 8 parts lists) with the label and step sheets of aspecs_1019 (fb_power) / aspecs_1018 (fb_logic, fb_br). Rev letter = the newest model row of <pn>.REVLOG.md (cad/fusebox/rev7, R152).
Run in WSL with handbuilt-cad's .venv from the repo root; the work dir holds copies of the model STEPs and the parts lists:

    W=<work dir>; R=<repo>/cad
    mkdir -p $W/src/st185_fusebox_rev8 $W/src/csv
    cp $R/fusebox/rev8/*.step $W/src/st185_fusebox_rev8/; cp $R/fusebox/rev8/fusebox-parts-*.csv $W/src/csv/
    ST185_WORK=$W ~/projects/handbuilt-cad/.venv/bin/python cad/drawings/run_fb_rev8.py [<key> | asm:<key>] ...

Writes out/st185_fusebox_rev8/<PN>.pdf + <PN>.checks.json and previews/<PN>_shN.png.
Claude Code, 2026-11-13."""
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
from specs_1017 import PARTS  # noqa: E402
import part  # noqa: E402

JOB = 'st185_fusebox_rev8'
KEYS = ['fb_power_base', 'fb_power_pan', 'fb_power_cover', 'fb_logic_base', 'fb_logic_pan', 'fb_logic_cover', 'fb_br_cover']
SRC8 = 'C:\\projects\\active\\st185-link-ecu-config\\cad\\fusebox\\rev8\\'
for k in KEYS:
    p = PARTS[k]
    f = os.path.basename(p['file'])
    p['job'], p['file'], p['source'] = JOB, 'src/%s/%s' % (JOB, f), SRC8 + f
    rows = [r for r in open(p['revlog'], encoding='utf-8').read().splitlines() if r.startswith('| ') and not r.startswith('| Rev')]
    p['rev'] = rows[-1].split('|')[1].strip()          # the newest model row of the rev log (R152)
keys = sys.argv[1:] or (KEYS + ['asm:fb_power', 'asm:fb_logic', 'asm:fb_br'])
os.makedirs('out/' + JOB, exist_ok=True)
for k in keys:
    if k.startswith('asm:'):
        import aspecs_1018
        import aspecs_1019
        import asm
        sp = (aspecs_1019.ASM if k[4:] == 'fb_power' else aspecs_1018.ASM)[k[4:]]()    # the live specs: aspecs.py + the 1018 / 1019 label sheets
        rows = [r for r in open(sp['revlog'], encoding='utf-8').read().splitlines() if r.startswith('| ') and not r.startswith('| Rev')]
        sp['rev'] = rows[-1].split('|')[1].strip()
        r = asm.make_assembly(sp, 'out/%s/%s.pdf' % (JOB, sp['pn']), 'previews/%s' % sp['pn'])
        print('OK', k, sp['pn'], sp.get('rev'), 'checks ok' if r['ok'] else 'CHECKS FAIL', flush=True)
        continue
    sp = PARTS[k]
    pdf = 'out/%s/%s.pdf' % (JOB, sp['pn'])
    part.make_part(sp, pdf, None, 'previews/%s' % sp['pn'])
    print('OK', k, sp['pn'], sp['rev'], 'checks ok' if sp['_checks']['ok'] else 'CHECKS FAIL', flush=True)
