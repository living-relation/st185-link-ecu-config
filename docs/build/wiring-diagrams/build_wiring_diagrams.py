"""Regenerates the assembly wiring diagrams from the SoT chain.

    python docs/build/wiring-diagrams/build_wiring_diagrams.py            # write SVG (+ PDF when PyMuPDF is installed) and MISMATCHES.md
    python docs/build/wiring-diagrams/build_wiring_diagrams.py --check    # exit 1 when a committed SVG / MISMATCHES.md is out of date

Writes next to this file: fusebox-wiring.svg / .pdf / -A3-tiles.pdf, oem-<box>.svg, oem-junction-boxes.pdf, MISMATCHES.md.
PDFs need `pip install pymupdf`; the SVGs and MISMATCHES.md need nothing.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wd_data as D          # noqa: E402
import fusebox_assembly      # noqa: E402
import oem_sheets            # noqa: E402
import pdf_out               # noqa: E402


def mismatch_md(mism, other):
    out = ['# Wiring diagram mismatches', '',
           'Written by `build_wiring_diagrams.py` on every run. A line here means the SoT chain / spec and the looms disagree about a',
           'wire the diagrams draw. The diagram follows the SoT (`sot/channels.csv`, `cad/fusebox/src/spec.py`, `docs/harness/interfaces.json`);',
           'nothing is guessed. Fix the disagreement at its source, then re-run.', '']
    if mism:
        out += ['## Mismatches (%d)' % len(mism), ''] + ['- ' + m for m in mism]
    else:
        out += ['## Mismatches', '', 'None. Checked: every spec fuse (MINI_COLS, AMI_ROWS) has a loom cavity with the same rating and the reverse;',
                'every `sot/channels.csv` PWR relay cavity has a loom wire; every box wire has a gauge; every box wire is drawn;',
                'every OEM splice in `interfaces.json` that sits on a junction box has a terminal and a wire in the looms.']
    out += ['', '## Left out on purpose', '',
            'The OEM sheets cover junction boxes, relay-block positions and plugs where power is injected or a circuit is spliced (R12, R61).',
            'These `flyingLeads` are splices into DEVICE plugs (switches, lamps, motors, A/C amplifier, combination meter), not junction boxes,',
            'and have no sheet: ' + ', '.join(o['id'] for o in other) + '.', '']
    return '\n'.join(out)


def run(outdir, pdfs):
    ents, wires = D.load()
    fuses = D.fuse_list(ents)
    mism = D.cross_check(ents, wires, fuses)
    made = {}
    sh = fusebox_assembly.build(ents, wires, fuses)
    made['fusebox-wiring.svg'] = sh.svg.render()
    bw = D.box_wires(wires)
    mism += ['fuse box sheet: wire %s touches a box but is not drawn' % w['id'] for w in bw if w['id'] not in sh.drawn]
    mism += ['fuse box sheet: text runs off the page: %s' % t[3] for t in sh.svg.overflow()]
    sheets, rows, other = oem_sheets.build(ents, wires)
    for key, sv in sheets.items():
        made['oem-%s.svg' % key] = sv.render()
        mism += ['OEM sheet %s: text runs off the page: %s' % (key, t[3]) for t in sv.overflow()]
        for r in rows[key]:
            if not r['wires']:
                mism.append('OEM %s %s: splice terminal %s has no wire in the looms' % (r['plug'], r['pin'], r['lead']['terminal']))
    made['MISMATCHES.md'] = mismatch_md(mism, other)
    for name, text in made.items():
        with open(os.path.join(outdir, name), 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    if pdfs and pdf_out.available():
        j = lambda n: os.path.join(outdir, n)                      # noqa: E731
        pdf_out.write_single(j('fusebox-wiring.svg'), j('fusebox-wiring.pdf'))
        pdf_out.write_tiles(j('fusebox-wiring.svg'), j('fusebox-wiring-A3-tiles.pdf'), sh.cuts)
        pdf_out.write_multi([j('oem-%s.svg' % k) for k in sheets], j('oem-junction-boxes.pdf'))
    print('fuse boxes: %d wires touch the three assemblies, %d drawn' % (len(bw), len(sh.drawn)))
    for key in sheets:
        print('oem-%s: %d splices' % (key, len(rows[key])))
    print('mismatches: %d' % len(mism))
    for m in mism:
        print('  -', m)
    return made, mism


def main():
    if '--check' in sys.argv:
        with tempfile.TemporaryDirectory() as tmp:
            made, _ = run(tmp, False)
            stale = []
            for name, text in made.items():
                p = os.path.join(HERE, name)
                old = open(p, encoding='utf-8').read() if os.path.exists(p) else None
                if old != text:
                    stale.append(name)
        if stale:
            print('OUT OF DATE (re-run build_wiring_diagrams.py and commit): ' + ', '.join(stale))
            sys.exit(1)
        print('wiring diagrams are up to date')
        return
    run(HERE, True)
    if not pdf_out.available():
        print('PyMuPDF not installed: SVGs only (pip install pymupdf for the PDFs)')


if __name__ == '__main__':
    main()
