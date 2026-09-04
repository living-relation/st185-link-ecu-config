> **Note:** this is the text extracted from the project file
> `5SGTE Hybrid Timing Belt Install and Cam Degreeing Guide_ HKS 2.pdf` in the "5sgte Project
> Data" claude.ai Project. The tool used to pull project files into this repo only returns
> extracted text for PDF/document uploads (not the original PDF bytes), so this `.md` is a
> text-only copy — images/diagrams referenced at the end are not reproduced here. The original
> PDF remains in the claude.ai Project's file uploads. Copied into the repo 2026-09-04.

Timing Belt Installation &
Camshaft Degreeing — 5S-GTE
Hybrid (3S-GTE Gen 2 Head on
5S-FE Block)
HKS 264 Cams · ATS Adjustable Cam
Gears · ATI Super Damper · Degree­Wheel Method

TL;DR

Time it exactly like a normal 3S-GTE Gen 2 using
the 178-tooth Gen 2 timing belt (OE 13568-
79105-family / HKS 24999-AT007, 178T): the
crank sprocket, oil pump, idlers, tensioner, cam
sprockets and belt are all 3S-GTE parts bolted to a
3S-GTE head, so the block underneath doesn't
change the procedure. Set the belt on factory
marks first, verify true TDC with a screw-in piston
stop, then degree the cams.

For the HKS 264 outer-shim cams (intake 2202-
RT063, exhaust 2202-RT064), the HKS install­sheet centerlines are Intake 110° ATDC and
Exhaust 103° BTDC. On a turbo 3S-GTE the
community-proven bias is to start at HKS spec,
then retard the exhaust ~4–6° for top-end power;
advancing the intake favors spool and low-end
torque.

Critical torques (Toyota 3S-GTE FSM): crank
pulley/damper bolt 107 N·m / 79 ft-lb, cam
sprocket bolt 69 N·m / 51 ft-lb with the SST
holding tool (~80 ft-lb without), No.1 idler 52 N·m
/ 38 ft-lb (mount bolt 42 N·m / 31 ft-lb in the
procedure text), tensioner bolts 21 N·m / 15 ft-lb,
cam bearing caps 19 N·m / 14 ft-lb, cam/valve
cover 6 N·m / 53 in-lb. Treat this as an
interference build — with the 5S geometry plus
HKS 264 lift, a mistimed belt or wrong centerline
can cause valve-to-piston contact.

Key Findings

The hybrid does not change the timing procedure.
Builders on mr2oc.com and toyotanation.com confirm
the 5S-GTE (5S-FE block + 3S-GTE head) is timed
exactly like a normal 3S-GTE — one states plainly, "It's
the same as a 3S timing belt install." Toyota Forum
The measured deck-height difference between the
two blocks is negligible (a community teardown calc
put the 5S-FE deck within ~0.0016" of the 3S-GTE), so
the standard 178-tooth Gen 2 belt fits and tracks
correctly. All timing hardware you install is 3S-GTE
Gen 2 hardware.

Interference risk is real for THIS combination. A
stock Gen 2 3S-GTE is famously non-interference, but
the 5S-FE's longer stroke/taller piston geometry
combined with higher-lift HKS 264 cams changes
that. A builder who assembled a 5S block with a 3S
head and HKS 264 cams reported that with the belt
off, the No.1 piston at TDC and the cams at the No.1
TDC position, the pistons contacted the valves — "I'm
clearly operating as an interference setup now." Any
timing error, dropped tooth, or mis-degreed cam
therefore risks bent valves, so verification steps below
are mandatory.

HKS 264 spec (outer-shim, Gen 2 head). Duration
264°; valve lift 8.95 mm exhaust per HKS retailer spec
(Real Street Performance lists 2202-RT064 as
"Camshaft Duration: 264 Deg, Position: Exhaust, Valve
Lift: 8.95mm, Valve Timing: TBA"; RZCrew lists the
same cam as "Lift: 9mm"); duration at 0.050" ≈ 187°
intake / 186° exhaust. HKS designed valve events
(owner transcription of the HKS install sheet at
celica.dds.nl): intake — max lift 110° ATDC, opens 22°
BTDC, closes 62° ABDC; exhaust — max lift 103°
BTDC, opens 55° BBDC, closes 29° ATDC; 51°
overlap. HKS's distributor text states strengthened
valve springs are "required" for this Step-2 profile.

Two different "HKS 264" cams exist — don't confuse
them. The 2202-RT063/064 cams in this build are the
outer-shim (shim-over-bucket), lower-lift Gen 2
cams with centerlines 110°/103°. A separate high-lift,
shim-under-bucket Gen 3 264 (10.3 mm intake / 9.8
mm exhaust lift) uses ~105° intake / 117° exhaust —
those numbers are widely reposted but do not apply
to your parts.

ATS adjustable cam gears provide 10 cam degrees of
adjustment in either direction, use a stock steel
Toyota cam gear as the base (so belt-contact surface
is OEM), and are held by five set screws for minimal
slip. Atsracing ATS's recommended starting point
(stock cams): set each cam to true zero, then retard
exhaust ~6°. For HKS 264s, ATS techs have quoted "0
intake and 6 retard on the exhaust," MR2 Owners Club
while the ATS website historically listed "4 advance
intake / 8 retard exhaust." Dyno tuning is
recommended to finalize.

ATI Super Damper (P/N 918529): confirmed by ATI
distributor spec — "Two 4-groove belt drives, 7″
Overdrive… SFI 18.1 Certified for competition use.
Shell Material: 5.67″ Aluminum; Hub Material: Steel,
with Inner Shell Part #916147, 1.2195″ bore; Inertia
Weight: 2.2 lbs, 3-Ring." Laser-etched 360° timing
marks. It is retained by the OEM crank bolt at Toyota
spec (107 N·m / 79 ft-lb); the damper shell/pulley
screws use Loctite 242.

Details

Component & Torque Reference (Toyota 3S­GTE Gen 2 FSM)
From the Toyota 3S-GTE Repair Manual torque table
(ManualsLib page 104) and the 3S-GE/3S-GTE/5S-FE
engine repair manual (Scribd, "Timing Belt" section
EM-44/45/46):

Crankshaft pulley × crankshaft: 107 N·m (1,090
kgf-cm, 79 ft-lb) — verbatim from the FSM table.

Camshaft timing pulley × camshaft: 69 N·m (700
kgf-cm, 51 ft-lb) "for SST" (with the holding tool).
Without the SST, community sources cite ~80 ft-lb
/ 109 N·m.

Camshaft bearing cap × cylinder head: 19 N·m
(190 kgf-cm, 14 ft-lb) — verbatim from the FSM
table.

No.1 idler pulley × cylinder head: 52 N·m (530
kgf-cm, 38 ft-lb) in the torque table; the timing­belt procedure text lists the No.1 idler mount bolt
at 42 N·m (425 kgf-cm, 31 ft-lb) — reconcile
against your manual revision; apply Loctite 242 to
the first threads (community note).

Timing belt tensioner × cylinder head: 21 N·m
(210 kgf-cm, 15 ft-lb).

No.2 idler pulley × oil pump: per table
(community: ~13 ft-lb / ~18 N·m).

Cylinder head cover (cam/valve cover): 6.0 N·m
(61 kgf-cm, 53 in-lb) — verbatim from the FSM
table.

No.4 timing belt cover × cylinder head cover: 8.0
N·m (82 kgf-cm, 71 in-lb) — verbatim from the
FSM table.

RH engine mounting bracket × block: 52 N·m (38
ft-lb).

Oil pump pulley nut: ~8 N·m (71 in-lb)
(community-reported).

FSM sources / mirrors: the 3S-GTE timing-belt section
is "EM-44/45/46" in the Big Green Book. Accessible
mirrors: ManualsLib ("Toyota 3S-GTE Repair Manual,"
torque table p.104), the "3sge 3sgte 5sfe Engine
Repair Manual" on Scribd, and celicatech's "TIMING
BELT (3S-GTE)" scan hosted on Yumpu. The photo­rich SW20 community how-to is at
mr2.com/ARTICLE/TimingBeltSW20.html.

Belt selection & hybrid notes

Gen 2 3S-GTE belt = 178 teeth (ST185); Gen 3
(ST205) = 177 teeth. Toymods OE-equivalent
"177/178T 3SGE/3SGTE" belts appear under
13568-79105 / 13568-79315 / 13568-88460 (e.g.,
Mag Engines A557Y100, 177T). HKS Gen 2 belt =
24999-AT007 (178T). Do NOT use the 163-tooth
FE-series (3S-FE/4S-FE/5S-FE) belt — that belt is
for the FE cylinder head, not the GTE head you're
running.

Match belt generation to the oil-pump generation:
the Gen 3 oil pump gear has fewer teeth than Gen
2. MR2 Owners Club For a Gen 2 head build use
Gen 2 oil pump + Gen 2 belt + Gen 2 tensioner. If
you fit a high-volume late-5S/Solara oil pump with
the small pulley, community notes report needing
the ST205 (Gen 3) belt to match.

Water pump front (gear) section is common
across gens; only the rear housing/coolant tubes
differ.

HKS 264 valve-spring & clearance gotchas

HKS's own product text: strengthened valve
springs "are required" for the Step-2 264 profile.
RZCrew Community consensus: stock springs
"can't keep up" and power drops off above ~6,500
rpm — upgrade to HKS/Crower/Engle springs +
retainers, and re-check lash after degreeing.

One documented Engle-spring measurement: coil
bind ~21.8 mm; at the ~9 mm intake lift the
spring sits ~25.5 mm compressed, leaving only
~2.7 mm to coil bind — verify coil-bind clearance
and retainer-to-seal clearance before revving.

Ferrea Ti retainers made for the Gen 3 3S-GE
Beams do NOT fit the Gen 3 3S-GTE without
modification MR2 Owners Club — verify
retainer/lock fitment for your exact head.

Spark-plug thread (for piston-stop selection)
3S-GTE spark plugs are 14 mm thread, 19 mm
(3/4") reach, 5/8" (16 mm) hex — so use a 14 mm
screw-in piston stop, not a 12 mm or 18 mm.

Recommended Sequenced
Procedure

PHASE 0 — Tools & Consumables

Degree wheel (9"+ preferred; note: the Midship
Runabout method uses a Summit 0-180-0 wheel
and the averaging math below assumes that style
— a full 360° wheel changes the arithmetic).

14 mm screw-in piston stop (spark-plug-hole
type).

Dial indicator (0.001") with magnetic base and a
long extension rod to reach the shim/bucket.

Cam-gear holding tool or Toyota SST; 22 mm
socket + breaker bar for the crank bolt;
flywheel/crank lock.

Torque wrenches spanning in-lb (to ~80 in-lb),
mid ft-lb (10–90 ft-lb), and a higher-range ft-lb
wrench for the 79 ft-lb crank bolt.

Loctite 242 (blue), anti-seize, FIPG sealant,
paint/white-out pen; new belt, tensioner, idlers,
water pump, cam/crank seals; upgraded valve
springs + retainers.

ATI damper install tool (#918999) and Torx T-40
Plus bit (#918997) for the shell screws.

PHASE 1 — Preparation & Teardown to the Belt

1. Disconnect the negative battery terminal; wait ≥20
s (FSM caution). Yumpu Raise the car, remove the
RH rear wheel and engine under cover.

2. Remove intercooler, alternator, accessory belts,
EGR/throttle body as needed, then the upper
timing covers. On the SW20 remove the RH engine
mount/bracket (52 N·m on reinstall) — remove the
intercooler first so the long through-bolt clears.
MR2

3. Before disturbing anything, rotate to No.1 TDC
compression and paint-mark the belt-to-sprocket
relationship at all three sprockets (both cams +
crank) and the belt's rotation direction. At No.1
TDC compression both cam-sprocket holes align
with the marks on the front cam bearing caps.

4. Loosen the crank pulley/damper bolt while still
assembled (flywheel lock, or in-gear + brakes).

Remove the tensioner (2 bolts), belt, cam
sprockets as required, crank pulley, lower cover,
and crank timing sprocket. Never rotate the crank
backward (counterclockwise viewed from the belt
end).

PHASE 2 — Find True TDC (do this before
trusting any mark)

5. Fit the degree wheel to the crank snout with
spacer washers so the center isn't pulled in; fix a
stiff pointer to a block bolt. Remove all spark
plugs; rag the holes.

6. Piston-stop method (preferred): bring No.1 near
TDC, rotate ~15° backward, install the 14 mm
screw-in stop. Rotate forward (clockwise) until the
piston contacts the stop; record the wheel
reading. Rotate backward to the other contact;
record. True TDC is exactly halfway between the
two readings — set the wheel to 0 there, lock the
crank bolt, and re-verify at least twice.

7. Sanity check: at true TDC the cast crank­pulley/cover mark typically reads near "0," but 3–
5° off is commonly reported and normal due to
belt/tolerance stack — trust the degree wheel, not
the cast mark. ⚠️ This is the single most
important verification step; a TDC error
propagates into every centerline and directly risks
valve contact.

PHASE 3 — Install the Belt on Factory Marks

8. Install the No.2 idler (per table) and the No.1 idler
+ tension spring; pry the No.1 idler fully away from
the belt path and snug temporarily.

9. Rotate the crank so the crank sprocket timing
mark aligns with the oil-pump-housing notch
(keyway at 12 o'clock). 2CarPros Note: the crank
sprocket mark references the oil-pump notch; the
pulley/damper mark referencing the "0" on the
No.1 cover is a separate later reference. If your
crank sprocket has no visible external mark (some
don't), transfer a mark from the crank
keyway/notch onto the oil pump before removing
the old belt.

10. Align each cam-sprocket hole with the mark on
the cam bearing cap. Install the belt starting at
the crank, keeping the driver's-side (crank-to­exhaust-cam) run tight and driving all slack to the
tensioner side; keep tension on the water-pump
side as you route it.

11. Compress and pin the tensioner (grenade pin),
install it, torque the tensioner bolts to 21 N·m (15
ft-lb), then pull the pin. Loosen the No.1 idler bolt
½ turn to let the spring tension the belt, 2CarPros
then torque the No.1 idler (52 N·m / 38 ft-lb per
the table, or the 42 N·m / 31 ft-lb mount-bolt figure
per the procedure text — match your FSM
revision).

12. Rotate the crank two full revolutions clockwise
TDC→TDC and re-verify all three marks. If they
don't align, pull and re-seat the belt. (The belt's
own match-marks will NOT re-align after rotation
— that's normal; only the sprocket-to-cap /
sprocket-to-oil-pump marks matter.)

PHASE 4 — Degree the Intake Cam

13. With true TDC established (Phase 2) and the belt
on factory marks, mount the dial indicator on a
No.1 intake shim/bucket with a near-vertical rod.
Rotate clockwise; find max lift (indicator
reverses), and zero the gauge there.

14. Rotate to 0.050" before max lift, record the wheel
reading; continue to 0.050" after max lift, record.
Centerline = (opening reading + closing reading)
÷ 2 — the intake lobe centerline in crank degrees
ATDC.

15. Compare to HKS spec 110° ATDC. To correct,
loosen the ATS set screws and rotate the hub.
Remember the 2:1 ratio: 1 cam degree = 2 crank
degrees. The wheel reads crank degrees, so a 6-
crank-degree correction equals a 3-cam-degree
gear move. Advancing the intake (smaller ATDC
number) improves low-end torque and turbo
spool; retarding trades that for top end. Turbo
bias: start at HKS 110° (or slightly advanced) for a
street/spool-focused build.

16. Re-torque set screws, recheck the centerline,
repeat until within ~1°. For a large change, relieve
belt tension (re-pin the tensioner, or hold the
tensioner pulley with a 14 mm wrench + bungee)
and move a whole tooth rather than exhausting
the gear's ±10° range.

PHASE 5 — Degree the Exhaust Cam

17. Move the indicator to a No.1 exhaust
shim/bucket. Find max lift, zero the gauge, take
the 0.050"-before and 0.050"-after readings, and
average for the centerline (expressed in crank
degrees BTDC).

18. Compare to HKS spec 103° BTDC. Turbo-3S
community bias: retard the exhaust ~4–6° from
HKS zero for top-end power (ATS: "0 intake, 6
retard exhaust"; MR2 some run 4 advance / 8
retard — dyno-dependent). Retarding the exhaust
effectively widens the LSA and typically adds
high-rpm power with little low-end penalty on
these motors.

19. Lock the gear, recheck, and confirm both
centerlines a final time with the belt at full
operating tension.

PHASE 6 — Final Verification, Damper,
Reassembly

20. Valve-to-piston clearance check (mandatory on
this interference build): with the final springs
installed, either lay clay on the No.1 piston or bar
the engine slowly by hand through TDC overlap
and confirm clearance. Never spin it on the
starter until verified. If clearance is marginal,
valve reliefs or a thicker head gasket may be
required.

21. Re-check/set valve lash (shim & bucket): **intake
0.15–0.25 mm (0.006–0.010"), exhaust 0.20–0.30
mm (0.008–0.012") Toyota All-Trac ** — the cam
swap/degreeing changes lash.

22. Install the ATI Super Damper (P/N 918529):
deburr and anti-seize the crank snout (the steel
hub is a press/interference fit). Align the indent
dimple on the hub with the arrow decal on the
shell; draw the shell on with the countersunk Torx­40-Plus screws using Loctite 242 (16 ft-lb / ~120
in-lb class per ATI). Retain the whole assembly
with the OEM crank bolt torqued to 107 N·m / 79
ft-lb — do NOT use a long mandrel bolt (it
stretches with heat). Verify the ATI's laser-etched
timing mark against your true-TDC mark and treat
it as a reference to confirm, not to trust blind. The
elastomer may show slightly out of balance until
the engine first exceeds ~2,000 rpm (normal —
the weight self-centers).

23. Reinstall covers (No.4 cover 8 N·m / 71 in-lb,
cam/valve cover 6 N·m / 53 in-lb), accessories,
intercooler, and mount (52 N·m). Confirm
accessory-belt alignment — the ATI retains the
factory 4-groove A/C and alternator belt geometry.

24. Prime oil, crank without starting to build pressure,
then start and re-verify ignition timing.

Recommendations

1. Buy the correct Gen 2 kit first: 178-tooth Gen 2
3S-GTE belt (OE or HKS 24999-AT007), Gen 2
tensioner, Gen 2 idlers, Gen 2 oil pump, plus
HKS/Crower/Engle springs & retainers. Never
reuse an FE-series 163T belt.

2. Always find true TDC with the 14 mm piston stop
before degreeing — do not trust the cast
pulley/cover mark or the ATI etched mark. Re­verify twice.

3. Start the HKS 264s at the cam-card centerlines
(In 110° ATDC / Ex 103° BTDC), then dyno-tune.
For a spool-focused street turbo, bias intake
slightly advanced and retard exhaust 4–6°.
Thresholds to change: if top-end power plateaus
early or the turbo feels laggy, sweep exhaust
retard in 2° steps on a dyno; if low-end/spool is
the priority, advance intake in 2° steps. Re-verify
no lash drift after each move.

4. Treat this as interference: do a clay / hand-turn
valve-to-piston check with the final springs before
first start. If clearance is marginal, add valve
reliefs or a thicker head gasket.

5. Torque discipline: crank bolt 79 ft-lb; cam
sprockets 51 ft-lb (SST) / ~80 ft-lb (no SST); No.1
idler 38 ft-lb (or 31 ft-lb mount bolt per your FSM);
tensioner 15 ft-lb; cam caps 14 ft-lb. Loctite 242
on the idler pivot threads and ATI shell screws; re­check the cam-gear set screws after the first heat
cycle/dyno session.

Caveats

FSM torque figures are transcribed from
ManualsLib's 3S-GTE torque table (p.104) and the
Scribd 3S/5S engine manual. The No.1 idler
appears as 52 N·m (torque table) and 42 N·m / 31
ft-lb (procedure text, mount bolt) in different
sections — verify against your specific FSM
revision. The cam-sprocket 69 N·m figure is with
the SST holding tool; without it, community
sources cite ~80 ft-lb (109 N·m).

HKS 264 centerlines (110°/103°) come from an
owner's transcription of the HKS install sheet
(celica.dds.nl) corroborated by multiple MR2OC
owners who read the actual cam card; HKS
distributors list "Valve Timing: TBA." The

conflicting "105°/117°" figures belong to the high­lift Gen 3 (shim-under-bucket) 264, NOT the
2202-RT063/064 outer-shim cams in this build —
do not use them here.

Valve lift is listed as 8.95–9.0 mm by HKS
retailers but 9.2 mm in some community spec
sheets (likely advertised cam-lobe lift vs
measured valve lift). Flagged, not fully resolved.

Deck-height/interference: whether your specific
piston/rod/head-gasket stack is interference
depends on your exact parts. At least one
documented 5S-block + 3S-head + HKS 264 build
measured hard valve contact at TDC with the belt
off — verify on YOUR engine.

ATI crank-bolt torque: ATI's generic instructions
direct you to use the OEM crank bolt at the vehicle
manufacturer's spec (here 79 ft-lb). Confirm no
part-number-specific ATI instruction sheet
supersedes this for P/N 918529.

Degree-wheel math above assumes a 0-180-0
style wheel (per the Midship Runabout guide); a
full 360° wheel requires adjusting how the
opening/closing numbers are summed.

Images/diagrams (belt routing, cam/crank timing­mark photos, degree-wheel setup, ATS gear
markings, ATI installed):
mr2.com/ARTICLE/TimingBeltSW20.html (timing­belt walkthrough),

midshiprunabout.org/mk2/cam-degreeing/
(photo-rich degreeing guide, including dial­indicator-on-exhaust-cam and piston-stop TDC
photos), the celicatech/Yumpu FSM scan
(component/routing diagrams), and
atiracing.com/instructions/Super-Damper.pdf
(damper assembly/indexing diagram). There is
also a "How to Install an ATI Super Damper on a
Toyota MR2 3S-GTE" video on YouTube.
