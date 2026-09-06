"""
5S-GTE 2.2L Turbo Comparison Model
Shared physics/estimation model used by all chart scripts.

ENGINE: Toyota 5S-GTE, 2164cc (132.06 CID), HKS 264 cams,
        twin-scroll long-tube manifold, E85, 7500 RPM ceiling.
"""

import numpy as np

# ----------------------------------------------------------------------
# ENGINE CONSTANTS
# ----------------------------------------------------------------------
DISPLACEMENT_CC = 2164
CID = 132.06
AIR_DENSITY = 0.0765          # lb/ft^3 standard
K_FLOW = 0.0029233            # lb/min = K * RPM * VE * PR
RPM_MIN, RPM_MAX = 2000, 7500

WHP_PER_LBMIN_E85 = 9.35      # crank 11 hp/lb-min * 0.85 drivetrain
WHP_PER_LBMIN_PUMP = 8.50     # crank 10 hp/lb-min * 0.85 drivetrain

BOOST_LEVELS = [20, 22, 25, 28, 30]

# ----------------------------------------------------------------------
# VOLUMETRIC EFFICIENCY CURVE (built 2.2L, HKS 264 cams)
# ----------------------------------------------------------------------
_VE_RPM = np.array([2000, 2500, 3000, 3500, 4000, 4500,
                    5000, 5500, 6000, 6500, 7000, 7500])
_VE_VAL = np.array([0.85, 0.88, 0.92, 0.96, 1.00, 1.03,
                    1.05, 1.04, 1.01, 0.97, 0.92, 0.87])


def ve(rpm):
    """Volumetric efficiency at a given RPM (interpolated)."""
    return np.interp(rpm, _VE_RPM, _VE_VAL)


def pressure_ratio(boost_psi):
    """Absolute pressure ratio from gauge boost."""
    return (np.asarray(boost_psi, dtype=float) + 14.7) / 14.7


def airflow(rpm, boost_psi):
    """Engine airflow demand in lb/min."""
    return K_FLOW * np.asarray(rpm, dtype=float) * ve(rpm) * pressure_ratio(boost_psi)


def boost_from_flow(rpm, flow_lbmin):
    """Inverse: what boost does a given flow support at this RPM."""
    pr = flow_lbmin / (K_FLOW * np.asarray(rpm, dtype=float) * ve(rpm))
    return pr * 14.7 - 14.7


# ----------------------------------------------------------------------
# TURBO DEFINITIONS
#   full_boost_25: modeled RPM at which full boost is reached @25 psi
#   flow_max     : compressor max flow, lb/min (BorgWarner spec)
# ----------------------------------------------------------------------
TURBOS = {
    "EFR 7064-C (0.92 T4 TS)": dict(flow_max=56, full_boost_25=3350,
                                    color="#1b9e77", frame="B2", ar=0.92),
    "EFR 7163-G (0.80 T4 TS)": dict(flow_max=60, full_boost_25=3600,
                                    color="#d95f02", frame="B1", ar=0.80),
    "EFR 7670-C (0.92 T4 TS)": dict(flow_max=64, full_boost_25=3900,
                                    color="#7570b3", frame="B2", ar=0.92),
    "EFR 8374-C (0.92 T4 TS)": dict(flow_max=79, full_boost_25=4250,
                                    color="#e7298a", frame="B2", ar=0.92),
}

# Full A/R variant matrix for the response comparison chart.
# Deltas derived from report: 0.83 single ~-200 rpm, 1.05 twin ~+350 rpm
AR_VARIANTS = {
    "EFR 7064": {"0.83 T3 single": 3150, "0.92 T4 twin": 3350, "1.05 T4 twin": 3700},
    "EFR 7163": {"0.80 T4 twin": 3600, "0.85 T25 single": 3800},
    "EFR 7670": {"0.83 T3 single": 3700, "0.92 T4 twin": 3900, "1.05 T4 twin": 4250},
    "EFR 8374": {"0.83 T3 single": 4050, "0.92 T4 twin": 4250, "1.05 T4 twin": 4600},
}

MODEL_COLORS = {
    "EFR 7064": "#1b9e77",
    "EFR 7163": "#d95f02",
    "EFR 7670": "#7570b3",
    "EFR 8374": "#e7298a",
}


def full_boost_rpm(base_25, target_boost):
    """Full-boost RPM shifts later as target boost rises (~30 rpm per psi)."""
    return base_25 + (target_boost - 25) * 30.0


def _smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def spool_curve(rpm, base_25, target_boost, ramp_width=1200):
    """
    Modeled boost vs RPM during spool-up.
    Boost ramps smoothly from onset to full-boost RPM.
    """
    fb = full_boost_rpm(base_25, target_boost)
    onset = fb - ramp_width
    t = (np.asarray(rpm, dtype=float) - onset) / (fb - onset)
    return target_boost * _smoothstep(t)


def achieved_boost(rpm, turbo_key, target_boost):
    """
    Actual boost delivered: spool-limited at low RPM,
    compressor-choke-limited at high RPM.
    """
    t = TURBOS[turbo_key]
    rpm = np.asarray(rpm, dtype=float)

    boost = spool_curve(rpm, t["full_boost_25"], target_boost)

    # Choke ceiling: boost the compressor can still support at max flow
    ceiling = boost_from_flow(rpm, t["flow_max"])
    return np.minimum(boost, ceiling)


def whp_curve(rpm, turbo_key, target_boost, fuel="E85"):
    """Wheel horsepower vs RPM for a turbo at a target boost."""
    b = achieved_boost(rpm, turbo_key, target_boost)
    flow = airflow(rpm, b)
    k = WHP_PER_LBMIN_E85 if fuel == "E85" else WHP_PER_LBMIN_PUMP
    return flow * k


# ----------------------------------------------------------------------
# COMPRESSOR MAP RECONSTRUCTIONS
#   NOTE: These are MODELED approximations built from published
#   BorgWarner map parameters (max flow, PR range, peak efficiency,
#   speed lines, island location). They are NOT traced from the
#   official BorgWarner map contours. Verify against the official
#   PDF maps before finalizing boost targets.
# ----------------------------------------------------------------------
COMP_MAPS = {
    "EFR 7064": dict(flow_max=56, pr_max=5.0, eff_peak=0.76,
                     center=(36.0, 2.50), spread=(15.0, 1.35),
                     speeds=[46, 86, 113, 134, 153], surge_a=6.0, surge_b=3.4),
    "EFR 7163": dict(flow_max=60, pr_max=4.2, eff_peak=0.74,
                     center=(41.5, 2.60), spread=(16.0, 1.30),
                     speeds=[44, 84, 111, 132, 150], surge_a=6.5, surge_b=3.8),
    "EFR 7670": dict(flow_max=64, pr_max=5.0, eff_peak=0.75,
                     center=(46.0, 2.55), spread=(17.5, 1.40),
                     speeds=[42, 79, 103, 123, 140], surge_a=7.0, surge_b=4.2),
    "EFR 8374": dict(flow_max=79, pr_max=5.0, eff_peak=0.77,
                     center=(61.5, 2.70), spread=(21.0, 1.45),
                     speeds=[64, 85, 101, 115, 128], surge_a=9.0, surge_b=5.5),
}

# Which housing each map panel is paired with for operating-point overlay
MAP_TO_TURBO = {
    "EFR 7064": "EFR 7064-C (0.92 T4 TS)",
    "EFR 7163": "EFR 7163-G (0.80 T4 TS)",
    "EFR 7670": "EFR 7670-C (0.92 T4 TS)",
    "EFR 8374": "EFR 8374-C (0.92 T4 TS)",
}


def surge_flow(pr, m):
    """Surge line: minimum stable flow at a given pressure ratio."""
    return m["surge_a"] + m["surge_b"] * (pr - 1.0)


def efficiency_field(F, PR, m):
    """Modeled compressor efficiency field over (flow, PR)."""
    fc, prc = m["center"]
    sf, sp = m["spread"]
    r2 = ((F - fc) / sf) ** 2 + ((PR - prc) / sp) ** 2
    eff = m["eff_peak"] * np.exp(-0.85 * r2)

    # Mask outside surge / choke
    eff = np.where(F < surge_flow(PR, m), np.nan, eff)
    eff = np.where(F > m["flow_max"], np.nan, eff)
    return eff
