# ST185 Combined Harness Overlay

Interactive SVG overlay of Signal, Power, CAN, and EngineRoom-C harnesses.

## Open

From repo root:

```bash
python -m http.server 8765
```

Then open: http://localhost:8765/apps/harness-overlay/

## Rebuild data

```bash
python apps/harness-overlay/build_data.py
```

Writes `data.js` (`window.HARNESS_DATA`) from `docs/harness/ST185-*.harness`.
