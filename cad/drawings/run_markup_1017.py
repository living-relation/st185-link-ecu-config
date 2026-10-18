"""2026-10-17 markup (Dan's 16 screenshots, DECISIONS R157 - R160) reissue of the fuse box drawings whose models changed: ST185-FB-101 POWER
base (T), -103 POWER cover (G), -104 R1 retainer clip (D), -105 LOGIC base (P), -106 LOGIC pan (G), -107 LOGIC cover (J), -108 battery block
base (H), -112 battery block pad (C), -115 / -116 LOGIC strips (E). The changes are in specs_1017.py; rev letters come from the
<part no>.REVLOG.md files in cad/fusebox/rev7.
Run in WSL from the repo root, with the rev 7 STEPs (from the build) in <work>/src/st185_fusebox_1017/:

    ST185_WORK=<work dir> ~/projects/handbuilt-cad/.venv/bin/python cad/drawings/run_markup_1017.py [<keys>]

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

P = specs_1017.PARTS     # the markup changes (notes, the pad source, rev logs) live in specs_1017.py

for name in (sys.argv[1:] or ['fb_power_base', 'fb_power_cover', 'fb_retainer', 'fb_logic_base', 'fb_logic_pan', 'fb_logic_cover', 'fb_br_base',
                              'fb_pad', 'fb_strip1', 'fb_strip2']):
    sp = P[name]
    os.makedirs('out/' + sp['job'], exist_ok=True)
    s = part.make_part(sp, 'out/%s/%s.pdf' % (sp['job'], sp['pn']), None, 'previews/%s' % sp['pn'])
    print('OK', name, sp['pn'], sp['rev'], s)
