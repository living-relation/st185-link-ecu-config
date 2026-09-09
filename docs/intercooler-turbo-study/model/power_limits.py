#!/usr/bin/env python3
"""Calculated power + knock/IAT limits for the ST185 5S-GTE.

Power is computed from airflow (Phase 1) and MatchBot (Phase 2). It is not
a target the user picked. Knock/IAT ceilings are estimated from charge temp
and fuel; they must be confirmed on a knock-logged dyno.

Writes model/power_limits.json.
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


def f_to_c(f):
    return (f - 32.0) * 5.0 / 9.0


def main():
    loss = INPUTS["driveline"]["loss_fraction_modeled"]
    mb_pts = MB["runs"][0]["points"]  # engine-side identical across compressors

    matchbot_curve = []
    for p in mb_pts:
        cor = float(p["cor_lbmin"])
        rpm = int(p["rpm"])
        boost = float(p["boost"])
        iat_f = p.get("iat_f")
        iat_c = f_to_c(float(iat_f)) if iat_f not in (None, "") else None
        pump_crank = float(p["power_hp"])          # MatchBot BSFC method
        e85_crank = cor * INPUTS["fuels"]["e85"]["hp_per_lbmin_crank"]
        matchbot_curve.append({
            "rpm": rpm,
            "boost_psi": boost,
            "cor_lbmin": cor,
            "pr": float(p["cpr"]),
            "iat_c": None if iat_c is None else round(iat_c, 1),
            "t2_c": round(f_to_c(float(p["t2_f"])), 1),
            "emp_psi": float(p["emp_psi"]),
            "dp_psi": float(p["dp_psi"]),
            "phi": float(p["phi"]),
            "wg_pct": float(p["wg_pct"]),
            "pump_crank_bhp_matchbot": round(pump_crank),
            "pump_whp_matchbot": round(pump_crank * (1 - loss)),
            "e85_crank_bhp": round(e85_crank),
            "e85_whp": round(e85_crank * (1 - loss)),
        })

    # Phase-1 grid peaks (breathing-eroded VE in inputs.yaml — more conservative
    # at 8000 than the MatchBot breathing-VE case).
    def at(rpm, psi):
        row = next(r for r in AIR["rows"] if r["rpm"] == rpm)
        return row["boost"][str(psi)]

    grid_peaks = {
        "7500_30": at(7500, 30),
        "8000_27": at(8000, 27) if 27 in INPUTS["boost_scenarios_psi"] else None,
        "6000_30": at(6000, 30),
        "5000_30": at(5000, 30),
    }

    # Knock / IAT ceiling (estimated).
    # 93 pump: IAT above ~45 C at 25+ psi on 8.5:1 is the usual knock-onset
    # band for a well-tuned 4-cyl. We do not have a knock log; this is a
    # planning ceiling, not a tune.
    # E85: charge cooling + octane moves the ceiling to the turbo/IAT hardware
    # limit, not knock. Water/meth above 27 psi is extra charge cooling.
    tf = next(c for c in IC["cores_at_60mph"]
              if c["kind"] == IC["pick"]["core"] and c["thick_in"] == IC["pick"]["thick_in"])
    iat_road_c = tf["t_out_c"]

    knock = {
        "pump_93": {
            "knock_limited": True,
            "planning_boost_ceiling_psi": 22,
            "why": (
                "8.5:1 forged 5S-GTE on 93. MatchBot IAT at 25–30 psi is still "
                f"in the {iat_road_c:.0f} C region after a 4.5 in core — "
                "survivable, but 93 will want timing pulled as boost climbs. "
                "Street seed stays 18 psi; 22 psi is the planning ceiling "
                "until a knock-logged pull says otherwise."
            ),
            "use_water_meth": False,
        },
        "e85": {
            "knock_limited": False,
            "planning_boost_ceiling_psi": 30,
            "why": (
                "E85 at λ≈0.78 is not knock-limited at these cylinder pressures "
                "on 8.5:1. The ceiling is compressor choke / turbine dP / IAT, "
                "not octane. 30 psi is the hardware max, not a required point."
            ),
            "use_water_meth": True,
            "water_meth_engage_psi": INPUTS["water_meth"]["engage_boost_psi"],
            "water_meth_effect": (
                "Engage ≥27 psi to cut compressor-out temp 20–40 C in the "
                "hottest island. That is extra IAT margin and can hold 28–30 "
                "psi farther into the redline band instead of tapering to 27. "
                "It is not free power — it is permission to keep the boost "
                "you already computed."
            ),
        },
    }

    # Headline calculated numbers (honest band, not a single trophy figure)
    e85_peak = max(matchbot_curve, key=lambda x: x["e85_crank_bhp"])
    pump_peak = max(matchbot_curve, key=lambda x: x["pump_crank_bhp_matchbot"])

    headline = {
        "e85_peak_rpm": e85_peak["rpm"],
        "e85_peak_boost_psi": e85_peak["boost_psi"],
        "e85_crank_bhp": e85_peak["e85_crank_bhp"],
        "e85_whp": e85_peak["e85_whp"],
        "pump_peak_rpm": pump_peak["rpm"],
        "pump_crank_bhp_matchbot": pump_peak["pump_crank_bhp_matchbot"],
        "pump_whp_matchbot": pump_peak["pump_whp_matchbot"],
        "driveline_loss": loss,
        "note": (
            "MatchBot pump-gas hp uses official gasoline BSFC/AFR (tooltip: "
            "keep those even for alcohol). E85 crank uses 11 hp per lb/min "
            "on the same corrected airflow. Wheel figures use 17% AWD loss "
            "(carbon 1-pc shaft + lightened flywheel + rebuilt E150F)."
        ),
    }

    rec = {
        "matchbot_curve": matchbot_curve,
        "grid_peaks": grid_peaks,
        "knock": knock,
        "headline": headline,
        "turbo_fit": {
            "EFR_7064": "55 lb/min @ PR 3.0 is the published 56 lb/min wall. Choke. Not the turbo.",
            "EFR_7163": "55 lb/min sits on the right side of a 60 lb/min map. Usable, little choke margin at 8000/27.",
            "EFR_7670": "55 lb/min is inside a 64 lb/min map. Best top-end island; more shaft inertia than 7163.",
            "recommendation": (
                "Keep 7163-G if the car is a road car and you value 3–4k "
                "response (mixed-flow 63 mm turbine, 0.80 A/R). Step to "
                "7670-C if the goal is holding 30 psi to 7500+ without riding "
                "the 7163 choke line. 7064 is the wrong compressor for this "
                "displacement × boost. That agrees with the prior Drive PDF "
                "on 7670-C first / 7163-G second, now on 2189 cc and 8000 rpm "
                "instead of 2164 cc / 7500."
            ),
        },
    }
    OUT.write_text(json.dumps(rec, indent=2))
    print(f"wrote {OUT}")
    print("headline E85", headline["e85_crank_bhp"], "crank /", headline["e85_whp"], "whp @",
          headline["e85_peak_rpm"], "rpm", headline["e85_peak_boost_psi"], "psi")
    print("headline pump MatchBot", headline["pump_crank_bhp_matchbot"], "crank")


if __name__ == "__main__":
    main()
