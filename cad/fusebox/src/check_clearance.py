"""Gate: Dan's 3 mm rule - no two live (bare metal) parts in the selected fuse boxes closer than 3 mm.
Reads the clearances the Fusion build measured (cad/fusebox/rev7/fusebox_report.json "live_clearance") and, when present,
the wire simulation (cad/fusebox/rev7/wiring_report.json "live_to_live"). Every live-to-live key listed below fails under
3.0 mm. Live-to-plastic / live-to-insulation keys (a printed part or a wire's insulation, not a second live part) are
printed for information only.
SAME CIRCUIT (Dan's J1 = A, 2026-10-14, DECISIONS R94): the 3 mm rule is between different circuits. A gap between two live
parts of ONE circuit (the jumper lugs on one bus strip) is printed, not gated - permanently. Only the keys in SAME_CIRCUIT get
this; the build measures them on one strip only, and every gap between circuits (Bus 1 to Bus 2) stays gated.
A WAIVER holds a failing key only while its question is still open in the docs/OPEN-ITEMS.md Needs Dan table (Dan has not answered
yet); once the question is answered the waiver expires and the key fails again until the model is fixed. None open today.
    python cad/fusebox/src/check_clearance.py
Claude Code, 2026-10-14.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
RULE = 3.0
REPORT = os.path.join(REPO, 'cad', 'fusebox', 'rev7', 'fusebox_report.json')
WIRING = os.path.join(REPO, 'cad', 'fusebox', 'rev7', 'wiring_report.json')
sys.path.insert(0, os.path.join(REPO, 'docs'))
from needs_dan import open_questions  # noqa: E402

LIVE_LIVE = {   # key -> what the two live parts are
    'strap_to_strap_min_mm': 'POWER: AMI copper strap to the next strap (R155)',
    'strap_station_to_station_min_mm': 'POWER: any live part of one strap station (strap, PEM nuts, ear / lug bolts, lug) to the next (R155)',
    'bar_to_strap_min_mm': 'POWER: + bar to a copper strap',
    'input_lug_to_strap_min_mm': 'POWER: bus zone 1/0 lug to a copper strap',
    'under_deck_lug_to_lug_min_mm': 'POWER: lugs under the deck',
    'bus_pos_lug_to_lug_min_mm': 'POWER bus zone: + bar lug to lug',
    'bus_neg_to_pos_min_mm': 'POWER bus zone: any NEG part to any + part',
    'bus_pos_lug_to_out_strap_min_mm': 'POWER: + bus lug to an AMI copper strap',
    'logic_strip_to_strip_mm': 'LOGIC: Bus 1 strip to Bus 2 strip',
    'logic_bolt_to_other_strip_min_mm': 'LOGIC: a strip bolt tip to the OTHER strip',
    'logic_pem_nut_to_other_strip_min_mm': 'LOGIC: a PEM nut head (N2) to the OTHER strip',
    'logic_bus1_to_bus2_min_mm': 'LOGIC: any Bus 1 part to any Bus 2 part',
    'logic_feed_lug_to_lug_mm': 'LOGIC: Bus 1 feed lug to Bus 2 feed lug',
    'battrelay_bar_to_pad_mm': 'battery block: bar to output pad',
    'battrelay_relay_lug_to_lug_mm': 'battery block: HCR150 terminal 3 lug to terminal 5 lug',
}
LIVE_INSULATION = ('pan_to_nearest_live_power_mm', 'logic_jumper_parts_to_printed_min_mm', 'logic_jumper_parts_to_harness_min_mm',
                   'logic_strip_to_printed_min_mm', 'logic_pan_rib_to_live_min_mm', 'logic_base_to_live_min_mm')
# J1 = A (R94): live to live inside ONE circuit - reported, never gated (the key must still be there)
SAME_CIRCUIT = {'logic_jumper_lug_to_lug_min_mm': 'LOGIC: fuse input jumper lug to the next one on the SAME strip (one circuit, J1 = A)',
                # SteveCAD v3 F05 (2026-10-16): the GND stud moved to x 100.5 puts its ring edge on the GND IG 6R8 lug at x 84 - every
                # lug on the NEG bar is the one ground node, so J1 = A applies as on a LOGIC strip; spanner room there is OPEN-2 (Dan)
                'bus_neg_lug_to_lug_min_mm': 'POWER bus zone: NEG bar lug to lug (one ground bar = one circuit, J1 = A)',
                'bus_neg_nut_to_nut_min_mm': 'POWER bus zone: NEG bar M8 nut to nut (one ground node)'}
# N3 (Dan 2026-10-16, OPEN-2): the NEG stud pitch is accepted if the gap between the NEG lugs / nuts meets a stated spec. They are one
# ground node, so no electrical clearance applies; the practical spec is spec.REV7 neg_lug_gap (1.5 mm: lugs that turn under torque never
# touch, the bus looks tidy). Same-circuit keys listed here fail under their own minimum.
import importlib.util as _ilu
_sp = _ilu.spec_from_file_location('spec', os.path.join(HERE, 'spec.py')); _S = _ilu.module_from_spec(_sp); _sp.loader.exec_module(_S)
SAME_CIRCUIT_MIN = {'bus_neg_lug_to_lug_min_mm': _S.REV7['neg_lug_gap'], 'bus_neg_nut_to_nut_min_mm': _S.REV7['neg_lug_gap']}
# key -> question id: the key may stay under 3 mm only while that question is open (Dan to decide)
WAIVERS = {}


def main():
    rep = json.load(open(REPORT, encoding='utf-8'))
    lc = rep.get('live_clearance', {})
    if os.path.exists(WIRING):
        lc = dict(lc, **json.load(open(WIRING, encoding='utf-8')).get('live_to_live', {}))
    open_q = {q['id'] for q in open_questions()}
    bad, waived = [], []
    missing = [k for k in list(LIVE_LIVE) + list(SAME_CIRCUIT) if k not in lc]
    for k, what in LIVE_LIVE.items():
        v = lc.get(k)
        if v is None or v >= RULE:
            continue
        q = WAIVERS.get(k)
        (waived if q in open_q else bad).append((k, v, what, q))
    for k in sorted(lc):
        if k.startswith('wire_') and lc[k] < RULE and k not in LIVE_LIVE:
            bad.append((k, lc[k], 'wire simulation: live parts', None))
    print('fuse box clearances (%s): %d live-to-live keys, rule %.1f mm' % (os.path.relpath(REPORT, REPO), len(LIVE_LIVE), RULE))
    for k in LIVE_INSULATION:
        if k in lc:
            print('  info (live to plastic / insulation, not gated): %s = %.2f mm' % (k, lc[k]))
    for k, what in SAME_CIRCUIT.items():
        if k in lc:
            mn = SAME_CIRCUIT_MIN.get(k)
            print('  same circuit (J1 = A%s): %s = %.2f mm (%s)' % (', practical min %.1f' % mn if mn else ', not gated', k, lc[k], what))
            if mn and lc[k] < mn:
                bad.append((k, lc[k], what + ' - under its practical minimum %.1f' % mn, None))
    for (k, v, what, q) in waived:
        print('  WAIVED while %s is open: %s = %.2f mm (%s)' % (q, k, v, what))
    for k in missing:
        print('  MISSING: %s - re-run the Fusion build (build_fusion.build(rev=7))' % k)
    for (k, v, what, q) in bad:
        print('  FAIL: %s = %.2f mm < %.1f (%s)%s' % (k, v, RULE, what, ' - waiver %s needs that question open in OPEN-ITEMS Needs Dan' % q if q else ''))
    if bad or missing:
        print('check_clearance: %d failure(s)' % (len(bad) + len(missing)))
        return 1
    print('check_clearance: OK (%d waived)' % len(waived))
    return 0


if __name__ == '__main__':
    sys.exit(main())
