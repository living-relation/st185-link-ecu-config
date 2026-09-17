# CAN Frame Contracts

**Canonical text: `docs/RECONCILIATION-RULES.md` Rule 2. Read it before finalizing any CAN
change.** This file is a pointer plus the facts most often got wrong — deliberately not a
second copy, so the two cannot drift.

## The rule

A CAN change on **any** device is not done until it has been reconciled against **all** the
others — Link ECU, center cluster, RealDash, ECUMaster CSB3. Every time, not just the pair
you were working on. This crosses repository boundaries: a change here that affects the
cluster is incomplete until the cluster side is checked.

For every frame touched, confirm across all participants: frame ID, byte offsets, field
widths, endianness, scaling, offset, units, and which device transmits vs receives.

## Bus facts

- **Link CAN-Lambda is on CAN bus 1**, with everything else. Not a separate bus.
- **CAN bus 2 is unused** — its ECU pins are free for any purpose. Do not reserve them.
- Single bus, 1 Mbit/s.

## Authority order

1. **Center cluster firmware as flashed** — highest, and **frozen**.
2. PCLink CAN configuration on the ECU.
3. Everything else.

Frozen means the *other* device changes on conflict. Reflashing the cluster is a last resort
needing explicit approval from Daniel — never to clear a mismatch.

## Contract details

- Frame IDs `0x3E8`-`0x3F1` and `0x640`-`0x643` follow `link_g4x_can_setup.json`.
- Keep CAN ID usage and field sizing aligned between `bench/frames.py` and that file.
- BigEndian for multibyte fields unless a canonical doc says otherwise.
- Warning bits stay in sync with `WARN_*` in `bench/frames.py`.
- RealDash receives ECU-owned `0x3EF`-`0x3F1`; it does not read switchboard `0x640`-`0x642`.

A mismatch found and not fixed in the same pass gets written down as an open item. Never
leave it silent.
