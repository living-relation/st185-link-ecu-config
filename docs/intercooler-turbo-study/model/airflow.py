#!/usr/bin/env python3
"""Engine airflow-demand and power model for the ST185 5S-GTE build.

Reads model/inputs.yaml (single source of truth) and computes, across the rpm x
boost grid:

  * mass airflow demand (lb/min) from VE, displacement and pressure ratio,
  * crank BHP and wheel WHP for each fuel (93 pump vs E85),

then writes model/airflow_demand.json for the report generators to consume and
prints a validation table.

Physics
-------
    mdot [lb/min] = VE * (CID * RPM / 2 / 1728) * rho_air * PR
    PR            = (boost_psi + baro_psi) / baro_psi        (absolute)
    crank_bhp     = mdot * hp_per_lbmin(fuel)
    wheel_whp     = crank_bhp * (1 - driveline_loss)

VE is linearly interpolated from the estimated ve_curve. This is a planning
model; VE and the hp/lb-min and driveline-loss rules of thumb must be confirmed
on a load-bearing dyno. No turbine-backpressure erosion is applied here (that is
turbo/housing specific and handled in the Phase 2 turbo overlays).
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs.yaml"
OUT = HERE / "airflow_demand.json"


def lerp(xs, ys, x):
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            t = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
            return ys[i - 1] + t * (ys[i] - ys[i - 1])
    return ys[-1]


def main() -> None:
    cfg = yaml.safe_load(INPUTS.read_text())
    eng = cfg["engine"]
    amb = cfg["ambient"]
    cid = eng["cid"]
    rho = amb["air_density_lb_ft3"]
    baro = amb["baro_psi"]
    ve_rpm = cfg["ve_curve"]["rpm"]
    ve_val = cfg["ve_curve"]["ve"]
    loss = cfg["driveline"]["loss_fraction_modeled"]

    coeff = cid / (2.0 * 1728.0) * rho  # lb/min = coeff * rpm * VE * PR

    rows = []
    for rpm in cfg["rpm_axis"]:
        ve = lerp(ve_rpm, ve_val, rpm)
        row = {"rpm": rpm, "ve": round(ve, 3), "boost": {}}
        for psi in cfg["boost_scenarios_psi"]:
            pr = (psi + baro) / baro
            mdot = coeff * rpm * ve * pr
            entry = {"pr": round(pr, 3), "mdot_lbmin": round(mdot, 2)}
            for fkey, fuel in cfg["fuels"].items():
                crank = mdot * fuel["hp_per_lbmin_crank"]
                whp = crank * (1.0 - loss)
                entry[fkey] = {"crank_bhp": round(crank), "whp": round(whp)}
            row["boost"][psi] = entry
        rows.append(row)

    OUT.write_text(json.dumps({"coeff": coeff, "loss": loss, "rows": rows}, indent=2))

    # ---- validation / summary ------------------------------------------
    def at(rpm, psi):
        r = next(r for r in rows if r["rpm"] == rpm)
        return r["boost"][psi]

    print(f"coeff (lb/min per rpm*VE*PR) = {coeff:.7f}   driveline loss = {loss:.0%}")
    print("\nPeak airflow + power at redline band (per fuel):")
    print(f"{'rpm':>5}{'psi':>5}{'mdot':>8}{'93 whp':>9}{'E85 whp':>9}{'E85 crank':>11}")
    for rpm in (7000, 7500, 8000):
        for psi in (25, 30):
            e = at(rpm, psi)
            print(f"{rpm:>5}{psi:>5}{e['mdot_lbmin']:>8}{e['pump_93']['whp']:>9}"
                  f"{e['e85']['whp']:>9}{e['e85']['crank_bhp']:>11}")

    # sanity check vs the prior Drive analysis (~58 lb/min at 30 psi / 7500 on
    # 2164 cc; slightly higher here on 2189 cc).
    m75_30 = at(7500, 30)["mdot_lbmin"]
    assert 57.0 <= m75_30 <= 61.0, f"airflow @7500/30psi out of expected band: {m75_30}"
    print(f"\nOK: airflow @7500/30psi = {m75_30} lb/min (expected ~58-59 for 2189 cc)")
    print(f"wrote {OUT.relative_to(HERE.parents[2])}")


if __name__ == "__main__":
    main()
