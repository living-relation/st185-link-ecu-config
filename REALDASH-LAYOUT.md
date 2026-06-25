# RealDash Layout Design — ST185 TrackCluster

Buildable dashboard design for the **Raspberry Pi RealDash** secondary display on the 1993 Celica
GT-Four (3S-GTE) track build. This is the spec you build against in the RealDash visual editor; it
pairs 1:1 with the inputs defined in [`link_g4x_realdash.xml`](link_g4x_realdash.xml).

**Two pages:**

1. **DASH** — one consolidated engineering page (all gauges on a single 800×480 screen, 3D tiles,
   bright LED warning lights, large automotive fonts, strobing alarms, cruise-mode readout).
2. **MEDIA** — a music-player page (SD/USB local files, streaming-app control, phone audio over
   Bluetooth — see the platform reality check in §2 before you wire it up).

> **Why a spec and not a `.rd` file?** RealDash dashboards (`.rd`) are a binary format produced only
> by the in-app visual editor — *"No XML needed of any kind when designing dashboards; XMLs are just
> for specifying custom connections"* (RealDash devs). So the layout is version-controlled here as a
> precise, buildable spec plus the importable channel XML it binds to. You build it once in edit
> mode, then RealDash saves your `.rd`.

---

## 1. Design principles

RealDash is the **secondary** display. The ESP32 center cluster already shows the primary vitals —
RPM, boost/MGP, ECT, IAT, oil temp/pressure, speed, gear, **actual** lambda, fuel level, and the
full-screen engine-protection warnings (0x3E8–0x3EE). **RealDash must not duplicate those.** It
surfaces what the cluster does not: driver-assist state, extended sensors, ECU health, and the
RealDash-side warning bits. See [`CAN-BUS-MASTER-DESIGN.md`](CAN-BUS-MASTER-DESIGN.md) §7.

Track-display rules:

- **Glanceable** — readable in < 0.5 s of peripheral vision; big numerals, high contrast.
- **Color = meaning** — neutral when OK; amber = caution; red = act now; blue = informational/on.
- **LEDs for state** — active states light a bright indicator; true warnings **strobe**.
- **No duplication** — anything already on the cluster is omitted on purpose.

---

## 2. Platform & media reality check (read before building Page 2)

RealDash's media features depend heavily on the operating system on your Pi. Be realistic about what
is and isn't possible:

| You want… | Does RealDash do it? | How |
|---|---|---|
| Play **SD-card / USB local files** | ✅ Yes, directly | Settings → User → Music Player → *RealDash as music player*, pick the music folder. Page 2 controls it. |
| Show now-playing + control **Spotify / Apple / Google** | ✅ Android only | Settings → User → Music Player → pick the service; grant Notification access. |
| Show now-playing + control **Amazon Prime Music** | ⚠️ Android only, via *Other* | Amazon Music isn't a named source; use the **"Other"** option, which reads the Android media session of any player. Controls = play/pause/next/prev; album art may not appear. |
| **Stream** Amazon Prime Music *from inside RealDash* | ❌ No | RealDash never streams a service itself. The **Amazon Music app** streams; RealDash only displays/controls it. |
| **Receive Bluetooth audio** from your phone | ❌ Not in RealDash | *"RealDash has no functionality to receive Bluetooth audio streams"* (RealDash dev). The **OS** must be the Bluetooth A2DP **sink**; RealDash can then show/control it via the media session (Android *Other*). |

**Bottom line / recommendation**

- For the **richest media page** (Amazon Music, Spotify, Bluetooth-from-phone, album art), run
  **RealDash on Android** on the Pi (Android image / Android board), not the Linux build.
- The **Linux** RealDash Pi build reliably does **local SD/USB files** and basic transport; streaming
  metadata and Bluetooth control are limited/OS-dependent.
- **Bluetooth from your phone** is always an **OS** job (pair + A2DP sink at the OS level). RealDash
  shows/controls it only if the OS exposes a media session.

Page 2 below is built to **degrade gracefully**: the local-file player and transport always work; the
streaming/Bluetooth now-playing tiles simply stay blank on platforms that can't provide the data.

---

## 3. Hardware & canvas

| Property | Value |
|---|---|
| Device | Raspberry Pi 4+/Pi 5 running RealDash (**Android recommended** if you want full media — see §2) |
| Screen | 7" **800 × 480** landscape touch panel (project docs also say "840×480"; design proportionally, RealDash auto-fits) |
| CAN | USB-CAN adapter (CANable / PCAN), **1 Mbit/s**, passive listener, `bus="0"` |
| Connection XML | `link_g4x_realdash.xml` (RealDash CAN v2, BigEndian) |
| Pages | 2 (DASH, MEDIA), swipe left/right to switch |

All coordinates are an **800 × 480** design grid (origin top-left, `x,y,w,h` px). Treat px as
proportional guidance — RealDash scales the finished dash to the panel. Outer margin 12 px, gutter
12 px.

---

## 4. Visual style — 3D tiles, LEDs, fonts

### 4.1 Palette

| Token | Hex | Use |
|---|---|---|
| `bg` | `#070A0F` | page background (near-black) |
| `tile-top` | `#1C2430` | tile gradient top (lighter — fakes a top light source) |
| `tile-bot` | `#0E141C` | tile gradient bottom (darker) |
| `tile-edge` | `#2A3645` | 1 px top/left highlight edge |
| `tile-shadow` | `#000000 @60%` | drop shadow under each tile |
| `text` | `#F5F7FA` | primary numerals |
| `text-dim` | `#8A94A6` | labels, units |
| `accent` | `#22D3EE` | normal active accent (cyan) |
| `good` | `#34D399` | in-spec green |
| `caution` | `#F5B301` | amber / yellow warning |
| `alarm` | `#FF3B30` | red alarm |
| `info` | `#3B82F6` | informational on-state (fan, flat-shift) |
| `led-off` | `#202833` | dim LED when inactive |

### 4.2 The 3D tile look (two routes)

**Route A — no assets (build entirely in RealDash, recommended start).** Each tile is a **Box /
Background gauge**:

- Fill = vertical **gradient** `tile-top → tile-bot`.
- **Corner radius** ~14 px.
- **Border** 1 px `tile-edge` (the light top edge sells the bevel).
- **Drop shadow:** RealDash boxes don't have a true shadow toggle, so fake it — place a second box
  **6 px below/right**, same size, solid `#000` at ~45% opacity, *behind* the tile. Group them so the
  tile reads as floating. (Skip if performance on the Pi suffers; the gradient + edge alone already
  reads as 3D.)

**Route B — polished PNG tiles (optional later).** Make one 512×512 rounded-rect PNG with a baked
top-highlight, vertical gradient, and soft outer drop shadow; use it as the **Background Image** of an
Image gauge behind each tile's value gauges. One PNG reused everywhere keeps it consistent and fast.
Grab tile/LED art from RealDash **Gallery → Examples** if you don't want to draw your own.

### 4.3 LEDs

An LED = a small **circular Indicator** (Image or Shape gauge) bound to a 0/1 input:

- **Off:** color `led-off`, opacity ~25% (still faintly visible so the layout reads).
- **On:** bright fill in the LED's color + a soft outer glow (Route A: a slightly larger blurred
  circle behind it; Route B: a glow baked into the PNG).
- Use the **Image Blend Color / Normal–Warning–Critical levels** trick (RealDash *Make an indicator*
  tutorial) so the LED is dim at value 0 and bright at value 1.

### 4.4 Typography

- **Hero numerals:** condensed bold, 7-seg/`DSEG`-style, **64–84 px**.
- **Tile numerals:** 34–46 px. **Compact numerals:** 26–32 px.
- **Labels:** uppercase, letter-spaced ~2 px, `text-dim`, 13–16 px, above the value.
- **Units:** `text-dim`, ~55% of the numeral size, trailing the value.

### 4.5 Strobe (blinking warnings)

Two ways; use **B** for the eye-catching strobe the brief asks for:

- **A — solid color (no animation):** in the gauge's **Input & Values**, set Warning/Critical levels
  so the active state is "Critical", then set the Critical **color** to red/amber. Color changes but
  doesn't flash.
- **B — true strobe (looping fade):** select the tile/LED → **Edit → Animations → add Fade**, opacity
  100 → 0, duration **0.35 s**, **Loop = on (ping-pong)**. Gate it with two triggers on the bound
  input: *value ≥ 1 → start/show*, *value < 1 → stop/hide (opacity 100)*. Result: a steady ~1.4 Hz
  strobe while the warning is active, off otherwise. (Red strobe = critical, amber/yellow strobe =
  caution.) Animations save into the `.rd`; to version them as text, export to
  `realdash_st185_anim.xml` — see <https://github.com/janimm/RealDash-extras/tree/master/Dashboard-animation-examples>.

---

## 5. Page 1 — DASH (single consolidated page)

```
┌──────────────────────────────────── TOP STRIP (h56) ──────────────────────────────────────┐
│ ST185  10:42 │ CRUISE: SET │ ●FLAT ●FAN ●LOFUEL ●SBFLT ●COOL-P ●OILP2 │      ♪ MEDIA ►     │
├───────────────────────────┬───────────────────────────┬────────────────────────────────────┤
│  CHARGE-PIPE IAT          │  COOLANT PRESSURE         │  TURBO SPEED                       │
│        52 °C              │       110 kPa             │      132,000 rpm                   │ HEROES
│  (strobe red >60)         │  (strobe red if COOL-P)   │  (red near turbo max)             │ h180
├──────────────┬────────────┼────────────┬──────────────┴──────────────┬─────────────────────┤
│ BOOST MAP    │ TC SETTING │ THROTTLE   │ ENGINE LOAD                 │                     │
│   2 "HIGH"   │   3        │   87 %     │   64 %                      │                     │ ROW C
│              │ interv ▭▭□ │  ▌bar      │  ▌bar                       │                     │ h116
├────────┬─────┴────┬───────┴───┬────────┴───┬────────────┬───────────┴─────────────────────┤
│ TARGET │ FUEL     │ ETHANOL   │ CABIN      │ TRIGGER    │ A/C                              │
│ LAMBDA │ TEMP     │           │ TEMP       │ ERRORS     │                                  │ ROW D
│ 0.88 λ │ 46 °C    │ E30       │ 24 °C      │ 0          │ ON                               │ h100
└────────┴──────────┴───────────┴────────────┴────────────┴──────────────────────────────────┘
```

### 5.1 Top strip (`x0 y0 w800 h56`, fill `bg`, 1 px bottom border `tile-edge`)

| Element | x,y,w,h | Input | Behavior |
|---|---|---|---|
| Title + clock | 12,14,150,30 | built-in **Time** | "ST185" + HH:MM, `text-dim` |
| **CRUISE badge** | 172,10,150,38 | `ST185: Cruise State` | Text from enum (OFF/STBY/SET/RES/OVR). `text-dim` when OFF; `accent` cyan when SET/RES; **amber** when OVR. Shows the engaged mode at a glance. |
| LED: FLAT | 336,16,58,26 | `ST185: Flat Shift` | `info` blue when 1, dim when 0. Steady. |
| LED: FAN | 396,16,52,26 | `ST185: Radiator Fan` | `info` blue when 1. Steady. |
| LED: LOFUEL | 450,16,76,26 | `ST185: Low Fuel` | **Strobe amber** when 1. |
| LED: SBFLT | 528,16,66,26 | `ST185: Switchboard Fault` | **Strobe amber** when 1. |
| LED: COOL-P | 596,16,72,26 | `ST185: High Coolant Press` | **Strobe red** when 1. |
| LED: OILP2 | 670,16,58,26 | `ST185: Low Oil Press 2` | **Strobe red (fast 0.25 s)** when 1. |
| **MEDIA nav** | 690,8,98,40 | — | Button. Tap → Page 2 (or just swipe left). Icon "♪ ►". |

> The cluster owns primary engine protection (knock, cut, primary oil pressure, over-temp) via its
> own full-screen overlay. These six LEDs are only the RealDash-side 0x3F1 bits — keep the mental
> model: **cluster = engine protection, RealDash = assist + extended + these bits.**

### 5.2 Heroes (`y64 h180`, three tiles, w250, x = 12 / 274 / 536)

| # | Tile | Gauge | Input | Range | Caution (amber) | Alarm (red, strobe) | x,y,w,h |
|---|---|---|---|---|---|---|---|
| 1 | Charge-Pipe IAT | Numeric hero + small arc | `ST185: Charge-Pipe IAT` | 0–80 °C | 50–60 | **>60** (heat soak → pull timing) | 12,64,250,180 |
| 2 | Coolant Pressure | Numeric hero + small arc | `ST185: Coolant Pressure` | 0–300 kPa | 150–200 | **>200 or `High Coolant Press`=1** | 274,64,250,180 |
| 3 | Turbo Speed | Numeric hero + small arc | `ST185: Turbo Speed` | 0–200k rpm | 90–95 % | **>95 % of turbo max** (set to your turbo) | 536,64,250,180 |

### 5.3 Row C (`y252 h116`, four tiles, w185, x = 12 / 209 / 406 / 603)

| # | Tile | Gauge | Input | Range | Notes / colors | x,y,w,h |
|---|---|---|---|---|---|---|
| 4 | Boost Map | Big index + name text | `ST185: Boost Map` | 0–3 | `accent`; map name layer 0=LOW,1=MID,2=HIGH,3=MAX | 12,252,185,116 |
| 5 | TC Setting | Big index + intervention bar | `ST185: TC Setting` (+`ST185: TC Intervention` sub-bar) | 0–4 | index `accent`; bar `good`<10 / amber 10–40 / red >40 | 209,252,185,116 |
| 6 | Throttle | Horizontal bar + % | `ST185: Throttle` | 0–100 % | `accent`, no alarm (driver input) | 406,252,185,116 |
| 7 | Engine Load | Horizontal bar + % | `ST185: Engine Load` | 0–100 % | `accent`, informational | 603,252,185,116 |

### 5.4 Row D (`y376 h100`, six compact tiles, w119, x = 12 / 143 / 274 / 405 / 536 / 667)

| # | Tile | Gauge | Input | Range | Caution / Alarm | x,y,w,h |
|---|---|---|---|---|---|---|
| 8 | Target Lambda | Numeric | `ST185: Target Lambda` | 0.60–1.30 λ | — (tune reference) | 12,376,119,100 |
| 9 | Fuel Temp | Numeric | `ST185: Fuel Temp` | 0–90 °C | amber 55–70 / **strobe red >70** | 143,376,119,100 |
| 10 | Ethanol % | Numeric (E-blend) | `ST185: Ethanol` | 0–100 % | — (flex reference) | 274,376,119,100 |
| 11 | Cabin Temp | Numeric | `ST185: Cabin Temp` | −10–60 °C | — (comfort) | 405,376,119,100 |
| 12 | Trigger Errors | Numeric (large 0) | `ST185: Trigger Errors` | 0–255 | amber 1–4 / **strobe red ≥5** (sync loss) | 536,376,119,100 |
| 13 | A/C | Text (enum) | `ST185: AC Status` | enum | `text-dim` OFF / `good` ON / **red FLT** | 667,376,119,100 |

Cruise (`#15`) lives in the top-strip badge (§5.1) so the engaged mode is always visible. Enum text
for Cruise and A/C comes straight from the XML; bind the gauge and enable **Show as text / enum**.

> **Note:** `ST185: Accel X/Y/Z` remain defined in the XML (the IMU frame is still received for the
> warning bits) but are **not shown** on this layout. They're available if you ever re-add a g-force
> view.

---

## 6. Page 2 — MEDIA (music player)

Built from RealDash's built-in **Media** inputs and **music actions** (not from the CAN XML). See §2
for what each platform can actually deliver.

```
┌──────────────────────────────────── TOP STRIP (h56) ──────────────────────────────────────┐
│ ◄ DASH      MEDIA                       SOURCE: SD CARD ▾                           10:42   │
├───────────────────────────────┬────────────────────────────────────────────────────────────┤
│                               │  TRACK TITLE  (large, scrolls if long)                     │
│         ALBUM ART             │  Artist Name                                               │
│         300 × 300             │  Album Name                                                │
│        (blank if n/a)         │  ┌──────────────────────────────── progress ───────────┐  │
│                               │  0:42                                          3:51      │  │
│                               │                                                            │
│                               │   [ ⏮ PREV ]   [ ⏯ PLAY/PAUSE ]   [ ⏭ NEXT ]   [ 🔀 ]   │
├───────────────────────────────┴────────────────────────────────────────────────────────────┤
│  MUSIC LIST  (browse SD/USB folders — scrollable; tap a track to play)                       │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.1 Top strip (`x0 y0 w800 h56`)

| Element | x,y,w,h | Input / action |
|---|---|---|
| **◄ DASH** nav | 12,8,96,40 | Button → Page 1 (or swipe right) |
| "MEDIA" title | 120,14,120,30 | static text |
| **SOURCE** label | 430,14,220,30 | static text reflecting Settings → User → Music Player (e.g. "SD CARD", "SPOTIFY", "OTHER"). Optional button = action *Open Settings*. |
| Clock | 700,14,88,30 | built-in **Time** |

### 6.2 Now-playing + transport

| # | Element | Gauge | Input / action | x,y,w,h |
|---|---|---|---|---|
| 1 | Album art | Image gauge | **Media → Album Art** input (blank if unavailable) | 24,80,300,300 |
| 2 | Track title | Text (large, marquee) | **Media → Track/Title** | 344,86,432,44 |
| 3 | Artist | Text | **Media → Artist** | 344,134,432,30 |
| 4 | Album | Text (`text-dim`) | **Media → Album** | 344,166,432,28 |
| 5 | Progress bar | Horizontal bar | **Media → Position** (range 0…**Media → Duration**) | 344,210,432,16 |
| 6 | Elapsed / total | Text ×2 (`units="time"`) | Position / Duration | 344,230,432,22 |
| 7 | **PREV** | Button | action **Previous Song** | 344,276,96,84 |
| 8 | **PLAY / PAUSE** | Button (toggles icon) | action **Toggle Pause Music** | 452,276,120,84 |
| 9 | **NEXT** | Button | action **Next Song** | 584,276,96,84 |
| 10 | **SHUFFLE** | Button (lit when on) | action **Toggle Music Playback Shuffle** | 692,276,84,84 |

Make the transport buttons **big (≥80 px)** — they're the only touch targets you use while moving.
Give them the same 3D tile treatment (§4.2) and an `accent` glow on press.

### 6.3 Browser

| # | Element | Gauge | Input / action | x,y,w,h |
|---|---|---|---|---|
| 11 | Music List | **Music List** gauge | local library / chosen folder | 12,392,776,84 |

The **Music List** gauge is RealDash's built-in file browser/playlist for the local player — tap a
row to play. (Start from the **Gallery → Examples → Music player** dash if you want a ready-made list
gauge to copy.) For streaming/Bluetooth sources the list reflects the OS player as far as the
platform allows (§2).

### 6.4 Configure the music source

1. **Settings → User → Music Player.** Pick one:
   - **RealDash as music player** → plays **SD/USB local files**; choose the music folder. Album art,
     list, and all transport work everywhere.
   - **Spotify / Apple Music / Google Play** *(Android)* → now-playing + transport for that app.
   - **Other** *(Android)* → for **Amazon Prime Music** and any other player; reads the Android media
     session (play/pause/next/prev; metadata as the app provides).
2. **Android only:** grant RealDash **Notification access** (Android Settings → Apps → Special access →
   Notification access → RealDash) or titles/artist won't show.
3. **Spotify only:** Spotify app → Settings → enable **Device Broadcast Status**.
4. **Bluetooth from your phone:** pair the phone to the **Pi's OS** and set the OS as the **A2DP
   sink** (Android handles this natively; on Linux use e.g. `bluez`/`bluealsa`/PulseAudio). Audio
   plays through the Pi's output; RealDash then shows/controls it via *Other* if a media session
   exists. **RealDash itself does not receive the Bluetooth stream** (§2).

---

## 7. Warning & strobe summary

Priority high→low. The two **critical** bits also raise a full-screen alert.

| Pri | Condition | Source | Where it shows | Color | Strobe? | Alert? |
|---|---|---|---|---|---|---|
| 1 | Low oil pressure (2nd) | `ST185: Low Oil Press 2`=1 | OILP2 LED | red | yes (fast) | **Fullscreen Alert** |
| 2 | High coolant pressure | `ST185: High Coolant Press`=1 | COOL-P LED + Coolant hero | red | yes | **Fullscreen Alert** |
| 3 | Trigger errors rising | `ST185: Trigger Errors`≥5 | Trigger tile | red | yes | no |
| 4 | Charge-pipe IAT critical | value > 60 °C | IAT hero | red | yes | no |
| 5 | Fuel temp critical | value > 70 °C | Fuel Temp tile | red | yes | no |
| 6 | Switchboard comm fault | `ST185: Switchboard Fault`=1 | SBFLT LED | amber | yes | no |
| 7 | Low fuel | `ST185: Low Fuel`=1 | LOFUEL LED | amber | yes | no |
| 8 | Radiator fan on | `ST185: Radiator Fan`=1 | FAN LED | blue | no (steady) | no |
| 9 | Flat-shift active | `ST185: Flat Shift`=1 | FLAT LED | blue | no (steady) | no |

**Fullscreen alert:** use the built-in **Fullscreen Alert** action from a trigger
(`Low Oil Press 2`=1 OR `High Coolant Press`=1) → red full-screen message; it clears when the bit
clears (latching is the ECU's job, not the display's).

---

## 8. Install & build — simple step-by-step

You do this once on the Pi; RealDash then remembers everything.

**Part A — get the data flowing (CAN)**

1. Copy **`link_g4x_realdash.xml`** onto the Pi (USB stick, SD card, or download).
2. Open RealDash → **Garage** → tap the car door → tap the instrument cluster.
3. **Connections → add a CAN bus connection** on your USB-CAN adapter, speed **1,000,000 (1 Mbit/s)**.
4. On that connection: **Select Vehicle → Custom Channel Description File →** browse to
   `link_g4x_realdash.xml`. Tap **Done**.
5. Back out of the Garage. Confirm under **Settings → Inputs → ECU Specific** you see the **`ST185:`**
   values. (Data appears once the car/ECU is powered and broadcasting.)

**Part B — build the DASH page (Page 1)**

6. Create a **new dashboard** (landscape). Set background to `#070A0F`.
7. Build the **top strip** (§5.1): clock, the cruise badge, the six LEDs, the MEDIA button.
8. Add the **three hero tiles** (§5.2), **Row C** (§5.3), **Row D** (§5.4). For each tile: add the
   3D box (§4.2), drop a Numeric/Bar/Text gauge on it, bind it to its `ST185:` input, set the range
   and Warning/Critical levels, and apply the palette/fonts (§4.4).
9. Add the **strobe** animations (§4.5, route B) to the warning LEDs and the IAT/Coolant/Fuel/Trigger
   tiles.

**Part C — build the MEDIA page (Page 2)**

10. Add a **second page** (it auto-becomes swipeable from Page 1).
11. Add album art, title/artist/album text, progress bar, and the four big transport buttons (§6.2),
    plus the Music List gauge (§6.3). *Shortcut:* open **Gallery → Examples → Music player**, copy its
    media gauges onto your page, then restyle to match.
12. Set your music source and permissions (§6.4).

**Part D — make it car-ready**

13. **Save** the dashboard (`.rd`). Keep `link_g4x_realdash.xml` on the device — the dash needs the
    `ST185:` inputs to exist.
14. Settings → set this dash as **default/auto-load**, enable **fullscreen**, and (optional) auto-start
    RealDash on boot so it comes up with the car.

> **Tip — test on a PC/phone first.** Build and eyeball the whole layout on RealDash for
> Windows/Android using the **simulator/demo input** before deploying to the Pi; it's much faster than
> editing on the car.

---

## 9. Input inventory

All CAN gauges bind to custom inputs from `link_g4x_realdash.xml` (Settings → Inputs → **ECU
Specific**, prefixed `ST185:`). Media gauges bind to RealDash's built-in **Media** inputs (not the CAN
XML). Temps carry `units="C"` so you can switch to °F per-gauge.

| Input | Frame | Raw → value | Page / tile |
|---|---|---|---|
| `ST185: Charge-Pipe IAT` | 0x3F0 | V−50 °C | DASH hero 1 |
| `ST185: Coolant Pressure` | 0x3F0 | V kPa | DASH hero 2 |
| `ST185: Turbo Speed` | 0x3F0 | V×100 rpm | DASH hero 3 |
| `ST185: Boost Map` | 0x3EF | index 0–3 | DASH C-4 |
| `ST185: TC Setting` | 0x3EF | index 0–4 | DASH C-5 |
| `ST185: TC Intervention` | 0x3EF | V % | DASH C-5 sub-bar |
| `ST185: Throttle` | 0x3EF | V % | DASH C-6 |
| `ST185: Engine Load` | 0x3F0 | V % | DASH C-7 |
| `ST185: Target Lambda` | 0x3EF | V×0.001 λ | DASH D-8 |
| `ST185: Fuel Temp` | 0x3F0 | V−50 °C | DASH D-9 |
| `ST185: Ethanol` | 0x3F0 | V % | DASH D-10 |
| `ST185: Cabin Temp` | 0x3F0 | V−50 °C | DASH D-11 |
| `ST185: Trigger Errors` | 0x3F0 | V count | DASH D-12 |
| `ST185: AC Status` | 0x3EF | enum | DASH D-13 |
| `ST185: Cruise State` | 0x3EF | enum | DASH top badge |
| `ST185: Flat Shift` | 0x3F1 | bit0 | DASH LED |
| `ST185: Radiator Fan` | 0x3F1 | bit1 | DASH LED |
| `ST185: Low Fuel` | 0x3F1 | bit2 | DASH LED |
| `ST185: High Coolant Press` | 0x3F1 | bit3 | DASH LED + hero |
| `ST185: Low Oil Press 2` | 0x3F1 | bit4 | DASH LED + alert |
| `ST185: Switchboard Fault` | 0x3F1 | bit5 | DASH LED |
| `ST185: Accel X/Y/Z` | 0x3F1 | V×0.1 g | defined, not shown |
| Media: Title / Artist / Album / Album Art / Position / Duration | — | RealDash built-in | MEDIA page |

---

## 10. Maintenance notes

- **Inputs are the contract.** Rename a value in `link_g4x_realdash.xml` and every gauge bound to the
  old name breaks. Keep names stable or re-bind.
- **Thresholds are starting points.** IAT/coolant/turbo/fuel-temp bands are sane 3S-GTE defaults —
  tune to your engine, turbo, and event from logged data. Turbo Speed redline depends on the fitted
  turbo; set the hero's caution/critical to **your** turbo's max.
- **No transmit.** RealDash is listen-only here — never add `writeInterval`/`initialValue` to the CAN
  frames; the ECU owns 0x3EF–0x3F1 (master-design §7 / Conflict B).
- **Bit map is canonical.** The 0x3F1 byte-6 warning bits follow `link_g4x_can_setup.json` /
  `CAN-BUS-ID-ALLOCATION-TABLE.md` §6. If those change, update the per-bit `<value>` entries.
- **Media reality.** Re-read §2 before promising yourself Amazon/Bluetooth on a Linux Pi — Android is
  the path of least resistance for full media.
