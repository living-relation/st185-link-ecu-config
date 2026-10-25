# Circuit plan - decided by complete circuit

Dan reviews the rewire by whole circuits, not single wires (2026-10-21). This is what is decided; none of it is in the
master yet (row 164). The full 21-circuit table was reviewed in chat on 2026-10-21; Dan approved it with the changes
below. Pins are 1993 EWD; ECU pins are Link G4X XtremeX.

| Circuit | Decision | Dan |
|---|---|---|
| Starter | The OEM starter relay in R/B No.4 stays. Coil + from key START; coil - through the clutch start switch C11 to Link Aux 8 (the Link runs the start). No `k_str` in the glove-box boxes. | after 2026-10-21 ("I need a starter") |
| Clutch | The cruise clutch switch C17 gives the CSB3 a continuous clutch state (flat shift, rev match). C11 is for the starter only. Car check: C17 is present and where it clicks. | "1. A" |
| Reverse | No K-REV. The OEM back-up switch drives the lamps as built. Its output is tapped through opto IN2 to the CSB3. The new switch wires (engine harness, bulkhead A) splice to the IG2-4 / IG2-13 pigtails. | 2026-10-21 (#11) |
| Rear lights | The OEM rear lighting wires are in the car and are reused. No new RearLights harness (replaces R55). | "2. B" |
| Power windows, locks, sunroof, seat | R/B No.2 stays; its 30 A POWER fuse gets one new feed wire from the glove-box boxes. `k_pwr` not needed. | 2026-10-21 (#18) |
| Blower and A/C fuses | R/B No.4 stays with its heater relay, 40 A HEATER and 10 A A/C fuses; one short new feed wire from the glove-box boxes. | 2026-10-21 |
| Charge lamp | IG2-16 Y (alternator L) stays; the ClusterLED charge LED sinks to OEM cluster plug C12-8. | 2026-10-21 |
| ECU-IG / alternator IG | IG2-15 B-R keeps a 6 in pigtail: kill switch, then alternator IG. | 2026-10-21 |
| ETB hold power | Already designed, all cabin, J/B No.1 stays: Aux 6 (A28) holds K-EFI; DI 9 (B28) senses IG2; the IG2 wake diode feeds A5 from J/B1 1H-7; K-ETB on Aux 2 (A20) feeds B5. G4X spec sheet p.3 lists ECU Hold Power Control. | checked 2026-10-21 |
| Fog / spare | No fog lights; R/B No.3 goes. A spare relay circuit runs to the old fog-lamp spots, ends insulated. | 2026-10-21 |
| A/C compressor amp A15 | Kept. RPM and lock feed: Needs Dan N61 (bench test first: Link tacho -> 4.7 kohm -> pin 9). | open |
| Fuse box | Parked. The glove-box boxes are not built and only fill blanks. After the rest is designed: drop `k_pwr`, `k_htr`, `k_str`, K-REV; add the R/B No.2 / No.4 feed fuses. | 2026-10-21 |
