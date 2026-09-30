#!/usr/bin/env python3
"""Shopping lists from a live harness.design BOM export.

The `.harness` files in rebuild/ are behind the live looms. Quantities in
NEED-TO-BUY.md, PARTS-LISTS.md and HARNESS-BOM.csv come from a BOM export of
those live looms — never from walking the older drawings.

    python docs/harness/from_live_boms.py --from-export path/to/boms.json
    python docs/harness/from_live_boms.py --check-committed
    python docs/harness/from_live_boms.py --check-export path/to/boms.json

Do not commit the export JSON (it is drawing/loom data). Do not hand-edit the
three generated lists — re-run this script against a new export.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
from collections import OrderedDict, defaultdict
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import buylist

BOM_CSV = os.path.join(HERE, "HARNESS-BOM.csv")
PARTS_MD = os.path.join(HERE, "PARTS-LISTS.md")
BUY_MD = os.path.join(HERE, "NEED-TO-BUY.md")

NOT_A_PART = re.compile(r"^\(|^TBD\b")
FORBIDDEN_PINS = ("AUX4_AC_KILL", "TAM_RTN")
CLUSTER_NAME = "Center Cluster"
EA = "ea"

# One physical DRB102 housing is listed on both letter-halves in the live BOM
# (A-cabin + B-cabin receptacle, A-engine + B-engine plug). Shop one of each
# housing, not two. Per-loom parts lists still show the export quantity on
# each half. Confirmed against the 2026-09-30 export ids below.
ONE_HOUSING = {
    "DRB12-102PAE-L018": ("7AgB", "mED3"),
    "DRB16-102SAE-L018": ("lpq1", "nzvp"),
}

# Manufacturer for display only. Empty when the export did not name one and
# the PN is not a known family already used in this project. Never invented
# as a substitute part number.
PN_MFR = {
    "0413-204-2005": "TE DEUTSCH",
    "0413-214-1205": "TE DEUTSCH",
    "0460-202-1631": "TE DEUTSCH",
    "0460-220-1231": "TE DEUTSCH",
    "0462-201-16141": "TE DEUTSCH",
    "0462-201-1631": "TE DEUTSCH",
    "0462-201-2031": "TE DEUTSCH",
    "0462-203-08141": "TE DEUTSCH",
    "0462-210-1231": "TE DEUTSCH",
    "1 928 403 874": "Bosch",
    "1-1355833-1": "TE Connectivity",
    "1-1355844-1": "TE Connectivity",
    "1-1355877-1": "TE Connectivity",
    "1-1355880-1": "TE Connectivity",
    "1-1393304-0": "TE Connectivity",
    "1-1414147-0": "TE Connectivity",
    "1-1904045-6": "TE Connectivity",
    "114017": "TE DEUTSCH",
    "12052641": "Aptiv",
    "12084200": "Aptiv",
    "12110293": "Aptiv",
    "13519047": "Aptiv",
    "1393310-4": "TE Connectivity",
    "15326426": "Aptiv",
    "15326427": "Aptiv",
    "15419715": "Aptiv",
    "160927-4": "TE Connectivity",
    "2141029-1": "TE Connectivity",
    "280755-4": "TE Connectivity",
    "280756-4": "TE Connectivity",
    "280919-4": "TE Connectivity",
    "282110-1": "TE Connectivity",
    "3-1447221-3": "TE Connectivity",
    "3-1447221-4": "TE Connectivity",
    "4-1437290-0": "TE Connectivity",
    "4-1437290-1": "TE Connectivity",
    "4-1904124-2": "TE Connectivity",
    "42281-1": "TE Connectivity",
    "7-1904094-9": "TE Connectivity",
    "8100-0461": "Sumitomo",
    "90980-11062": "Toyota",
    "90980-11143": "Toyota",
    "90980-11885": "Toyota",
    "BDK 2.8": "Bosch",
    "D 261 205 358-01": "Bosch",
    "DRB12-102PAE-L018": "TE DEUTSCH",
    "DRB16-102SAE-L018": "TE DEUTSCH",
    "DRBF-1A": "TE DEUTSCH",
    "DT04-2P": "TE DEUTSCH",
    "DT04-6P": "TE DEUTSCH",
    "DT06-12SA": "TE DEUTSCH",
    "DT06-2S": "TE DEUTSCH",
    "DT06-3S": "TE DEUTSCH",
    "DT06-6S": "TE DEUTSCH",
    "DTHD06-1-8S": "TE DEUTSCH",
    "DTM06-4S": "TE DEUTSCH",
    "DTM06-6S": "TE DEUTSCH",
    "HD36-24-33SE": "TE DEUTSCH",
    "LMI5-M-2-CB1AD": "Eaton Bussmann",
    "RL00801-50BK": "Amphenol",
    "RL00801-50RE": "Amphenol",
    "S200-2-WI-22-9": "TE Connectivity",
    "S200-3-WI-22-9": "TE Connectivity",
    "S200-4-WI-22-9": "TE Connectivity",
    "V23132-A2001-B200": "TE Connectivity",
    "W12S": "TE DEUTSCH",
    "W2P": "TE DEUTSCH",
    "W2S": "TE DEUTSCH",
    "W3S": "TE DEUTSCH",
    "W6P": "TE DEUTSCH",
    "W6S": "TE DEUTSCH",
    "WB-51PAL": "TE DEUTSCH",
    "WB-51PAR": "TE DEUTSCH",
    "WB-51SAL": "TE DEUTSCH",
    "WB-51SAR": "TE DEUTSCH",
    "WM-4S": "TE DEUTSCH",
    "WM-6S": "TE DEUTSCH",
}


def dec(value) -> Decimal:
    return Decimal(str(value))


def fmt_qty(value: Decimal) -> str:
    if value == value.to_integral():
        return str(int(value))
    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def unit_of(line: dict) -> str:
    return line.get("unit") or EA


def ny_stamp(exported_at: str) -> str:
    """Human stamp: ISO offset plus 9:48 AM America/New_York style clock."""
    # exportedAt is already offset-aware, e.g. 2026-09-30T09:48:41-04:00
    date_part, rest = exported_at.split("T", 1)
    clock = rest.split("-", 1)[0].split("+", 1)[0]
    hh, mm, *_ = clock.split(":")
    hour = int(hh)
    suffix = "AM" if hour < 12 else "PM"
    hour12 = hour % 12 or 12
    return "%s (%s %d:%s %s America/New_York)" % (
        exported_at, date_part, hour12, mm, suffix,
    )


def source_lines(exported_at: str, looms: list) -> list[str]:
    stamp = ny_stamp(exported_at)
    named = ", ".join("`%s` %s" % (loom["id"], loom["name"]) for loom in looms)
    return [
        "Quantities came from the live harness.design looms exported %s, "
        "not from the `.harness` files in `docs/harness/rebuild/` "
        "(main is behind those drawings). Drawing / loom JSON is not in this repo."
        % stamp,
        "Looms in this export (id and name): %s." % named,
    ]


def load_export(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if "exportedAt" not in data or "looms" not in data:
        raise SystemExit("%s is not a harness.design BOM export" % path)
    for pin in FORBIDDEN_PINS:
        blob = json.dumps(data)
        if pin in blob:
            raise SystemExit("export contains forbidden pin %s" % pin)
    return data


def loom_rows(data: dict) -> list[dict]:
    rows = []
    for loom in data["looms"]:
        for line in loom["lines"]:
            rows.append({
                "export_at": data["exportedAt"],
                "loom_id": loom["id"],
                "loom_name": loom["name"],
                "part_number": line["partNumber"],
                "description": line.get("description") or "",
                "quantity": fmt_qty(dec(line["quantity"])),
                "unit": unit_of(line),
            })
    return rows


def to_mm(quantity: Decimal, unit: str) -> tuple[Decimal, str]:
    if unit == "m":
        return quantity * Decimal(1000), "mm"
    return quantity, unit


def shop_need(pn: str, by_loom: dict[str, Decimal]) -> Decimal:
    """Sum of export quantities, except one-housing DRB shells (max of the halves)."""
    pair = ONE_HOUSING.get(pn)
    if not pair:
        return sum(by_loom.values(), Decimal(0))
    halves = [by_loom.get(loom_id, Decimal(0)) for loom_id in pair]
    others = sum(
        (qty for loom_id, qty in by_loom.items() if loom_id not in pair),
        Decimal(0),
    )
    return max(halves) + others


def aggregate(rows: list[dict], loom_names: dict[str, str], st185_only: bool):
    """pn -> {desc, unit, need, by_loom} for a shop group."""
    grouped = OrderedDict()
    for row in rows:
        if st185_only and row["loom_name"] == CLUSTER_NAME:
            continue
        if (not st185_only) and row["loom_name"] != CLUSTER_NAME:
            continue
        qty, unit = to_mm(dec(row["quantity"]), row["unit"])
        pn = row["part_number"]
        slot = grouped.get(pn)
        if slot is None:
            grouped[pn] = {
                "desc": row["description"],
                "unit": unit,
                "by_loom": defaultdict(lambda: Decimal(0)),
            }
            slot = grouped[pn]
        elif slot["unit"] != unit:
            raise SystemExit(
                "part %s mixes units %s and %s after mm conversion" % (
                    pn, slot["unit"], unit,
                )
            )
        slot["by_loom"][row["loom_id"]] += qty
        # Prefer a non-empty description; do not invent a new one.
        if row["description"] and not slot["desc"]:
            slot["desc"] = row["description"]
    out = []
    for pn, slot in grouped.items():
        need = shop_need(pn, slot["by_loom"])
        out.append({
            "pn": pn,
            "desc": slot["desc"],
            "unit": slot["unit"],
            "need": need,
            "by_loom": dict(slot["by_loom"]),
            "mfr": PN_MFR.get(pn, ""),
        })
    return out, loom_names


def classify(item: dict):
    pn, need, unit = item["pn"], item["need"], item["unit"]
    have = Decimal(buylist.ONHAND.get(pn, 0)) if unit == EA else Decimal(0)
    short = max(Decimal(0), need - have)
    if NOT_A_PART.match(pn):
        return "na", have, short
    if need == 0:
        return "zero", have, short
    if short:
        return "buy", have, short
    return "ok", have, short


def md_escape(text: str) -> str:
    return text.replace("|", "\\|")


def write_bom_csv(data: dict, rows: list[dict]) -> None:
    stamp = ny_stamp(data["exportedAt"])
    loom_note = "; ".join("%s %s" % (loom["id"], loom["name"]) for loom in data["looms"])
    buf = io.StringIO()
    buf.write(
        "# Quantities came from the live harness.design looms exported %s. "
        "Not a reading of docs/harness/rebuild/. "
        "Looms (id name): %s.\n" % (stamp, loom_note)
    )
    writer = csv.DictWriter(
        buf,
        fieldnames=[
            "export_at", "loom_id", "loom_name",
            "part_number", "description", "quantity", "unit",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)
    with open(BOM_CSV, "w", encoding="utf-8", newline="") as fh:
        fh.write(buf.getvalue())


def write_parts_lists(data: dict, rows: list[dict]) -> None:
    out = ["# Harness parts lists — live harness.design export", ""]
    out.extend(source_lines(data["exportedAt"], data["looms"]))
    out += [
        "",
        "Regenerate with `python docs/harness/from_live_boms.py --from-export <boms.json>`. "
        "Do not hand-edit. Do not treat `docs/harness/rebuild/*.harness` as the quantity source.",
        "",
        "## Looms in this export",
        "",
        "| id | name |",
        "|---|---|",
    ]
    for loom in data["looms"]:
        out.append("| `%s` | %s |" % (loom["id"], loom["name"]))
    by_loom = OrderedDict((loom["id"], []) for loom in data["looms"])
    names = {loom["id"]: loom["name"] for loom in data["looms"]}
    for row in rows:
        by_loom[row["loom_id"]].append(row)
    for loom_id, lines in by_loom.items():
        out += [
            "",
            "## `%s` — %s" % (loom_id, names[loom_id]),
            "",
            "| Part number | Description | Qty | Unit |",
            "|---|---|---:|---|",
        ]
        for row in lines:
            out.append(
                "| `%s` | %s | %s | %s |" % (
                    md_escape(row["part_number"]),
                    md_escape(row["description"]),
                    row["quantity"],
                    row["unit"],
                )
            )
    out.append("")
    with open(PARTS_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))


def buy_table(items: list[dict], kind: str) -> list[str]:
    rows = []
    for item in items:
        bucket, have, short = classify(item)
        if bucket != kind:
            continue
        rows.append((item, have, short))
    lines = []
    if kind == "buy":
        rows.sort(key=lambda r: (-r[2], r[0]["pn"]))
        lines += [
            "| Part number | Mfr | Description | Unit | Need | Have | **Buy** |",
            "|---|---|---|---|---:|---:|---:|",
        ]
        for item, have, short in rows:
            lines.append(
                "| `%s` | %s | %s | %s | %s | %s | **%s** |" % (
                    md_escape(item["pn"]),
                    md_escape(item["mfr"]),
                    md_escape(item["desc"]),
                    item["unit"],
                    fmt_qty(item["need"]),
                    fmt_qty(have),
                    fmt_qty(short),
                )
            )
    elif kind == "ok":
        rows.sort(key=lambda r: r[0]["pn"])
        lines += [
            "| Part number | Description | Unit | Need | Have |",
            "|---|---|---|---:|---:|",
        ]
        for item, have, _short in rows:
            lines.append(
                "| `%s` | %s | %s | %s | %s |" % (
                    md_escape(item["pn"]),
                    md_escape(item["desc"]),
                    item["unit"],
                    fmt_qty(item["need"]),
                    fmt_qty(have),
                )
            )
    elif kind == "na":
        rows.sort(key=lambda r: r[0]["pn"])
        lines += [
            "| Modelled as | What it really is | Unit | Qty |",
            "|---|---|---|---:|",
        ]
        for item, _have, _short in rows:
            lines.append(
                "| `%s` | %s | %s | %s |" % (
                    md_escape(item["pn"]),
                    md_escape(item["desc"]),
                    item["unit"],
                    fmt_qty(item["need"]),
                )
            )
    else:
        rows.sort(key=lambda r: r[0]["pn"])
        lines += [
            "| Part number | Description | Unit | Qty in export |",
            "|---|---|---|---:|",
        ]
        for item, _have, _short in rows:
            lines.append(
                "| `%s` | %s | %s | %s |" % (
                    md_escape(item["pn"]),
                    md_escape(item["desc"]),
                    item["unit"],
                    fmt_qty(item["need"]),
                )
            )
    return lines


def housing_section(data: dict, items: list[dict]) -> list[str]:
    names = {loom["id"]: loom["name"] for loom in data["looms"]}
    by_pn = {item["pn"]: item for item in items}
    out = [
        "## Shop once — one housing on two letter-halves",
        "",
        "The live BOM lists each DRB102 shell on both ECU-letter halves. That is one",
        "physical connector, not two. Per-loom parts lists keep the export quantity",
        "on each half; the Need / Buy columns above use one housing.",
        "",
        "| Part number | Halves in this export | Qty on each half | Shop |",
        "|---|---|---|---:|",
    ]
    for pn, pair in ONE_HOUSING.items():
        item = by_pn.get(pn)
        if not item:
            continue
        halves = ", ".join("`%s` %s" % (loom_id, names[loom_id]) for loom_id in pair)
        each = ", ".join(
            "%s on `%s`" % (fmt_qty(item["by_loom"].get(loom_id, Decimal(0))), loom_id)
            for loom_id in pair
        )
        out.append(
            "| `%s` | %s | %s | %s |" % (
                pn, halves, each, fmt_qty(item["need"]),
            )
        )
    out.append("")
    return out


def write_buy_list(data: dict, rows: list[dict]) -> None:
    names = {loom["id"]: loom["name"] for loom in data["looms"]}
    st185, _ = aggregate(rows, names, st185_only=True)
    cluster, _ = aggregate(rows, names, st185_only=False)
    st185_pieces = [item for item in st185 if item["unit"] == EA]
    st185_lengths = [item for item in st185 if item["unit"] != EA]
    out = [
        "# Harness — need to buy",
        "",
    ]
    out.extend(source_lines(data["exportedAt"], data["looms"]))
    out += [
        "On-hand piece counts come from `TE_BOM_with_screenshots.xlsx` plus the three TE invoices in Drive "
        "(`docs/harness/buylist.py` `ONHAND`). Lengths are not on that stock list.",
        "Regenerate with `python docs/harness/from_live_boms.py --from-export <boms.json>`. "
        "Do not hand-edit. `buylist.py` no longer writes this file from `rebuild/`.",
        "ClusterLED (`gklj`) exported a few M22759 runs in metres; those lengths are added as millimetres in the totals below.",
        "",
        "## Short — order these (ST185 looms)",
        "",
    ]
    out += buy_table(st185_pieces, "buy")
    out += ["", "## Wire and cable — cut lengths (ST185 looms)", ""]
    out += buy_table(st185_lengths, "buy")
    out.append("")
    out += housing_section(data, st185)
    out += ["## Covered by stock (ST185 looms)", ""]
    out += buy_table(st185_pieces, "ok")
    out += [
        "",
        "## Not purchased — already on the car, or supplied with the device (ST185 looms)",
        "",
    ]
    out += buy_table(st185, "na")
    out += [
        "",
        "## Quantity 0 in the live BOM (ST185 looms)",
        "",
        "Present on a live loom's parts list at quantity 0. Not ordered from this export.",
        "",
    ]
    out += buy_table(st185, "zero")
    out += [
        "",
        "## Center Cluster (`lpqV`) — order these",
        "",
        "From the same live export (`lpqV` Center Cluster). Not an ST185 rebuild file.",
        "",
    ]
    out += buy_table(cluster, "buy")
    out += [
        "",
        "## Center Cluster (`lpqV`) — quantity 0 in the live BOM",
        "",
    ]
    out += buy_table(cluster, "zero")
    out.append("")
    text = "\n".join(out)
    for pin in FORBIDDEN_PINS:
        if pin in text:
            raise SystemExit("buy list would contain forbidden pin %s" % pin)
    with open(BUY_MD, "w", encoding="utf-8") as fh:
        fh.write(text)


def generate(export_path: str) -> None:
    data = load_export(export_path)
    ids = {loom["id"] for loom in data["looms"]}
    for pn, pair in ONE_HOUSING.items():
        missing = [loom_id for loom_id in pair if loom_id not in ids]
        if missing:
            raise SystemExit("ONE_HOUSING %s refers to missing loom ids %s" % (pn, missing))
    rows = loom_rows(data)
    write_bom_csv(data, rows)
    write_parts_lists(data, rows)
    write_buy_list(data, rows)
    print("wrote", BOM_CSV)
    print("wrote", PARTS_MD)
    print("wrote", BUY_MD)
    print("looms:", len(data["looms"]), "BOM lines:", len(rows))


def read_bom_csv(path: str = BOM_CSV) -> tuple[str, list[dict]]:
    with open(path, encoding="utf-8") as fh:
        raw = fh.readlines()
    comments = [line[2:].strip() for line in raw if line.startswith("#")]
    body = [line for line in raw if not line.startswith("#")]
    rows = list(csv.DictReader(body))
    return " ".join(comments), rows


def check_committed() -> None:
    errors = []
    for path in (BOM_CSV, PARTS_MD, BUY_MD):
        if not os.path.isfile(path):
            errors.append("missing %s" % path)
            continue
        text = open(path, encoding="utf-8").read()
        if "live harness.design looms exported" not in text:
            errors.append("%s is not stamped as a live harness.design export" % path)
        if "rebuild/" in text and "not from the `.harness` files" not in text and "Not a reading of docs/harness/rebuild/" not in text:
            errors.append("%s still presents rebuild/ as the quantity source" % path)
        for pin in FORBIDDEN_PINS:
            if pin in text:
                errors.append("%s contains forbidden pin %s" % (path, pin))
    comment, rows = read_bom_csv()
    if not rows:
        errors.append("HARNESS-BOM.csv has no rows")
    loom_ids = list(OrderedDict((row["loom_id"], row["loom_name"]) for row in rows).items())
    parts = open(PARTS_MD, encoding="utf-8").read()
    buy = open(BUY_MD, encoding="utf-8").read()
    for loom_id, loom_name in loom_ids:
        token = "`%s`" % loom_id
        if token not in parts or token not in buy:
            errors.append("loom id %s missing from a generated list" % loom_id)
        if loom_name not in parts or loom_name not in buy:
            errors.append("loom name %s missing from a generated list" % loom_name)
    # PARTS-LISTS must carry every BOM row's PN at that loom.
    for row in rows:
        header = "## `%s` — %s" % (row["loom_id"], row["loom_name"])
        if header not in parts:
            errors.append("missing parts-list section %s" % header)
        if "`%s`" % row["part_number"] not in parts:
            errors.append("parts list missing PN %s" % row["part_number"])
    if "from the %d `.harness` files" % 15 in buy or "from the 15 `.harness` files" in buy:
        errors.append("NEED-TO-BUY.md still claims it was generated from rebuild/ harness files")
    if errors:
        raise SystemExit("from_live_boms --check-committed failed:\n  " + "\n  ".join(errors))
    print("committed shopping lists are stamped live-export; looms:", len(loom_ids), "BOM lines:", len(rows))


def check_export(export_path: str) -> None:
    data = load_export(export_path)
    expected = loom_rows(data)
    _comment, actual = read_bom_csv()
    if len(expected) != len(actual):
        raise SystemExit(
            "BOM csv has %d lines, export has %d" % (len(actual), len(expected))
        )
    for exp, got in zip(expected, actual):
        for key in ("export_at", "loom_id", "loom_name", "part_number", "description", "quantity", "unit"):
            if str(exp[key]) != str(got[key]):
                raise SystemExit(
                    "BOM csv mismatch on %s: export %r vs csv %r (%s %s %s)" % (
                        key, exp[key], got[key],
                        exp["loom_id"], exp["loom_name"], exp["part_number"],
                    )
                )
    parts = open(PARTS_MD, encoding="utf-8").read()
    buy = open(BUY_MD, encoding="utf-8").read()
    stamp = ny_stamp(data["exportedAt"])
    for path, text in ((PARTS_MD, parts), (BUY_MD, buy), (BOM_CSV, open(BOM_CSV, encoding="utf-8").read())):
        if data["exportedAt"] not in text:
            raise SystemExit("%s missing exportedAt %s" % (path, data["exportedAt"]))
        if "America/New_York" not in text:
            raise SystemExit("%s missing America/New_York clock" % path)
        if stamp.split(" (")[0] not in text:
            raise SystemExit("%s missing export stamp" % path)
    for loom in data["looms"]:
        if loom["id"] not in parts or loom["name"] not in parts:
            raise SystemExit("PARTS-LISTS.md missing loom %s %s" % (loom["id"], loom["name"]))
        if loom["id"] not in buy or loom["name"] not in buy:
            raise SystemExit("NEED-TO-BUY.md missing loom %s %s" % (loom["id"], loom["name"]))
    # Per-loom qty cells must match the export exactly.
    for row in expected:
        needle = "| `%s` | %s | %s | %s |" % (
            row["part_number"].replace("|", "\\|"),
            row["description"].replace("|", "\\|"),
            row["quantity"],
            row["unit"],
        )
        if needle not in parts:
            raise SystemExit("PARTS-LISTS.md missing exact line: %s" % needle)
    check_committed()
    print("export parity ok:", export_path, stamp)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-export", metavar="JSON", help="live harness.design BOM export")
    parser.add_argument("--check-committed", action="store_true")
    parser.add_argument("--check-export", metavar="JSON")
    args = parser.parse_args(argv)
    if args.from_export:
        generate(args.from_export)
    if args.check_export:
        check_export(args.check_export)
    elif args.check_committed:
        check_committed()
    if not (args.from_export or args.check_committed or args.check_export):
        parser.error("pass --from-export, --check-committed, and/or --check-export")


if __name__ == "__main__":
    main()
