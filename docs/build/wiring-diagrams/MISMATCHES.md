# Wiring diagram mismatches

Written by `build_wiring_diagrams.py` on every run. A line here means the SoT chain / spec and the looms disagree about a
wire the diagrams draw. The diagram follows the SoT (`sot/channels.csv`, `cad/fusebox/src/spec.py`, `docs/harness/interfaces.json`);
nothing is guessed. Fix the disagreement at its source, then re-run.

## Mismatches

None. Checked: every spec fuse (MINI_COLS, AMI_ROWS) has a loom cavity with the same rating and the reverse;
every `sot/channels.csv` PWR relay cavity has a loom wire; every box wire has a gauge; every box wire is drawn;
every OEM splice in `interfaces.json` that sits on a junction box has a terminal and a wire in the looms.

## Left out on purpose

The OEM sheets cover junction boxes, relay-block positions and plugs where power is injected or a circuit is spliced (R12, R61).
These `flyingLeads` are splices into DEVICE plugs (switches, lamps, motors, A/C amplifier, combination meter), not junction boxes,
and have no sheet: FL_ACAMP_ACT, FL_BRAKE_SW_C1, FL_CLUTCH_SW_C1, FL_CRUISE_STALK_C1, FL_CRUISE_STALK_C3, FL_CRUISE_STALK_C17, FL_AC_PRESS_C1, FL_B4_C2, FL_H1_C3, FL_H2_C3, FL_CL_C11_C2, FL_CL_C11_C11, FL_CL_C11_C12, FL_CL_C12_C1, FL_CL_C12_C8, FL_CL_C12_C9, FL_ACAMP_MG, FL_A4_3, FL_A4_4, FL_ACAMP_PSW, FL_A5_4, FL_OEM_S9_C1, FL_R11_C1, FL_R11_C2, FL_R11_C3, FL_R11_C4, FL_R11_C5, FL_R11_C6, FL_R12_C1, FL_R12_C2, FL_R12_C3, FL_R12_C4, FL_R12_C5, FL_R12_C6, FL_L1_C1, FL_L1_C2, FL_H6_C1, FL_H6_C2, FL_W1_COWL_C2, FL_W1_COWL_C1, FL_F7_C1, FL_F7_C2, FL_F7_C3, FL_F8_C1, FL_F8_C2, FL_F8_C3, FL_H1_C1, FL_H1_C2, FL_H2_C1, FL_H2_C2, FL_R2_C1, FL_R2_C2, FL_R2_C3, FL_R2_C4, FL_R2_C5, FL_R3_C1, FL_R3_C2, FL_R3_C3, FL_R3_C4, FL_R3_C5, FL_W1_C1, FL_W1_C2, FL_F9_C1, FL_F9_C2, FL_F9_C3, FL_F9_C4.
