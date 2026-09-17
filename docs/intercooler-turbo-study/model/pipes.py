#!/usr/bin/env python3
"""2.50 in charge-pipe check at the MatchBot peak-flow point.

The 3.00 in cold-side recommendation is withdrawn. Both runs were validated at
2.50 in OD. 3.00 in adds volume and fill delay without helping the turbo or
the engine at 55 lb/min.

Writes model/pipes.json.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "pipes.json"

# Design-point numbers from research/data/throttle-body-plumbing/pipe-sizing-output.txt
# (Colebrook, 0.0015 mm roughness, bend K=0.20). Scaled to new peak flow.
BASE_LBMIN = 45.7
BASE = {
    2.50: {"id_mm": 60.20, "hot_fts": 189.1, "hot_dp": 0.442, "cold_fts": 144.0, "cold_dp": 0.446, "L_per_m": 2.85},
    2.75: {"id_mm": 66.55, "hot_fts": 154.7, "hot_dp": 0.288, "cold_fts": 117.9, "cold_dp": 0.291, "L_per_m": 3.48},
    3.00: {"id_mm": 72.90, "hot_fts": 128.9, "hot_dp": 0.196, "cold_fts": 98.2, "cold_dp": 0.198, "L_per_m": 4.17},
}
HOT_LEN_M = 1.1
COLD_LEN_M = 1.5
PEAK_LBMIN = 55.13          # MatchBot point 6 / Phase-1 8000/27
GARRETT_LO, GARRETT_HI = 200.0, 300.0
FT_TO_M = 0.3048


def scale(od, peak=PEAK_LBMIN):
    r = peak / BASE_LBMIN
    b = BASE[od]
    return {
        "od_in": od,
        "id_mm": b["id_mm"],
        "hot_fts": round(b["hot_fts"] * r, 1),
        "cold_fts": round(b["cold_fts"] * r, 1),
        "hot_dp_psi": round(b["hot_dp"] * r * r, 3),
        "cold_dp_psi": round(b["cold_dp"] * r * r, 3),
        "vol_L_per_m": b["L_per_m"],
        "hot_vol_L": round(b["L_per_m"] * HOT_LEN_M, 2),
        "cold_vol_L": round(b["L_per_m"] * COLD_LEN_M, 2),
        "hot_transit_ms": round(1000.0 * HOT_LEN_M / (b["hot_fts"] * r * FT_TO_M), 1),
        "cold_transit_ms": round(1000.0 * COLD_LEN_M / (b["cold_fts"] * r * FT_TO_M), 1),
        "hot_in_garrett": GARRETT_LO <= b["hot_fts"] * r <= GARRETT_HI,
        "cold_in_garrett": GARRETT_LO <= b["cold_fts"] * r <= GARRETT_HI,
    }


def main():
    rows = {od: scale(od) for od in (2.50, 2.75, 3.00)}
    both_25 = rows[2.50]
    mixed = {
        "hot_2_5_cold_2_5_dp": round(both_25["hot_dp_psi"] + both_25["cold_dp_psi"], 3),
        "hot_2_5_cold_3_0_dp": round(both_25["hot_dp_psi"] + rows[3.00]["cold_dp_psi"], 3),
        "extra_cold_volume_L": round(rows[3.00]["cold_vol_L"] - both_25["cold_vol_L"], 2),
        "extra_cold_transit_ms": round(rows[3.00]["cold_transit_ms"] - both_25["cold_transit_ms"], 1),
    }
    rec = {
        "peak_lbmin": PEAK_LBMIN,
        "base_lbmin": BASE_LBMIN,
        "garrett_fts": [GARRETT_LO, GARRETT_HI],
        "rows": {f"{od:.2f}": v for od, v in rows.items()},
        "mixed": mixed,
        "pick": {
            "hot_od_in": 2.50,
            "cold_od_in": 2.50,
            "why": (
                "At 55.13 lb/min the 2.50 in hot side is 228 ft/s — inside "
                "Garrett's 200–300 ft/s band. The 2.50 in cold side is 174 ft/s, "
                "under the band because the charge is denser after the IC, but "
                "dP is 0.65 psi and the pipe is not a restriction versus the "
                "7163's 60 lb/min wall or the engine's 55 lb/min demand. "
                "3.00 in cold saves ~0.36 psi and adds 2.0 L plus ~14 ms of "
                "fill delay. That volume is why 3 in felt slower. Both sides "
                "stay 2.50 in × 0.065 wall."
            ),
        },
    }
    # Sanity: 2.5 in is not choking the 55 lb/min point
    assert both_25["hot_fts"] < 300
    assert both_25["hot_dp_psi"] + both_25["cold_dp_psi"] < 2.0
    OUT.write_text(json.dumps(rec, indent=2))
    print(f"wrote {OUT}")
    print("2.50/2.50 @", PEAK_LBMIN, "lb/min: hot", both_25["hot_fts"], "ft/s",
          "cold", both_25["cold_fts"], "ft/s  dP", mixed["hot_2_5_cold_2_5_dp"],
          "extra 3in vol", mixed["extra_cold_volume_L"], "L")


if __name__ == "__main__":
    main()
