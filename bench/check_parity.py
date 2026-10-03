"""CAN contract parity check - every copy of the wire layout must agree.

    python bench/check_parity.py          exit 0 = all agree, 1 = a mismatch (listed per field)

Standard library only (runs in CI with no pip step). What it compares:

  link_g4x_can_setup.json   ECU broadcast 0x3E8-0x3F1. ENCODE convention:
                            raw = value * scale + offset  (what PCLink asks for)
  link_g4x_can_setup.lcs    same frames. DECODE convention: value = raw * Scale + Offset
  CAN-BUS-ID-ALLOCATION-TABLE.md   same frames + switchboard, DECODE convention
  bench/frames.py           encode_*/decode_* round-trip at a test value per field,
                            WARN_* bits, SW_* bits
  link_g4x_realdash.xml     RealDash frames: offset/length/signed/conversion, warn bits
  apps/trackcluster-can-sender/ui/index.html   both device profiles: byte/len/signed/bit,
                            and the RealDash profile's toRaw() at the same test value
  switchboard_frames.json   0x640-0x643 vs frames.py and the ID table

D2 (2026-10-02): the JSON stays in PCLink's encode form and everything else uses decode.
The conversion is decode_scale = 1 / scale, decode_offset = -offset / scale; this script
applies it, so a scale written in the wrong convention shows up as a mismatch.

The cluster firmware (center-cluster-esp32-p4 main/canbus.c) is frozen and lives in
another repo, so CI cannot read it. Reconcile against it by hand on any CAN change
(docs/RECONCILIATION-RULES.md Rule 2).
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bench"))
sys.dont_write_bytecode = True   # always read frames.py itself, never a cached .pyc
import frames as F  # noqa: E402

ERR: list = []


def err(where: str, msg: str) -> None:
    ERR.append("%-34s %s" % (where, msg))


def close(a, b, tol=1e-9) -> bool:
    return a is not None and b is not None and math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=tol)


def rd(path: str) -> str:
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return fh.read()


def hexid(s) -> int:
    return int(str(s), 16) if str(s).lower().startswith("0x") else int(s)


# --- 1. canonical model from link_g4x_can_setup.json ----------------------------------

def load_json_contract():
    j = json.loads(rd("link_g4x_can_setup.json"))
    if j.get("byte_order") != "BigEndian":
        err("json", "byte_order is %r, expected BigEndian" % j.get("byte_order"))
    model = {}
    for s in j["streams"]:
        fid = hexid(s["id"])
        fields = {}
        for c in s["channels"]:
            if not c.get("length"):
                continue
            sc, of = float(c.get("scale", 1)), float(c.get("offset", 0))
            fields[c["byte"]] = {
                "name": c["name"], "length": c["length"], "signed": bool(c.get("signed")),
                "enc_scale": sc, "enc_offset": of,
                "dec_scale": 1.0 / sc, "dec_offset": (-of / sc) + 0.0,   # +0.0: no "-0" in messages
                "note": c.get("note", ""),
            }
        model[fid] = {"name": s["name"], "cycle": s["cycle_ms"], "fields": fields}
    return model


def enc_raw(field, value):
    return int(round(value * field["enc_scale"] + field["enc_offset"]))


def raw_at(payload: bytes, byte: int, length: int, signed: bool) -> int:
    return int.from_bytes(payload[byte:byte + length], "big", signed=signed)


# --- 2. bench/frames.py: encode/decode round-trip per field ----------------------------
# (byte, decode key, test value) in the encoder's argument order.
ENC = {
    0x3E8: (F.encode_engine_fast, F.decode_engine_fast,
            [(0, "rpm", 6500), (2, "map_kpa", 180), (4, "ect_c", 90), (5, "iat_c", 40), (6, "oil_temp_c", 110)]),
    0x3E9: (F.encode_speed_press_ign, F.decode_speed_press_ign,
            [(0, "ign_angle_deg", 15.5), (2, "vehicle_speed", 120), (3, "oil_press", 400), (5, "fuel_press", 350)]),
    0x3EA: (F.encode_lambda, F.decode_lambda, [(0, "lambda1", 0.85)]),
    0x3EB: (F.encode_gear_fuel, F.decode_gear_fuel, [(0, "gear", 3), (1, "fuel_level_pct", 60)]),
    0x3EE: (F.encode_engine_protect, F.decode_engine_protect,
            [(0, "knock", 1), (1, "ignition_cut", 2), (2, "fuel_cut", 3), (3, "boost_cut", 4),
             (4, "sensor_error", 5), (5, "throttle_error", 6)]),
    0x3EF: (F.encode_drive_assist, F.decode_drive_assist,
            [(0, "target_lambda", 0.82), (2, "throttle_pct", 55), (3, "tc_setting", 2),
             (4, "tc_intervention_pct", 30), (5, "boost_map_index", 1), (6, "cruise_state", 2),
             (7, "ac_status", 1)]),
    0x3F0: (F.encode_ext_sensors, F.decode_ext_sensors,
            [(0, "fuel_temp_c", 35), (1, "engine_load_pct", 70), (2, "coolant_press_kpa", 120),
             (4, "ethanol_pct", 85), (5, "charge_pipe_iat_c", 45), (6, "turbo_speed_rpm", 150000),
             (7, "trigger_error_count", 3)]),
    0x3F1: (F.encode_imu_warn, F.decode_imu_warn,
            [(0, "accel_x_g", -1.5), (2, "accel_y_g", 0.8), (4, "accel_z_g", 1.0), (6, "warnings", 0x25)]),
}
TEST_VALUE = {(fid, b): v for fid, (_, _, args) in ENC.items() for b, _, v in args}

ID_CONST = {0x3E8: "ID_ENGINE_FAST", 0x3E9: "ID_SPEED_PRESS_IGN", 0x3EA: "ID_LAMBDA",
            0x3EB: "ID_GEAR_FUEL", 0x3EE: "ID_ENGINE_PROTECT", 0x3EF: "ID_DRIVE_ASSIST",
            0x3F0: "ID_EXT_SENSORS", 0x3F1: "ID_IMU_WARN"}


def check_frames_py(model):
    if set(model) != set(ENC):
        err("json vs frames.py", "frame sets differ: json %s, frames.py %s"
            % (sorted(map(hex, model)), sorted(map(hex, ENC))))
    for fid, const in ID_CONST.items():
        if getattr(F, const, None) != fid:
            err("frames.py", "%s should be 0x%03X" % (const, fid))
    for fid, (enc, dec, args) in ENC.items():
        if fid not in model:
            continue
        where = "frames.py 0x%03X" % fid
        fields = model[fid]["fields"]
        if set(fields) != {b for b, _, _ in args}:
            err(where, "fields at bytes %s, json has %s" % (sorted(b for b, _, _ in args), sorted(fields)))
        payload = enc(*[v for _, _, v in args])
        if len(payload) != 8:
            err(where, "payload is %d bytes, expected 8" % len(payload))
        decoded = dec(payload)
        for b, key, v in args:
            f = fields.get(b)
            if not f:
                continue
            got = raw_at(payload, b, f["length"], f["signed"])
            want = enc_raw(f, v)
            if got != want:
                err(where, "byte %d %-22s raw %d, json says %d (value %s)" % (b, f["name"], got, want, v))
            back = decoded.get(key)
            if not close(back, v, tol=abs(f["dec_scale"]) / 2 + 1e-9):
                err(where, "byte %d %-22s decode gives %r for %r" % (b, key, back, v))


# --- 3. link_g4x_can_setup.lcs (decode convention) --------------------------------------

def check_lcs(model):
    root = ET.fromstring(rd("link_g4x_can_setup.lcs").encode("utf-8"))
    seen = set()
    for ch in root.iter("Channel"):
        fid = hexid(ch.get("ID"))
        seen.add(fid)
        where = ".lcs 0x%03X" % fid
        m = model.get(fid)
        if not m:
            err(where, "channel not in link_g4x_can_setup.json")
            continue
        if int(ch.get("CycleTime")) != m["cycle"]:
            err(where, "CycleTime %s, json cycle_ms %s" % (ch.get("CycleTime"), m["cycle"]))
        got = {}
        for p in ch.iter("Parameter"):
            sb, ln = int(p.get("StartBit")), int(p.get("Length"))
            if sb % 8 or ln % 8:
                err(where, "%s StartBit/Length not byte aligned" % p.get("Name"))
                continue
            got[sb // 8] = p
            if p.get("ByteOrder") != "BigEndian":
                err(where, "%s ByteOrder %s" % (p.get("Name"), p.get("ByteOrder")))
        if set(got) != set(m["fields"]):
            err(where, "parameters at bytes %s, json has %s" % (sorted(got), sorted(m["fields"])))
        for b, p in got.items():
            f = m["fields"].get(b)
            if not f:
                continue
            if int(p.get("Length")) != f["length"] * 8:
                err(where, "byte %d %s Length %s bits, json %d bytes" % (b, p.get("Name"), p.get("Length"), f["length"]))
            if (p.get("Signed", "false").lower() == "true") != f["signed"]:
                err(where, "byte %d %s Signed=%s, json signed=%s" % (b, p.get("Name"), p.get("Signed"), f["signed"]))
            if not close(p.get("Scale"), f["dec_scale"]) or not close(p.get("Offset"), f["dec_offset"]):
                err(where, "byte %d %s Scale/Offset %s/%s, json decodes to %g/%g"
                    % (b, p.get("Name"), p.get("Scale"), p.get("Offset"), f["dec_scale"], f["dec_offset"]))
    if seen != set(model):
        err(".lcs", "channel set %s differs from json %s" % (sorted(map(hex, seen)), sorted(map(hex, model))))


# --- 4. CAN-BUS-ID-ALLOCATION-TABLE.md -----------------------------------------------------

def md_tables(text):
    """Yield (heading, [rows as list of cells]) for every markdown table under a ### heading."""
    head, rows = None, []
    for ln in text.splitlines():
        if ln.startswith("#"):
            if head and rows:
                yield head, rows
            head, rows = ln.strip("# ").strip(), []
        elif ln.startswith("|"):
            cells = [c.strip().strip("*").strip() for c in ln.strip().strip("|").split("|")]
            if not all(set(c) <= set("-: ") for c in cells):
                rows.append(cells)
        elif rows and head:
            yield head, rows
            rows = []
    if head and rows:
        yield head, rows


def num(s, default):
    s = s.replace("−", "-").strip()
    if s in ("", "—", "-"):
        return default
    try:
        return float(s)
    except ValueError:
        return None


def byte_span(s):
    s = s.replace("–", "-").replace("—", "-")
    m = re.match(r"^(\d+)(?:-(\d+))?$", s)
    if not m:
        return None
    a = int(m.group(1))
    return a, int(m.group(2) or a) - a + 1


def check_id_table(model, sb):
    text = rd("CAN-BUS-ID-ALLOCATION-TABLE.md")
    master, sections = {}, {}
    for head, rows in md_tables(text):
        hdr = rows[0]
        if hdr[:2] == ["CAN ID (hex)", "CAN ID (dec)"]:
            for r in rows[1:]:
                m = re.match(r"^(0x[0-9A-Fa-f]{3})$", r[0])
                if m:
                    master[hexid(m.group(1))] = r
        m = re.match(r"^(0x[0-9A-Fa-f]{3})\b", head)
        if m:   # first table under the heading is the byte layout; later ones are extras
            sections.setdefault(hexid(m.group(1)), (head, rows))
    for fid, mdl in model.items():
        where = "ID table 0x%03X" % fid
        r = master.get(fid)
        if not r:
            err(where, "missing from the master table")
        else:
            cyc = re.search(r"(\d+)\s*ms", r[4])
            if not cyc or int(cyc.group(1)) != mdl["cycle"]:
                err(where, "master-table cycle %r, json %s ms" % (r[4], mdl["cycle"]))
        sec = sections.get(fid)
        if not sec:
            err(where, "no ### section")
            continue
        head, rows = sec
        cyc = re.search(r"CycleTime\s*(\d+)\s*ms", head)
        if not cyc or int(cyc.group(1)) != mdl["cycle"]:
            err(where, "section heading cycle %r, json %s ms" % (head, mdl["cycle"]))
        hdr = rows[0]
        ib = 0
        it = hdr.index("Type") if "Type" in hdr else None
        isc = hdr.index("Scale") if "Scale" in hdr else None
        iof = hdr.index("Offset") if "Offset" in hdr else None
        got = {}
        for r in rows[1:]:
            span = byte_span(r[ib])
            if not span or r[1] in ("—", "-", ""):
                continue
            got[span[0]] = (span[1], r)
        if set(got) != set(mdl["fields"]):
            err(where, "fields at bytes %s, json has %s" % (sorted(got), sorted(mdl["fields"])))
        for b, (ln, r) in got.items():
            f = mdl["fields"].get(b)
            if not f:
                continue
            if ln != f["length"]:
                err(where, "byte %d %s spans %d bytes, json %d" % (b, r[1], ln, f["length"]))
            if it is not None:
                signed = r[it].lower().startswith("int")
                if signed != f["signed"]:
                    err(where, "byte %d %s type %r, json signed=%s" % (b, r[1], r[it], f["signed"]))
            sc = num(r[isc], 1.0) if isc is not None else 1.0
            of = num(r[iof], 0.0) if iof is not None else 0.0
            if not close(sc, f["dec_scale"]) or not close(of, f["dec_offset"]):
                err(where, "byte %d %s scale/offset %s/%s, json decodes to %g/%g"
                    % (b, r[1], sc, of, f["dec_scale"], f["dec_offset"]))
    # switchboard section 5 vs switchboard_frames.json
    for fr in sb["frames"]:
        fid = hexid(fr["id"])
        where = "ID table 0x%03X" % fid
        if fid not in master:
            err(where, "missing from the master table")
        sec = next((v for k, v in sections.items() if k == fid), None)
        if not sec:
            err(where, "no ### section")
            continue
        rows = sec[1]
        spans = {}
        for r in rows[1:]:
            span = byte_span(r[0])
            if span:
                spans[span[0]] = span[1]
        for c in fr["channels"]:
            if c.get("length") and spans.get(c["byte"]) not in (c["length"],):
                if not (fid == 0x643 and c["byte"] == 4):
                    err(where, "byte %d %s: table spans %s, switchboard_frames.json %d"
                        % (c["byte"], c["name"], spans.get(c["byte"]), c["length"]))
    return text


# --- 5. warning bits (0x3F1 byte 6) ------------------------------------------------------
WARN_KEYWORD = {"WARN_FLAT_SHIFT": "flat", "WARN_RADIATOR_FAN": "fan", "WARN_LOW_FUEL": "fuel",
                "WARN_HIGH_COOLANT_PRESS": "coolant", "WARN_LOW_OIL_PRESS": "oil",
                "WARN_SWITCHBOARD_COMM_FAULT": "switchboard"}


def warn_bits():
    bits = {}
    for name in dir(F):
        if name.startswith("WARN_"):
            v = getattr(F, name)
            if v & (v - 1) or not v:
                err("frames.py", "%s = %r is not a single bit" % (name, v))
                continue
            if name not in WARN_KEYWORD:
                err("check_parity.py", "new %s - add it to WARN_KEYWORD" % name)
                continue
            bits[v.bit_length() - 1] = WARN_KEYWORD[name]
    return bits


def check_warn_text(where, text, bits):
    found = {int(b): t.lower() for b, t in re.findall(r"bit\s*(\d)\s*=\s*([^,;|]+)", text)}
    for b, kw in bits.items():
        if kw not in found.get(b, ""):
            err(where, "bit%d should be the %r warning, text says %r" % (b, kw, found.get(b)))
    for b in found:
        if b not in bits and "spare" not in found[b]:
            err(where, "bit%d %r has no WARN_* constant in frames.py" % (b, found[b]))


# --- 6. link_g4x_realdash.xml --------------------------------------------------------------
REALDASH_FRAMES = {0x3EB, 0x3EF, 0x3F0, 0x3F1}   # D5: RealDash also reads 0x3EB (gear only)


def conv(c):
    c = (c or "V").replace(" ", "")
    if c == "V":
        return 1.0, 0.0
    m = re.match(r"^V\*([\d.]+)$", c)
    if m:
        return float(m.group(1)), 0.0
    m = re.match(r"^V([+-])([\d.]+)$", c)
    if m:
        return 1.0, float(m.group(2)) * (1 if m.group(1) == "+" else -1)
    m = re.match(r"^V\*([\d.]+)([+-])([\d.]+)$", c)
    if m:
        return float(m.group(1)), float(m.group(3)) * (1 if m.group(2) == "+" else -1)
    return None, None


def check_xml(model, bits):
    root = ET.fromstring(rd("link_g4x_realdash.xml").encode("utf-8"))
    seen = set()
    for fr in root.iter("frame"):
        fid = int(fr.get("id"), 0)
        seen.add(fid)
        where = "RealDash XML 0x%03X" % fid
        if fr.get("endianness") != "big":
            err(where, "endianness %r, expected big" % fr.get("endianness"))
        m = model.get(fid)
        if not m:
            err(where, "frame not in link_g4x_can_setup.json")
            continue
        covered = set()
        for v in fr.iter("value"):
            off, ln = int(v.get("offset")), int(v.get("length", "1"))
            name = v.get("name")
            if v.get("startbit") is not None:
                b = int(v.get("startbit"))
                if fid != 0x3F1 or off != 6:
                    err(where, "%s: bit value outside 0x3F1 byte 6" % name)
                elif bits.get(b) is None or bits[b] not in name.lower():
                    err(where, "%s on bit %d, frames.py says bit %d is %r" % (name, b, b, bits.get(b)))
                covered.add(off)
                continue
            f = m["fields"].get(off)
            if not f:
                err(where, "%s at byte %d - json has no field there" % (name, off))
                continue
            covered.add(off)
            if ln != f["length"]:
                err(where, "%s length %d, json %d" % (name, ln, f["length"]))
            if (v.get("signed") == "true") != f["signed"]:
                err(where, "%s signed=%s, json %s" % (name, v.get("signed"), f["signed"]))
            sc, of = conv(v.get("conversion"))
            if sc is None:
                err(where, "%s conversion %r not understood" % (name, v.get("conversion")))
            elif not close(sc, f["dec_scale"]) or not close(of, f["dec_offset"]):
                err(where, "%s conversion %r = %g/%g, json decodes to %g/%g"
                    % (name, v.get("conversion"), sc, of, f["dec_scale"], f["dec_offset"]))
        if fid != 0x3EB and covered != set(m["fields"]):
            err(where, "covers bytes %s, json frame has %s" % (sorted(covered), sorted(m["fields"])))
    if seen != REALDASH_FRAMES:
        err("RealDash XML", "frames %s, expected %s" % (sorted(map(hex, seen)), sorted(map(hex, REALDASH_FRAMES))))
    return seen


# --- 7. sender UI device profiles ----------------------------------------------------------
CLUSTER_FRAMES = {0x3E8, 0x3E9, 0x3EA, 0x3EB, 0x3EE}   # what main/canbus.c decodes
CLUSTER_SRC = os.environ.get("CLUSTER_CANBUS_C") or os.path.join(
    os.path.dirname(ROOT), "center-cluster-esp32-p4", "main", "canbus.c")


def check_cluster_source():
    """Local only: if the frozen cluster repo sits next to this one, confirm the set of
    frames it decodes still equals CLUSTER_FRAMES. Skipped silently in CI."""
    if not os.path.exists(CLUSTER_SRC):
        return False
    src = open(CLUSTER_SRC, encoding="utf-8", errors="replace").read()
    got = {int(x, 16) for x in re.findall(r"case\s+(0x[0-9A-Fa-f]+)\s*:\s*decode_", src)}
    if got != CLUSTER_FRAMES:
        err("cluster canbus.c", "decodes %s, check_parity expects %s"
            % (sorted(map(hex, got)), sorted(map(hex, CLUSTER_FRAMES))))
    return True


def js_eval(expr, v):
    py = expr.replace("Math.round(", "_jsround(").replace("Number(", "float(")
    if re.search(r"[^\w\s().*/+\-,]", py):
        return None
    try:
        return eval(py, {"__builtins__": {}}, {"_jsround": lambda x: math.floor(x + 0.5), "float": float, "v": v})
    except Exception:
        return None


def ui_profile(text, const):
    m = re.search(r"const\s+%s\s*=\s*\[(.*?)\n\];" % const, text, re.S)
    if not m:
        err("sender UI", "%s not found" % const)
        return {}
    body, out = m.group(1), {}
    chunks = re.split(r"\bid:\s*'(0x[0-9A-Fa-f]{3})'", body)
    for i in range(1, len(chunks), 2):
        fid, chunk = hexid(chunks[i]), chunks[i + 1]
        per = re.search(r"period:\s*(\d+)", chunk)
        sigs = []
        for s in re.split(r"\{\s*key:", chunk)[1:]:
            key = re.match(r"\s*'([^']+)'", s).group(1)
            b = re.search(r"\bbyte:\s*(\d+)", s)
            ln = re.search(r"\blen:\s*(\d+)", s)
            bit = re.search(r"\bbit:\s*(\d+)", s)
            tr = re.search(r"toRaw:\s*\(v\)\s*=>\s*(.+?)\s*\}", s, re.S)
            sigs.append({"key": key, "byte": int(b.group(1)) if b else None,
                         "len": int(ln.group(1)) if ln else None,
                         "signed": bool(re.search(r"\bsigned:\s*true", s)),
                         "bit": int(bit.group(1)) if bit else None,
                         "isBool": bool(re.search(r"\bisBool:\s*true", s)),
                         "toRaw": tr.group(1).rstrip(",").strip() if tr else None})
        out[fid] = {"period": int(per.group(1)) if per else None, "signals": sigs}
    return out


def check_ui(model, bits, xml_frames):
    text = rd("apps/trackcluster-can-sender/ui/index.html")
    for const, want, check_raw in (("FRAMES_REALDASH", xml_frames, True),
                                   ("FRAMES_CLUSTER", CLUSTER_FRAMES, False)):
        prof = ui_profile(text, const)
        if set(prof) != want:
            err("sender UI " + const, "frames %s, expected %s" % (sorted(map(hex, prof)), sorted(map(hex, want))))
        for fid, p in prof.items():
            where = "sender UI %s 0x%03X" % (const.split("_")[1].lower(), fid)
            m = model.get(fid)
            if not m:
                err(where, "frame not in link_g4x_can_setup.json")
                continue
            if p["period"] != m["cycle"]:
                err(where, "period %s ms, json cycle %s ms" % (p["period"], m["cycle"]))
            for s in p["signals"]:
                if s["bit"] is not None:
                    if fid != 0x3F1 or s["byte"] != 6 or bits.get(s["bit"]) is None:
                        err(where, "%s: bit %s at byte %s is not a known warning bit" % (s["key"], s["bit"], s["byte"]))
                    continue
                f = m["fields"].get(s["byte"])
                if not f:
                    err(where, "%s at byte %s - json has no field there" % (s["key"], s["byte"]))
                    continue
                if s["len"] != f["length"] or s["signed"] != f["signed"]:
                    err(where, "%s len/signed %s/%s, json %s/%s" % (s["key"], s["len"], s["signed"], f["length"], f["signed"]))
                tv = TEST_VALUE.get((fid, s["byte"]))
                if check_raw and s["toRaw"] and not s["isBool"] and tv is not None:
                    got = js_eval(s["toRaw"], tv)
                    if got is None:
                        err(where, "%s toRaw %r not understood" % (s["key"], s["toRaw"]))
                    elif int(got) != enc_raw(f, tv):
                        err(where, "%s toRaw(%s) = %s, json says %d" % (s["key"], tv, got, enc_raw(f, tv)))


# --- 8. switchboard_frames.json vs frames.py and the ID table -------------------------------

def check_switchboard(sb, id_table_text):
    where = "switchboard_frames.json"
    ids = {hexid(fr["id"]): fr for fr in sb["frames"]}
    consts = {0x640: "ID_SB_ANALOG_1_4", 0x641: "ID_SB_ANALOG_5_8", 0x642: "ID_SB_ROTARY_SW", 0x643: "ID_SB_LS_CONTROL"}
    if set(ids) != set(consts):
        err(where, "frames %s, expected 0x640-0x643" % sorted(map(hex, ids)))
    for fid, c in consts.items():
        if getattr(F, c, None) != fid:
            err("frames.py", "%s should be 0x%03X" % (c, fid))
    if sb.get("byte_order") != "BigEndian":
        err(where, "byte_order should be BigEndian")
    # analog frames: four u16 BE mV values
    for fid, base in ((0x640, 1), (0x641, 5)):
        fr = ids.get(fid)
        if not fr:
            continue
        pay = F.encode_sb_analog(1000, 2000, 3000, 4000)
        dec = F.decode_sb_analog(pay, base)
        for i, c in enumerate(x for x in fr["channels"] if x.get("length")):
            if c["byte"] != 2 * i or c["length"] != 2:
                err(where, "0x%03X %s at byte %d len %d, frames.py packs u16 at byte %d"
                    % (fid, c["name"], c["byte"], c["length"], 2 * i))
            if raw_at(pay, c["byte"], 2, False) != 1000 * (i + 1):
                err("frames.py", "0x%03X analog %d not u16 BE at byte %d" % (fid, base + i, c["byte"]))
            if dec.get("analog_%d_mv" % (base + i)) != 1000 * (i + 1):
                err("frames.py", "decode_sb_analog key analog_%d_mv wrong" % (base + i))
    # 0x642: nibble rotaries, SW/AS/LS masks, heartbeat
    pay = F.encode_sb_rotary_sw(rotaries=(1, 2, 3, 4, 5, 6, 7, 8), sw_mask=0xA5, as_mask=0x5A, ls_mask=0x0F, heartbeat=7)
    if list(pay) != [0x12, 0x34, 0x56, 0x78, 0xA5, 0x5A, 0x0F, 7]:
        err("frames.py", "encode_sb_rotary_sw layout %s != manual layout" % list(pay))
    fr = ids.get(0x642)
    if fr:
        names = {c["byte"]: c["name"] for c in fr["channels"]}
        for b, nm in ((4, "SW_MASK"), (5, "AS_MASK"), (6, "LS_MASK"), (7, "Heartbeat")):
            if nm not in names.get(b, ""):
                err(where, "0x642 byte %d should be %s, is %r" % (b, nm, names.get(b)))
        swc = next((c for c in fr["channels"] if c["byte"] == 4), {})
        assigned = {int(k) for k, v in swc.get("bits", {}).items() if "unassigned" not in v.lower()}
        sw_consts = {getattr(F, n).bit_length() - 1 for n in dir(F) if n.startswith("SW_")}
        if assigned != sw_consts:
            err(where, "SW_MASK assigned bits %s, frames.py SW_* constants %s" % (sorted(assigned), sorted(sw_consts)))
        # ID table SW_MASK assignment table must mark the same bits unassigned
        for m in re.finditer(r"^\|\s*(\d)\s*\|\s*Switch (\d)\s*\|\s*(.+?)\s*\|\s*$", id_table_text, re.M):
            b, txt = int(m.group(1)), m.group(3).lower()
            if ("unassigned" in txt) == (b in assigned):
                err("ID table SW_MASK", "bit %d %r disagrees with switchboard_frames.json" % (b, m.group(3)))
    # 0x643: L1-L4 one byte each, DLC 8 with bytes 4-7 zero
    pay = F.encode_ls_control(1, 2, 3, 4)
    if list(pay) != [1, 2, 3, 4, 0, 0, 0, 0]:
        err("frames.py", "encode_ls_control layout %s, manual is L1-L4 in bytes 0-3" % list(pay))
    fr = ids.get(0x643)
    if fr:
        lb = [c["byte"] for c in fr["channels"] if c.get("length") == 1]
        if lb != [0, 1, 2, 3]:
            err(where, "0x643 control bytes %s, expected [0, 1, 2, 3]" % lb)
        if "ecu" not in fr.get("direction", "").lower().split("->")[0]:
            err(where, "0x643 must be transmitted by the ECU (D4)")


# --- main -----------------------------------------------------------------------------------

def main() -> int:
    model = load_json_contract()
    sb = json.loads(rd("switchboard_frames.json"))
    bits = warn_bits()
    check_frames_py(model)
    check_lcs(model)
    text = check_id_table(model, sb)
    xml_frames = check_xml(model, bits)
    check_ui(model, bits, xml_frames)
    check_switchboard(sb, text)
    cluster_seen = check_cluster_source()
    j3f1 = model.get(0x3F1, {}).get("fields", {}).get(6, {})
    check_warn_text("json 0x3F1 byte 6 note", j3f1.get("note", ""), bits)
    row = re.search(r"^\|\s*6\s*\|\s*Extended Warnings Bitmask.*$", text, re.M)
    check_warn_text("ID table 0x3F1 byte 6", row.group(0) if row else "", bits)
    if ERR:
        print("CAN parity: %d mismatch(es)" % len(ERR))
        for e in ERR:
            print("  " + e)
        return 1
    print("CAN parity OK: %d ECU frames, 4 switchboard frames, %d warning bits - "
          "json / .lcs / frames.py / ID table / RealDash XML / sender UI agree" % (len(model), len(bits)))
    print("cluster canbus.c: " + ("decoded frame set matches (%s)" % CLUSTER_SRC if cluster_seen
                                  else "not found next to this repo - reconcile by hand"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
