"""Sanity gate for the PCLink seed tables in tune/.

    python tune/scripts/validate_tune.py      exit 0 = OK, 1 = problems (listed)

Checks (seeds only - this does not judge whether a number is a good tune):
  1. Every CSV in tune/tables/ parses: '#' comment lines and blank lines skipped,
     one header row, every data row the same width as the header, every cell numeric
     (except the labelled footer block in boost_shakedown_stages.csv).
  2. Axes are strictly increasing (first column, and the numeric header of 2-D tables).
  3. The three main 2-D tables (VE 93, VE E85, ignition) and lambda_target share one
     axis pair: MAP 20-200 kPa rows x RPM 800-7000 columns (tune/README.md).
  4. Boost ceilings match tune/engine_constants.yaml targets:
       boost_target_psi.csv max      == targets.boost_psi_street_seed  (18)
       boost_target_full_psi.csv max == targets.boost_psi_max_eventual (30)
     and no boost table anywhere exceeds boost_psi_max_eventual.
     limits.yaml ethanol_sensor_fault_cap_psi == the street-seed ceiling.
  5. Files that engine_constants.yaml / tune/README.md point at exist.
  6. docs/intercooler-turbo-study/model/inputs.yaml engine numbers match
     engine_constants.yaml (bore, stroke, displacement, compression, rev limits).

Needs PyYAML (installed with the rd-build/tools deps on dansPC).
"""
from __future__ import annotations

import csv
import io
import os
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("validate_tune.py needs PyYAML: python -m pip install pyyaml")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TUNE = os.path.join(ROOT, "tune")
TABLES = os.path.join(TUNE, "tables")
ERR: list = []

EXPECTED_TABLES = 14
SHARED_AXIS_TABLES = ("ve_base_pct.csv", "ve_e85_pct.csv", "ignition_base_deg.csv", "lambda_target.csv")
MAP_AXIS = [20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 150, 200]
RPM_AXIS = [800, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000]
FOOTER_TABLES = {"boost_shakedown_stages.csv": "# Overboost cut setting per stage"}


def err(where, msg):
    ERR.append("%-34s %s" % (where, msg))


def num(s):
    try:
        return float(s)
    except ValueError:
        return None


def load_csv(name):
    """Return (header, rows) with rows as lists of floats. Comment/blank lines skipped."""
    text = open(os.path.join(TABLES, name), encoding="utf-8").read()
    stop = FOOTER_TABLES.get(name)
    if stop and stop in text:
        text = text[:text.index(stop)]
    lines = [ln for ln in csv.reader(io.StringIO(text))
             if ln and not ln[0].lstrip().startswith("#") and any(c.strip() for c in ln)]
    if not lines:
        err(name, "no header / data rows")
        return [], []
    header, rows = [h.strip() for h in lines[0]], []
    for i, r in enumerate(lines[1:], 1):
        if len(r) != len(header):
            err(name, "data row %d has %d cells, header has %d" % (i, len(r), len(header)))
            continue
        vals = [num(c) for c in r]
        if None in vals:
            err(name, "data row %d has a non-numeric cell: %s" % (i, r))
            continue
        rows.append(vals)
    if not rows:
        err(name, "no data rows")
    return header, rows


def monotonic(name, label, seq):
    """Strictly increasing or strictly decreasing (injector dead time lists ΔkPa high -> low,
    as copied from PCLink); flat or zig-zag axes are an error."""
    up = all(b > a for a, b in zip(seq, seq[1:]))
    down = all(b < a for a, b in zip(seq, seq[1:]))
    if not (up or down):
        err(name, "%s axis is not monotonic: %s" % (label, seq))


def check_tables(consts):
    names = sorted(f for f in os.listdir(TABLES) if f.endswith(".csv"))
    if len(names) != EXPECTED_TABLES:
        err("tune/tables", "%d CSV files, expected %d - update EXPECTED_TABLES and tune/README.md together"
            % (len(names), EXPECTED_TABLES))
    readme = open(os.path.join(TUNE, "README.md"), encoding="utf-8").read()
    for n in names:
        if "tables/" + n not in readme:
            err(n, "not listed in tune/README.md")
    data = {}
    for n in names:
        header, rows = load_csv(n)
        data[n] = (header, rows)
        if not rows:
            continue
        monotonic(n, "row (%s)" % header[0], [r[0] for r in rows])
        col_axis = [num(h) for h in header[1:]]
        if len(col_axis) > 1 and None not in col_axis:      # 2-D table: numeric column axis
            monotonic(n, "column", col_axis)
    for n in SHARED_AXIS_TABLES:
        header, rows = data.get(n, ([], []))
        if not rows:
            err(n, "missing")
            continue
        if [r[0] for r in rows] != MAP_AXIS:
            err(n, "MAP rows %s, shared axis is %s" % ([r[0] for r in rows], MAP_AXIS))
        if [num(h) for h in header[1:]] != RPM_AXIS:
            err(n, "RPM columns %s, shared axis is %s" % (header[1:], RPM_AXIS))
    # boost ceilings
    t = consts.get("targets", {})
    street, eventual = t.get("boost_psi_street_seed"), t.get("boost_psi_max_eventual")
    if street is None or eventual is None:
        err("engine_constants.yaml", "targets.boost_psi_street_seed / boost_psi_max_eventual missing")
        return
    _, rows = data.get("boost_target_psi.csv", ([], []))
    if rows and max(v for r in rows for v in r[1:]) != street:
        err("boost_target_psi.csv", "max %s psi, targets.boost_psi_street_seed is %s"
            % (max(v for r in rows for v in r[1:]), street))
    _, rows = data.get("boost_target_full_psi.csv", ([], []))
    if rows and max(r[1] for r in rows) != eventual:
        err("boost_target_full_psi.csv", "max %s psi, targets.boost_psi_max_eventual is %s"
            % (max(r[1] for r in rows), eventual))
    for n, (header, rows) in data.items():
        if not n.startswith("boost_") or "mult" in n:
            continue
        for ci, h in enumerate(header):
            if ci and "psi" in h.lower() and rows:
                peak = max(r[ci] for r in rows)
                if peak > eventual:
                    err(n, "column %r peaks at %s psi, above boost_psi_max_eventual %s" % (h, peak, eventual))
    return street


def check_limits(street):
    lim = yaml.safe_load(open(os.path.join(TUNE, "limits.yaml"), encoding="utf-8")) or {}
    cap = (((lim.get("ecu_limits") or {}).get("boost") or {}).get("ethanol_sensor_fault_cap_psi"))
    if street is not None and cap != street:
        err("limits.yaml", "ethanol_sensor_fault_cap_psi %s, street-seed ceiling is %s" % (cap, street))


def check_paths(consts):
    """Every 'tune/...' or 'tables/...' path named in engine_constants.yaml or tune/README.md exists."""
    texts = {"engine_constants.yaml": open(os.path.join(TUNE, "engine_constants.yaml"), encoding="utf-8").read(),
             "tune/README.md": open(os.path.join(TUNE, "README.md"), encoding="utf-8").read()}
    for src, text in texts.items():
        for m in sorted(set(re.findall(r"\b((?:tune/)?(?:tables|docs|scripts)/[\w.\-/]+\.\w+)", text))):
            # a bare docs/... may mean tune/docs/... or the repo-root docs/ - accept either
            cands = [m] if m.startswith("tune/") else ["tune/" + m, m]
            if not any(os.path.exists(os.path.join(ROOT, c)) for c in cands):
                err(src, "points at %s, which does not exist" % " or ".join(cands))


def check_inputs_yaml(consts):
    p = os.path.join(ROOT, "docs", "intercooler-turbo-study", "model", "inputs.yaml")
    if not os.path.exists(p):
        return
    inp = yaml.safe_load(open(p, encoding="utf-8")) or {}
    e, ie = consts.get("engine", {}), inp.get("engine", {})
    t = consts.get("targets", {})
    pairs = [("bore_mm", e.get("bore_mm"), ie.get("bore_mm")),
             ("stroke_mm", e.get("stroke_mm"), ie.get("stroke_mm")),
             ("displacement_cc", e.get("displacement_cc"), ie.get("displacement_cc")),
             ("compression_ratio", e.get("compression_ratio"), ie.get("compression_ratio")),
             ("rev_limit_rpm", t.get("rev_limit_rpm"), ie.get("rev_limit_rpm")),
             ("rev_limit_soft_first_start", t.get("rev_limit_soft_first_start"), ie.get("rev_limit_soft_first_start_rpm"))]
    for key, a, b in pairs:
        if a != b:
            err("inputs.yaml", "%s = %r, tune/engine_constants.yaml says %r" % (key, b, a))


def main():
    consts = yaml.safe_load(open(os.path.join(TUNE, "engine_constants.yaml"), encoding="utf-8")) or {}
    street = check_tables(consts)
    check_limits(street)
    check_paths(consts)
    check_inputs_yaml(consts)
    if ERR:
        print("tune check: %d problem(s)" % len(ERR))
        for e in ERR:
            print("  " + e)
        return 1
    print("tune check OK: %d tables, shared MAP x RPM axis, boost ceilings, paths, inputs.yaml"
          % EXPECTED_TABLES)
    return 0


if __name__ == "__main__":
    sys.exit(main())
