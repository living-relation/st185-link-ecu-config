"""ONE project BOM + shopping list (Dan 2026-10-19). Two sections: Mechanical assemblies, Wire harness.

  python docs/sourcing/build_project_bom.py            write PROJECT-BOM.csv + PROJECT-BOM.xlsx
  python docs/sourcing/build_project_bom.py --check    fail if the committed CSV / xlsx is stale (check_all.py)

Inputs, all in git: docs/harness/MASTER-wirelist.csv (every housing, accessory, contact, plug, lug, cable, wire and ident
band; R221), the drawing sets' layouts (DR-25 tubing), docs/sourcing/harness-parts.csv (maker and description of each
harness part; fixed_qty = boots and labels counted from the retired harness.design files), cad/fusebox/fusebox-parts-*.csv, docs/enclosures/*-bom.csv,
docs/sourcing/mech-extra.csv (machined parts / pump), docs/sourcing/te-on-hand-bom.csv (on hand),
docs/sourcing/bom-links.csv (hand-kept buy links, prices, link status, te_sample = Y when te.com shows "Get free samples" for that exact TE PN; sample_other = "<maker> <PN>" of a validated drop-in equivalent whose maker offers free samples; both feed the "Free sample" column).
Nothing is typed in twice: edit the source, rerun. A line with no validated link goes on the To do sheet."""
import collections
import csv
import glob
import io
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))


def P(*a):
    return os.path.join(ROOT, *a)


MADE_AT_WORK = "made at work (Dan, R210)"
# R210: labels and ident-band sleeves are listed but not priced
UNPRICED = re.compile(r"^(TMS-SCE-|RNF-100-[0-9/]+-(4|6|9)-STK$)")
ALIAS = {"2R5": "Klauke 2R5"}   # buylist name -> bom-links name
MARGIN = 1.15
FT_PER_M = 3.28084
COLS = ["section", "assembly", "part_number", "maker", "free_sample", "description", "qty_needed", "unit", "qty_on_hand", "qty_to_buy",
        "unit_price_usd", "line_total_usd", "buy_link", "alt_cheaper_link", "price_basis", "link_status", "notes"]
NUMCOLS = ("qty_needed", "qty_on_hand", "qty_to_buy", "unit_price_usd", "line_total_usd")
HEAD = {"free_sample": "Free sample"}   # xlsx header labels; the CSV keeps the column names
SECTIONS = ("Mechanical assemblies", "Wire harness")


def rd(path):
    return list(csv.DictReader(open(path, encoding="utf-8-sig", newline="")))


def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


ONHAND = {}
for _r in rd(P("docs", "sourcing", "te-on-hand-bom.csv")):
    ONHAND[_r["pn"]] = ONHAND.get(_r["pn"], 0) + int(_r["qty_ordered"] or 0)
LINKS = {r["pn"]: r for r in rd(P("docs", "sourcing", "bom-links.csv"))}
rows = []


def add(section, assembly, pn, maker, desc, need, have, unit="ea", notes="", kind="buy", price=None, basis=None):
    need = int(math.ceil(need))
    have = min(int(have), need)
    buy = need - have
    L = LINKS.get(pn) or LINKS.get(ALIAS.get(pn, ""), {})
    dead = L.get("link_status", "").startswith("404")
    if not L.get("buy_url") and not dead and re.search(r"TE |DEUTSCH|Deutsch|Raychem|AMP", maker) and kind == "buy" and not pn.startswith("("):
        L = dict(L, buy_url="https://www.te.com/en/product-%s.html" % pn.replace("/", "-"),
                 link_status="te.com URL form, page NOT opened (te.com blocked the automated check): confirm")
    if price is None:
        price = num(L.get("unit_usd"))
    basis = basis if basis is not None else L.get("price_basis", "")
    link, status = L.get("buy_link", L.get("buy_url", "")), L.get("link_status", "")
    if kind == "print":
        link, status, price, basis = "", "printed on Dan's PA12 printer (R82: no buy link)", 0.0, MADE_AT_WORK
    elif kind == "machine":
        link, status, price, basis = "", "machined to the drawing (R210: made at work, no buy link)", 0.0, MADE_AT_WORK
    elif UNPRICED.match(pn) and section == SECTIONS[1]:
        price, basis = 0.0, "not priced (Dan)"
    elif not link:
        status = L.get("link_status") or "NO LINK"
    rows.append(dict(section=section, assembly=assembly, part_number=pn, maker=maker, free_sample="✓ TE" if L.get("te_sample") == "Y" else ("✓ " + L["sample_other"] if L.get("sample_other") else ""),
                     description=desc, qty_needed=need,
                     unit=unit, qty_on_hand=have, qty_to_buy=buy, unit_price_usd="" if price is None else "%.2f" % price,
                     line_total_usd="" if price is None or not buy else "%.2f" % (price * buy), buy_link=link,
                     alt_cheaper_link=L.get("alt_url", ""), price_basis=basis, link_status=status,
                     notes=notes or L.get("note", "")))


# ---------- Wire harness: counted from the ONE master wire list (DECISIONS R221) ----------
# Every housing, accessory, contact, sealing plug, lug, resistor / diode, cable and wire is read from
# docs/harness/MASTER-wirelist.csv. Fuse-box ends (the POWER / LOGIC boxes, their relays, the battery relay block) are
# the fuse-box parts lists' (Mechanical section). Ident bands come from the master's ident_bands; covering tubing from a
# drawing set's layout (docs/harness/tools/<set>.layout.json, DR-25 per segment); boots and labels from the fixed_qty of
# docs/sourcing/harness-parts.csv (counted from the harness.design files when they were retired, R225).
MASTER = rd(P("docs", "harness", "MASTER-wirelist.csv"))
PARTS = rd(P("docs", "sourcing", "harness-parts.csv"))
LIBP = {q["part_number"]: q for q in PARTS}
BOX = re.compile(r"^(LOGIC|POWER|POWER-STUDS|BATT-RELAY-BLOCK|K-)")
NOT_PN = re.compile(r"^(TBD|INTEGRAL|none|solder|screw terminal|flying lead|crimp splice|factory|cut-and-cap|heat-shrink)", re.I)
H_NEED, H_TBD = collections.Counter(), collections.Counter()
seen_conn = set()
SENSOR_IDS = {
    "CRANK", "CAM", "MAP", "IAT", "ECT", "FLEX", "TURBO-SPD", "OIL-T", "KNOCK-1",
    "FUEL-P", "OIL-P", "CLNT-P", "CHARGE-IAT", "VSS", "WSS-FL", "WSS-FR", "WSS-RL",
    "WSS-RR", "APS-PEDAL", "FUEL-LEVEL", "REV-SW", "A5", "A1",
    # plugs Dan already owns that are not sensors (Dan 2026-10-30): the 1ZZ coil plugs and the MR-S pump plugs
    "COIL-1", "COIL-2", "COIL-3", "COIL-4", "MRS-A", "MRS-B", "MRS-C",
    # injector plug kits Ballenger CONN-76270, owned x4 (Dan 2026-10-31)
    "INJ-1", "INJ-2", "INJ-3", "INJ-4",
}
SENSOR_PN = set()


def h_count(pn, n=1, what=""):
    pn = re.sub(r" \(bussed cap\)$", "", (pn or "").strip())
    if not pn:
        return
    if pn == "TBD":
        H_TBD[what] += n
    elif not NOT_PN.match(pn):
        H_NEED[pn] += n


for r in MASTER:
    for s in ("from", "to"):
        t, i = r[s + "_type"], r[s + "_id"]
        if not t or BOX.match(i):
            continue
        if t == "connector":
            if i not in seen_conn:
                seen_conn.add(i)
                h_count(r[s + "_housing_pn"], what="housing (%s)" % i)
                for x in (r[s + "_housing_extra"] or "").split(";"):
                    h_count(x)
            h_count(r[s + "_terminal_pn"], what="contact / plug (%s)" % i)
            if i in SENSOR_IDS:
                for col in ("housing_pn", "terminal_pn"):
                    pn = re.sub(r" \(bussed cap\)$", "", (r[s + "_" + col] or "").strip())
                    if pn and pn != "TBD" and not NOT_PN.match(pn):
                        SENSOR_PN.add(pn)
        elif t == "terminal":
            h_count(r[s + "_terminal_pn"], what="lug / terminal (%s)" % i)
        elif t in ("resistor", "diode") and ("rd", i) not in seen_conn:
            seen_conn.add(("rd", i))
            h_count(r[s + "_housing_pn"], what="%s (%s)" % (t, i))
WIRE_MM, CABLE_MM = collections.Counter(), collections.defaultdict(dict)
for r in MASTER:
    if not r["wire_id"]:
        continue
    mm = num(r["est_length_mm"]) or 0
    if r["cable"]:
        CABLE_MM[r["cable_pn"]][r["cable"]] = max(CABLE_MM[r["cable_pn"]].get(r["cable"], 0), mm)
    elif r["wire_pn"] and r["wire_pn"] != "TBD":
        WIRE_MM[r["wire_pn"]] += mm
BANDS = collections.Counter()
for r in MASTER:
    g = int(r["gauge_awg"]) if r["gauge_awg"].isdigit() else None
    if not r["wire_id"] or not r["ident_bands"] or g is None or g < 8:
        continue
    size = "3/32" if g >= 14 else "3/16"
    for b in r["ident_bands"].split("-"):
        BANDS["RNF-100-%s-%s-STK" % (size, {"Blue": "6", "Yellow": "4", "White": "9"}[b])] += 2
TUBE_MM = collections.Counter()
sys.path.insert(0, P("docs", "harness", "tools"))
import build_drawings as BD   # noqa: E402  (the drawing sets and their DR-25 per segment)
for s in BD.own_harnesses():
    H = BD.Harness(s)
    seg = collections.Counter()
    sq = collections.Counter()
    for r in H.wires:
        p, _ = H.route(r)
        for a, b in zip(p or [], (p or [])[1:]):
            k = tuple(sorted((a, b)))
            seg[k] += 1
            sq[k] += BD.od(r) ** 2
    for a, b, mm in H.layout["segments"]:
        k = tuple(sorted((a, b)))
        if seg[k]:
            TUBE_MM[BD.dr25_for(1.2 * math.sqrt(sq[k])) + "-SP"] += mm
for q in PARTS:
    if q["fixed_qty"]:
        H_NEED[q["part_number"]] += int(q["fixed_qty"])

# Master parts list: owned / needed / short. On-hand first. Sensor plugs and terminals are never a buy.
PARTS_COLS = ["part_number", "manufacturer", "description", "fixed_qty", "owned", "needed", "short"]
for q in PARTS:
    pn = q["part_number"]
    need = int(H_NEED.get(pn, 0))
    owned = int(ONHAND.get(pn, 0))
    short = 0 if pn in SENSOR_PN else max(0, need - owned)
    q["owned"], q["needed"], q["short"] = str(owned), str(need), str(short)
parts_path = P("docs", "sourcing", "harness-parts.csv")
if "--check" not in sys.argv:
    with open(parts_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, PARTS_COLS, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows({c: q.get(c, "") for c in PARTS_COLS} for q in PARTS)


def lib_desc(pn):
    q = LIBP.get(pn) or {}
    return q.get("manufacturer", ""), q.get("description", "")


HARNESS_PN = set(H_NEED) | set(BANDS) | set(TUBE_MM) | set(WIRE_MM) | set(CABLE_MM)


# ---------- Mechanical: fuse boxes, enclosures, machined parts, pump ----------
ntb_early = HARNESS_PN   # a part the harness section counts is not added again from an enclosure BOM
BOXNAME = {"POWER": "POWER box", "LOGIC": "LOGIC box", "BATTRELAY": "Battery relay block"}
MECH_PN = set()
# The selected fuse box is rev 7 (cad/README.md "Selected for build"): its POWER list is cad/fusebox/rev7/; the LOGIC box and
# battery relay block keep their lists in cad/fusebox/. The rev 6 POWER list there is superseded and not counted.
FB_LISTS = [f for f in sorted(glob.glob(P("cad", "fusebox", "fusebox-parts-*.csv"))) if not f.endswith("fusebox-parts-power.csv")]
FB_LISTS.append(P("cad", "fusebox", "rev7", "fusebox-parts-power.csv"))
for f in FB_LISTS:
    for r in rd(f):
        n = int(r["qty_need"] or 0) + int(r["qty_spare"] or 0)
        pn = r["part_number"]
        if n == 0 or re.match(r"^(none$|cut from)", pn):
            continue
        printed = r["group"] == "Printed"
        MECH_PN.add(pn)
        add(SECTIONS[0], BOXNAME.get(r["box"], r["box"]), pn, r["maker"], "%s: %s" % (r["item"], r["description"]), n,
            int(r["own"] or 0), kind="print" if printed else "buy",
            price=None)
for tag, fn, qk in (("CSB3 enclosure", "csb3-bom.csv", "qty"), ("VRC enclosure (2 per car)", "vr-conditioner-bom.csv", "qty_car")):
    for r in rd(P("docs", "enclosures", fn)):
        pn = r["pn"]
        n = int(r[qk] or 0)
        if not pn or n == 0 or pn in ntb_early:
            continue
        kind = r["buy_vs_print"] if r["buy_vs_print"] in ("machine", "print") else "buy"
        add(SECTIONS[0], tag, pn, r["mfr"], "%s: %s" % (r["item"], r["role"]), n, ONHAND.get(pn, 0), kind=kind)
for r in rd(P("docs", "sourcing", "mech-extra.csv")):
    add(SECTIONS[0], r["assembly"], r["part_number"], r["maker"], "%s: %s" % (r["item"], r["description"]),
        int(r["qty"]), ONHAND.get(r["part_number"], 0), notes=r["note"], kind=r["buy_vs_print"])

# ---------- Wire harness lines ----------
ASSY = "All harnesses (master wire list)"
for pn, need in sorted(H_NEED.items()):
    if pn in MECH_PN:
        continue
    mk, desc = lib_desc(pn)
    have = need if pn in SENSOR_PN else ONHAND.get(pn, 0)
    add(SECTIONS[1], ASSY, pn, mk, desc, need, have,
        notes="on hand (sensor plug / terminal: never a buy)" if pn in SENSOR_PN else "")
for what, n in sorted(H_TBD.items()):
    add(SECTIONS[1], ASSY, "TBD", "", "part number not confirmed yet: %s (check_wiring.py --tbd)" % what, n, 0,
        notes="no maker document in the repo yet; never guessed")
for pn, n in sorted(BANDS.items()):
    mk, desc = lib_desc(pn)
    add(SECTIONS[1], ASSY, pn, mk, desc, -(-n // 180), ONHAND.get(pn, 0), unit="stick", notes="%d bands of 6 mm, both ends of each wire" % n)
for pn, mm in sorted(TUBE_MM.items()):
    mk, desc = lib_desc(pn)
    add(SECTIONS[1], ASSY, pn, mk, desc, -(-int(mm * 1.10) // 1000), ONHAND.get(pn, 0), unit="m",
        notes="%.1f m of bundle + 10 %% cut / recovery margin" % (mm / 1000.0))
for pn, mm in sorted(WIRE_MM.items()):
    mk, desc = lib_desc(pn)
    ft = mm / 1000.0 * MARGIN * FT_PER_M
    if mm > 0:
        add(SECTIONS[1], ASSY, pn, mk, desc, max(1, math.ceil(ft)), 0, unit="ft", notes="%.1f m in the master + 15%% margin" % (mm / 1000.0))
for pn, cables in sorted(CABLE_MM.items()):
    mm = sum(cables.values())
    mk, desc = lib_desc(pn)
    if pn == "TBD":
        add(SECTIONS[1], ASSY, "TBD", "", "shielded cable, part number not confirmed: %s" % ", ".join(sorted(cables)),
            max(1, math.ceil(mm / 1000.0 * MARGIN * FT_PER_M)), 0, unit="ft", notes="OPEN-ITEMS row 140")
    elif mm > 0:
        add(SECTIONS[1], ASSY, pn, mk, desc, max(1, math.ceil(mm / 1000.0 * MARGIN * FT_PER_M)), ONHAND.get(pn, 0), unit="ft",
            notes="%d cable runs, %.1f m + 15%% margin" % (len(cables), mm / 1000.0))

rows.sort(key=lambda r: (SECTIONS.index(r["section"]), r["assembly"], r["part_number"]))
def advice(r):
    pn, mk = r["part_number"], r["maker"]
    if pn.startswith("M22759/16"):
        return "buy by the foot (Wings and Wheels / Flight Store); confirm the supplier and the colour code page"
    if pn.startswith("BC-"):
        return "pick a welding / battery cable supplier (no PN exists for this drawn wire); recommend ProWire USA"
    if pn.startswith("GENERIC") or mk == "generic" or pn.startswith("Jump"):
        return "generic part: name a real PN (TE first, then an approved supplier); I propose one on your OK"
    if "Toyota" in mk or pn.startswith("90980"):
        return "OEM Toyota part: buy from a Toyota parts dealer; confirm it is not already on the car"
    if "not opened" in r["link_status"]:
        return "te.com product page by PN; I open it once te.com stops blocking, or you confirm"
    return "I find and validate a maker page or approved-supplier listing"


NEEDS = [(r["section"], r["part_number"], r["link_status"] or "no price / link", advice(r)) for r in rows
         if r["qty_to_buy"] and r["unit_price_usd"] != "0.00" and (not r["buy_link"] or r["unit_price_usd"] == "")]


def csv_text():
    b = io.StringIO()
    w = csv.DictWriter(b, COLS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return b.getvalue()


def write_xlsx(path):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    wb = Workbook()
    wb.remove(wb.active)
    hair, thick = Side(style="hair", color="A6A6A6"), Side(style="thick", color="1F1F1F")
    band = (PatternFill("solid", fgColor="E7E6F7"), PatternFill("solid", fgColor="F3F2FB"))
    widths = dict(free_sample=14, section=14, assembly=22, part_number=24, maker=18, description=60, qty_needed=9, unit=6, qty_on_hand=9,
                  qty_to_buy=9, unit_price_usd=10, line_total_usd=10, buy_link=48, alt_cheaper_link=40, price_basis=11,
                  link_status=30, notes=40)

    def sheet(name, cols, data, w):
        ws = wb.create_sheet(name)
        ws.append([HEAD.get(c, c) for c in cols])
        for c in ws[1]:
            c.font = Font(bold=True, size=12)
            c.border = Border(bottom=thick)
            c.alignment = Alignment(wrap_text=True, vertical="center")
        for i, row in enumerate(data):
            ws.append(row)
            for c in ws[ws.max_row]:
                c.fill, c.border = band[i % 2], Border(bottom=hair)
                c.alignment, c.font = Alignment(wrap_text=True, vertical="top"), Font(size=10)
                if isinstance(c.value, str) and c.value.startswith("http"):
                    c.hyperlink = c.value
                    c.font = Font(size=10, color="0563C1", underline="single")
        for j, c in enumerate(cols, 1):
            ws.column_dimensions[get_column_letter(j)].width = w.get(c, 16)
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        ws.sheet_view.zoomScale = 80
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        return ws

    summ = []
    for s in SECTIONS:
        sub = [r for r in rows if r["section"] == s]
        buy = [r for r in sub if r["qty_to_buy"]]
        priced = [r for r in buy if r["line_total_usd"]]
        zero = sum(1 for r in buy if r["unit_price_usd"] == "0.00")
        sheet(s, COLS, [[num(r[c]) if c in NUMCOLS and r[c] != "" else r[c] for c in COLS] for r in sub], widths)
        summ.append([s, len(sub), len(buy), len(priced), round(sum(float(r["line_total_usd"]) for r in priced), 2), zero])
    summ.append(["TOTAL"] + [round(sum(x[i] for x in summ), 2) for i in range(1, 6)])
    ws = sheet("Summary", ["section", "lines", "lines to buy", "lines with a price", "priced spend USD", "lines at $0 (made at work / not priced)"],
               summ, {"section": 26, "lines": 10, "lines to buy": 14, "lines with a price": 18, "priced spend USD": 18,
                      "lines at $0 (made at work / not priced)": 36})
    ws.append([])
    ws.append(["Spend counts only lines that have a unit price; lines to buy minus lines with a price are NOT in the total. Wire is in ft "
               "(drawn length + 15 %). On hand = docs/sourcing/te-on-hand-bom.csv (qty_ordered, an upper bound; confirm on the shelf)."])
    wb.move_sheet("Summary", offset=-2)
    sheet("To do", ["section", "part", "problem", "recommended answer"], [list(n) for n in NEEDS],
          {"section": 22, "part": 28, "problem": 40, "recommended answer": 70})
    wb.save(path)


text = csv_text()
cpath, xpath = P("docs", "sourcing", "PROJECT-BOM.csv"), P("docs", "sourcing", "PROJECT-BOM.xlsx")
if "--check" in sys.argv:
    old = open(cpath, encoding="utf-8", newline="").read().replace("\r\n", "\n") if os.path.exists(cpath) else ""
    if old != text:
        print("STALE: docs/sourcing/PROJECT-BOM.csv. Fix: python docs/sourcing/build_project_bom.py, commit the CSV and xlsx.")
        sys.exit(1)
    from openpyxl import load_workbook
    wb = load_workbook(xpath, read_only=True)
    n = sum(wb[s].max_row - 1 for s in SECTIONS)
    if n != len(rows):
        print("STALE: PROJECT-BOM.xlsx has %d lines, the CSV %d. Fix: python docs/sourcing/build_project_bom.py" % (n, len(rows)))
        sys.exit(1)
    print("up to date: PROJECT-BOM (%d lines)" % len(rows))
else:
    open(cpath, "w", encoding="utf-8", newline="\n").write(text)
    write_xlsx(xpath)
    print("wrote PROJECT-BOM.csv + .xlsx:", len(rows), "lines,", len(NEEDS), "needs-Dan")
