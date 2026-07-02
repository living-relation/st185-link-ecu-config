# RealDash CAN Live Sender — build & run

Separate desktop app, companion to `apps/canbus-bench-test.html` (which stays browser-only
and unmodified). This one actually transmits the RealDash frames (0x3EF–0x3F1) to a CAN-USB
adapter via `python-can`, so the RealDash dashboard reacts live on the bench.

## Run from source (fastest way to iterate)

```powershell
cd apps\canbus-live-sender
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

A native window opens with the same UI as the bench-test tool, plus a Connect panel at the top.

On macOS/Linux the venv activate step is `source .venv/bin/activate` instead.

## One-time adapter setup (Windows)

- **candleLight/gs_usb firmware** (the default on this hardware, same as CANgaroo uses): the
  device needs the **WinUSB** driver bound via **[Zadig](https://zadig.akeo.ie/)** — same
  one-time step CANgaroo already required. Run Zadig, select the CANable device, install WinUSB,
  then relaunch this app.
- **slcan firmware**: shows up as a normal COM port, no driver step needed.

On Linux, a gs_usb/candleLight adapter also works via SocketCAN
(`sudo ip link set can0 up type can bitrate 1000000`); python-can's `gs_usb` backend used here
talks to it directly over libusb, so no `ip link` step is required.

## Package as a standalone `.exe`

```powershell
pip install pyinstaller
pyinstaller --onefile --windowed --add-data "ui;ui" --name RealDashLiveSender app.py
```

The finished executable is at `dist\RealDashLiveSender.exe` — copy that file anywhere and
double-click to run; no Python install needed on the target machine.

Notes:
- `--add-data "ui;ui"` bundles the `ui/index.html` file into the executable (Windows uses `;` as
  the separator; it's `:` on macOS/Linux — `--add-data "ui:ui"`).
- pywebview uses the Edge **WebView2** runtime on Windows, which ships pre-installed on
  Windows 10 (22H2+) and Windows 11. If it's somehow missing, install the
  [WebView2 Evergreen Runtime](https://developer.microsoft.com/microsoft-edge/webview2/) once.
- The `.exe` is unsigned, so Windows SmartScreen will likely warn on first run — click
  "More info" → "Run anyway".

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| "No adapters found" | Adapter not plugged in, or (gs_usb) Zadig driver not bound yet |
| Connect succeeds but Send fails immediately | Adapter unplugged mid-session, or another app (CANgaroo, SavvyCAN) already has it open — close the other app first |
| RealDash gauges don't react | Confirm CAN wiring / 1 Mbit/s (see the bench-test bus-settings panel), that RealDash's `link_g4x_realdash.xml` inputs are imported, and that "Send continuously" is checked for the frames you care about |
