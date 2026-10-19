"""2026-10-19 initials re-stamp (DECISIONS R200, Dan N41 = B): regenerate every CAD drawing so DRAWN and every rev-log BY are the
person's initials (DG), never an agent or tool name. Clerical, drawing-only (R197): each drawing takes the next .NN of the rev it has in
origin/main's `cad/drawing-models.json` (D -> D.01, D.01 -> D.02); models untouched. The specs are the latest pass of each drawing
(specs_1018 / aspecs_1018, then specs_1019 / aspecs_1019, run_fb117); this script only sets the rev, drops any legacy `revs` tuples
(the rev log beside the model is the one source, with DRAWN = its Rev A BY) and runs them. Needs ~/.drawing-initials (or DRAWING_INITIALS).

    W=<work dir>   # base-models.json (origin/main's cad/drawing-models.json), src/<job>/ with the model STEPs as for run_1017.sh / run_1019.py, plus src/st185_fuelhanger_1017/ and src/csv/
    ST185_WORK=$W ~/projects/handbuilt-cad/.venv/bin/python cad/drawings/run_initials.py [<pn> ...]

Writes out/<job>/<PN>.pdf + <PN>.checks.json, previews/<PN>_shN.png. Claude Code, 2026-10-19."""
import json
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
_TK = os.environ.get('HANDBUILT_CAD') or os.path.expanduser('~/projects/handbuilt-cad')
for _d in ('tools', 'tools/checks', 'tools/render', 'drawing'):
    sys.path.insert(0, os.path.join(_TK, _d))
sys.path.insert(0, HERE)
if os.environ.get('ST185_WORK'):
    os.chdir(os.environ['ST185_WORK'])
os.makedirs('previews', exist_ok=True)
import part  # noqa: E402
import asm  # noqa: E402
import revs  # noqa: E402
import settings  # noqa: E402

settings.requester_initials()          # stops here (agents) / asks once (a person at a terminal) before any work

# the revs the drawings carry on origin/main (idempotent: a re-run bumps from main, not from a half-done working tree).
# <work>/base-models.json = `git show origin/main:cad/drawing-models.json` (made on the Windows side; WSL cannot use a worktree's git).
with open('base-models.json', encoding='utf-8') as _f:
    BASE = {pn: d['rev'] for pn, d in json.load(_f)['drawings'].items()}
NEW = {pn: revs.bump_clerical(r) for pn, r in BASE.items()}
DONE = []

_make_part, _make_assembly = part.make_part, asm.make_assembly


with open(os.path.join(REPO, 'cad', 'rev-marks.json'), encoding='utf-8') as _f:
    EXEMPT = json.load(_f)['exempt_through']


def _stamp(spec):
    spec['rev'] = NEW[spec['pn']]
    spec.pop('revs', None)             # rev log beside the model is the only source (R152); DRAWN = its Rev A BY (R200)
    spec.pop('drawn', None)
    spec['rev_marks_exempt_through'] = EXEMPT.get(spec['pn'])      # R200: letters up to today's need no revision triangle
    DONE.append(spec['pn'])


def make_part(spec, *a, **k):
    if ONLY and spec['pn'] not in ONLY:
        return {'ok': True}
    _stamp(spec)
    return _make_part(spec, *a, **k)


def make_assembly(spec, *a, **k):
    if ONLY and spec['pn'] not in ONLY:
        return {'ok': True}
    _stamp(spec)
    return _make_assembly(spec, *a, **k)


part.make_part, asm.make_assembly = make_part, make_assembly
ONLY = set(sys.argv[1:])

import specs_1019  # noqa: E402  (imports specs_1018 -> specs_1017: PARTS carries every pass's changes)
import specs_1018  # noqa: E402
import aspecs_1018  # noqa: E402
import aspecs_1019  # noqa: E402

JOB18 = {'fuel_hanger': 'st185_fuelhanger_1017', 'fb_logic': 'st185_fusebox_1017', 'fb_br': 'st185_fusebox_1017'}
JOB19 = {'vrc': 'st185_vrc_1015', 'csb3': 'st185_csb3_1015', 'drb': 'st185_drb102_1015', 'fb_power': 'st185_fusebox_1015'}


def run_part(k):
    sp = specs_1019.PARTS[k]
    if ONLY and sp['pn'] not in ONLY:
        return
    os.makedirs('out/' + sp['job'], exist_ok=True)
    pdf = 'out/%s/%s.pdf' % (sp['job'], sp['pn'])
    part.make_part(sp, pdf, pdf[:-4] + '.dxf' if sp.get('dxf') else None, 'previews/%s' % sp['pn'])
    print('OK', k, sp['pn'], sp['rev'], 'checks ok' if sp['_checks']['ok'] else 'CHECKS FAIL', flush=True)


ASM_PN = {'fuel_hanger': 'ST185-FH-100', 'fb_logic': 'ST185-FB-100L', 'fb_br': 'ST185-FB-100B', 'vrc': 'ST185-VRC-100',
          'csb3': 'ST185-CSB3-100', 'drb': 'ST185-DRB-100', 'fb_power': 'ST185-FB-100P'}


def run_asm(mod, jobs, k):
    if ONLY and ASM_PN[k] not in ONLY:
        return                         # building an assembly spec loads its STEPs: skip it when it is not asked for
    sp = mod.ASM[k]()
    os.makedirs('out/' + jobs[k], exist_ok=True)
    r = asm.make_assembly(sp, 'out/%s/%s.pdf' % (jobs[k], sp['pn']), 'previews/%s' % sp['pn'])
    print('OK', 'asm:' + k, sp['pn'], sp['rev'], 'checks ok' if r['ok'] else 'CHECKS FAIL', flush=True)


for k in dict.fromkeys(specs_1018.KEYS + specs_1019.KEYS):
    run_part(k)
for k in JOB18:
    run_asm(aspecs_1018, JOB18, k)
for k in JOB19:
    run_asm(aspecs_1019, JOB19, k)
if not ONLY or 'ST185-FB-117' in ONLY:
    sys.argv = ['run_fb117.py']
    runpy.run_path(os.path.join(HERE, 'run_fb117.py'), run_name='__main__')
missing = sorted(set(NEW) - set(DONE) - (set() if not ONLY else set(NEW)))
print('stamped %d: %s' % (len(DONE), ' '.join(sorted(DONE))))
if missing:
    print('NOT BUILT:', ' '.join(missing))
    sys.exit(1)
