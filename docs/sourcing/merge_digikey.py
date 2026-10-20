"""Fold _research/digikey-results.json (from digikey_price.py) into docs/sourcing/bom-links.csv.

For each exact Digi-Key match, the unit price is read at the quantity the BOM line needs (to-buy, else needed; never below
the package minimum), the cheapest package variation wins, and the product URL, price basis and stock are written. A part
Digi-Key does not carry is left untouched. Run: python docs/sourcing/merge_digikey.py [--date 2026-10-20]
"""
import csv, json, os, re, sys, collections

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LINKS = os.path.join(ROOT, "docs", "sourcing", "bom-links.csv")
BOM = os.path.join(ROOT, "docs", "sourcing", "PROJECT-BOM.csv")
RES = os.path.join(ROOT, "_research", "digikey-results.json")
# Not merged: Digi-Key sells these by the spool with an unclear unit (cable, DR-25 tubing), and its AMI-50 / AMI-60 listings
# are not the bolt-down fuse the BOM names; they keep their existing price / link.
SKIP = re.compile(r"^(55A|DR-25-|AMI-)")


def price_at(breaks, q):
    ok = [b for b in breaks if b[0] <= q]
    return ok[-1][1] if ok else (breaks[0][1] if breaks else None)


def main():
    day = sys.argv[sys.argv.index("--date") + 1] if "--date" in sys.argv else "2026-10-20"
    res = json.load(open(RES))
    need = collections.defaultdict(int)
    for r in csv.DictReader(open(BOM, encoding="utf-8")):
        need[r["part_number"]] += int(float(r["qty_to_buy"] or 0)) or int(float(r["qty_needed"] or 0))
    rows = list(csv.DictReader(open(LINKS, encoding="utf-8-sig", newline="")))
    cols = list(rows[0].keys())
    if "sample_other" not in cols:
        cols.append("sample_other")
    by = {r["pn"]: r for r in rows}
    n = 0
    for pn, v in res.items():
        if v.get("status") != "ok" or not v.get("variations") or SKIP.match(pn):
            continue
        q = max(need.get(pn, 1), 1)
        best = None
        for var in v["variations"]:
            if not var["breaks"]:
                continue
            qq = max(q, var["min"] or 1)
            tot = price_at(var["breaks"], qq) * qq
            if best is None or tot < best[0]:
                best = (tot, price_at(var["breaks"], qq), qq, var)
        if not best:
            continue
        _, unit, qq, var = best
        r = by.get(pn)
        if r is None:
            r = {c: "" for c in cols}; r["pn"] = pn; rows.append(r); by[pn] = r
        r["buy_url"] = v["url"]
        r["unit_usd"] = "%.4f" % unit if unit < 0.1 else "%.2f" % unit
        basis = "Digi-Key qty %d (%s), %s" % (qq, var["pkg"] or "", day)
        if qq > max(50, 20 * q):
            basis += "; reel only at Digi-Key (min %d), unit price is the reel price" % qq
        if v.get("alias_of"):
            basis += "; listed as " + v["alias_of"]
        r["price_basis"] = basis
        r["link_status"] = "Digi-Key API %s: %s" % (day, "%s in stock" % v["stock"] if v["stock"] else "not stocked at Digi-Key now")
        n += 1
    w = csv.DictWriter(open(LINKS, "w", encoding="utf-8", newline=""), cols, lineterminator="\n")
    w.writeheader(); w.writerows(rows)
    print(n, "parts merged")


main()
