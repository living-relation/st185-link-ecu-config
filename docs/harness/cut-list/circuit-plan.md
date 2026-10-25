# Circuit plan - decided by complete circuit

Dan reviews the rewire by whole circuits, not single wires (2026-10-21). The 21-circuit table below was proposed in chat
on 2026-10-21 and approved by Dan with changes to #2, #9, #11 and #18; those changes are applied here. None of it is in
the master yet (row 164). Pins are 1993 EWD; ECU pins are Link G4X XtremeX.

| # | Circuit | Plan (Dan's changes applied) |
|---|---|---|
| 1 | Engine management (factory ECU, igniter, EFI relays) | Gone. The Link plus the new engine harness replace it. |
| 2 | Starting | **Changed:** the OEM starter relay in R/B No.4 stays. Coil + from key START; coil - through the clutch start switch C11 to Link Aux 8 (the Link runs the start). No `k_str`. |
| 3 | Charging | IG2-15 B-R keeps a 6 in pigtail: kill switch, then alternator IG. IG2-16 Y stays and drives the 12 V charge LED in the ClusterLED harness (sinks to OEM cluster plug C12-8); nothing else on it (Dan 2026-10-25). Alternator B+ on the heavy-cable harness. |
| 4 | Cruise | The OEM cruise ECU and actuator are gone; the stalk stays as CSB3 buttons (0x640 / 0x642 unchanged; Dan 2026-10-25). The clutch switch C17 (on the car, Dan 2026-10-25) gives the CSB3 the clutch state for flat shift and rev match; C11 is for the starter only. |
| 5 | SRS | Gone. |
| 6 | ABS | Gone. The wheel speed sensors get their own mini harnesses to the VRC enclosure (Route 17 lines 12-13). |
| 7 | Gauges + warning lamps | Gone; replaced by the CAN cluster. The LEDs take turn, high beam, charge and park brake from the OEM cluster plugs, oil pressure from the CSB3. Cluster dimming (Dan 2026-10-25): new wire from the dimmer rheostat R10 pin 1 (`T`, green, TAIL fuse output, steady +12 V with the lights on; 1993 EWD p.109) through 1.5 kohm to the center cluster's PC817 headlight-sense opto (cluster GPIO28, J8 pin 15, active-low; center-cluster-esp32-p4 `PINOUT.md`). The dimmer knob (rheostat R10, left of the steering wheel) is removed and the center cluster's dimmer encoder (encoder 3) mounts in its spot (Dan 2026-10-25); the encoder wires to the cluster (J8 pin 27 = GPIO24 A, pin 28 = GPIO25 B, pin 21 = GPIO2 push, plus a J8 ground) belong to the cluster repo's harness (R7). The car side uses the old R10 plug: pin 1 (green, TAIL +12 V) for the dimming sense. The old R10 plug pin 3 (white-green, the dimmed return of every other dash light) is jumpered to pin 2 (white-black ground), so those lights come on at full brightness (Dan 2026-10-25, N64 = A). |
| 8 | Main power (AM1, AM2, J/B1, dome, hazard, retract) | Trunk battery -> glove-box boxes -> cabin landings. |
| 9 | Blower | **Changed:** R/B No.4 stays with its heater relay, 40 A HEATER and 10 A A/C fuses; one short new feed wire from the glove-box boxes. No `k_htr`. |
| 10 | A/C | Both amps stay. The clutch runs on `k_acc`. A15 gets the tach signal, a compressor-speed signal and coolant-OK (Needs Dan N61, bench test first). The pressure switch gets a new wire. |
| 11 | Reverse + back-up lamps | **Changed:** not replaced, no K-REV. The OEM back-up switch drives the lamps; its output is tapped through opto IN2 to the CSB3. The new switch wires (engine harness, bulkhead A) splice to the IG2-4 / IG2-13 pigtails. The OEM rear lighting wires are reused (no new RearLights harness; replaces R55). |
| 12 | Fuel pump | `k_fp` in the trunk, rear-fuel harness. |
| 13 | Front lights + pop-ups | Front run (Route 17 line 10), spliced to the 6 in pigtails. |
| 14 | Horn | Front run, relay in the glove box. |
| 15 | Radiator + condenser fans | Link-controlled relays, front run. |
| 16 | Wiper + washer | Wiper on the driver fender run (line 11), washer pump on the front run. |
| 17 | Fog | Removed (Dan 2026-10-25): the fog light relay R/B No.3, the fog light switch F12 and every fog wire (the lamps were removed long ago). The 20 A FR FOG fuse in R/B No.4 is left as a spare. No spare circuit to the old fog-lamp spots: aux circuits come later and are separate. |
| 18 | Windows, locks, sunroof, seat | **Changed:** R/B No.2 stays; its 30 A POWER fuse gets one new feed wire from the glove-box boxes. No `k_pwr`. |
| 19 | Diagnostic plug (DLC1) | Gone. |
| 20 | Alarm hood pin + siren | Front run and driver fender run. |
| 21 | Engine-bay ground studs (EA, EB, EC) | The studs stay as ground points; every ground wire on them is new. |

Also checked 2026-10-21: the ETB hold power is all cabin and J/B No.1 stays: Aux 6 (A28) holds K-EFI; DI 9 (B28) senses
IG2; the IG2 wake diode feeds A5 from J/B1 1H-7; K-ETB on Aux 2 (A20) feeds B5. The G4X spec sheet p.3 lists ECU Hold
Power Control.

Fuse box: parked (Dan 2026-10-21). The glove-box boxes are not built and only fill blanks; after the rest is designed,
drop `k_pwr`, `k_htr`, `k_str` and K-REV, and add the R/B No.2 / No.4 feed fuses.
