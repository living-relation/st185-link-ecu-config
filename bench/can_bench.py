#!/usr/bin/env python3
"""CAN bench-test tool for the Celica ST185 TrackCluster bus.

Plug a USB-CAN adapter (CANable/slcan, PCAN USB, or a SocketCAN interface) into
your laptop, wire its CANH/CANL to a single isolated node on the bench, then use
the subcommands below to inject the traffic that node expects to see in normal
vehicle operation, or to monitor what it transmits.

Subcommands
-----------
  simulate-ecu          Send all ECU TX frames (cluster + RealDash) at their
                        real cycle times, sweeping values to exercise gauges.
  full-cluster          Guided center-P4 -> left/right-S3 test: keeps all five
                        cluster frames flowing while animating one signal at a
                        time, prompting what to check on each screen.
  full-realdash         Guided RealDash test: keeps 0x3EF/0x3F0/0x3F1 flowing
                        while animating one field at a time, prompting what to
                        check on the RealDash screen.
  simulate-switchboard  Send 0x640/0x641/0x642 with an incrementing heartbeat.
  inject-ls-command     Send 0x643 low-side output commands to the switchboard.
  monitor               Passively decode every known frame seen on the bus.

Examples
--------
  # CANable / slcan adapter at /dev/ttyACM0, 1 Mbit/s, drive a cluster:
  python can_bench.py --interface slcan --channel /dev/ttyACM0 --bitrate 1000000 simulate-ecu

  # Linux SocketCAN can0 already brought up at 1 Mbit/s, watch the switchboard:
  python can_bench.py --interface socketcan --channel can0 monitor

  # PCAN USB, pulse cooling-fan low-side output:
  python can_bench.py --interface pcan --channel PCAN_USBBUS1 --bitrate 1000000 \
      inject-ls-command --l1 255 --count 20
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from typing import Callable, List, Optional, Tuple

try:
    import can
except ImportError:  # pragma: no cover - dependency guard
    print(
        "ERROR: python-can is not installed.\n"
        "Install it with:  pip install -r requirements.txt",
        file=sys.stderr,
    )
    sys.exit(1)

import frames as f


# --- bus helpers -----------------------------------------------------------

def open_bus(args: argparse.Namespace) -> "can.BusABC":
    kwargs = {"interface": args.interface, "channel": args.channel}
    # SocketCAN channels are configured out-of-band (ip link); a bitrate kwarg
    # is rejected by that backend, so only pass it for the others.
    if args.bitrate and args.interface != "socketcan":
        kwargs["bitrate"] = args.bitrate
    try:
        return can.Bus(**kwargs)
    except Exception as exc:  # pragma: no cover - hardware dependent
        print(f"ERROR: could not open CAN bus ({args.interface}/{args.channel}): {exc}",
              file=sys.stderr)
        sys.exit(2)


def send(bus: "can.BusABC", can_id: int, data: bytes, verbose: bool = False) -> None:
    msg = can.Message(arbitration_id=can_id, data=data, is_extended_id=False)
    bus.send(msg)
    if verbose:
        hexd = " ".join(f"{b:02X}" for b in data)
        print(f"  TX 0x{can_id:03X} [{len(data)}] {hexd}")


# --- value sweeps ----------------------------------------------------------

def triangle(t: float, period: float, lo: float, hi: float) -> float:
    """Linear up/down sweep between lo and hi with the given period (seconds)."""
    phase = (t % period) / period
    tri = 2 * phase if phase < 0.5 else 2 * (1 - phase)
    return lo + (hi - lo) * tri


def sine(t: float, period: float, lo: float, hi: float) -> float:
    mid = (lo + hi) / 2.0
    amp = (hi - lo) / 2.0
    return mid + amp * math.sin(2 * math.pi * t / period)


# --- scheduler -------------------------------------------------------------

class PeriodicTask:
    def __init__(self, period_s: float, builder: Callable[[float], Tuple[int, bytes]]):
        self.period_s = period_s
        self.builder = builder
        self.next_due = 0.0


def run_scheduler(bus: "can.BusABC", tasks: List[PeriodicTask],
                  duration: Optional[float], verbose: bool,
                  on_tick: Optional[Callable[[float], bool]] = None) -> None:
    """Send periodic tasks until ``duration`` elapses or Ctrl-C.

    ``on_tick`` is called once per loop iteration with the elapsed seconds; if it
    returns False the scheduler stops. Use it to drive a scripted scenario that
    mutates the values the task builders read.
    """
    start = time.monotonic()
    for task in tasks:
        task.next_due = start
    try:
        while True:
            now = time.monotonic()
            elapsed = now - start
            if duration is not None and elapsed >= duration:
                break
            if on_tick is not None and on_tick(elapsed) is False:
                break
            soonest = None
            for task in tasks:
                if now >= task.next_due:
                    can_id, data = task.builder(elapsed)
                    send(bus, can_id, data, verbose)
                    task.next_due += task.period_s
                    # Avoid runaway catch-up if we fell behind.
                    if task.next_due < now:
                        task.next_due = now + task.period_s
                if soonest is None or task.next_due < soonest:
                    soonest = task.next_due
            sleep_for = max(0.0, (soonest - time.monotonic())) if soonest else 0.001
            time.sleep(min(sleep_for, 0.05))
    except KeyboardInterrupt:
        print("\nStopped.")


# --- simulate-ecu ----------------------------------------------------------

def build_ecu_tasks(include_realdash: bool) -> List[PeriodicTask]:
    tasks: List[PeriodicTask] = []

    def engine_fast(t: float) -> Tuple[int, bytes]:
        rpm = int(triangle(t, 8.0, 800, 7200))
        map_kpa = int(triangle(t, 8.0, 30, 220))
        ect = sine(t, 30.0, 70, 105)
        iat = sine(t, 25.0, 20, 55)
        oil = sine(t, 35.0, 60, 120)
        return f.ID_ENGINE_FAST, f.encode_engine_fast(rpm, map_kpa, ect, iat, oil)

    def speed_press_ign(t: float) -> Tuple[int, bytes]:
        ign = sine(t, 6.0, -5, 35)
        speed = int(triangle(t, 12.0, 0, 180))
        oilp = int(sine(t, 6.0, 100, 550))  # kPa-ish raw uint8 clamps at 255
        fuelp = int(sine(t, 6.0, 250, 400))
        return f.ID_SPEED_PRESS_IGN, f.encode_speed_press_ign(ign, speed, oilp, fuelp)

    def lambda_(t: float) -> Tuple[int, bytes]:
        lam = sine(t, 5.0, 0.78, 1.10)
        return f.ID_LAMBDA, f.encode_lambda(lam)

    def gear_fuel(t: float) -> Tuple[int, bytes]:
        gear = int(t // 3) % 8  # 0..7 cycling
        fuel = int(triangle(t, 60.0, 0, 100))
        return f.ID_GEAR_FUEL, f.encode_gear_fuel(gear, fuel)

    def engine_protect(t: float) -> Tuple[int, bytes]:
        # Pulse each warning in turn so the cluster overlay can be verified.
        slot = int(t // 4) % 7
        kwargs = dict(knock=0, ignition_cut=0, fuel_cut=0,
                      boost_cut=0, sensor_error=0, throttle_error=0)
        keys = ["knock", "ignition_cut", "fuel_cut", "boost_cut",
                "sensor_error", "throttle_error"]
        if slot < len(keys):
            kwargs[keys[slot]] = 1
        return f.ID_ENGINE_PROTECT, f.encode_engine_protect(**kwargs)

    tasks.append(PeriodicTask(0.010, engine_fast))
    tasks.append(PeriodicTask(0.010, speed_press_ign))
    tasks.append(PeriodicTask(0.010, lambda_))
    tasks.append(PeriodicTask(0.050, gear_fuel))
    tasks.append(PeriodicTask(0.050, engine_protect))

    if include_realdash:
        def drive_assist(t: float) -> Tuple[int, bytes]:
            target_lambda = sine(t, 5.0, 0.80, 1.00)
            throttle = int(triangle(t, 8.0, 0, 100))
            tc_setting = int(t // 5) % 6
            tc_interv = int(triangle(t, 4.0, 0, 40))
            boost_map = int(t // 7) % 4
            cruise = int(t // 6) % 5
            ac = int(t // 9) % 4
            return f.ID_DRIVE_ASSIST, f.encode_drive_assist(
                target_lambda, throttle, tc_setting, tc_interv,
                boost_map, cruise, ac)

        def ext_sensors(t: float) -> Tuple[int, bytes]:
            fuel_temp = sine(t, 40.0, 15, 60)
            load = int(triangle(t, 8.0, 0, 100))
            coolant_p = int(sine(t, 20.0, 80, 200))
            ethanol = int(sine(t, 50.0, 0, 85))
            charge_iat = sine(t, 25.0, 20, 70)
            cabin = sine(t, 45.0, 18, 30)
            turbo = int(triangle(t, 8.0, 0, 18000))
            trig_err = int(t // 10) % 5
            return f.ID_EXT_SENSORS, f.encode_ext_sensors(
                fuel_temp, load, coolant_p, ethanol, charge_iat,
                cabin, turbo, trig_err)

        def imu_warn(t: float) -> Tuple[int, bytes]:
            ax = sine(t, 4.0, -1.2, 1.2)
            ay = sine(t, 5.0, -1.5, 1.5)
            az = sine(t, 7.0, 0.5, 1.5)
            warn = (int(t // 3) % 6)
            warn_bits = (1 << warn) if warn < 6 else 0
            return f.ID_IMU_WARN, f.encode_imu_warn(ax, ay, az, warn_bits)

        tasks.append(PeriodicTask(0.050, drive_assist))
        tasks.append(PeriodicTask(0.100, ext_sensors))
        tasks.append(PeriodicTask(0.050, imu_warn))

    return tasks


def cmd_simulate_ecu(args: argparse.Namespace) -> None:
    bus = open_bus(args)
    include_rd = not args.cluster_only
    tasks = build_ecu_tasks(include_rd)
    scope = "cluster + RealDash" if include_rd else "cluster only"
    print(f"Simulating ECU TX frames ({scope}) on "
          f"{args.interface}/{args.channel}. Ctrl-C to stop.")
    try:
        run_scheduler(bus, tasks, args.duration, args.verbose)
    finally:
        bus.shutdown()


# --- full-cluster guided scenario ------------------------------------------
#
# The center ESP32-P4 is the only CAN node; it decodes the cluster frames into
# its dash-data model and forwards them to the left and right ESP32-S3 displays
# over UART (center GPIO20 -> left, GPIO21 -> right). To verify the WHOLE
# cluster chain (P4 -> both side S3 boards) we keep all five cluster frames
# flowing continuously (so the center keeps forwarding live snapshots), but
# animate one signal at a time with an on-screen prompt of what to look for on
# each physical screen.

class ClusterState:
    """Live engineering values, defaulting to a warm idle."""
    def __init__(self) -> None:
        self.rpm = 850
        self.map_kpa = 35
        self.ect_c = 88.0
        self.iat_c = 30.0
        self.oil_temp_c = 90.0
        self.ign_deg = 12.0
        self.vehicle_speed = 0
        self.oil_press = 250
        self.fuel_press = 350
        self.lambda1 = 1.00
        self.gear = 0          # 0=N, 1-6, 7=R
        self.fuel_pct = 60
        self.knock = 0
        self.ignition_cut = 0
        self.fuel_cut = 0
        self.boost_cut = 0
        self.sensor_error = 0
        self.throttle_error = 0

    def reset_transient(self) -> None:
        self.knock = self.ignition_cut = self.fuel_cut = 0
        self.boost_cut = self.sensor_error = self.throttle_error = 0


class Phase:
    """One step of a guided scenario.

    ``apply(state, t_in_phase)`` mutates the shared state; ``prompts`` is a list
    of ``(label, text)`` lines printed when the phase begins, telling the
    operator what to verify on each physical screen.
    """
    def __init__(self, name: str, duration: float,
                 apply: Callable[[object, float], None],
                 prompts: List[Tuple[str, str]]):
        self.name = name
        self.duration = duration
        self.apply = apply
        self.prompts = prompts


def run_scenario(bus: "can.BusABC", state, tasks: List[PeriodicTask],
                 phases: List[Phase], title: str, subtitle: str,
                 loop: bool, verbose: bool) -> None:
    """Drive a guided one-signal-at-a-time scenario over the given tasks."""
    ctrl = {"idx": -1, "phase_start": 0.0}
    total = sum(p.duration for p in phases)
    label_w = max((len(lbl) for p in phases for lbl, _ in p.prompts), default=6)

    print("=" * 70)
    print(title)
    print(subtitle)
    print(f"{len(phases)} phases, ~{total:.0f}s total."
          + ("  Looping until Ctrl-C." if loop else "  Ctrl-C to stop."))
    print("=" * 70, flush=True)

    reset = getattr(state, "reset_transient", None)

    def on_tick(elapsed: float) -> bool:
        idx = ctrl["idx"]
        t_in_phase = elapsed - ctrl["phase_start"]
        if idx < 0 or t_in_phase >= phases[idx].duration:
            idx += 1
            if idx >= len(phases):
                if loop:
                    idx = 0
                    if callable(reset):
                        reset()
                else:
                    return False
            ctrl["idx"] = idx
            ctrl["phase_start"] = elapsed
            t_in_phase = 0.0
            p = phases[idx]
            print(f"\n[{idx + 1:2d}/{len(phases)}] {p.name}  (~{p.duration:.0f}s)")
            for lbl, text in p.prompts:
                print(f"      {lbl:<{label_w}} : {text}")
            print("", end="", flush=True)
        phases[ctrl["idx"]].apply(state, t_in_phase)
        return True

    try:
        # duration=None: the scenario controls termination via on_tick.
        run_scheduler(bus, tasks, None, verbose, on_tick=on_tick)
        if not loop:
            print("\nScenario complete.")
    finally:
        bus.shutdown()


def build_cluster_scenario() -> List[Phase]:
    def idle(s: ClusterState, t: float) -> None:
        pass

    def rpm_sweep(s: ClusterState, t: float) -> None:
        s.rpm = int(triangle(t, 8.0, 850, 7200))
        s.map_kpa = int(triangle(t, 8.0, 35, 210))

    def speed_sweep(s: ClusterState, t: float) -> None:
        s.vehicle_speed = int(triangle(t, 8.0, 0, 180))

    def coolant_rise(s: ClusterState, t: float) -> None:
        s.ect_c = triangle(t, 10.0, 70, 115)
        s.oil_temp_c = triangle(t, 10.0, 70, 130)
        s.iat_c = sine(t, 6.0, 20, 55)

    def gear_cycle(s: ClusterState, t: float) -> None:
        s.gear = int(t // 1.2) % 8  # N,1..6,R, ~1.2 s each

    def fuel_drop(s: ClusterState, t: float) -> None:
        s.fuel_pct = int(triangle(t, 12.0, 0, 100))

    def lambda_sweep(s: ClusterState, t: float) -> None:
        s.lambda1 = sine(t, 5.0, 0.78, 1.10)

    def pressures(s: ClusterState, t: float) -> None:
        s.oil_press = int(triangle(t, 6.0, 80, 600))
        s.fuel_press = int(sine(t, 4.0, 250, 420))

    def ignition(s: ClusterState, t: float) -> None:
        s.ign_deg = sine(t, 5.0, -10, 40)

    warn_keys = ["knock", "ignition_cut", "fuel_cut",
                 "boost_cut", "sensor_error", "throttle_error"]
    warn_labels = ["Knock", "Ignition cut", "Fuel cut",
                   "Boost cut", "Sensor error", "Throttle error"]

    def make_warning(idx: int) -> Callable[["ClusterState", float], None]:
        key = warn_keys[idx]
        def apply(s: ClusterState, t: float) -> None:
            s.reset_transient()
            setattr(s, key, 1)
        return apply

    phases: List[Phase] = [
        Phase("Idle baseline", 4.0, idle, [
            ("CENTER", "Tach ~850, all gauges settled, gear N"),
            ("SIDES", "Both side screens show the same idle snapshot (no stale/blank data)")]),
        Phase("RPM + boost sweep", 9.0, rpm_sweep, [
            ("CENTER", "Tach sweeps 850->7200 and back; boost/MAP follows"),
            ("SIDES", "Whichever side mirrors RPM/boost tracks smoothly")]),
        Phase("Vehicle speed sweep", 9.0, speed_sweep, [
            ("CENTER", "Speedo sweeps 0->180->0"),
            ("SIDES", "Side screen showing speed tracks it")]),
        Phase("Coolant / oil / IAT temps", 11.0, coolant_rise, [
            ("CENTER", "ECT/oil rise to hot; temp gauges change color near the top"),
            ("SIDES", "Temp readouts on the sides match the center")]),
        Phase("Gear cycle", 10.0, gear_cycle, [
            ("CENTER", "Gear readout steps N,1,2,3,4,5,6,R"),
            ("SIDES", "Gear indicator on the sides follows the center exactly")]),
        Phase("Fuel level", 12.0, fuel_drop, [
            ("CENTER", "Fuel gauge ramps full<->empty"),
            ("SIDES", "Fuel readout mirrored on the sides")]),
        Phase("Lambda / AFR", 6.0, lambda_sweep, [
            ("CENTER", "Lambda/AFR swings 0.78<->1.10"),
            ("SIDES", "AFR readout mirrored on the sides")]),
        Phase("Oil / fuel pressure", 8.0, pressures, [
            ("CENTER", "Oil pressure swings low<->high; low-oil color/warn may trip"),
            ("SIDES", "Pressure readouts mirrored on the sides")]),
        Phase("Ignition timing", 6.0, ignition, [
            ("CENTER", "Ignition advance swings -10..+40 deg"),
            ("SIDES", "Timing readout (if shown) mirrored on the sides")]),
    ]
    for i, label in enumerate(warn_labels):
        phases.append(
            Phase(f"WARNING: {label}", 3.0, make_warning(i), [
                ("CENTER", f"Full-screen ECU WARNING overlay for '{label}'"),
                ("SIDES", "Right side screen raises the warning overlay (0x3EE)")]))
    phases.append(
        Phase("Clear warnings / idle", 4.0, idle, [
            ("CENTER", "Overlay clears, gauges return to idle"),
            ("SIDES", "Both sides return to a clean idle snapshot")]))
    return phases


def cmd_full_cluster(args: argparse.Namespace) -> None:
    bus = open_bus(args)
    state = ClusterState()
    phases = build_cluster_scenario()

    # All five cluster frames, built from the shared mutable state.
    def t_engine_fast(_t):
        return f.ID_ENGINE_FAST, f.encode_engine_fast(
            state.rpm, state.map_kpa, state.ect_c, state.iat_c, state.oil_temp_c)

    def t_speed(_t):
        return f.ID_SPEED_PRESS_IGN, f.encode_speed_press_ign(
            state.ign_deg, state.vehicle_speed, state.oil_press, state.fuel_press)

    def t_lambda(_t):
        return f.ID_LAMBDA, f.encode_lambda(state.lambda1)

    def t_gear(_t):
        return f.ID_GEAR_FUEL, f.encode_gear_fuel(state.gear, state.fuel_pct)

    def t_protect(_t):
        return f.ID_ENGINE_PROTECT, f.encode_engine_protect(
            state.knock, state.ignition_cut, state.fuel_cut,
            state.boost_cut, state.sensor_error, state.throttle_error)

    tasks = [
        PeriodicTask(0.010, t_engine_fast),
        PeriodicTask(0.010, t_speed),
        PeriodicTask(0.010, t_lambda),
        PeriodicTask(0.050, t_gear),
        PeriodicTask(0.050, t_protect),
    ]

    run_scenario(
        bus, state, tasks, phases,
        title="FULL CLUSTER TEST  (center P4 -> left & right S3 over UART)",
        subtitle="Inject CAN into the center board; watch all THREE screens.",
        loop=args.loop, verbose=args.verbose)


# --- full-realdash guided scenario -----------------------------------------
#
# RealDash is a passive listener of the three ECU->RealDash frames
# (0x3EF Drive Assist, 0x3F0 Extended Sensors, 0x3F1 IMU & Warnings). This
# scenario keeps all three flowing at their cycle times while animating one
# field at a time, prompting what to confirm on the RealDash screen.

class RealDashState:
    """Live engineering values for the RealDash-only frames; idle defaults."""
    def __init__(self) -> None:
        # 0x3EF Drive Assist & Status
        self.target_lambda = 0.95
        self.throttle_pct = 0
        self.tc_setting = 0
        self.tc_intervention_pct = 0
        self.boost_map_index = 0
        self.cruise_state = 0          # 0=Off,1=Standby,2=Set/Active,3=Resume,4=Override
        self.ac_status = 0             # 0=Off,1=Requested,2=Engaged,3=Fault
        # 0x3F0 Extended Sensors
        self.fuel_temp_c = 25.0
        self.engine_load_pct = 0
        self.coolant_press_kpa = 100
        self.ethanol_pct = 10
        self.charge_pipe_iat_c = 25.0
        self.cabin_temp_c = 22.0
        self.turbo_speed_rpm = 0
        self.trigger_error_count = 0
        # 0x3F1 IMU & Extended Warnings
        self.accel_x_g = 0.0
        self.accel_y_g = 0.0
        self.accel_z_g = 1.0           # 1 g resting (gravity)
        self.warnings = 0

    def reset_transient(self) -> None:
        self.warnings = 0


def build_realdash_scenario() -> List[Phase]:
    def idle(s: RealDashState, t: float) -> None:
        pass

    # --- 0x3EF Drive Assist & Status ---
    def throttle(s, t): s.throttle_pct = int(triangle(t, 8.0, 0, 100))
    def tgt_lambda(s, t): s.target_lambda = sine(t, 5.0, 0.80, 1.00)
    def tc_set(s, t): s.tc_setting = int(t // 1.5) % 6
    def tc_interv(s, t): s.tc_intervention_pct = int(triangle(t, 6.0, 0, 40))
    def boost_idx(s, t): s.boost_map_index = int(t // 1.5) % 4
    def cruise(s, t): s.cruise_state = int(t // 2.0) % 5
    def ac(s, t): s.ac_status = int(t // 2.0) % 4

    # --- 0x3F0 Extended Sensors ---
    def fuel_temp(s, t): s.fuel_temp_c = triangle(t, 8.0, 10, 70)
    def eng_load(s, t): s.engine_load_pct = int(triangle(t, 8.0, 0, 100))
    def coolant_p(s, t): s.coolant_press_kpa = int(triangle(t, 8.0, 80, 250))
    def ethanol(s, t): s.ethanol_pct = int(triangle(t, 8.0, 0, 85))
    def charge_iat(s, t): s.charge_pipe_iat_c = triangle(t, 8.0, 15, 75)
    def cabin(s, t): s.cabin_temp_c = sine(t, 8.0, 16, 32)
    def turbo(s, t): s.turbo_speed_rpm = int(triangle(t, 8.0, 0, 18000))
    def trig_err(s, t): s.trigger_error_count = int(t // 1.0) % 6

    # --- 0x3F1 IMU & Extended Warnings ---
    def accel_x(s, t): s.accel_x_g = sine(t, 4.0, -1.5, 1.5)
    def accel_y(s, t): s.accel_y_g = sine(t, 4.0, -1.5, 1.5)
    def accel_z(s, t): s.accel_z_g = sine(t, 4.0, -0.5, 2.5)

    warn_bits = [
        (f.WARN_FLAT_SHIFT, "Flat Shift Active"),
        (f.WARN_RADIATOR_FAN, "Radiator Fan On"),
        (f.WARN_LOW_FUEL, "Low Fuel Warning"),
        (f.WARN_HIGH_COOLANT_PRESS, "High Coolant Pressure"),
        (f.WARN_LOW_OIL_PRESS, "Low Oil Pressure"),
        (f.WARN_SWITCHBOARD_COMM_FAULT, "Switchboard Comm Fault"),
    ]

    def make_warning(bit: int) -> Callable[["RealDashState", float], None]:
        def apply(s: RealDashState, t: float) -> None:
            s.reset_transient()
            s.warnings = bit
        return apply

    phases: List[Phase] = [
        Phase("Idle baseline", 4.0, idle, [
            ("REALDASH", "All gauges live and steady at idle; no missing/stale frames")]),
        Phase("Throttle % (0x3EF)", 9.0, throttle, [
            ("REALDASH", "Throttle gauge sweeps 0->100%")]),
        Phase("Target lambda (0x3EF)", 6.0, tgt_lambda, [
            ("REALDASH", "Target AFR/lambda swings 0.80<->1.00 (scale 0.001)")]),
        Phase("TC setting (0x3EF)", 9.0, tc_set, [
            ("REALDASH", "TC setting index steps 0,1,2,3,4,5")]),
        Phase("TC intervention % (0x3EF)", 6.0, tc_interv, [
            ("REALDASH", "TC intervention gauge ramps 0->40%")]),
        Phase("Boost map index (0x3EF)", 6.0, boost_idx, [
            ("REALDASH", "Boost map index steps 0,1,2,3")]),
        Phase("Cruise state (0x3EF)", 10.0, cruise, [
            ("REALDASH", "Cruise state enum: Off,Standby,Set/Active,Resume,Override")]),
        Phase("AC status (0x3EF)", 8.0, ac, [
            ("REALDASH", "AC status enum: Off,Requested,Compressor Engaged,Fault")]),
        Phase("Fuel temp (0x3F0)", 8.0, fuel_temp, [
            ("REALDASH", "Fuel temp sweeps ~10..70 C (offset -50)")]),
        Phase("Engine load % (0x3F0)", 8.0, eng_load, [
            ("REALDASH", "Engine load gauge sweeps 0->100%")]),
        Phase("Coolant pressure (0x3F0)", 8.0, coolant_p, [
            ("REALDASH", "Coolant pressure sweeps ~80..250 kPa")]),
        Phase("Ethanol % (0x3F0)", 8.0, ethanol, [
            ("REALDASH", "Flex-fuel ethanol % sweeps 0->85")]),
        Phase("Charge-pipe IAT (0x3F0)", 8.0, charge_iat, [
            ("REALDASH", "Post-intercooler IAT sweeps ~15..75 C (offset -50)")]),
        Phase("Cabin temp (0x3F0)", 8.0, cabin, [
            ("REALDASH", "Cabin temp mirror swings ~16..32 C (offset -50)")]),
        Phase("Turbo speed (0x3F0)", 8.0, turbo, [
            ("REALDASH", "Turbo speed sweeps 0->18000 RPM (raw x100)")]),
        Phase("Trigger error count (0x3F0)", 6.0, trig_err, [
            ("REALDASH", "Trigger/sync error count steps 0..5")]),
        Phase("Accel X (0x3F1)", 6.0, accel_x, [
            ("REALDASH", "Lateral accel X swings -1.5..+1.5 g (signed, scale 0.1)")]),
        Phase("Accel Y (0x3F1)", 6.0, accel_y, [
            ("REALDASH", "Accel Y swings -1.5..+1.5 g (signed)")]),
        Phase("Accel Z (0x3F1)", 6.0, accel_z, [
            ("REALDASH", "Accel Z swings -0.5..+2.5 g (signed)")]),
    ]
    for bit, label in warn_bits:
        phases.append(
            Phase(f"WARNING: {label} (0x3F1)", 3.0, make_warning(bit), [
                ("REALDASH", f"Extended-warning indicator lights: '{label}'")]))
    phases.append(
        Phase("Clear warnings / idle", 4.0, idle, [
            ("REALDASH", "All warning indicators clear; gauges return to idle")]))
    return phases


def cmd_full_realdash(args: argparse.Namespace) -> None:
    bus = open_bus(args)
    state = RealDashState()
    phases = build_realdash_scenario()

    def t_drive_assist(_t):
        return f.ID_DRIVE_ASSIST, f.encode_drive_assist(
            state.target_lambda, state.throttle_pct, state.tc_setting,
            state.tc_intervention_pct, state.boost_map_index,
            state.cruise_state, state.ac_status)

    def t_ext_sensors(_t):
        return f.ID_EXT_SENSORS, f.encode_ext_sensors(
            state.fuel_temp_c, state.engine_load_pct, state.coolant_press_kpa,
            state.ethanol_pct, state.charge_pipe_iat_c, state.cabin_temp_c,
            state.turbo_speed_rpm, state.trigger_error_count)

    def t_imu_warn(_t):
        return f.ID_IMU_WARN, f.encode_imu_warn(
            state.accel_x_g, state.accel_y_g, state.accel_z_g, state.warnings)

    tasks = [
        PeriodicTask(0.050, t_drive_assist),
        PeriodicTask(0.100, t_ext_sensors),
        PeriodicTask(0.050, t_imu_warn),
    ]

    run_scenario(
        bus, state, tasks, phases,
        title="FULL REALDASH TEST  (ECU -> RealDash, passive listener)",
        subtitle="Inject 0x3EF/0x3F0/0x3F1; watch the RealDash screen.",
        loop=args.loop, verbose=args.verbose)


# --- simulate-switchboard --------------------------------------------------

def cmd_simulate_switchboard(args: argparse.Namespace) -> None:
    bus = open_bus(args)
    print(f"Simulating switchboard TX (0x640/0x641/0x642) on "
          f"{args.interface}/{args.channel}. Ctrl-C to stop.")
    heartbeat = {"v": 0}

    def analog_1_4(t: float) -> Tuple[int, bytes]:
        return f.ID_SB_ANALOG_1_4, f.encode_sb_analog(
            int(sine(t, 30.0, 500, 4500)),       # cabin temp thermistor
            int(triangle(t, 6.0, 0, 5000)),      # cruise stalk ladder sweep
            int(sine(t, 10.0, 0, 5000)),
            int(triangle(t, 15.0, 0, 5000)),
        )

    def analog_5_8(t: float) -> Tuple[int, bytes]:
        return f.ID_SB_ANALOG_5_8, f.encode_sb_analog(
            int(sine(t, 12.0, 0, 5000)),
            int(triangle(t, 9.0, 0, 5000)),
            int(sine(t, 14.0, 0, 5000)),
            int(triangle(t, 11.0, 0, 5000)),
        )

    def rotary_sw(t: float) -> Tuple[int, bytes]:
        # Cycle the assigned switch bits one at a time, sweep two rotaries.
        rot = int(t) % 16
        rotaries = (rot, (rot + 4) % 16, 0, 0, 0, 0, 0, 0)
        sw_mask = 0
        if args.toggle_switches:
            sw_slot = int(t // 2) % 6
            sw_mask = (1 << sw_slot) if sw_slot < 5 else 0
        hb = heartbeat["v"] & 0xFF
        heartbeat["v"] += 1
        return f.ID_SB_ROTARY_SW, f.encode_sb_rotary_sw(
            rotaries=rotaries, sw_mask=sw_mask, as_mask=0, ls_mask=0, heartbeat=hb)

    tasks = [
        PeriodicTask(0.050, analog_1_4),
        PeriodicTask(0.050, analog_5_8),
        PeriodicTask(0.050, rotary_sw),
    ]
    try:
        run_scheduler(bus, tasks, args.duration, args.verbose)
    finally:
        bus.shutdown()


# --- inject-ls-command -----------------------------------------------------

def cmd_inject_ls_command(args: argparse.Namespace) -> None:
    bus = open_bus(args)
    data = f.encode_ls_control(args.l1, args.l2, args.l3, args.l4)
    hexd = " ".join(f"{b:02X}" for b in data)
    print(f"Injecting 0x643 low-side control [{hexd}] x{args.count} "
          f"@ {args.period*1000:.0f} ms on {args.interface}/{args.channel}.")
    try:
        for _ in range(args.count):
            send(bus, f.ID_SB_LS_CONTROL, data, verbose=True)
            time.sleep(args.period)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        bus.shutdown()


# --- monitor ---------------------------------------------------------------

def cmd_monitor(args: argparse.Namespace) -> None:
    bus = open_bus(args)
    print(f"Monitoring {args.interface}/{args.channel}. Ctrl-C to stop.\n")
    counts: dict = {}
    try:
        while True:
            msg = bus.recv(timeout=1.0)
            if msg is None:
                continue
            cid = msg.arbitration_id
            counts[cid] = counts.get(cid, 0) + 1
            info = f.FRAME_REGISTRY.get(cid)
            hexd = " ".join(f"{b:02X}" for b in msg.data)
            if info:
                try:
                    decoded = info.decoder(bytes(msg.data))
                except Exception as exc:
                    decoded = f"<decode error: {exc}>"
                fields = ", ".join(
                    f"{k}={_fmt(v)}" for k, v in decoded.items()
                ) if isinstance(decoded, dict) else str(decoded)
                print(f"0x{cid:03X} {info.name:<22} #{counts[cid]:<6} [{hexd}]  {fields}")
            elif not args.known_only:
                print(f"0x{cid:03X} {'(unknown)':<22} #{counts[cid]:<6} [{hexd}]")
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        bus.shutdown()


def _fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:.3f}".rstrip("0").rstrip(".")
    if isinstance(v, list):
        return "[" + ",".join(str(x) for x in v) + "]"
    return str(v)


# --- argument parsing ------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="CAN bench-test tool for the Celica ST185 TrackCluster bus.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--interface", default="socketcan",
                   help="python-can interface: socketcan, slcan, pcan, ... (default: socketcan)")
    p.add_argument("--channel", default="can0",
                   help="channel/device, e.g. can0, /dev/ttyACM0, PCAN_USBBUS1 (default: can0)")
    p.add_argument("--bitrate", type=int, default=1000000,
                   help="bus bitrate in bps; ignored for socketcan (default: 1000000)")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="print every transmitted frame")

    sub = p.add_subparsers(dest="command", required=True)

    se = sub.add_parser("simulate-ecu", help="send ECU TX frames (cluster + RealDash)")
    se.add_argument("--duration", type=float, default=None,
                    help="seconds to run, then stop (default: run until Ctrl-C)")
    se.add_argument("--cluster-only", action="store_true",
                    help="send only the 5 ECU->cluster frames (skip 0x3EF-0x3F1)")
    se.set_defaults(func=cmd_simulate_ecu)

    fc = sub.add_parser("full-cluster",
                        help="guided P4->left/right S3 test: one signal at a time")
    fc.add_argument("--loop", action="store_true",
                    help="repeat the scenario until Ctrl-C")
    fc.set_defaults(func=cmd_full_cluster)

    fr = sub.add_parser("full-realdash",
                        help="guided RealDash test (0x3EF/0x3F0/0x3F1): one signal at a time")
    fr.add_argument("--loop", action="store_true",
                    help="repeat the scenario until Ctrl-C")
    fr.set_defaults(func=cmd_full_realdash)

    ss = sub.add_parser("simulate-switchboard",
                        help="send 0x640/0x641/0x642 with heartbeat")
    ss.add_argument("--duration", type=float, default=None,
                    help="seconds to run, then stop (default: run until Ctrl-C)")
    ss.add_argument("--toggle-switches", action="store_true",
                    help="cycle SW_MASK bits 0-4 one at a time")
    ss.set_defaults(func=cmd_simulate_switchboard)

    il = sub.add_parser("inject-ls-command",
                        help="send 0x643 low-side output command")
    il.add_argument("--l1", type=int, default=0, help="L1 control byte (0-255)")
    il.add_argument("--l2", type=int, default=0, help="L2 control byte (0-255)")
    il.add_argument("--l3", type=int, default=0, help="L3 control byte (0-255)")
    il.add_argument("--l4", type=int, default=0, help="L4 control byte (0-255)")
    il.add_argument("--count", type=int, default=1, help="how many frames to send")
    il.add_argument("--period", type=float, default=0.050,
                    help="seconds between frames (default: 0.050)")
    il.set_defaults(func=cmd_inject_ls_command)

    mon = sub.add_parser("monitor", help="passively decode known frames")
    mon.add_argument("--known-only", action="store_true",
                     help="hide frames not in the allocation table")
    mon.set_defaults(func=cmd_monitor)

    return p


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
