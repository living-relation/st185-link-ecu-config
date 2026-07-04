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
RPM, boost/MAP, ECT, IAT, oil temp/pressure, speed, gear, **actual** lambda, fuel level, and the
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

An LED indicator in the top strip = a small **circular Indicator** (Image or Shape gauge) + a text
label, bound to a 0/1 input. **All six strip LEDs behave the same way** (the info LEDs and the
warning LEDs are styled identically — only the dot color differs):

- **Off / inactive:** dot color `led-off` at ~25% opacity; label `text-dim`.
- **On / active:** dot lights in its own color with a soft outer glow **and the label turns white
  (`text`)**. No blink, no background tint — a steady, clean "lit" state.
- **Dot colors (kept per indicator):** FLAT / FAN = `info` blue · LOFUEL / SBFLT = `caution` amber ·
  ECT-P / OILP2 = `alarm` red.
- Use the **Image Blend Color / Normal–Warning–Critical levels** trick (RealDash *Make an indicator*
  tutorial) so the LED dot + label are dim at value 0 and bright/white at value 1.

> The **data tiles** (heroes / Row D) still strobe for true critical values — see §4.5. The strip
> LEDs deliberately do **not** strobe; they are clean status lights.

### 4.4 Typography

- **Hero numerals:** condensed bold, 7-seg/`DSEG`-style, **64–84 px**.
- **Tile numerals:** 34–46 px. **Compact numerals:** 26–32 px.
- **Labels:** uppercase, letter-spaced ~2 px, `text-dim`, 13–16 px, above the value.
- **Units:** `text-dim`, ~55% of the numeral size, trailing the value.

### 4.5 Strobe (blinking warnings)

Strobe is reserved for the **data tiles** (heroes + Row D) when a value goes critical/caution — the
top-strip LEDs stay steady (§4.3). Two ways; use **B** for the eye-catching strobe:

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
│ 10:42 │ CRUISE: SET │ ●FLAT ●FAN ●LOFUEL ●SBFLT ●ECT-P ●OILP2 │           ♪ MEDIA ►        │
├───────────────────────────┬───────────────────────────┬────────────────────────────────────┤
│  TARGET LAMBDA            │  COOLANT PRESSURE         │  TURBO SPEED                       │
│        0.88               │       16 PSI              │      132 K                         │ HEROES
│  TUNE ▬▬▬□  (no alarm)    │  (strobe red if ECT-P)    │  (red near turbo max)             │ h180
├──────────────┬────────────┼────────────┬──────────────┴──────────────┬─────────────────────┤
│ BOOST MAP    │ TC SETTING │ THROTTLE   │ ENGINE LOAD                 │                     │
│   2 "HIGH"   │   3        │   87 %     │   64 %                      │                     │ ROW C
│              │ INT % ▬▭□  │  ▌bar      │  ▌bar                       │                     │ h116
├────────┬─────┴────┬───────┴───┬────────┴───┬────────────┬───────────┴─────────────────────┤
│IAT2-CP │ FUEL     │ ETHANOL   │ TRIG ERR   │ A/C                                          │
│        │ TEMP     │           │            │                                              │ ROW D
│ 52 °C  │ 46 °C    │ E30       │ 0          │ ON                                           │ h100
└────────┴──────────┴───────────┴────────────┴──────────────────────────────────────────────┘
```

### 5.1 Top strip (`x0 y0 w800 h56`, fill `bg`, 1 px bottom border `tile-edge`)

All six LEDs use the same style (steady "lit dot + white label" when active, dim when inactive — see
§4.3); only the dot color differs. The MEDIA button is kept inside the right margin so it is never
clipped by the screen edge.

| Element | x,y,w,h | Input | Behavior |
|---|---|---|---|
| Clock | 12,14,74,30 | built-in **Time** | HH:MM, `text-dim` (no "ST185" text) |
| **CRUISE badge** | 96,10,128,38 | `ST185: Cruise State` | Shows the engaged mode from the enum: **OFF / STBY / SET / RES / OVR**. `text-dim` when OFF; `accent` cyan for any active mode. **Not a warning** — it only reflects the OEM cruise-stalk state (see note below). |
| LED: FLAT | 232,16,56,26 | `ST185: Flat Shift` | dot `info` blue + white label when 1, dim when 0 |
| LED: FAN | 292,16,52,26 | `ST185: Radiator Fan` | dot `info` blue + white label when 1 |
| LED: LOFUEL | 348,16,72,26 | `ST185: Low Fuel` | dot `caution` amber + white label when 1 |
| LED: SBFLT | 424,16,66,26 | `ST185: Switchboard Fault` | dot `caution` amber + white label when 1 |
| LED: ECT-P | 494,16,62,26 | `ST185: High Coolant Press` | dot `alarm` red + white label when 1 |
| LED: OILP2 | 560,16,58,26 | `ST185: Low Oil Press 2` | dot `alarm` red + white label when 1 |
| **MEDIA nav** | 678,9,110,38 | — | Button, fully inside the 12 px right margin (ends at 788). Tap → Page 2 (or swipe left). Icon "♪ ►". |

> **Cruise modes:** the OEM cruise-control stalk feeds the ECU (via the switchboard); the ECU
> broadcasts the resulting state on 0x3EF byte6, which RealDash shows as the enum text above. The
> badge is informational only — it never blinks or shows a warning color. (ECT-P = the coolant/ECT
> pressure warning bit; renamed from COOL-P.)

> The cluster owns primary engine protection (knock, cut, primary oil pressure, over-temp) via its
> own full-screen overlay. These six LEDs are only the RealDash-side 0x3F1 bits — keep the mental
> model: **cluster = engine protection, RealDash = assist + extended + these bits.**

### 5.2 Heroes (`y64 h180`, three tiles, w250, x = 12 / 274 / 536)

| # | Tile | Gauge | Input | Display | Caution (amber) | Alarm (red, strobe) | x,y,w,h |
|---|---|---|---|---|---|---|---|
| 1 | **Target Lambda** | Numeric hero + bottom mini-bar | `ST185: Target Lambda` | λ value, 2 decimals; bar spans 0.60–1.30. Left-aligned mini-label **"Tune"** above the bar. Label reads **"Target Lambda"** (the word, no glyph). | — | — (tune reference, no alarm) | 12,64,250,180 |
| 2 | Coolant Pressure | Numeric hero + small arc | `ST185: Coolant Pressure` | **PSI** — gauge **Gauge Math `=V*0.145038`**, unit "PSI" (input stays kPa). | ~22–29 PSI (150–200 kPa) | **>29 PSI (>200 kPa) or `High Coolant Press`=1** | 274,64,250,180 |
| 3 | Turbo Speed | Numeric hero + small arc | `ST185: Turbo Speed` | **"K" (thousands)** — Gauge Math `=V/1000`, 0 decimals, suffix **"K"** → 3 digits like `132K`. Optional: show 1 decimal under 1000 rpm (e.g. `0.5K`) via a second gauge gated by a `V<1000` trigger. | 90–95 % | **>95 % of turbo max** (set to your turbo) | 536,64,250,180 |

### 5.3 Row C (`y252 h116`, four tiles, w185, x = 12 / 209 / 406 / 603)

| # | Tile | Gauge | Input | Range | Notes / colors | x,y,w,h |
|---|---|---|---|---|---|---|
| 4 | Boost Map | Big index + name text | `ST185: Boost Map` | 0–3 | `accent`; map name layer 0=LOW,1=MID,2=HIGH,3=MAX | 12,252,185,116 |
| 5 | TC Setting | Big index + intervention bar | `ST185: TC Setting` (+`ST185: TC Intervention` sub-bar) | 0–4 | index `accent`; left-aligned mini-label **"Int %"** above the bar (= % intervention the ECU applies to correct wheel slip); bar `good`<10 / amber 10–40 / red >40 | 209,252,185,116 |
| 6 | Throttle | Horizontal bar + % | `ST185: Throttle` | 0–100 % | `accent`, no alarm (driver input) | 406,252,185,116 |
| 7 | Engine Load | Horizontal bar + % | `ST185: Engine Load` | 0–100 % | `accent`, informational | 603,252,185,116 |

### 5.4 Row D (`y376 h100`, five compact tiles, w145, x = 12 / 169 / 326 / 483 / 640)

> **Cabin Temp tile removed (2026-06-28):** dropped from the CAN config to free a byte for 2-byte Coolant Pressure. Trigger Errors is kept; Row D is now 5 tiles.

| # | Tile | Gauge | Input | Range | Caution / Alarm | x,y,w,h |
|---|---|---|---|---|---|---|
| 8 | **IAT2 - CP** (charge-pipe IAT) | Numeric | `ST185: Charge-Pipe IAT` | 0–80 °C | amber 50–60 / **strobe red >60** (heat soak) | 12,376,145,100 |
| 9 | Fuel Temp | Numeric | `ST185: Fuel Temp` | 0–90 °C | amber 55–70 / **strobe red >70** | 169,376,145,100 |
| 10 | Ethanol % | Numeric (E-blend) | `ST185: Ethanol` | 0–100 % | — (flex reference) | 326,376,145,100 |
| 11 | Trigger Errors | Numeric | `ST185: Trigger Errors` | 0–255 | amber ≥1 / **red rising** (crank/cam sync loss) | 483,376,145,100 |
| 12 | A/C | Text (enum) | `ST185: AC Status` | enum | `text-dim` OFF / `good` ON / **red FLT** | 640,376,145,100 |

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

Strip **LEDs are steady** (lit dot + white label when active — §4.3); **data tiles strobe** for true
critical/caution values. The two critical bits also raise a full-screen alert.

| Pri | Condition | Source | Where it shows | LED dot color | Tile strobe? | Alert? |
|---|---|---|---|---|---|---|
| 1 | Low oil pressure (2nd) | `ST185: Low Oil Press 2`=1 | OILP2 LED (steady) | red | — | **Fullscreen Alert** |
| 2 | High coolant pressure | `ST185: High Coolant Press`=1 | ECT-P LED (steady) + Coolant hero (PSI) | red | yes (hero) | **Fullscreen Alert** |
| 3 | Trigger/sync errors | `ST185: Trigger Errors` rising (≥1 caution) | Trigger Errors tile (Row D-11) | — | yes | no |
| 4 | Charge-pipe IAT critical | value > 60 °C | IAT2-CP tile (Row D) | — | yes | no |
| 5 | Fuel temp critical | value > 70 °C | Fuel Temp tile | — | yes | no |
| 6 | Switchboard comm fault | `ST185: Switchboard Fault`=1 | SBFLT LED (steady) | amber | — | no |
| 7 | Low fuel | `ST185: Low Fuel`=1 | LOFUEL LED (steady) | amber | — | no |
| 8 | Radiator fan on | `ST185: Radiator Fan`=1 | FAN LED (steady) | blue | — | no |
| 9 | Flat-shift active | `ST185: Flat Shift`=1 | FLAT LED (steady) | blue | — | no |

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

Input **names are unchanged** (do not rename them) — the columns below note the **display label/unit**
the gauge shows, which is a UI-only choice.

| Input (unchanged) | Frame | Raw → value | Display label / unit | Page / tile |
|---|---|---|---|---|
| `ST185: Target Lambda` | 0x3EF | V×0.001 λ | "Target Lambda", 2 dp + "Tune" bar | DASH hero 1 |
| `ST185: Coolant Pressure` | 0x3F0 | V kPa | "Coolant Pressure" in **PSI** (Gauge Math `=V*0.145038`) | DASH hero 2 |
| `ST185: Turbo Speed` | 0x3F0 | V×100 rpm | "Turbo Speed" in **K** (Gauge Math `=V/1000` + "K") | DASH hero 3 |
| `ST185: Boost Map` | 0x3EF | index 0–3 | "Boost Map" + name | DASH C-4 |
| `ST185: TC Setting` | 0x3EF | index 0–4 | "TC Setting" | DASH C-5 |
| `ST185: TC Intervention` | 0x3EF | V % | "Int %" bar | DASH C-5 sub-bar |
| `ST185: Throttle` | 0x3EF | V % | "Throttle" % | DASH C-6 |
| `ST185: Engine Load` | 0x3F0 | V % | "Engine Load" % | DASH C-7 |
| `ST185: Charge-Pipe IAT` | 0x3F0 | V−50 °C | "IAT2 - CP" °C | DASH D-8 |
| `ST185: Fuel Temp` | 0x3F0 | V−50 °C | "Fuel Temp" °C | DASH D-9 |
| `ST185: Ethanol` | 0x3F0 | V % | "Ethanol" (E-blend) | DASH D-10 |
| `ST185: Trigger Errors` | 0x3F0 | V count | "Trig Err" | DASH D-11 |
| `ST185: AC Status` | 0x3EF | enum | "A/C" (enum text) | DASH D-13 |
| `ST185: Cruise State` | 0x3EF | enum | "CRUISE: <mode>" | DASH top badge |
| `ST185: Flat Shift` | 0x3F1 | bit0 | "FLAT" LED (blue) | DASH LED |
| `ST185: Radiator Fan` | 0x3F1 | bit1 | "FAN" LED (blue) | DASH LED |
| `ST185: Low Fuel` | 0x3F1 | bit2 | "LOFUEL" LED (amber) | DASH LED |
| `ST185: High Coolant Press` | 0x3F1 | bit3 | "ECT-P" LED (red) + hero strobe | DASH LED + hero |
| `ST185: Low Oil Press 2` | 0x3F1 | bit4 | "OILP2" LED (red) | DASH LED + alert |
| `ST185: Switchboard Fault` | 0x3F1 | bit5 | "SBFLT" LED (amber) | DASH LED |
| `ST185: Accel X/Y/Z` | 0x3F1 | V×0.1 g | — | defined, not shown |
| Media: Title / Artist / Album / Album Art / Position / Duration | — | RealDash built-in | now-playing | MEDIA page |

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
