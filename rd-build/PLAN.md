# Build a real `.rd` file with a LOCAL Cursor agent driving the RealDash editor

## Context

The goal is an actual, working RealDash `.rd` dashboard file for the ST185 TrackCluster (to run on
a Raspberry Pi) — not just a spec. RealDash's `.rd` format is a proprietary binary produced only by
RealDash's own in-app visual editor (confirmed by inspecting a real sample byte-for-byte: custom
length-prefixed UTF-16LE + packed-float stream, no documented structure, no public generator). The
only way to produce a valid, loadable `.rd` is to actually drive RealDash's editor.

**This package is written for a Cursor agent running LOCALLY on the user's own PC**, where RealDash
is installed and the desktop has a real GPU. The agent "learns" the editor's UI with a
screenshot -> decide -> click/type -> verify loop, builds the exact ST185 single-page dashboard
tile by tile (section 4), saves it, and hands back the resulting `.rd` (+ animation sidecar) to copy
onto the Pi.

> Why local (and not a cloud VM): this build was first attempted on a headless cloud VM with no GPU.
> RealDash installs, launches, and logs in there, but it renders through OpenGL ES / EGL, and the
> software-only Mesa (llvmpipe) EGL buffer-swap **deadlocks** on a headless display — RealDash hangs
> forever on the post-login loading spinner and never reaches the editor. On a normal PC with a real
> GPU (or a VM with working hardware-accelerated OpenGL) this problem does not occur. See
> `FINDINGS.md` for the full diagnosis. **Bottom line: run this on a real, GPU-backed desktop
> session, not a headless/software-GL environment.**

The dashboard spec (section 4) and the CAN channel file (`link_g4x_realdash.xml`, section 3) are the
authoritative source of truth and are unchanged from the original package.

---

## 0. Prerequisites (resolve before automation starts)

1. **A PC with a normal, GPU-backed desktop session** (Windows, macOS, or Linux). It must NOT be a
   headless/software-only-OpenGL environment (see the Context note and `FINDINGS.md`). Confirm
   hardware GL is in use — e.g. on Linux `glxinfo | grep "OpenGL renderer"` should NOT say
   `llvmpipe`; on Windows/macOS the normal logged-in desktop already uses the GPU.
2. **RealDash installed and able to reach the editor.**
   - Windows: install from the Microsoft Store ("RealDash").
   - macOS: install the RealDash app (requires a My RealDash subscription for the desktop build).
   - Linux: install the `.deb` from the My RealDash Downloads area (`my.realdash.net` ->
     Downloads -> the `amd64` package). The Linux/macOS desktop builds are gated behind a My
     RealDash subscription + login.
   - Credentials for the My RealDash account are in `CREDENTIALS.md`. The account has an active
     subscription and 0/3 devices used, so logging in on this PC is fine.
3. **The Cursor agent runs on this same PC** with:
   - Terminal access (Cursor agents have this by default).
   - Ability to read image files (Cursor agents can read screenshots).
   - A desktop-automation tool so the agent can screenshot the screen and inject mouse/keyboard.
     This package ships one: `tools/automation_helper.py` (Python + PyAutoGUI, cross-platform).
     See `tools/SETUP.md` for install + OS permissions. No MCP server or remote-desktop connector
     is required because the agent and RealDash are on the same machine.
4. **No network egress restrictions** on the PC (RealDash does an online license/login check).

### Tools / MCP / connectors summary
- **Required:** RealDash (installed); Python 3 + PyAutoGUI (`tools/requirements.txt`); the shipped
  `tools/automation_helper.py`.
- **MCP servers:** none required. (Optional: if you prefer an MCP-based computer-use tool over the
  terminal + helper approach, `tools/mcp.example.json` shows how you *could* wire a desktop-control
  MCP into Cursor. It is not needed for this build.)
- **Connectors / remote desktop:** none required for the local setup. (Only needed if you instead
  run the Cursor agent on a *different* machine than RealDash — see `tools/SETUP.md` "Remote option".)

---

## 1. Set up the PC for the build

1. Install RealDash (section 0.2) and launch it once. Log in with the `CREDENTIALS.md` account when
   prompted. Confirm it reaches the **Garage** screen (the home screen for adding a vehicle /
   dashboard). If it hangs on a loading spinner here, you are almost certainly on a
   software-GL / headless display — fix that first (section 0.1 / `FINDINGS.md`).
2. Install the automation tool: `pip install -r tools/requirements.txt` (see `tools/SETUP.md` for
   per-OS notes, including macOS Accessibility + Screen Recording permissions, and Linux
   `scrot`/`python3-tk` requirements).
3. Sanity-check the tool:
   - `python tools/automation_helper.py size` prints the screen resolution.
   - `python tools/automation_helper.py screenshot /tmp/rd_check.png` saves a screenshot the agent
     can read back.
4. Keep RealDash maximized/fullscreen on the primary display for the whole build.

---

## 2. The automation loop (how the local agent drives the editor)

RealDash's UI is not accessibility-tree friendly, so the build is vision-based: the agent takes a
screenshot, reads it, decides the next action, injects it, then screenshots again to verify. Use the
shipped helper for every step:

- Screenshot: `python tools/automation_helper.py screenshot <path>` then read `<path>`.
- Move/click: `python tools/automation_helper.py click <x> <y>` (also `doubleclick`, `move`,
  `rightclick`, `dragto`).
- Type text: `python tools/automation_helper.py type "<text>"`.
- Keys: `python tools/automation_helper.py key <name>` (e.g. `enter`, `tab`, `esc`) or
  `hotkey <a> <b> ...` for combos.
- Read a pixel color (handy to verify a color band / LED state):
  `python tools/automation_helper.py pixel <x> <y>`.

Guidelines:
- Calibrate first: screenshot the Garage screen and click 2-3 known elements (e.g. an "Add" button,
  the Settings gear) to confirm coordinate accuracy before the real build.
- Save a screenshot checkpoint after every meaningful step (audit trail + easier recovery).
- `File -> Save As` every 3-4 tiles, not just at the end — editors can crash; frequent saves protect
  the work.
- Coordinates depend on this PC's resolution; recompute from fresh screenshots rather than reusing
  numbers from another machine.

---

## 3. Import the CAN channel description (the data contract)

> **Correction, 2026-09-04 — Turbo Speed scaling was wrong in this package.** This file's Turbo
> Speed line previously read `conversion="V*100" rangeMax="200000"`, which is inconsistent with
> its own stated range (a single byte, max raw 255, can only reach 25,500 at x100 — never
> 200,000) and disagreed with every other source in the repo. Checked against the canonical
> config contract, `link_g4x_can_setup.json` ("Turbo Speed x1000... raw x 1000 = RPM... e.g. 150 =
> 150,000"), plus `CAN-BUS-ID-ALLOCATION-TABLE.md`, `REALDASH-LAYOUT.md`, and the root
> `link_g4x_realdash.xml` — all four agree on **x1000, range 0–255,000 RPM**. Corrected below and
> in `rd-build/link_g4x_realdash.xml`. This also means the row-7 TURBO tile's `value/1000 → "k rpm"`
> display logic (section 4.3) was already written for the *correct* scaling — it just needs to
> receive a correctly-scaled input, which this fix provides. If a `.rd` file was already built
> against the old `V*100` line, re-import this corrected channel file before trusting turbo-speed
> readings on it.

Copy the file below onto the VM as `link_g4x_realdash.xml`, then in RealDash: **Garage → add/open
the car → Connections → add a CAN/Serial connection → Select Vehicle → Custom Channel Description
File → browse to `link_g4x_realdash.xml` → Done.** This registers every `ST185:`-prefixed input
under **Settings → Inputs → ECU Specific**, which the dashboard gauges bind to by name.

Bus facts: **1 Mbit/s, BigEndian, passive/listen-only** (RealDash never transmits). Only 3 frames
matter to RealDash — `0x3E8–0x3EE` and `0x640–0x643` are read by the cluster/ECU only, not RealDash.

```xml
<?xml version="1.0" encoding="utf-8"?>
<RealDashCAN version="2">
  <frames>

    <!-- 0x3EF (1007) Drive Assist & Status — 50ms, BigEndian -->
    <frame id="1007" endianness="big" timeout="2000">
      <value name="ST185: Target Lambda"    offset="0" length="2" conversion="V*0.001" rangeMin="0.6" rangeMax="1.3"/>
      <value name="ST185: Throttle"         offset="2" length="1" conversion="V"        rangeMin="0"   rangeMax="100"/>
      <value name="ST185: TC Setting"       offset="3" length="1" conversion="V"        rangeMin="0"   rangeMax="4"/>
      <value name="ST185: TC Intervention"  offset="4" length="1" conversion="V"        rangeMin="0"   rangeMax="100"/>
      <value name="ST185: Boost Map"        offset="5" length="1" conversion="V"        rangeMin="0"   rangeMax="3"/>
      <value name="ST185: Cruise State"     offset="6" length="1" enum="0:OFF,1:STBY,2:SET,3:RES,4:OVR,#:---"/>
      <value name="ST185: AC Status"        offset="7" length="1" enum="0:OFF,1:REQ,2:ON,3:FLT,#:---"/>
    </frame>

    <!-- 0x3F0 (1008) Extended Sensors — 100ms, BigEndian -->
    <frame id="1008" endianness="big" timeout="2000">
      <value name="ST185: Fuel Temp"        offset="0" length="1" conversion="V-50"  units="C"/>
      <value name="ST185: Engine Load"      offset="1" length="1" conversion="V"     rangeMin="0" rangeMax="100"/>
      <value name="ST185: Coolant Pressure" offset="2" length="2" conversion="V"     rangeMin="0" rangeMax="1000"/>
      <value name="ST185: Ethanol"          offset="4" length="1" conversion="V"     rangeMin="0" rangeMax="100"/>
      <value name="ST185: Charge-Pipe IAT"  offset="5" length="1" conversion="V-50"  units="C"/>
      <value name="ST185: Turbo Speed"      offset="6" length="1" conversion="V*1000" rangeMin="0" rangeMax="255000"/>
      <value name="ST185: Trigger Errors"   offset="7" length="1" conversion="V"     rangeMin="0" rangeMax="255"/>
    </frame>

    <!-- 0x3F1 (1009) IMU & Extended Warnings — 50ms, BigEndian -->
    <frame id="1009" endianness="big" timeout="2000">
      <value name="ST185: Accel X"          offset="0" length="2" signed="true" conversion="V*0.1" rangeMin="-2" rangeMax="2"/>
      <value name="ST185: Accel Y"          offset="2" length="2" signed="true" conversion="V*0.1" rangeMin="-2" rangeMax="2"/>
      <value name="ST185: Accel Z"          offset="4" length="2" signed="true" conversion="V*0.1" rangeMin="-2" rangeMax="2"/>
      <value name="ST185: Warn Bits"        offset="6" length="1" conversion="V"/>
      <value name="ST185: Flat Shift"       offset="6" length="1" startbit="0" bitcount="1" units="bit"/>
      <value name="ST185: Radiator Fan"     offset="6" length="1" startbit="1" bitcount="1" units="bit"/>
      <value name="ST185: Low Fuel"         offset="6" length="1" startbit="2" bitcount="1" units="bit"/>
      <value name="ST185: High Coolant Press" offset="6" length="1" startbit="3" bitcount="1" units="bit"/>
      <value name="ST185: Low Oil Press 2"  offset="6" length="1" startbit="4" bitcount="1" units="bit"/>
      <value name="ST185: Switchboard Fault" offset="6" length="1" startbit="5" bitcount="1" units="bit"/>
    </frame>

  </frames>
</RealDashCAN>
```

Bit map reference (0x3F1 byte 6, canonical per `CAN-BUS-ID-ALLOCATION-TABLE.md` §6): bit0 Flat
Shift Active · bit1 Radiator Fan On · bit2 Low Fuel Warning · bit3 High Coolant Pressure · bit4 Low
Oil Pressure (secondary threshold) · bit5 Switchboard Comm Fault (ECU-set) · bits6-7 spare.

---

## 4. Build target — single-page dashboard, exact spec

This is the corrected design (matches `realdash-simulation.html` with its stale **Cabin Temp**
tile removed, per prior agreement). Canvas **800×480, one page, no swipe/second page.**

### 4.1 Palette
| Token | Hex |
|---|---|
| bg | `#1a2430` |
| bg2 (radial lift) | `#243446` |
| panel (tile fill bottom) | `#243243` |
| panel-hi (tile fill top) | `#2c3c50` |
| edge (tile border) | `#3c5066` |
| blue (primary accent) | `#34a8ff` |
| blue-deep | `#1c6fd6` |
| cyan (secondary accent) | `#46e6ff` |
| chrome gradient | `#f4f7fb → #c3ccd8 → #889aac` |
| text | `#f3f8ff` |
| dim (labels/units) | `#9fb1c6` |
| good | `#46e0a6` |
| caution (amber) | `#ffc233` |
| alarm (red) | `#ff4d57` |

Fonts: `"Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`; tabular/mono numerals for values.

### 4.2 Top strip — `x0,y0,w800,h54`, gradient fill `#26384c → #1b2836`, 1px bottom border `#3c5066`
| Element | Approx x,y,w,h | Bound input | Behavior |
|---|---|---|---|
| Title "ST185 / DASH" | 14,14,172,26 | — | static, chrome-gradient text |
| FLAT pill | ~186,12,60,30 | `ST185: Flat Shift` | dim by default; lit blue (`#34a8ff` bg, white text) when =1 |
| FAN pill | ~250,12,54,30 | `ST185: Radiator Fan` | same style, blue when =1 |
| LOFUEL pill | ~308,12,70,30 | `ST185: Low Fuel` | amber (`#ffc233`) strobe-style fill when =1 |
| SBFLT pill | ~382,12,64,30 | `ST185: Switchboard Fault` | amber when =1 |
| (spacer) | flexible | — | pushes remaining 2 pills to the right edge |
| ⚠ COOLANT P pill | ~640,12,90,30 | `ST185: High Coolant Press` | **strobing red** (`#ff4d57`, ~0.3s ping-pong fade) when =1 |
| ⚠ OIL P 2 pill | ~734,12,66,30 | `ST185: Low Oil Press 2` | **strobing red**, same recipe, when =1 |

### 4.3 4×4 grid — `x0,y54,w800,h426`, 11px outer padding, 9px gap → cell ≈188×94px
Column left-edges: **11, 208, 405, 601** (width 188 each). Row top-edges: **65, 168, 272, 375**
(height 94 each). Span-2 tiles (row 4) are 385px wide (`188*2+9`).

Each tile: rounded-rect box, vertical gradient fill `panel-hi → panel`, 1px `edge` border, thin
chrome top rail, uppercase label (dim, ~10.5px, letter-spaced), large bold value (~35px), unit
suffix (dim, ~15px), optional bottom mini-bar.

| # | Row,Col | x,y,w,h | Label | Bound input | Display | Caution | Alarm |
|---|---|---|---|---|---|---|---|
| 1 | R1C1 | 11,65,188,94 | BOOST MAP | `ST185: Boost Map` | index 0-3 + name text (0=MAP LOW,1=MID,2=HIGH,3=MAX) | — | — |
| 2 | R1C2 | 208,65,188,94 | TC | `ST185: TC Setting` (+ `ST185: TC Intervention` sub-bar, label "int %") | index 0-4 + %-bar | bar amber 10-40% | bar red >40% |
| 3 | R1C3 | 405,65,188,94 | THROTTLE | `ST185: Throttle` | 0-100% + bar | — | — |
| 4 | R1C4 | 601,65,188,94 | TARGET λ | `ST185: Target Lambda` | 2 decimals, mono | — | — |
| 5 | R2C1 | 11,168,188,94 | CHARGE IAT | `ST185: Charge-Pipe IAT` | °C + bar | amber 50-60°C | red >60°C |
| 6 | R2C2 | 208,168,188,94 | COOLANT P | `ST185: Coolant Pressure` | kPa + bar (scale /300 for bar) | amber ≥150 kPa | red when `High Coolant Press`=1 |
| 7 | R2C3 | 405,168,188,94 | TURBO | `ST185: Turbo Speed` | value/1000 → "k rpm" + bar (scale /200000) | amber 180k-190k | red >190k |
| 8 | R2C4 | 601,168,188,94 | ENGINE LOAD | `ST185: Engine Load` | 0-100% + bar | — | — |
| 9 | R3C1 | 11,272,188,94 | FUEL TEMP | `ST185: Fuel Temp` | °C + bar | amber 55-70°C | red >70°C |
| 10 | R3C2 | 208,272,188,94 | ETHANOL | `ST185: Ethanol` | "E"+value% + bar | — | — |
| 11 | R3C3-4 (span2) | 405,272,385,94 | TRIGGER ERR | `ST185: Trigger Errors` | count + status text ("healthy"/"watch"/"SYNC LOSS") | amber 1-4 | red ≥5 |
| 12 | R4C1-2 (span2, state tile) | 11,375,385,94 | CRUISE | `ST185: Cruise State` | enum text OFF/STBY/SET/RES/OVR | tile tint blue when active, amber if OVR | — |
| 13 | R4C3-4 (span2, state tile) | 405,375,385,94 | A/C | `ST185: AC Status` | enum text OFF/REQ/ON/FLT | tint blue when ON | red tint when FLT |

Note: `ST185: Accel X/Y/Z` are registered inputs but intentionally **not shown** on this page
(reserved for a possible future g-force view) — do not add tiles for them.

### 4.4 Strobe animation recipe (for the two alarm pills in §4.2, and the red-alarm states above)
Select the element → **Edit → Animations → Add → Fade**, opacity 100 → 0, duration **0.35s**,
**Loop = ping-pong (on)**. Gate with two triggers on the bound bit: value ≥1 → start/show; value <1
→ stop/hide (opacity 100). This yields a ~1.4 Hz strobe while active, steady/off otherwise.

---

## 5. Automated build procedure (what the computer-use agent actually does)

1. **New dashboard**: File → New, set canvas to landscape 800×480, background color `#1a2430`
   with the radial-gradient lift toward `#243446` if RealDash's background gauge supports a radial
   fill (else flat `#1a2430` is an acceptable fallback — note the deviation).
2. **Top strip** (§4.2): add a background box for the strip, then each pill as a small
   rounded-rect/Text or Indicator gauge, positioned per the table, bound to its input, colors per
   the on/off states listed.
3. **Grid tiles** (§4.3): for each of the 13 tiles — add the 3D box (gradient fill + border), drop
   the appropriate gauge type (Numeric / Numeric+Bar / Index+Text / Enum text) on top, bind to the
   listed `ST185:` input, set range and Warning/Critical levels exactly as tabled, apply label/unit
   text and the palette colors.
4. Apply the strobe animation (§4.4) to: the two alarm pills, the Turbo/IAT/Coolant/Fuel-Temp
   tiles' alarm state, and the Trigger-Err tile's alarm state.
5. **Save** (`File → Save As`) after every 3-4 tiles, not just at the end — RealDash editors can
   crash; frequent saves protect the work. Screenshot each save.
6. After all tiles are placed, do a full visual pass: screenshot the finished dashboard, compare
   tile-by-tile against §4.3's table (position, label, color) and flag any mismatch for a follow-up
   correction pass before calling the build "done."

---

## 6. Validation (bounded by what a cloud VM can actually test)

1. RealDash's **Demo/manual input override** (Settings → Inputs → tap a value → enter a test
   number) lets you punch in specific values per `ST185:` input and confirm each gauge's color
   bands, enum text, and strobe triggers react correctly — do this for every tile, including the
   boundary values (e.g. Coolant Pressure at 149/150/200 kPa, Trigger Errors at 0/1/5).
2. **What cannot be validated on this VM**: real CAN traffic end-to-end, since cloud VMs have no
   USB-CAN passthrough. That final check only happens once the `.rd` + `link_g4x_realdash.xml` are
   on the actual Pi with the real bus (or the bench tools already in this repo —
   `apps/canbus-bench-test.html` / `apps/canbus-live-sender` — feeding simulated frames into a
   USB-CAN adapter connected to the Pi). Call this out explicitly to the user as the required last
   mile step they must do themselves on real hardware.

---

## 7. Deliver the result

1. Export/locate the saved `.rd` file (and its `_anim.xml` sidecar, since animations are also
   written as a separate versionable XML alongside the `.rd`) on the VM.
2. Copy both files off the VM (shared folder / RDP file transfer / VM's own file-share mechanism)
   to this session's scratchpad.
3. **Create a fresh feature branch** off the repo's current default branch (do not reuse any
   branch with pre-existing unrelated commits).
4. Add the `.rd` + `_anim.xml` to the repo (e.g. `st185_dash.rd`, `st185_dash_anim.xml`), and add a
   short note to `README.md`'s file table and `CAN-CONFIG-STATUS.md` recording that a built `.rd`
   now exists alongside the buildable spec, plus which RealDash version built it.
4. Push the branch and open a PR; also `SendUserFile` the `.rd`/`_anim.xml` directly so the user
   can copy them straight onto their Pi (per the existing install steps: copy both files onto the
   Pi, put the `.rd` where RealDash looks for dashboards, keep `link_g4x_realdash.xml` alongside
   it, set it as default/fullscreen).

---

## Open risks to flag to the user up front

- Needs a paid RealDash license + an actual VM (cloud $ or local hardware) — infra the user must
  provision or approve spend for; not something this session can materialize on its own.
- No computer-use/remote-desktop tool is currently attached to this session — must be added before
  Phase 2 can start.
- RealDash's UI automation will be vision-based (no accessibility tree), so expect iteration/retry
  loops and occasional manual-correction passes, not a single unattended run.
- Final validation against real CAN traffic can only happen on the user's actual Pi/car, not the VM.

---

## Appendix A. Findings from the cloud-VM attempt (read before you start)

A prior agent attempted this exact build on a headless cloud VM. Key results, so you don't repeat
the dead ends:

- **RealDash native Linux build works to a point.** The `realdash-mrd_*_amd64.deb` (v2.6.7) was
  downloaded from `my.realdash.net` Downloads, installed with its deps, launched, rendered its UI,
  and the My RealDash login network round-trip **succeeded** (verified by packet capture).
- **The account is healthy.** Subscription is **active** ("Subscribed (Single user), renews
  April 19, 2027"). Devices: **0 / 3 used** — no device-limit problem.
- **The blocker was purely GPU/GL, not RealDash, network, login, subscription, or device limit.**
  On a headless VM (no GPU), Mesa uses the `llvmpipe` software rasterizer, and its software
  **EGL / OpenGL-ES buffer swap deadlocks**: RealDash hangs forever on the post-login loading
  spinner and never reaches the Garage/editor. The app login does not even register a device (still
  0/3 afterward), confirming it stalls during post-login init.
- **Reproduced independent of RealDash:** `glxgears` (desktop GL via GLX) ran ~1800 FPS, but
  `es2gears` (OpenGL ES via EGL — the same path RealDash uses) produced zero frames and hung in
  `eglSwapBuffers`. gdb showed RealDash's main thread blocked in `libEGL_mesa` -> `libgallium`.
- **Fixes tried that did NOT help** (all on the headless VM): PulseAudio null sink, reduced render
  size via nested Xephyr (800x600), extra llvmpipe threads, `vblank_mode=0`,
  `LIBGL_DRI3_DISABLE` / `DRI2_DISABLE` / `KOPPER_DISABLE` / `KOPPER_DRI2`,
  `MESA_LOADER_DRIVER_OVERRIDE=swrast/llvmpipe/zink`, zink+lavapipe (no Vulkan device), Xvfb.

**Implication for you:** run on a real GPU-backed desktop (a normal Windows/macOS/Linux session, or
a VM with genuine hardware-accelerated OpenGL). If RealDash reaches the Garage screen after login,
the GL environment is fine and the rest of this plan applies normally.

## Appendix B. Login / account notes

- On first launch RealDash shows a language dialog (pick English -> DONE), then a **My RealDash**
  login (email + password). Use the account in `CREDENTIALS.md`.
- The desktop Linux/macOS builds require login + an active subscription and do periodic online
  license checks — keep the PC online during the build.
- After a successful login on a GPU-backed machine, RealDash proceeds to the Garage; this PC then
  counts as 1 of the 3 allowed devices (fine).
