"""CAN frame encode/decode for the Celica ST185 TrackCluster bus.

Every layout here is derived directly from ``CAN-BUS-ID-ALLOCATION-TABLE.md``.
All multi-byte fields are BigEndian (Link "Custom" stream convention).

Scale/offset convention (matches the allocation table):

    physical_value = raw * scale + offset
    raw            = round((physical_value - offset) / scale)

Each frame has an ``encode_*`` helper that takes physical/engineering values
and returns an 8-byte ``bytes`` payload, and a ``decode_*`` helper that takes a
payload and returns a dict of physical values.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Callable, Dict


# --- CAN IDs ---------------------------------------------------------------

# ECU -> Cluster (immutable, coded-complete)
ID_ENGINE_FAST = 0x3E8      # 10 ms
ID_SPEED_PRESS_IGN = 0x3E9  # 10 ms
ID_LAMBDA = 0x3EA           # 10 ms
ID_GEAR_FUEL = 0x3EB        # 50 ms
ID_ENGINE_PROTECT = 0x3EE   # 50 ms

# Cluster -> ECU (event driven, button press)
ID_BOOST_MAP_SEL = 0x3EC
ID_TC_SEL = 0x3ED

# ECU -> RealDash (new streams)
ID_DRIVE_ASSIST = 0x3EF     # 50 ms
ID_EXT_SENSORS = 0x3F0      # 100 ms
ID_IMU_WARN = 0x3F1         # 50 ms

# Switchboard -> ECU
ID_SB_ANALOG_1_4 = 0x640    # 20 Hz
ID_SB_ANALOG_5_8 = 0x641    # 20 Hz
ID_SB_ROTARY_SW = 0x642     # 20 Hz

# ECU -> Switchboard
ID_SB_LS_CONTROL = 0x643    # event / 50 ms


# --- low-level helpers -----------------------------------------------------

def _enc(value: float, scale: float, offset: float) -> int:
    return int(round((value - offset) / scale))

def _dec(raw: int, scale: float, offset: float) -> float:
    return raw * scale + offset

def _u8(value: int) -> int:
    return max(0, min(255, int(value))) & 0xFF


# --- 0x3E8 Engine Fast -----------------------------------------------------

def encode_engine_fast(rpm: int, map_kpa: int, ect_c: float,
                        iat_c: float, oil_temp_c: float) -> bytes:
    return struct.pack(
        ">HHBBBB",
        _enc(rpm, 1, 0) & 0xFFFF,
        _enc(map_kpa, 1, 0) & 0xFFFF,
        _u8(_enc(ect_c, 1, -50)),
        _u8(_enc(iat_c, 1, -50)),
        _u8(_enc(oil_temp_c, 1, -50)),
        0,  # byte 7 free
    )

def decode_engine_fast(data: bytes) -> Dict[str, float]:
    rpm, mgp, ect, iat, oil, _ = struct.unpack(">HHBBBB", data[:8])
    return {
        "rpm": rpm,
        "map_kpa": mgp,
        "ect_c": _dec(ect, 1, -50),
        "iat_c": _dec(iat, 1, -50),
        "oil_temp_c": _dec(oil, 1, -50),
    }


# --- 0x3E9 Speed / Press / Ign ---------------------------------------------

def encode_speed_press_ign(ign_angle_deg: float, vehicle_speed: int,
                           oil_press: int, fuel_press: int) -> bytes:
    return struct.pack(
        ">HBBBBBB",
        _enc(ign_angle_deg, 0.1, -100) & 0xFFFF,
        _u8(_enc(vehicle_speed, 1, 0)),
        _u8(_enc(oil_press, 1, 0)),
        _u8(_enc(fuel_press, 1, 0)),
        0, 0, 0,  # bytes 5-7 free
    )

def decode_speed_press_ign(data: bytes) -> Dict[str, float]:
    ign, spd, oilp, fuelp, _, _, _ = struct.unpack(">HBBBBBB", data[:8])
    return {
        "ign_angle_deg": _dec(ign, 0.1, -100),
        "vehicle_speed": spd,
        "oil_press": oilp,
        "fuel_press": fuelp,
    }


# --- 0x3EA Lambda ----------------------------------------------------------

def encode_lambda(lambda1: float) -> bytes:
    return struct.pack(">HBBBBBB",
                       _enc(lambda1, 0.001, 0) & 0xFFFF, 0, 0, 0, 0, 0, 0)

def decode_lambda(data: bytes) -> Dict[str, float]:
    (raw,) = struct.unpack(">H", data[:2])
    return {"lambda1": _dec(raw, 0.001, 0)}


# --- 0x3EB Gear / Fuel -----------------------------------------------------

def encode_gear_fuel(gear: int, fuel_level_pct: int) -> bytes:
    # gear: 0=N, 1-6, 7=R (firmware maps 7 -> -1)
    return struct.pack(">BBBBBBBB",
                       _u8(gear), _u8(fuel_level_pct), 0, 0, 0, 0, 0, 0)

def decode_gear_fuel(data: bytes) -> Dict[str, float]:
    gear, fuel = data[0], data[1]
    return {"gear": gear, "fuel_level_pct": fuel}


# --- 0x3EE Engine Protect --------------------------------------------------

def encode_engine_protect(knock: int = 0, ignition_cut: int = 0,
                          fuel_cut: int = 0, boost_cut: int = 0,
                          sensor_error: int = 0, throttle_error: int = 0) -> bytes:
    return struct.pack(">BBBBBBBB",
                       _u8(knock), _u8(ignition_cut), _u8(fuel_cut),
                       _u8(boost_cut), _u8(sensor_error), _u8(throttle_error),
                       0, 0)

def decode_engine_protect(data: bytes) -> Dict[str, float]:
    return {
        "knock": data[0],
        "ignition_cut": data[1],
        "fuel_cut": data[2],
        "boost_cut": data[3],
        "sensor_error": data[4],
        "throttle_error": data[5],
    }


# --- 0x3EC / 0x3ED Cluster selections (DLC 1) ------------------------------

def encode_boost_map_selection(index: int) -> bytes:
    return bytes([_u8(index)])

def decode_boost_map_selection(data: bytes) -> Dict[str, float]:
    return {"boost_map_index": data[0]}

def encode_tc_selection(index: int) -> bytes:
    return bytes([_u8(index)])

def decode_tc_selection(data: bytes) -> Dict[str, float]:
    return {"tc_setting_index": data[0]}


# --- 0x3EF Drive Assist & Status -------------------------------------------

def encode_drive_assist(target_lambda: float, throttle_pct: int,
                        tc_setting: int, tc_intervention_pct: int,
                        boost_map_index: int, cruise_state: int,
                        ac_status: int) -> bytes:
    return struct.pack(
        ">HBBBBBB",
        _enc(target_lambda, 0.001, 0) & 0xFFFF,
        _u8(throttle_pct),
        _u8(tc_setting),
        _u8(tc_intervention_pct),
        _u8(boost_map_index),
        _u8(cruise_state),
        _u8(ac_status),
    )

def decode_drive_assist(data: bytes) -> Dict[str, float]:
    tl, thr, tc, tci, bmi, cruise, ac = struct.unpack(">HBBBBBB", data[:8])
    return {
        "target_lambda": _dec(tl, 0.001, 0),
        "throttle_pct": thr,
        "tc_setting": tc,
        "tc_intervention_pct": tci,
        "boost_map_index": bmi,
        "cruise_state": cruise,
        "ac_status": ac,
    }


# --- 0x3F0 Extended Sensors ------------------------------------------------

def encode_ext_sensors(fuel_temp_c: float, engine_load_pct: int,
                       coolant_press_kpa: int, ethanol_pct: int,
                       charge_pipe_iat_c: float, cabin_temp_c: float,
                       turbo_speed_rpm: int, trigger_error_count: int) -> bytes:
    return struct.pack(
        ">BBBBBBBB",
        _u8(_enc(fuel_temp_c, 1, -50)),
        _u8(engine_load_pct),
        _u8(coolant_press_kpa),
        _u8(ethanol_pct),
        _u8(_enc(charge_pipe_iat_c, 1, -50)),
        _u8(_enc(cabin_temp_c, 1, -50)),
        _u8(_enc(turbo_speed_rpm, 100, 0)),
        _u8(trigger_error_count),
    )

def decode_ext_sensors(data: bytes) -> Dict[str, float]:
    ft, load, cp, eth, cpiat, cabin, turbo, trig = struct.unpack(">BBBBBBBB", data[:8])
    return {
        "fuel_temp_c": _dec(ft, 1, -50),
        "engine_load_pct": load,
        "coolant_press_kpa": cp,
        "ethanol_pct": eth,
        "charge_pipe_iat_c": _dec(cpiat, 1, -50),
        "cabin_temp_c": _dec(cabin, 1, -50),
        "turbo_speed_rpm": _dec(turbo, 100, 0),
        "trigger_error_count": trig,
    }


# --- 0x3F1 IMU & Extended Warnings -----------------------------------------

# Extended Warnings bitmask (byte 6)
WARN_FLAT_SHIFT = 1 << 0
WARN_RADIATOR_FAN = 1 << 1
WARN_LOW_FUEL = 1 << 2
WARN_HIGH_COOLANT_PRESS = 1 << 3
WARN_LOW_OIL_PRESS = 1 << 4
WARN_SWITCHBOARD_COMM_FAULT = 1 << 5

def encode_imu_warn(accel_x_g: float, accel_y_g: float, accel_z_g: float,
                    warnings: int = 0) -> bytes:
    return struct.pack(
        ">hhhBB",
        _enc(accel_x_g, 0.1, 0),
        _enc(accel_y_g, 0.1, 0),
        _enc(accel_z_g, 0.1, 0),
        _u8(warnings),
        0,  # byte 7 reserved
    )

def decode_imu_warn(data: bytes) -> Dict[str, float]:
    ax, ay, az, warn, _ = struct.unpack(">hhhBB", data[:8])
    return {
        "accel_x_g": _dec(ax, 0.1, 0),
        "accel_y_g": _dec(ay, 0.1, 0),
        "accel_z_g": _dec(az, 0.1, 0),
        "warnings": warn,
    }


# --- 0x640 / 0x641 Switchboard analog inputs -------------------------------

def encode_sb_analog(mv0: int, mv1: int, mv2: int, mv3: int) -> bytes:
    def clamp(mv: int) -> int:
        return max(0, min(5000, int(mv))) & 0xFFFF
    return struct.pack(">HHHH", clamp(mv0), clamp(mv1), clamp(mv2), clamp(mv3))

def decode_sb_analog(data: bytes, base_channel: int = 1) -> Dict[str, float]:
    a, b, c, d = struct.unpack(">HHHH", data[:8])
    return {
        f"analog_{base_channel}_mv": a,
        f"analog_{base_channel + 1}_mv": b,
        f"analog_{base_channel + 2}_mv": c,
        f"analog_{base_channel + 3}_mv": d,
    }


# --- 0x642 Switchboard rotary / switch / heartbeat -------------------------

# SW_MASK bit assignments (allocation table section 5)
SW_EVAP_CORE = 1 << 0
SW_AC_REQUEST = 1 << 1
SW_CRUISE_ACTIVE = 1 << 2
SW_CRUISE_SET_ACCEL = 1 << 3
SW_CRUISE_RESUME_DECEL = 1 << 4

def encode_sb_rotary_sw(rotaries=(0, 0, 0, 0, 0, 0, 0, 0),
                        sw_mask: int = 0, as_mask: int = 0,
                        ls_mask: int = 0, heartbeat: int = 0) -> bytes:
    r = list(rotaries) + [0] * (8 - len(rotaries))
    r = [v & 0x0F for v in r[:8]]
    byte0 = (r[0] << 4) | r[1]
    byte1 = (r[2] << 4) | r[3]
    byte2 = (r[4] << 4) | r[5]
    byte3 = (r[6] << 4) | r[7]
    return bytes([byte0, byte1, byte2, byte3,
                  _u8(sw_mask), _u8(as_mask), _u8(ls_mask), _u8(heartbeat)])

def decode_sb_rotary_sw(data: bytes) -> Dict[str, float]:
    rotaries = []
    for i in range(4):
        rotaries.append((data[i] >> 4) & 0x0F)
        rotaries.append(data[i] & 0x0F)
    return {
        "rotaries": rotaries,
        "sw_mask": data[4],
        "as_mask": data[5],
        "ls_mask": data[6],
        "heartbeat": data[7],
    }


# --- 0x643 Low-side output control (ECU -> Switchboard) --------------------

def encode_ls_control(l1: int = 0, l2: int = 0, l3: int = 0, l4: int = 0) -> bytes:
    return struct.pack(">BBBBBBBB",
                       _u8(l1), _u8(l2), _u8(l3), _u8(l4), 0, 0, 0, 0)

def decode_ls_control(data: bytes) -> Dict[str, float]:
    return {"l1": data[0], "l2": data[1], "l3": data[2], "l4": data[3]}


# --- frame registry (for the monitor) --------------------------------------

@dataclass
class FrameInfo:
    can_id: int
    name: str
    decoder: Callable[[bytes], Dict[str, float]]


FRAME_REGISTRY: Dict[int, FrameInfo] = {
    ID_ENGINE_FAST: FrameInfo(ID_ENGINE_FAST, "Engine Fast", decode_engine_fast),
    ID_SPEED_PRESS_IGN: FrameInfo(ID_SPEED_PRESS_IGN, "Speed/Press/Ign", decode_speed_press_ign),
    ID_LAMBDA: FrameInfo(ID_LAMBDA, "Lambda", decode_lambda),
    ID_GEAR_FUEL: FrameInfo(ID_GEAR_FUEL, "Gear/Fuel", decode_gear_fuel),
    ID_ENGINE_PROTECT: FrameInfo(ID_ENGINE_PROTECT, "Engine Protect", decode_engine_protect),
    ID_BOOST_MAP_SEL: FrameInfo(ID_BOOST_MAP_SEL, "Boost Map Selection", decode_boost_map_selection),
    ID_TC_SEL: FrameInfo(ID_TC_SEL, "TC Selection", decode_tc_selection),
    ID_DRIVE_ASSIST: FrameInfo(ID_DRIVE_ASSIST, "Drive Assist & Status", decode_drive_assist),
    ID_EXT_SENSORS: FrameInfo(ID_EXT_SENSORS, "Extended Sensors", decode_ext_sensors),
    ID_IMU_WARN: FrameInfo(ID_IMU_WARN, "IMU & Ext Warnings", decode_imu_warn),
    ID_SB_ANALOG_1_4: FrameInfo(ID_SB_ANALOG_1_4, "SB Analog 1-4", lambda d: decode_sb_analog(d, 1)),
    ID_SB_ANALOG_5_8: FrameInfo(ID_SB_ANALOG_5_8, "SB Analog 5-8", lambda d: decode_sb_analog(d, 5)),
    ID_SB_ROTARY_SW: FrameInfo(ID_SB_ROTARY_SW, "SB Rotary/Switch/HB", decode_sb_rotary_sw),
    ID_SB_LS_CONTROL: FrameInfo(ID_SB_LS_CONTROL, "SB Low-Side Control", decode_ls_control),
}
