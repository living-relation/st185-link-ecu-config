"""Styled Excel views of the master wire list (Dan 2026-10-19: "add table style alternating colors
between rows, and between to/from column sets also"). The CSVs are the git source; these
workbooks are generated from the same rows and checked for staleness by `wirelist.py --check`.

  A-cabin-wirelist.xlsx  sheets Wires, Splices, Connectors, Mates
  A-cabin-pinouts.xlsx   one sheet per connector: Pin | Wire | Description | Other end

Every sheet is an Excel Table (filters on, banded rows), header row frozen, widths set, long
text wrapped. Columns are grouped into sets (id, FROM, TO, net, wire spec, notes / OEM); each set
has its own colour family, with a light and a darker tint on alternate rows, so neighbouring
sets - FROM and TO above all - read apart at a glance.
"""
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

STYLE_VERSION = "wirelist-xlsx v1"

# set -> (header fill, light row, darker row). FROM is blue, TO is orange: never confused.
PALETTE = {
    "id":   ("44546A", "F2F2F2", "E0E0E0"),
    "from": ("1F4E79", "DDEBF7", "BDD7EE"),
    "to":   ("C55A11", "FCE4D6", "F8CBAD"),
    "net":  ("375623", "E2EFDA", "C6E0B4"),
    "spec": ("5B2C6F", "EDE1F2", "D9C3E3"),
    "note": ("7F6000", "FFF2CC", "FFE699"),
}
WIDE = {"from_conn_name": 30, "to_conn_name": 30, "from_desc": 26, "to_desc": 26, "net_name": 32,
        "from_note": 40, "to_note": 40, "oem_location": 40, "oem_ewd_page": 44, "oem_method": 40,
        "route_branch": 32, "sot_check": 60, "status": 30, "notes": 50, "name": 40, "note": 50,
        "Description": 30, "Other end": 44, "location": 34, "method": 34, "this_desc": 26, "mate_desc": 26}
WRAP = {"from_note", "to_note", "oem_location", "oem_ewd_page", "oem_method", "sot_check", "status",
        "notes", "note", "Other end", "route_branch"}
THIN = Side(style="thin", color="FFFFFF")


def column_sets(cols):
    """column name -> set name."""
    out = {}
    for c in cols:
        if c.startswith("from_") or c in ("this_conn", "this_pin", "this_desc", "Description"):
            out[c] = "from"
        elif c.startswith("to_") or c.startswith("mate_") or c == "Other end":
            out[c] = "to"
        elif c in ("net_id", "net_name", "splice", "cable", "net", "wires", "gauges_awg", "combined_cma",
                   "equivalent_awg", "mates_with", "cavities"):
            out[c] = "net"
        elif c in ("gauge_awg", "colour", "stripe", "ident_bands", "part_number", "method"):
            out[c] = "spec"
        elif c in ("circuit_id", "wire_id", "harness", "passes_through", "splice_id", "conn_id", "Pin", "Wire",
                   "name"):
            out[c] = "id"
        else:
            out[c] = "note"
    return out


def _sheet(wb, title, cols, rows, table_name):
    ws = wb.create_sheet(title[:31])
    sets = column_sets(cols)
    ws.append(cols)
    for r in rows:
        ws.append([_value(r.get(c, "")) for c in cols])
    for j, c in enumerate(cols, 1):
        hdr, light, dark = PALETTE[sets[c]]
        cell = ws.cell(row=1, column=j)
        cell.fill = PatternFill("solid", start_color=hdr)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        for i in range(2, len(rows) + 2):
            x = ws.cell(row=i, column=j)
            x.fill = PatternFill("solid", start_color=light if i % 2 == 0 else dark)
            x.border = Border(left=THIN, right=THIN)
            x.alignment = Alignment(vertical="top", wrap_text=c in WRAP)
        ws.column_dimensions[get_column_letter(j)].width = WIDE.get(c, max(10, min(22, len(c) + 3)))
    ws.freeze_panes = "A2"
    ref = "A1:%s%d" % (get_column_letter(len(cols)), max(2, len(rows) + 1))
    t = Table(displayName=table_name, ref=ref)
    t.tableStyleInfo = TableStyleInfo(name="TableStyleLight1", showRowStripes=True, showColumnStripes=False)
    ws.add_table(t)
    return ws


def _value(v):
    if isinstance(v, str) and v.strip().lstrip("-").isdigit() and len(v) < 9:
        return int(v)
    return v


def wirelist_workbook(tables):
    """tables: [(sheet title, columns, rows, table name)]."""
    wb = Workbook()
    wb.remove(wb.active)
    wb.properties.description = STYLE_VERSION
    for title, cols, rows, name in tables:
        _sheet(wb, title, cols, rows, name)
    return wb


def pinout_workbook(pinouts):
    """pinouts: [(sheet title, [{"Pin", "Wire", "Description", "Other end"}])]."""
    wb = Workbook()
    wb.remove(wb.active)
    wb.properties.description = STYLE_VERSION
    used = set()
    for i, (title, rows) in enumerate(pinouts):
        t = "".join(ch for ch in title if ch not in "[]:*?/\\")[:31] or "Sheet%d" % i
        while t in used:
            t = t[:28] + "_%d" % i
        used.add(t)
        _sheet(wb, t, ["Pin", "Wire", "Description", "Other end"], rows, "Pinout%d" % (i + 1))
    return wb


def values(path_or_wb):
    """{sheet: [[cell values]]} plus the style version, for the staleness check."""
    wb = load_workbook(path_or_wb) if isinstance(path_or_wb, str) else path_or_wb
    out = {"_style": wb.properties.description}
    for ws in wb.worksheets:
        out[ws.title] = [[None if c == "" else c for c in row] for row in ws.iter_rows(values_only=True)]
    return out
