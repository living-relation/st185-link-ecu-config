"""Gate: every shop drawing matches its model (DECISIONS R183, Dan 2026-10-18: "whenever a model is updated or changed it's drawing must
also be updated to match" and "if a drawing is incorrect or wrong the model needs to be updated to fix it").

The model is the master. Rev letters follow R147 - R152 and handbuilt-cad `drawing/DRAWING-RULES.md` 1 - 12 / `drawing/revs.py`:
letters A..Z skipping I, L, O, Q, then AA, AB ...; the model's letter is the newest row of its rev log (<pn>.REVLOG.md, models never
get decimals); the drawing carries the model's letter, or that letter + .NN for a clerical, drawing-only change (notes, anything that
does not touch form, fit or function).

The register of drawings is `cad/DRAWING-REVS.md`; `cad/drawing-models.json` records, for each drawing, the model files it was made from
and their fingerprints at the time it was issued:
  steps  - the STEP files (DATA section sha256: the header with the export time is ignored, so a re-export of the same geometry matches);
           the files are gitignored, so this is checked only where they are on disk (the main checkout; CI has none)
  ci     - tracked fingerprints CI can check: `report` = a part's geometry entry in a tracked build report (size / volume / bbox / mass),
           `src` = a build script (comments, blank lines and docstrings ignored)
  pdf    - sha256 of the issued PDF

Checks (check mode, the default; nothing is written):
  D1 every drawing row of the register has a manifest entry and the reverse
  D2 the register rev = the manifest rev; it is a valid revs.py rev; its letter = the newest rev-log letter; no decimal in a rev log
  D3 the PDF on disk is the one registered (a regenerated drawing is re-registered with --update)
  D4 the tracked fingerprints (ci) are unchanged since the drawing was issued - else the model changed and the drawing was not regenerated
  D5 where the STEP files are on disk: their fingerprints are unchanged (same meaning); CI prints "skipped"
  D6 where pypdf is installed: the PDF's text carries its part number and rev

    python cad/check_drawings_current.py                    # check (check_all.py runs this)
    python cad/check_drawings_current.py --update PN [PN]   # after regenerating drawings: record rev, PDF and model fingerprints
    python cad/check_drawings_current.py --update-all

--update refuses a model change without a new letter (R147: a model change bumps the letter) and a changed PDF without a new rev
(a drawing-only change is a clerical .NN) unless --same-rev (a re-render with no content change, e.g. the date). A new drawing: add its
entry to drawing-models.json by hand (pdf, revlog, steps paths, ci sources), then --update it.
Claude Code, 2026-10-18.
"""
import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tokenize

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CAD = HERE
MANIFEST = os.path.join(CAD, 'drawing-models.json')
REGISTER = os.path.join(CAD, 'DRAWING-REVS.md')

# ---------------- revs.py logic (handbuilt-cad drawing/revs.py, kept in step; CI has no handbuilt-cad checkout)
LETTERS = [c for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if c not in 'ILOQ']
_IDX = {c: i for i, c in enumerate(LETTERS)}
_REV_RE = re.compile(r'^\s*([A-Za-z]+)(?:\.(\d{1,3}))?\s*$')


def is_valid_letter(s):
    return bool(s) and all(c in _IDX for c in s.strip().upper())


def letter_to_index(s):
    n = 0
    for c in s.strip().upper():
        n = n * len(LETTERS) + _IDX[c] + 1
    return n - 1


def parse_rev(rev):
    """'C' -> ('C', 0); 'C.01' -> ('C', 1). ValueError on anything else (I / L / O / Q are not letters)."""
    m = _REV_RE.match(str(rev))
    if not m or not is_valid_letter(m.group(1)):
        raise ValueError('bad rev %r' % (rev,))
    return m.group(1).upper(), int(m.group(2) or 0)


def revlog_letters(path):
    """Letters in a <pn>.REVLOG.md table, file order (revs.read_revlog)."""
    out = []
    for line in open(path, encoding='utf-8'):
        s = line.strip()
        if not s.startswith('|'):
            continue
        cells = [c.strip() for c in s.strip('|').split('|')]
        if len(cells) < 4 or cells[0].lower() == 'rev' or set(cells[0]) <= set('-: '):
            continue
        out.append(cells[0])
    return out


# ---------------- fingerprints
def sha(b):
    return hashlib.sha256(b).hexdigest()[:16]


def step_fp(path):
    t = open(path, 'rb').read()
    i = t.find(b'DATA;')
    return sha(t[i:] if i >= 0 else t)


def src_fp(path):
    """Python source without comments, blank lines and bare string statements (docstrings)."""
    raw = open(path, 'rb').read().replace(bytes([13, 10]), bytes([10]))     # the Windows checkout is CRLF (autocrlf), CI is LF
    toks = list(tokenize.tokenize(io.BytesIO(raw).readline))
    keep, start = [], True
    sig = [t for t in toks if t.type not in (tokenize.COMMENT, tokenize.NL, tokenize.ENCODING)]
    for k, t in enumerate(sig):
        if t.type == tokenize.STRING and start and k + 1 < len(sig) and sig[k + 1].type in (tokenize.NEWLINE, tokenize.ENDMARKER):
            continue
        keep.append('NEWLINE' if t.type == tokenize.NEWLINE else t.string)
        start = t.type in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT)
    return sha(' '.join(keep).encode())


GEOM = ('size_mm', 'volume_cm3', 'volume_mm3', 'bbox', 'mass_g', 'solids', 'lumps', 'shells', 'bodies')


def report_fp(spec):
    """spec 'file#section#key' (paths from cad/): the part's geometry entry in a tracked build report."""
    f, section, key = spec.split('#')
    d = json.load(open(os.path.join(CAD, f), encoding='utf-8')).get(section, {})
    if key not in d:
        return None
    e = d[key]
    if isinstance(e, dict):
        e = {k: e[k] for k in GEOM if k in e}
    return sha(json.dumps(e, sort_keys=True).encode())


def ci_fp(spec):
    kind, _, ref = spec.partition(':')
    if kind == 'report':
        return report_fp(ref)
    if kind == 'src':
        p = os.path.join(CAD, ref)
        return src_fp(p) if os.path.exists(p) else None
    raise ValueError('unknown ci fingerprint %r' % spec)


def main_checkout():
    """The gitignored model files live in the main checkout; a worktree has only tracked files (build-research-hub.py)."""
    try:
        out = subprocess.run(['git', 'rev-parse', '--git-common-dir'], cwd=REPO, capture_output=True, text=True, timeout=10,
                             check=True).stdout.strip()
        return os.path.dirname(os.path.abspath(os.path.join(REPO, out)))
    except Exception:
        return REPO


def find_step(rel):
    for root in (REPO, main_checkout()):
        p = os.path.join(root, 'cad', rel)
        if os.path.exists(p):
            return p
    return None


def pdf_text(path):
    try:
        import pypdf
    except ImportError:
        return None
    try:
        return pypdf.PdfReader(path).pages[0].extract_text() or ''
    except Exception:
        return ''


# ---------------- register
def register():
    """{pn: rev} from the main table of cad/DRAWING-REVS.md (rows with a drawing file)."""
    out = {}
    for line in open(REGISTER, encoding='utf-8'):
        c = [x.strip() for x in line.strip().strip('|').split('|')]
        if len(c) >= 8 and re.fullmatch(r'ST185-[A-Z0-9]+-\d+[A-Z]?', c[1]) and '.pdf' in c[7]:
            out[c[1]] = c[3]
    return out


def load_manifest():
    return json.load(open(MANIFEST, encoding='utf-8'))


def check(man=None, reg=None, quiet=False):
    """Returns a list of failure strings (empty = pass)."""
    man = man if man is not None else load_manifest()
    reg = reg if reg is not None else register()
    D = man['drawings']
    fails, skipped, n_step = [], 0, 0
    for pn in sorted(set(reg) - set(D)):
        fails.append('D1 %s: in cad/DRAWING-REVS.md but not in cad/drawing-models.json (add its models, then --update %s)' % (pn, pn))
    for pn in sorted(set(D) - set(reg)):
        fails.append('D1 %s: in cad/drawing-models.json but has no drawing row in cad/DRAWING-REVS.md' % pn)
    for pn in sorted(set(D) & set(reg)):
        e = D[pn]
        rev = e['rev']
        if reg[pn] != rev:
            fails.append('D2 %s: register rev %s != drawing rev %s (regenerate the drawing and --update it, or fix the register)' % (pn, reg[pn], rev))
        try:
            letter, cler = parse_rev(rev)
        except ValueError as ex:
            fails.append('D2 %s: %s (letters A-Z without I / L / O / Q, clerical .NN)' % (pn, ex))
            continue
        rl = os.path.join(CAD, e['revlog'])
        if not os.path.exists(rl):
            fails.append('D2 %s: rev log %s missing' % (pn, e['revlog']))
        else:
            rows = revlog_letters(rl)
            bad = [r for r in rows if not is_valid_letter(r)]
            if bad:
                fails.append('D2 %s: rev log rows %s are not model letters (models never get decimals; clerical revs are not logged)' % (pn, bad))
            good = [r for r in rows if is_valid_letter(r)]
            newest = max(good, key=letter_to_index) if good else None
            if newest != letter:
                fails.append('D2 %s: drawing rev %s but the model is at %s (newest row of %s): the drawing letter must equal the model letter'
                             % (pn, rev, newest, e['revlog']))
        pdf = os.path.join(CAD, e['pdf'])
        if not os.path.exists(pdf):
            fails.append('D3 %s: drawing %s missing' % (pn, e['pdf']))
        elif sha(open(pdf, 'rb').read()) != e['pdf_sha']:
            fails.append('D3 %s: %s is not the registered drawing (regenerate it from the model, never hand-edit; then --update %s)' % (pn, e['pdf'], pn))
        for spec, fp in e.get('ci', {}).items():
            now = ci_fp(spec)
            if now != fp:
                fails.append('D4 %s: model changed since rev %s was drawn (%s) - regenerate the drawing from the model with the new model letter (R183)'
                             % (pn, rev, spec))
        for rel, fp in e.get('steps', {}).items():
            p = find_step(rel)
            if p is None:
                skipped += 1
                continue
            n_step += 1
            if step_fp(p) != fp:
                fails.append('D5 %s: model %s changed since rev %s was drawn - regenerate the drawing with the new model letter (R183)' % (pn, rel, rev))
        if os.path.exists(pdf):
            t = pdf_text(pdf)
            if t is not None and (pn not in t or not re.search(r'(?<![A-Z0-9.])%s(?![A-Z0-9])' % re.escape(rev), t)):
                fails.append('D6 %s: the PDF does not show %s rev %s' % (pn, pn, rev))
    if not quiet:
        print('drawings vs models (R183, R147-R152): %d drawings, %d model STEP fingerprints checked%s'
              % (len(D), n_step, ', %d STEP files not on this disk (CI: tracked fingerprints only)' % skipped if skipped else ''))
    return fails


def update(pns, same_rev=False):
    man = load_manifest()
    reg = register()
    D = man['drawings']
    errs = []
    for pn in pns:
        if pn not in D:
            errs.append('%s: no entry in drawing-models.json - add pdf / revlog / steps / ci first' % pn)
            continue
        e = D[pn]
        new = dict(e)
        new['rev'] = reg.get(pn, e['rev'])
        letter, cler = parse_rev(new['rev'])
        new['ci'] = {s: ci_fp(s) for s in e.get('ci', {})}
        steps = {}
        for rel in e.get('steps', {}):
            p = find_step(rel)
            if p is None:
                errs.append('%s: model file %s is not on this disk - run --update where the model files are' % (pn, rel))
                break
            steps[rel] = step_fp(p)
        else:
            new['steps'] = steps
        if any(x.startswith(pn + ':') for x in errs):
            continue
        new['pdf_sha'] = sha(open(os.path.join(CAD, e['pdf']), 'rb').read())
        model_changed = new['ci'] != e.get('ci', {}) or new['steps'] != e.get('steps', {})
        if e.get('pdf_sha'):
            ol, oc = parse_rev(e['rev'])
            if model_changed and letter_to_index(letter) <= letter_to_index(ol):
                errs.append('%s: the model changed but its letter did not (%s -> %s): a model change bumps the letter (R147)' % (pn, e['rev'], new['rev']))
                continue
            if not model_changed and new['pdf_sha'] != e['pdf_sha'] and (letter, cler) == (ol, oc) and not same_rev:
                errs.append('%s: the drawing changed but the model and the rev did not: a drawing-only change is a clerical %s.%02d '
                            '(or --same-rev for a re-render with no content change)' % (pn, ol, oc + 1))
                continue
        t = pdf_text(os.path.join(CAD, e['pdf']))
        if t is not None and (pn not in t or new['rev'] not in t):
            errs.append('%s: the PDF does not show %s rev %s - regenerate it' % (pn, pn, new['rev']))
            continue
        D[pn] = new
        print('updated %s rev %s%s' % (pn, new['rev'], ' (model changed)' if model_changed and e.get('pdf_sha') else ''))
    with open(MANIFEST, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(man, f, indent=1, sort_keys=False)
        f.write('\n')
    for x in errs:
        print('NOT UPDATED ' + x)
    return 1 if errs else 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--update', nargs='+', metavar='PN')
    ap.add_argument('--update-all', action='store_true')
    ap.add_argument('--same-rev', action='store_true')
    a = ap.parse_args()
    if a.update or a.update_all:
        sys.exit(update(sorted(load_manifest()['drawings']) if a.update_all else a.update, a.same_rev))
    f = check()
    for x in f:
        print('FAIL ' + x)
    print('check_drawings_current: %s' % ('OK' if not f else '%d problem(s)' % len(f)))
    sys.exit(1 if f else 0)
