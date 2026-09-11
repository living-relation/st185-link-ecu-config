#!/usr/bin/env python3
"""Power, knock ceilings, and water/meth on vs off for 93 / E50 / E85.

Writes model/power_limits.json. Power is calculated. WMI activation is a
fuel-specific RPM × boost gate, plotted on every curve.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
INPUTS = yaml.safe_load((HERE / "inputs.yaml").read_text())
AIR = json.loads((HERE / "airflow_demand.json").read_text())
MB = json.loads((HERE / "matchbot_results.json").read_text())
IC = json.loads((HERE / "ic_stack.json").read_text())
OUT = HERE / "power_limits.json"

LOSS = INPUTS["driveline"]["loss_fraction_modeled"]
WMI = INPUTS["water_meth"]
FUELS = INPUTS["fuels"]


def f_to_c(f):
    return (f - 32.0) * 5.0 / 9.0


def wmi_on(fuel_key, rpm, boost_psi, iat_c=None, tps=100):
    gate = WMI["activate"][fuel_key]
    if boost_psi < gate["min_boost_psi"]:
        return False
    if rpm < gate["min_rpm"]:
        return False
    if tps < gate["min_tps_pct"]:
        return False
    if iat_c is not None and iat_c < gate["min_iat_c"]:
        return False
    return True


def crank(mdot, fuel_key, spraying):
    base = FUELS[fuel_key]["hp_per_lbmin_crank"]
    bump = WMI["hp_per_lbmin_bump"][fuel_key] if spraying else 0.0
    return mdot * (base + bump)


def main():
    mb_pts = MB["runs"][0]["points"]

    matchbot_curve = []
    for p in mb_pts:
        cor = float(p["cor_lbmin"])
        rpm = int(p["rpm"])
        boost = float(p["boost"])
        iat_f = p.get("iat_f")
        iat_c = f_to_c(float(iat_f)) if iat_f not in (None, "") else 50.0
        iat_wmi = iat_c - WMI["t2_drop_c"] * 0.45   # post-IC share of the T2 drop
        row = {
            "rpm": rpm,
            "boost_psi": boost,
            "cor_lbmin": cor,
            "pr": float(p["cpr"]),
            "iat_c": round(iat_c, 1),
            "iat_c_wmi": round(iat_wmi, 1),
            "t2_c": round(f_to_c(float(p["t2_f"])), 1),
            "emp_psi": float(p["emp_psi"]),
            "dp_psi": float(p["dp_psi"]),
            "phi": float(p["phi"]),
            "wg_pct": float(p["wg_pct"]),
            "pump_crank_bhp_matchbot": round(float(p["power_hp"])),
            "fuels": {},
        }
        for fkey in ("pump_93", "mix_50_50", "e85"):
            on = wmi_on(fkey, rpm, boost, iat_c)
            off_c = crank(cor, fkey, False)
            on_c = crank(cor, fkey, True)
            dry_ceil = {"pump_93": 22, "mix_50_50": 25, "e85": 30}[fkey]
            wmi_ceil = {"pump_93": 27, "mix_50_50": 30, "e85": 30}[fkey]
            if boost > wmi_ceil + 1e-9:
                used = off_c
                used_on = False
            elif on and boost <= wmi_ceil + 1e-9:
                used = on_c
                used_on = True
            elif boost > dry_ceil + 1e-9:
                used = off_c
                used_on = False
            else:
                used = off_c
                used_on = False
            row["fuels"][fkey] = {
                "wmi_gate": used_on,
                "over_dry_ceiling": boost > dry_ceil + 1e-9,
                "over_wmi_ceiling": boost > wmi_ceil + 1e-9,
                "crank_off": round(off_c),
                "whp_off": round(off_c * (1 - LOSS)),
                "crank_on": round(on_c),
                "whp_on": round(on_c * (1 - LOSS)),
                "crank_used": round(used),
                "whp_used": round(used * (1 - LOSS)),
            }
        matchbot_curve.append(row)

    # Full rpm × boost grid from Phase-1 airflow (for the activation heatmap)
    grid = []
    for r in AIR["rows"]:
        rpm = r["rpm"]
        for psi_s, e in r["boost"].items():
            psi = float(psi_s)
            mdot = e["mdot_lbmin"]
            cell = {"rpm": rpm, "boost_psi": psi, "mdot_lbmin": mdot, "fuels": {}}
            for fkey in ("pump_93", "mix_50_50", "e85"):
                on = wmi_on(fkey, rpm, psi, iat_c=50)
                off_c = crank(mdot, fkey, False)
                on_c = crank(mdot, fkey, True)
                cell["fuels"][fkey] = {
                    "wmi_gate": on,
                    "crank_off": round(off_c),
                    "whp_off": round(off_c * (1 - LOSS)),
                    "crank_on": round(on_c),
                    "whp_on": round(on_c * (1 - LOSS)),
                }
            grid.append(cell)

    tf = next(c for c in IC["cores_at_60mph"]
              if c["kind"] == IC["pick"]["core"] and c["thick_in"] == IC["pick"]["thick_in"])

    knock = {
        "pump_93": {
            "knock_limited": True,
            "ceiling_psi_no_wmi": 22,
            "ceiling_psi_wmi": 27,
            "why": "8.5:1 on 93. Without WMI, plan 22 psi. WMI at ≥22 psi / ≥3500 rpm buys IAT and timing toward 27.",
        },
        "mix_50_50": {
            "knock_limited": True,
            "ceiling_psi_no_wmi": 25,
            "ceiling_psi_wmi": 30,
            "why": "50/50 93+E85 is ~E42. Mid octane. 25 psi dry, 30 psi with WMI once RPM ≥4000.",
        },
        "e85": {
            "knock_limited": False,
            "ceiling_psi_no_wmi": 30,
            "ceiling_psi_wmi": 30,
            "why": "E85 is hardware-limited. WMI at ≥27 psi / ≥4500 rpm is IAT margin so 28–30 psi can hold farther into the redline band.",
        },
    }

    def peak_grid(fkey, spraying):
        ceiling = knock[fkey]["ceiling_psi_wmi" if spraying else "ceiling_psi_no_wmi"]
        best = None
        for cell in grid:
            if cell["boost_psi"] > ceiling + 1e-9:
                continue
            fuel = cell["fuels"][fkey]
            on = spraying and fuel["wmi_gate"]
            crank_v = fuel["crank_on"] if on else fuel["crank_off"]
            whp_v = fuel["whp_on"] if on else fuel["whp_off"]
            cand = {
                "rpm": cell["rpm"],
                "boost_psi": cell["boost_psi"],
                "crank": crank_v,
                "whp": whp_v,
                "wmi_gate": on,
            }
            if best is None or cand["crank"] > best["crank"]:
                best = cand
        return best

    headline = {}
    for fkey, label in (("e85", "e85"), ("mix_50_50", "mix"), ("pump_93", "pump")):
        u = peak_grid(fkey, True)
        o = peak_grid(fkey, False)
        headline[label] = {
            "rpm": u["rpm"],
            "boost_psi": u["boost_psi"],
            "crank_wmi_strategy": u["crank"],
            "whp_wmi_strategy": u["whp"],
            "crank_dry": o["crank"],
            "whp_dry": o["whp"],
            "dry_rpm": o["rpm"],
            "dry_boost_psi": o["boost_psi"],
        }
    headline["driveline_loss"] = LOSS
    headline["note"] = (
        "Dry crank uses hp/lb-min (10 / 10.5 / 11) and stops at that fuel's "
        "knock ceiling (22 / 25 / 30 psi). WMI adds 0.40 / 0.25 / 0.15 "
        "hp/lb-min when the gate is true and may raise the ceiling "
        "(27 / 30 / 30). Wheel uses 17% AWD loss. Headlines are from the "
        "Phase-1 rpm×boost grid so 93 dry is not taken from a 27 psi MatchBot point."
    )

    rec = {
        "matchbot_curve": matchbot_curve,
        "grid": grid,
        "knock": knock,
        "wmi": {
            "mix": WMI["mix"],
            "t2_drop_c": WMI["t2_drop_c"],
            "activate": WMI["activate"],
            "bump": WMI["hp_per_lbmin_bump"],
            "ecu": WMI["ecu"],
            "why_gates": (
                "Spray only where T2/IAT and cylinder pressure need it. "
                "93 gates earliest (knock). E42 in the middle. E85 last "
                "(compressor-outlet heat at high PR × high flow). Cold IAT "
                "and part-throttle stay dry so the tank lasts and the charge "
                "is not over-wet at idle."
            ),
        },
        "activation_chart": [
            {
                "fuel": FUELS[k]["name"],
                "key": k,
                "min_boost_psi": WMI["activate"][k]["min_boost_psi"],
                "min_rpm": WMI["activate"][k]["min_rpm"],
                "min_tps_pct": WMI["activate"][k]["min_tps_pct"],
                "min_iat_c": WMI["activate"][k]["min_iat_c"],
                "why": knock[k]["why"],
            }
            for k in ("pump_93", "mix_50_50", "e85")
        ],
        "headline": headline,
        "turbo_fit": {
            "EFR_7064": "55 lb/min @ PR 3.0 is the published 56 lb/min wall. Choke.",
            "EFR_7163": "55 lb/min sits on the right side of a 60 lb/min map.",
            "EFR_7670": "55 lb/min is inside a 64 lb/min map.",
            "recommendation": (
                "Keep 7163-G for a road car. Step to 7670-C to hold 30 psi "
                "to 7500+ in-island. 7064 is the wrong compressor."
            ),
        },
        "iat_road_c": tf["t_out_c"],
    }
    OUT.write_text(json.dumps(rec, indent=2))
    print(f"wrote {OUT}")
    for k, v in headline.items():
        if k in ("driveline_loss", "note"):
            continue
        print(k, "wmi", v["crank_wmi_strategy"], "dry", v["crank_dry"],
              "@", v["rpm"], v["boost_psi"])


if __name__ == "__main__":
    main()
