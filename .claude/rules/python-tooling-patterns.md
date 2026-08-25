---
paths:
  - apps/trackcluster-can-sender/**
  - rd-build/tools/**
  - bench/**
---

# Python Tooling Patterns

- Follow existing adapter handling style in `apps/trackcluster-can-sender/app.py` (`gs_usb`, `slcan`, `seeedstudio`, vendor interfaces).
- Keep CAN payload validation strict (`11-bit ID`, `8-byte payload`) before transmit.
- Prefer small utility scripts with explicit CLI usage strings in `rd-build/tools/`.
- Keep dependency docs aligned with `requirements.txt` files under `bench/`, `apps/trackcluster-can-sender/`, and `rd-build/tools/`.
- For GUI automation scripts, preserve cross-platform caveats from `rd-build/tools/SETUP.md`.
