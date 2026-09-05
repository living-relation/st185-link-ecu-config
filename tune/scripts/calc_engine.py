#!/usr/bin/env python3
"""ST185 hybrid engine math helpers. Run: python calc_engine.py"""
import math

BORE_MM = 87.5
STROKE_MM = 91.0
CYLINDERS = 4
INJECTOR_CC = 1400  # @ reference pressure in ATS rating
BASE_FUEL_PSI = 43.5
STOICH_AFR_93 = 14.7
STOICH_AFR_E85 = 9.8


def displacement_cc() -> float:
    r = BORE_MM / 2
    return math.pi * r * r * STROKE_MM * CYLINDERS / 1000


def injector_flow_at_pressure(cc_at_ref: float, ref_psi: float, rail_psi: float) -> float:
    return cc_at_ref * math.sqrt(rail_psi / ref_psi)


def main() -> None:
    disp = displacement_cc()
    print(f"Displacement: {disp:.1f} cc")
    for rail in (43.5, 50.0, 58.0):
        flow = injector_flow_at_pressure(INJECTOR_CC, 43.5, rail)
        print(f"Injector flow @ {rail:.1f} psi rail: ~{flow:.0f} cc/min per injector")
    print(f"Base FPR setpoint (startup map): {BASE_FUEL_PSI} psi, 1:1 boost referenced")
    print(f"E85 vs 93 stoich ratio (fuel mass): ~{STOICH_AFR_93 / STOICH_AFR_E85:.2f}x more fuel on E85")


if __name__ == "__main__":
    main()
