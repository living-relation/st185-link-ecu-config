# Harness drawing notes - the long ones

The full text of drawing notes too long to fit inside a drawing's frame for the PDF export
(DECISIONS R88). Dan's answer to question I5 (2026-10-14): widen a note first, then split it
into the gaps, and only then move long reference text here, leaving a short note on the drawing
that points to this file. Each section below belongs to one drawing in `docs/harness/rebuild/`;
the drawing keeps a short version of each note. The text is as it stood on the drawing before
the move (nothing reworded). Change a fact here and on the drawing together.

## ST185-WheelSpeed-Front

**Scope.** FRONT WHEEL SPEED - two pieces. IN: the FL and FR ABS drops run as separate cables to
a point by the IN plug and land in it. OUT: the OUT plug, the screened 4-core output cable and the
6-way inline DT04-6P near the ECU (IX_WS_FRONT). The ECU side owns only the short spur and the
DT06-6S mating half. No bulkhead.

**VRC not drawn.** The VR conditioner and its enclosure belong to the enclosure build. This
harness is two separate pieces with no drawn link (Daniel 2026-10-12): IN - the FL and FR legs
land in the IN plug lp16_vrc_f_in (pin 1 ABS+ FL, 2 ABS- FL, 3 shield drain, 4 ABS+ FR, 5 ABS- FR);
OUT - the OUT plug lp16_vrc_f_out (pin 1 +5V, 2 Gnd, 3 FL out, 4 FR out, 5 screen drain) ->
4-core screened cable -> IX_WS_FRONT c1-c5 (c6 spare). Both plugs: CNLINKO LP-16-J05PE-02-001,
female, 5 pins, unshielded, solder cups 22-20 AWG; the box takes the LP-16-C05SX-02-101 rear-nut
panel socket.

**Shields** (docs/SHIELD-RULES.md; no connector shells, drains on pins). Each sensor screen
floats at the sensor. Every screen is drawn as if it had a drain wire (R29): both sensor screens
meet at ONE splice by the IN plug and one drain wire (M22759/16-20-06) runs from it to IN pin 3.
Build method, not drawn (R30): the FL drain is the one crimped (soldered) into IN pin 3; the FR
drain is soldered onto it about 6 mm (0.25 in) behind the rear of the plug, where 6 mm of the FL
drain's insulation is cut away. The output cable screen lands straight on OUT pin 5 and on inline
pin 5, which runs on to the ECU shield ground. Inside the VRC the build joins IN pin 3 to OUT
pin 5 by wire. One screen node, grounded once, at the ECU.

**Isolation.** The PCB must not touch the enclosure - nylon standoffs; the board grounds through
the output cable only. The screen never touches the case either: the drains run pin to pin inside
the box. Mount the enclosure on nylon hardware.

**No connector or case landings for the screen.** Drains run by pin (IN 3, OUT 5) and join inside
the box by wire - nothing bonds to the case and no connector shell carries the screen, so there is
no bare-metal spot to mask before powder coat.

## ST185-WheelSpeed-Rear

**Scope.** REAR WHEEL SPEED - two pieces. IN: the RL and RR ABS drops run as separate cables to a
point by the IN plug and land in it. OUT: the OUT plug, the screened 4-core output cable and the
6-way inline DT04-6P near the ECU (IX_WS_REAR). The ECU side owns only the short spur and the
DT06-6S mating half. No bulkhead.

**VRC not drawn.** The VR conditioner and its enclosure belong to the enclosure build. This
harness is two separate pieces with no drawn link (Daniel 2026-10-12): IN - the RL and RR legs
land in the IN plug lp16_vrc_r_in (pin 1 ABS+ RL, 2 ABS- RL, 3 shield drain, 4 ABS+ RR, 5 ABS- RR);
OUT - the OUT plug lp16_vrc_r_out (pin 1 +5V, 2 Gnd, 3 RL out, 4 RR out, 5 screen drain) ->
4-core screened cable -> IX_WS_REAR c1-c5 (c6 spare). Both plugs: CNLINKO LP-16-J05PE-02-001,
female, 5 pins, unshielded, solder cups 22-20 AWG; the box takes the LP-16-C05SX-02-101 rear-nut
panel socket.

**Shields** (docs/SHIELD-RULES.md; no connector shells, drains on pins). Each sensor screen
floats at the sensor. Every screen is drawn as if it had a drain wire (R29): both sensor screens
meet at ONE splice by the IN plug and one drain wire (M22759/16-20-06) runs from it to IN pin 3.
Build method, not drawn (R30): the RL drain is the one crimped (soldered) into IN pin 3; the RR
drain is soldered onto it about 6 mm (0.25 in) behind the rear of the plug, where 6 mm of the RL
drain's insulation is cut away. The output cable screen lands straight on OUT pin 5 and on inline
pin 5, which runs on to the ECU shield ground. Inside the VRC the build joins IN pin 3 to OUT
pin 5 by wire. One screen node, grounded once, at the ECU.

**Isolation** and **no connector or case landings for the screen**: word for word the same as
ST185-WheelSpeed-Front above.

## ST185-AntiTheft

**Scope.** ST185 ANTI-THEFT HARNESS
- Harness side = Deutsch DT sockets (TE), gold 0462-201-1631 (owned stock).
- Device leads get DT04 pin mates - see NEED-TO-BUY.md, not drawn (device side).
- All conductors 20 AWG to fit DT size-16 contacts (20-16 AWG).
- TIE-IN = generic butt splice onto the car lead. Fused feeds come from the LOGIC box (ALM 5A,
  ALMS 2A, ALMIG 2A) on ST185-CabinPower, broken off.
- Grounds: 3 generic M6 rings stacked on one cabin stud (max 2 x 20 AWG per ring).
- Bundle lengths are estimates - final tape-measure pass sets them.
- Folds into ST185-CabinAccessory in the Option C restructure.

**The alarm does not cut the starter.** Our starter is switched by k_str on the Link's Aux 8 /
A26. The alarm's ground-when-armed output drives a G4X DIGITAL INPUT and the ECU's own anti-theft
function does the fuel and ignition cut. Link XtremeX spec: 'Anti-Theft control through digital
inputs, over CAN or both'. One less relay, and the cut sits inside the ECU where it cannot be
hot-wired around. DI accepts a ground-switched input directly - enable the 4k7 pull-up.

**No relay or fuse in the engine bay.** The siren is in the bay but its feed comes from the cabin
LOGIC box. The park-lamp flash output drives a relay in the CABIN block.

**Cavity notes** - full text of the signals marked * on this drawing:

| Where | Full text |
|---|---|
| Alarm module - main harness (D 1 | +12V CONSTANT - from the fuse box LOGIC ALM 5A (ST185-CabinPower). Alarm must stay live with the key off. |
| Alarm module - main harness (D 2 | GROUND - cabin chassis stud, same stud as the rest of the accessory loom |
| Alarm module - main harness (D 3 | IGNITION SENSE - +12V key-on, tells the alarm the car is running |
| Alarm module - main harness (D 4 | SIREN + - switched +12V out, 2A. Siren is in the bay, this feed comes from the cabin. |
| Alarm module - main harness (D 5 | PARKING LIGHT OUT - flashes the park lamps on trigger. Drive the OEM circuit through a relay in the CABIN block, not a bay relay. |
| Alarm module - main harness (D 6 | DOOR TRIGGER IN - negative. OEM door courtesy switches. |
| Alarm module - main harness (D 9 | IMMOBILISER OUT - grounds when armed. Goes to a G4X DIGITAL INPUT, not a starter-kill relay. The ECU does the fuel and ignition cut. |
| Alarm module - main harness (D 12 | SHOCK SENSOR TRIGGER IN - negative, from the sensor's signal pin |
| shock (label) | Shock / tilt sensor (replaces the OEM glass-break sensor) |
| Status LED (dash) 2 | LED cathode to ground. Kit LED - module limits the current. |
| t_at_12v | +12V CONSTANT, LOGIC ALM 5A (ST185-CabinPower, broken off). NOT the engine bay. |
| t_at_gnd | Cabin chassis ground stud M6 - ring A (alarm + siren) |
| t_at_door | OEM door courtesy switches - negative when a door opens |
| t_at_hood | Hood pin switch - ADD ONE, the car has no factory hood pin |
| t_at_park | Park lamp flash - to a relay in the CABIN block, never a bay relay |
| t_at_gnd_b | Cabin chassis ground stud M6 - ring B (shock + LED) |
| t_at_12v_shk | +12V CONSTANT, 2A fuse, LOGIC ALMS 2A - shock sensor feed |

## ST185-RearLights

**Scope.** REAR LIGHTS HARNESS (Route 15, approved by Dan 2026-10-13). New harness: the original
rear lighting wires are missing (R55); every wire is new, project colours follow the factory
colours. Lift-back; tail, stop, high-mount stop (in the spoiler), back-up, rear turn L/R, license
plate lights. Rear wiper / washer deleted (R54). Run: J/B No.1 / left kick panel -> LH sill ->
left quarter panel (no inline connector, C2) -> hatch branch to H6 at the upper left (OEM path,
C7) -> rear panel: R11, L1 + ground BL, R12.

**Ground.** One rear ground for all rear lamps, H6 included (Dan C6) - sp_rl_gnd -> body ground
BL, back panel center. Lamp ends (R113): no lamp plugs - the factory bulb sockets stay and each
end is a flying lead, soldered to the factory bulb-socket pigtail + adhesive heat-shrink
(ATUM-4/1-0, 40 mm). Lengths are route estimates - measure at the build.

(The FEEDS note stays on the drawing word for word.)
