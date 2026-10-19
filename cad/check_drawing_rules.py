"""Gate: Dan's drawing rules of 2026-10-18 (DECISIONS R184 - R196), checked on what the drawing engine printed.

Every drawing run of the handbuilt-cad engine (DRAWING-RULES 24-30, handbuilt-cad PR #13) writes `<pdf minus .pdf>.checks.json`
beside the PDF: the PDF's sha256 (16 hex), the printed NOTES and tolerance block, and per view the balloons placed and any
overlapping / crowded balloons or hidden labelled parts. This gate reads those reports for every drawing in
`cad/drawing-models.json`, so it runs in CI without the CAD stack.

Checks:
  K1 the report exists and was written for the registered PDF (its pdf_sha = the manifest's pdf_sha), by the 2026-10-18 engine
  K2 the engine's own rule check passed (`ok`): no balloon overlaps, no crowded leader tips, every modelled BOM item ballooned
     in some view (hidden ones in an exploded or alternate view, R186), no hidden part on a label sheet (R189), tangent edges
     drawn in the trimetric (R187)
  K3 the NOTES and the tolerance block carry none of the banned notes:
     - "envelope model" (R184: the real maker model is used)
     - a pin / socket gender rule ("pins on the box, sockets on the harness") (R185)
     - notes about things not in the model: edge breaks, "not modelled" (R191)
     - change notes: markup dates, rule / PR numbers, "superseded", "verified ..." (R192: those go in the rev log)

PENDING lists the drawings issued before these rules; each leaves the list when it is regenerated with the new engine
(DECISIONS R196 sets the order: all model changes first, then every drawing). A pending drawing is reported, not failed; a
pending drawing that now passes fails until it is taken off the list, so the list only shrinks.

    python cad/check_drawing_rules.py          # check (check_all.py runs this)
Claude Code, 2026-10-18.
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = HERE
MANIFEST = os.path.join(CAD, 'drawing-models.json')
ENGINE_RULES = '2026-10-18'

# issued before the 2026-10-18 rules; regenerated in the drawing pass that follows the model PRs (R196)
PENDING = {
    'ST185-CSB3-100', 'ST185-CSB3-101', 'ST185-CSB3-102', 'ST185-DRB-100', 'ST185-DRB-101',
    'ST185-FB-100B', 'ST185-FB-100L', 'ST185-FB-100P', 'ST185-FB-101', 'ST185-FB-102', 'ST185-FB-103', 'ST185-FB-104',
    'ST185-FB-105', 'ST185-FB-106', 'ST185-FB-107', 'ST185-FB-108', 'ST185-FB-109', 'ST185-FB-111', 'ST185-FB-112',
    'ST185-FB-113', 'ST185-FB-114', 'ST185-FB-115', 'ST185-FB-116', 'ST185-FB-117',
    'ST185-FH-100', 'ST185-FH-101', 'ST185-FH-103', 'ST185-FH-104', 'ST185-FH-105',
    'ST185-VRC-100', 'ST185-VRC-101', 'ST185-VRC-102', 'ST185-VRC-103',
}

BANNED = [
    ('R184 envelope model', re.compile(r'\bENVELOPE', re.I)),
    ('R185 pin / socket gender note', re.compile(r'\bPINS?\b[^.]*\bSOCKETS?\b|\bSOCKETS?\b[^.]*\bPINS?\b', re.I)),
    ('R191 edge-break note', re.compile(r'\bBREAK\s+(?:SHARP\s+|ALL\s+)?EDGES?\b|\bEDGE\s+BREAKS?\b', re.I)),
    ('R191 not-modelled note', re.compile(r'\bNOT\s+(?:BEEN\s+)?MODELL?ED\b', re.I)),
    ('R192 change note: markup', re.compile(r'\bMARK-?UP\b|\bREDLINE', re.I)),
    ('R192 change note: date', re.compile(r'\b20\d\d-\d\d-\d\d\b|\b\d\d/\d\d/\d\d\b')),
    ('R192 change note: rule number', re.compile(r'\(\s*R\d{1,3}(?![\d.])|\bR1\d\d\b|\bDECISIONS\b')),
    ('R192 change note: PR number', re.compile(r'#\d{2,4}\b')),
    ('R192 change note: superseded / verified / fixed', re.compile(r'\bSUPERSEDED\b|\bVERIFIED\b|\bWAS\s+FIXED\b|\bNOW\s+FIXED\b', re.I)),
]


def sha(b):
    return hashlib.sha256(b).hexdigest()[:16]


def banned_in(text):
    """[(rule, matched text)] for one note."""
    out = []
    for name, rx in BANNED:
        m = rx.search(text or '')
        if m:
            out.append((name, m.group(0)))
    return out


def problems(pn, ent):
    """list of problem strings for one drawing (empty = passes)."""
    pdf = os.path.join(CAD, ent['pdf'])
    rep = os.path.splitext(pdf)[0] + '.checks.json'
    if not os.path.exists(rep):
        return ['K1 no engine check report (%s)' % os.path.relpath(rep, CAD).replace('\\', '/')]
    try:
        d = json.load(open(rep, encoding='utf-8'))
    except ValueError as e:
        return ['K1 unreadable check report: %s' % e]
    out = []
    if d.get('pdf_sha') != ent.get('pdf_sha'):
        out.append('K1 report is for another PDF (report %s, registered %s)' % (d.get('pdf_sha'), ent.get('pdf_sha')))
    if str(d.get('engine_rules', '')) < ENGINE_RULES:
        out.append('K1 made by an engine older than the %s rules' % ENGINE_RULES)
    if not d.get('tangent_edges_in_pictorial'):
        out.append('K2 trimetric drawn without tangent edges (R187)')
    if not d.get('ok'):
        why = []
        if d.get('not_ballooned'):
            why.append('not ballooned in any view: items %s (R186)' % ', '.join(d['not_ballooned']))
        for v in d.get('balloon_views', []):
            if v.get('overlaps') or v.get('crowded'):
                why.append('%s: %d overlapping balloons, %d crowded tips (R188)' % (v['view'], v.get('overlaps', 0), v.get('crowded', 0)))
            if str(v.get('view', '')).startswith('LABELS') and v.get('hidden'):
                why.append('%s: labelled parts not visible %s (R189)' % (v['view'], v['hidden']))
        out.append('K2 engine rule check failed: ' + ('; '.join(why) or 'see the report'))
    for i, n in enumerate(d.get('notes') or [], 1):
        for name, hit in banned_in(n):
            out.append('K3 note %d: %s ("%s")' % (i, name, hit))
    for name, hit in banned_in(d.get('tol_block') or ''):
        out.append('K3 tolerance block: %s ("%s")' % (name, hit))
    return out


def check(quiet=False):
    man = json.load(open(MANIFEST, encoding='utf-8'))['drawings']
    fails = []; pend = []
    for pn in sorted(man):
        p = problems(pn, man[pn])
        if pn in PENDING:
            if p:
                pend.append((pn, p))
            else:
                fails.append((pn, ['stale PENDING entry: the drawing now passes - take it off PENDING in cad/check_drawing_rules.py']))
        elif p:
            fails.append((pn, p))
    for pn in sorted(PENDING - set(man)):
        fails.append((pn, ['PENDING names a drawing that is not in drawing-models.json']))
    if not quiet:
        for pn, p in fails:
            print('FAIL %s' % pn)
            for x in p:
                print('   ' + x)
        if pend:
            print('PENDING (R196: regenerated after the model PRs) %d drawings: %s' % (len(pend), ', '.join(pn for pn, _ in pend)))
        print('check_drawing_rules: %d drawings, %d pass, %d pending, %d fail'
              % (len(man), len(man) - len(pend) - len([f for f in fails if f[0] in man]), len(pend), len(fails)))
    return not fails


if __name__ == '__main__':
    sys.exit(0 if check() else 1)
