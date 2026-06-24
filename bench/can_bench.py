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
                  duration: Optional[float], verbose: bool) -> None:
    start = time.monotonic()
    for task in tasks:
        task.next_due = start
    try:
        while True:
            now = time.monotonic()
            elapsed = now - start
            if duration is not None and elapsed >= duration:
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
