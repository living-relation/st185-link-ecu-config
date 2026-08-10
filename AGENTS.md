# AGENTS.md

## Cursor Cloud specific instructions

This repo is mostly CAN-bus **config + documentation** for the Celica ST185 build. The only
runnable code is:

- `bench/can_bench.py` — a `python-can` CLI bench harness (encode/transmit/monitor CAN frames).
  Frame layouts live in `bench/frames.py`. This is the primary thing to run/test in the cloud VM.
- Browser tools (standalone, no build): `apps/canbus-bench-test.html`, `realdash-demo.html`,
  `realdash-simulation.html`. Open directly, or serve the repo (`python3 -m http.server`) and
  browse to the file. `apps/canbus-bench-test.html` only covers the 3 RealDash frames
  (`0x3EF`/`0x3F0`/`0x3F1`); the CLI harness covers the full frame set.
- `apps/canbus-live-sender/` — a `pywebview` + `python-can` **desktop GUI** that transmits to a
  physical CAN-USB adapter. It needs native WebKit/GTK libs, `libusb`, and real hardware, so it is
  **not runnable headless** in the cloud VM. Treat it as out of scope for cloud testing; see its
  `BUILD.md` for the hardware/desktop setup.

There is **no lint config and no automated test suite**. For a quick correctness check, use
`python -m py_compile` on the bench scripts and/or an encode→decode round-trip via `frames.py`.

### Python env
The update script creates a `.venv` at the repo root and installs `bench/requirements.txt` (plus
`msgpack`, needed for the headless test path below). Run the tools with `.venv/bin/python`.

### Running the bench harness end-to-end (no CAN hardware)
This cloud VM has **no SocketCAN kernel module and no `ip` command**, so
`--interface socketcan --channel vcan0` (the README/BENCH-TEST.md default) will **not** work here.
Use `python-can`'s cross-process `udp_multicast` backend instead — it bridges two processes over
loopback multicast. Run a monitor and a simulator on the same multicast group:

```bash
# terminal 1 (receiver)
.venv/bin/python bench/can_bench.py --interface udp_multicast --channel 239.1.2.3 monitor
# terminal 2 (transmitter)
.venv/bin/python bench/can_bench.py --interface udp_multicast --channel 239.1.2.3 simulate-ecu --duration 5
```

`monitor` will print every decoded frame. `simulate-switchboard` and `inject-ls-command` work the
same way. On real hardware/Linux you would instead use `--interface socketcan`/`slcan`/`pcan`.

### Gotcha
`-v`/`--verbose` is a **global** flag on `can_bench.py` and must come **before** the subcommand
(e.g. `can_bench.py -v simulate-ecu`), not after it.
