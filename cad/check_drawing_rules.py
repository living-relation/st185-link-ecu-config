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

  K4 initials (R200, Dan N41 = B): in the drawing's rev log (`<pn>.REVLOG.md`) every BY is a person's initials (2-4 letters), never blank and
     never an agent / tool name (Claude, SteveCAD, Grok, Fairsolid, unknown ...); the log has a Rev A row; DRAWN (the title block) is the
     Rev A BY, so where pypdf is installed the PDF's sheet-1 text must carry those initials and no banned BY. handbuilt-cad's engine
     refuses to render a bad log (DRAWING-RULES 32), this keeps a hand edit or an old PDF from slipping through.

  K5 revision triangles (R200, handbuilt-cad DRAWING-RULES 33): a full-letter rev made after 2026-10-19 (a letter above the one listed for
     the drawing in `cad/rev-marks.json` `exempt_through`; Rev A needs none) has at least one triangle in the engine report (`rev_marks`);
     no drawing may report a declared triangle it could not place (`rev_marks_unplaced`). .01 clerical revs need none and are not in the
     rev log.

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
PENDING = set()     # every drawing regenerated to these rules (2026-10-19)

# names of agents / tools / placeholders: never DRAWN or a rev-log BY (R200; same list as handbuilt-cad drawing/settings.py BANNED)
BANNED_NAMES = {'claude', 'stevecad', 'steve', 'sc', 'grok', 'grokbot', 'fairsolid', 'cursor', 'codex', 'gpt', 'gemini', 'copilot',
                'agent', 'bot', 'tool', 'system', 'auto', 'script', 'unknown', 'none', 'null', 'tbd', 'xx', 'xxx'}
INITIALS_RE = re.compile(r'^[A-Z]{2,4}$')

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


def bad_initials(by):
    """Why `by` is not a person's initials, or None."""
    by = (by or '').strip()
    if not by:
        return 'blank'
    if by.lower() in BANNED_NAMES or re.sub(r'[^a-z]', '', by.lower()) in BANNED_NAMES:
        return '"%s" is an agent / tool / placeholder name' % by
    if not INITIALS_RE.match(by.upper()):
        return '"%s" is not 2-4 letters' % by
    return None


def revlog_rows(path):
    """[(rev, by)] of a <pn>.REVLOG.md table, oldest first."""
    rows = []
    for line in open(path, encoding='utf-8'):
        c = [x.strip() for x in line.strip().strip('|').split('|')] if line.lstrip().startswith('|') else []
        if len(c) >= 4 and c[0].lower() != 'rev' and not set(c[0]) <= set('-: '):
            rows.append((c[0].upper(), c[2]))
    return rows


def initials_problems(pn, ent, pdf_text=None):
    """K4: rev-log BY / Rev A = DRAWN. `pdf_text` = sheet-1 text when pypdf is available."""
    path = os.path.join(CAD, ent['revlog'])
    if not os.path.exists(path):
        return ['K4 no rev log (%s)' % ent['revlog']]
    rows = revlog_rows(path)
    out = ['K4 rev %s: BY %s (BY is the initials of the person who requested the change, R200)' % (r, bad_initials(b))
           for r, b in rows if bad_initials(b)]
    a = [b for r, b in rows if r == 'A']
    if not a:
        out.append('K4 no Rev A row, so DRAWN is unknown')
    elif pdf_text is not None:
        m = re.search(r'DRAWN\r?\n([^\r\n]*)\r?\n', pdf_text)       # the title block prints the label, then the value
        if not m or m.group(1).strip().upper() != a[0].upper():
            out.append('K4 the PDF title block DRAWN is "%s", the Rev A BY is %s: regenerate it'
                       % (m.group(1).strip() if m else '?', a[0]))
    return out


def sheet1_text(pdf):
    """Sheet-1 text of the PDF, or None without pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        return PdfReader(pdf).pages[0].extract_text() or ''
    except Exception:    # unreadable PDF: D3 / D6 of check_drawings_current report it
        return None


def rev_index(letter):
    L = [c for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if c not in 'ILOQ']
    n = 0
    for c in letter.upper():
        n = n * len(L) + L.index(c) + 1
    return n - 1


def marks_problems(pn, ent, rep):
    """K5: revision triangles. `rep` = the engine check report."""
    out = ['K5 declared revision triangle could not be placed: %s (%s)' % (json.dumps({k: v for k, v in u.items() if k != 'why'}), u.get('why'))
           for u in rep.get('rev_marks_unplaced') or []]
    m = re.match(r'^([A-Z]+)', str(ent.get('rev') or '').upper())
    if not m or m.group(1) == 'A':
        return out
    letter = m.group(1)
    path = os.path.join(CAD, 'rev-marks.json')
    ex = (json.load(open(path, encoding='utf-8')).get('exempt_through') or {}).get(pn) if os.path.exists(path) else None
    if ex and rev_index(letter) <= rev_index(ex):
        return out
    if not (rep.get('rev_marks') or {}).get(letter):
        out.append('K5 rev %s has no revision triangle (R200): declare what changed in rev_marks / %s.REVMARKS.json and regenerate' % (letter, pn))
    return out


def problems(pn, ent):
    """list of problem strings for one drawing (empty = passes)."""
    pdf = os.path.join(CAD, ent['pdf'])
    rep = os.path.splitext(pdf)[0] + '.checks.json'
    k4 = initials_problems(pn, ent, sheet1_text(pdf) if os.path.exists(pdf) else None)
    if not os.path.exists(rep):
        return ['K1 no engine check report (%s)' % os.path.relpath(rep, CAD).replace('\\', '/')] + k4
    try:
        d = json.load(open(rep, encoding='utf-8'))
    except ValueError as e:
        return ['K1 unreadable check report: %s' % e] + k4
    out = list(k4) + marks_problems(pn, ent, d)
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
