# AGENTS.md

## CAN bus / wiring compatibility check (mandatory)

This repo defines only one side of the CAN bus (ECU, RealDash, switchboard). The
other node — the gauge cluster — lives in a separate repo:

**[center-cluster-esp32-p4](https://github.com/living-relation/center-cluster-esp32-p4)**

Cluster firmware is frozen; everything here must stay compatible with it **as-is**.

Any time you are working with CAN bus IDs/frames/byte layouts, or with wiring
(harness, transceivers, pinout), you MUST reference `center-cluster-esp32-p4`
before making changes:

- Its `CANBUS-ENCODE-DECODE-REFERENCE.html` (derived from `main/canbus.c`) is the
  **single source of truth** for CAN IDs, byte layouts, scales, and offsets — see
  `CAN-CONFIG-STATUS.md` in this repo.
- Its `main/protocols/link_g4x.json` and `sdkconfig`/`Kconfig.projbuild` define the
  cluster's TWAI GPIO pinout and transceiver wiring — see `WIRING.md` and
  `CAN-BUS-MASTER-DESIGN.md` in this repo for how it fits the 4-node topology.
- Do not introduce a CAN ID, frame layout, or wiring change here that the cluster
  firmware doesn't already decode/expect — the cluster is not being modified as
  part of work in this repo.

If a local checkout of `center-cluster-esp32-p4` exists (commonly
`C:\projects\center-cluster-esp32-p4`), prefer reading its source files directly;
otherwise consult the GitHub repo linked above.
