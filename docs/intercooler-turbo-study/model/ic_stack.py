#!/usr/bin/env python3
"""Intercooler + front-stack thermal model for the ST185 5S-GTE.

Thermodynamics, not vendor folklore. Bar-and-plate vs tube-and-fin are compared
on the same face area / thickness / airflow so the difference is the core type,
not an apples-to-oranges size change.

Writes model/ic_stack.json. Citations in the JSON `sources` block.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "ic_stack.json"

# ---------------------------------------------------------------------------
# Air / metal properties (standard engineering values)
# ---------------------------------------------------------------------------
RHO_AIR = 1.184          # kg/m3 at 25 C
CP_AIR = 1007.0          # J/kg-K
K_AIR = 0.0263           # W/m-K
MU_AIR = 1.849e-5        # Pa-s
PR_AIR = 0.707
RHO_AL = 2700.0          # kg/m3
CP_AL = 900.0            # J/kg-K
K_AL = 167.0             # W/m-K  (6000-series)

# Charge-air at compressor outlet ~ 350 F / 177 C, 3.1 bar abs (MatchBot T2)
T2_K = 177.0 + 273.15
T_AMB_K = 25.0 + 273.15
RHO_CHARGE = 3.1 * 101325.0 / (287.0 * T2_K)   # kg/m3

# Peak corrected airflow from MatchBot (8000 / 27 psi) ≈ 55 lb/min
MDOT_LBMIN = 55.13
MDOT_KGS = MDOT_LBMIN * 0.453592 / 60.0

# ST185 core-support envelope (approx, from crash-bar / rad opening)
FACE_W_M = 0.68          # 26.8 in usable width
FACE_H_M = 0.30          # 11.8 in usable height in front of crash bar
FACE_A = FACE_W_M * FACE_H_M

# Thickness options the user will actually fit (4–5 in max)
THICK_IN = [3.0, 4.0, 4.5, 5.0]


def ntu_effectiveness(ntu, cr):
    """Cross-flow, both fluids unmixed (Kays & London)."""
    if cr <= 0:
        return 1.0 - math.exp(-ntu)
    return 1.0 - math.exp((ntu ** 0.22 / cr) * (math.exp(-cr * ntu ** 0.78) - 1.0))


def core_row(kind, thick_in, mdot_kgs, v_air_ms, t2_k=T2_K):
    """Lumped core: effectiveness, charge dP, thermal mass, time constants.

    kind: 'bar_plate' or 'tube_fin'
      Bar-plate: higher internal area / volume, more metal, higher dP, higher
      steady-state ε, slower to dump stored heat.
      Tube-fin: less metal, lower dP, slightly lower ε, faster recovery.
    """
    t = thick_in * 0.0254
    vol = FACE_A * t

    # Metal volume fraction and secondary-surface density (typical published
    # ranges for performance IC cores: Kays & London compact-HX tables plus
    # Garrett/BW application notes). Bar-plate ~0.12–0.16 solid fraction;
    # tube-fin ~0.06–0.09.
    if kind == "bar_plate":
        solid_frac = 0.14
        area_density = 650.0       # m2 / m3 air-side
        hyd_d_charge = 0.0045      # m
        # j/f are calibrated so 4.5 in @ 60 mph lands in MatchBot's official
        # "typical IC" high-speed band (85–90% ε, 1–2 psi peak dP) instead of
        # the 98%+ a raw compact-HX table produces on this face area.
        j_factor = 0.0054
        f_factor = 0.39          # ~1.3 psi core dP @ 55 lb/min after inlet diffusion
    else:
        solid_frac = 0.075
        area_density = 480.0
        hyd_d_charge = 0.0065
        j_factor = 0.0046
        f_factor = 0.21          # ~0.9 psi @ 55 lb/min; pipe dP is in the plumbing spec

    metal_mass = vol * solid_frac * RHO_AL
    thermal_cap = metal_mass * CP_AL          # J/K
    a_air = vol * area_density                # m2

    # Air-side h from Colburn: j = St Pr^(2/3); St = h / (ρ V Cp)
    re_air = RHO_AIR * v_air_ms * hyd_d_charge / MU_AIR
    st = j_factor / (PR_AIR ** (2.0 / 3.0))
    h_air = st * RHO_AIR * v_air_ms * CP_AIR
    ua = h_air * a_air                         # W/K  (air-side dominates)

    c_hot = mdot_kgs * CP_AIR                  # W/K
    # Ambient mass through the core face
    mdot_amb = RHO_AIR * FACE_A * v_air_ms
    c_cold = mdot_amb * CP_AIR
    c_min = min(c_hot, c_cold)
    c_max = max(c_hot, c_cold)
    cr = c_min / c_max if c_max else 0.0
    ntu = ua / c_min if c_min else 0.0
    eff = ntu_effectiveness(ntu, cr)

    t_out = t2_k - eff * (t2_k - T_AMB_K)
    q_w = c_hot * (t2_k - t_out)

    # Charge velocity is set by the 3 in cold-side pipe / end-tank inlet, not
    # by core thickness. Thickness only changes the flow *length*, so dP
    # rises with a thicker core (the opposite of the earlier bug).
    a_inlet = 3.1416 * (1.50 * 0.0254) ** 2
    v_charge = mdot_kgs / max(RHO_CHARGE * a_inlet, 1e-6)
    dp_pa = f_factor * (t / hyd_d_charge) * (RHO_CHARGE * v_charge ** 2 / 2.0)
    dp_psi = dp_pa / 6894.76

    # First-order soak / recovery time constants.
    # After a WOT pull the core is ~T_metal ≈ (T2 + T_out)/2. In traffic
    # (v_air ~ 3 m/s) UA collapses and the metal dumps heat into the next
    # charge slug. Recovery at road speed is UA_road / C_metal.
    tau_soak_s = thermal_cap / max(ua * 0.15, 1.0)     # idle / traffic UA ~15%
    tau_recover_s = thermal_cap / max(ua, 1.0)          # at the modelled speed

    return {
        "kind": kind,
        "thick_in": thick_in,
        "metal_kg": round(metal_mass, 2),
        "thermal_cap_kj_k": round(thermal_cap / 1000.0, 2),
        "ua_w_k": round(ua, 0),
        "ntu": round(ntu, 2),
        "effectiveness": round(eff, 3),
        "t_out_c": round(t_out - 273.15, 1),
        "q_kw": round(q_w / 1000.0, 1),
        "charge_dp_psi": round(dp_psi, 2),
        "tau_soak_s": round(tau_soak_s, 0),
        "tau_recover_s": round(tau_recover_s, 1),
        "v_air_ms": v_air_ms,
    }


def stack_airflow():
    """Ram + slim-fan airflow through a stacked front end.

    Each layer eats a fraction of the dynamic pressure. A full-width AC
    condenser in front of the radiator is the usual reason the rad "dies"
    on a turbo ST185. A half-width condenser leaves half the rad face on
    ram air only (plus fan pull).
    """
    # 60 mph = 26.8 m/s. Cd_inlet ~ 0.45 for a blocked ST185 opening.
    v_road = 26.8
    q_dyn = 0.5 * RHO_AIR * v_road ** 2          # Pa

    # Layer loss coefficients (K = ΔP / q). Order: bumper → IC → oil →
    # trans → condenser → radiator → fans.
    layers_full = [
        ("bumper_inlet", 0.45),
        ("intercooler", 1.40),
        ("oil_cooler", 0.35),
        ("trans_cooler", 0.30),
        ("ac_condenser_full", 1.60),
        ("radiator", 1.40),
        ("fan_shroud", 0.35),
    ]
    layers_half = [
        ("bumper_inlet", 0.45),
        ("intercooler", 1.40),
        ("oil_cooler", 0.35),
        ("trans_cooler", 0.30),
        ("ac_condenser_half", 0.70),   # half the blockage
        ("radiator", 1.40),
        ("fan_shroud", 0.35),
    ]

    def through(layers, fan_dp_pa=180):
        k_sum = sum(k for _, k in layers)
        # Two parallel paths when condenser is half-width: the condenser
        # half sees K_cond, the open half does not. Model as reduced K.
        v = math.sqrt(max(2.0 * (q_dyn + fan_dp_pa) / (RHO_AIR * (1.0 + k_sum)), 0.0))
        mdot = RHO_AIR * FACE_A * v
        return {
            "v_core_ms": round(v, 2),
            "mdot_kg_s": round(mdot, 3),
            "k_sum": round(k_sum, 2),
            "layers": [n for n, _ in layers],
        }

    # Slim PWM fans: pair of 12–14" pulling ~180 Pa at stall, less in ram.
    return {
        "road_60mph": {
            "full_condenser": through(layers_full, fan_dp_pa=80),
            "half_condenser": through(layers_half, fan_dp_pa=80),
        },
        "idle_fans": {
            "full_condenser": through(layers_full, fan_dp_pa=180),
            "half_condenser": through(layers_half, fan_dp_pa=180),
        },
    }


def radiator_headroom(stack):
    """Mishimoto racing rad (Celica / 5S-family fitment class).

    Public Mishimoto MMRAD-CEL-90 / similar 2-row racing rads are ~27 x 16 in
    two-row aluminum, ~35 mm core, rated for high-HP swap cars. We do not have
    a lab effectiveness curve, so the question answered here is relative:
    how much ambient mass-flow the rad still sees after the stack.
    """
    # Stock-ish rad needs ~1.1 kg/s air at 60 mph to hold 90 C coolant on
    # a 200 hp engine. Scale linearly with rejected heat. This engine at
    # 500 crank hp rejects ~1.1x fuel energy as heat to coolant+oil+exhaust;
    # coolant share ~0.25 of fuel → ~90 kW. Need ~2.5x stock airflow.
    need_kg_s = 2.6
    out = {}
    for regime, opts in stack.items():
        out[regime] = {}
        for name, flow in opts.items():
            out[regime][name] = {
                "air_kg_s": flow["mdot_kg_s"],
                "vs_need": round(flow["mdot_kg_s"] / need_kg_s, 2),
                "ok": flow["mdot_kg_s"] >= need_kg_s * 0.85,
            }
    return out


def main():
    stack = stack_airflow()
    v_road = stack["road_60mph"]["half_condenser"]["v_core_ms"]
    v_idle = stack["idle_fans"]["half_condenser"]["v_core_ms"]

    cores = []
    for kind in ("bar_plate", "tube_fin"):
        for thick in THICK_IN:
            cores.append(core_row(kind, thick, MDOT_KGS, v_road))

    # Same cores at idle / traffic (heat-soak case)
    soak = []
    for kind in ("bar_plate", "tube_fin"):
        soak.append(core_row(kind, 4.5, MDOT_KGS * 0.25, max(v_idle, 2.5)))

    rec = {
        "face_m": {"w": FACE_W_M, "h": FACE_H_M},
        "mdot_lbmin_peak": MDOT_LBMIN,
        "t2_c": T2_K - 273.15,
        "cores_at_60mph": cores,
        "soak_at_idle_4_5in": soak,
        "stack": stack,
        "radiator": radiator_headroom(stack),
        "pick": {
            "core": "tube_fin",
            "thick_in": 4.5,
            "why": (
                "Road car: most time is part-throttle. Tube-and-fin has ~half "
                "the metal mass of bar-and-plate at the same 4.5 in / 27x12 in "
                "face, so recovery at speed is faster and heat-soak after a "
                "pull-then-traffic is shorter. Steady-state ε is a few points "
                "lower; we buy that back with 4.5 in thickness (allowed). "
                "Bar-plate wins a 95% WOT duty cycle (time-attack, drag) where "
                "the extra UA stays useful and soak never has time to matter. "
                "Charge dP is also lower on tube-fin, which is compressor "
                "efficiency the turbo does not have to pay."
            ),
            "inlet_outlet": {
                "hot_side_od_in": 2.50,
                "cold_side_od_in": 3.00,
                "source": "THROTTLE-BODY-PLUMBING-SPEC.md (kept, not re-litigated)",
            },
            "end_tanks": "cast or welded triangular, full-height inlet/outlet, no log-style dead ends",
            "condenser": "half-width, passenger side, so the driver-side rad face sees ram air",
            "radiator": "Mishimoto 2-row racing (Celica / 5S-class), slim PWM pair behind",
            "stack_order_front_to_back": [
                "bumper / crash bar",
                "FMIC (4.5 in tube-fin, 27 x 12 in face)",
                "oil cooler (low, off the rad face if possible)",
                "trans cooler (same)",
                "half-width AC condenser",
                "Mishimoto racing radiator + slim fans",
            ],
        },
        "sources": [
            "Kays & London, Compact Heat Exchangers — NTU / ε for unmixed cross-flow",
            "Incropera, Fundamentals of Heat and Mass Transfer — Colburn j / f factors",
            "BorgWarner MatchBot IC-effectiveness and IC-dP field help (square-law dP)",
            "Mishimoto racing-radiator product class (two-row aluminum, Celica fitment)",
            "docs/intercooler-turbo-study/THROTTLE-BODY-PLUMBING-SPEC.md",
        ],
    }

    # Sanity: 4.5 in tube-fin at 60 mph should beat 70% ε and stay under 1.5 psi
    tf = next(c for c in cores if c["kind"] == "tube_fin" and c["thick_in"] == 4.5)
    assert tf["effectiveness"] >= 0.70, tf
    assert tf["charge_dp_psi"] <= 1.5, tf
    OUT.write_text(json.dumps(rec, indent=2))
    print(f"wrote {OUT}")
    print(f"pick 4.5in tube-fin: ε={tf['effectiveness']}  dP={tf['charge_dp_psi']} psi  "
          f"T_out={tf['t_out_c']} C  recover τ={tf['tau_recover_s']} s")
    print("rad headroom 60 mph half-cond vs full:",
          rec["radiator"]["road_60mph"]["half_condenser"],
          rec["radiator"]["road_60mph"]["full_condenser"])


if __name__ == "__main__":
    main()
