"""2026-10-17 N14 = B (DECISIONS R155) reissue of the fuse box drawings the copper C-strap touches: ST185-FB-101 POWER base (rev S),
ST185-FB-102 POWER belly pan (rev F), ST185-FB-112 output pad (now the battery block pad only: clerical B.01). The strap itself is
ST185-FB-117 (run_fb117.py). The changes are in specs_1017.py; rev letters come from the <part no>.REVLOG.md files in cad/fusebox/rev7.
Run in WSL from the repo root, with the rev 7 STEPs (from the build) in <work>/src/st185_fusebox_1017/:

    ST185_WORK=<work dir> ~/projects/handbuilt-cad/.venv/bin/python cad/drawings/run_n14.py [fb_power_base fb_power_pan fb_pad]

Claude Code, 2026-10-17.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
REV7 = os.path.join(REPO, 'cad', 'fusebox', 'rev7')
_TK = os.environ.get('HANDBUILT_CAD') or os.path.expanduser('~/projects/handbuilt-cad')
for _d in ('tools', 'tools/checks', 'tools/render', 'drawing'):
    sys.path.insert(0, os.path.join(_TK, _d))
sys.path.insert(0, HERE)
if os.environ.get('ST185_WORK'):
    os.chdir(os.environ['ST185_WORK'])
os.makedirs('previews', exist_ok=True)
import specs_1017  # noqa: E402
import part  # noqa: E402

P = specs_1017.PARTS     # the N14 changes (notes, the pad source, rev logs) live in specs_1017.py

for name in (sys.argv[1:] or ['fb_power_base', 'fb_power_pan', 'fb_pad']):
    sp = P[name]
    os.makedirs('out/' + sp['job'], exist_ok=True)
    s = part.make_part(sp, 'out/%s/%s.pdf' % (sp['job'], sp['pn']), None, 'previews/%s' % sp['pn'])
    print('OK', name, sp['pn'], sp['rev'], s)
