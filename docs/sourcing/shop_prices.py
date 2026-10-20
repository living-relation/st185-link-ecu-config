"""Price BOM lines from the approved small vendors that run Shopify stores (public products.json, no login):
KSV Looms, Custom Connector Kits, Race Spec Online. Exact SKU match to the BOM part number only; terminals use the
"-L" loose-piece listing (not the reel). Writes unit price, product URL and basis into bom-links.csv for lines that
have no Digi-Key price. Run: python docs/sourcing/shop_prices.py [--date 2026-10-20]
"""
import csv, json, os, re, sys, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LINKS = os.path.join(ROOT, "docs", "sourcing", "bom-links.csv")
BOM = os.path.join(ROOT, "docs", "sourcing", "PROJECT-BOM.csv")
SHOPS = {"KSV Looms": "https://www.ksvlooms.com", "Custom Connector Kits": "https://www.customconnectorkits.com",
         "Race Spec Online": "https://racespeconline.com"}
FT_PER_M = 3.28084
# BOM part number -> (shop, SKU) where the vendor's SKU is not the plain part number; "equivalent" = not the OEM part itself
SKU = {"90980-10897": ("KSV Looms", None, "equivalent kit"), "90980-11062": ("KSV Looms", None, "equivalent kit"),
       "90980-11885": ("KSV Looms", None, "equivalent kit"), "D 261 205 358-01": ("KSV Looms", None, "equivalent kit")}


def norm(s):
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


def catalog():
    out = []
    for shop, base in SHOPS.items():
        pg = 1
        while pg < 40:
            req = urllib.request.Request("%s/products.json?limit=250&page=%d" % (base, pg), headers={"User-Agent": "Mozilla/5.0"})
            ps = json.load(urllib.request.urlopen(req, timeout=60)).get("products", [])
            if not ps:
                break
            for p in ps:
                for v in p["variants"]:
                    out.append(dict(shop=shop, title=p["title"], sku=v.get("sku") or "", price=float(v["price"]), ok=v.get("available"),
                                    url="%s/products/%s?variant=%s" % (base, p["handle"], v["id"])))
            pg += 1
    return out


def pick(pn, cat):
    n = norm(pn)
    for sku in (n + "L", n):   # loose piece first, then the plain listing
        hits = [c for c in cat if norm(c["sku"]) == sku and c["ok"] and "REEL" not in c["title"].upper()]
        if hits:
            return min(hits, key=lambda c: c["price"]), ""
    if pn in SKU:
        kw = {"90980-10897": "90980-10897", "90980-11062": "90980-11062", "90980-11885": "90980-11885", "D 261 205 358-01": "358-01"}[pn]
        hits = [c for c in cat if c["shop"] == "KSV Looms" and kw in c["title"] and c["ok"] and "Pack" not in c["title"]]
        hits = [c for c in hits if "Connector Kit" in c["title"]]
        if hits:
            return min(hits, key=lambda c: c["price"]), "; equivalent connector kit, not the OEM part: confirm it fits"
    return None, ""


def main():
    day = sys.argv[sys.argv.index("--date") + 1] if "--date" in sys.argv else "2026-10-20"
    cat = catalog()
    bom = list(csv.DictReader(open(BOM, encoding="utf-8")))
    unit = {r["part_number"]: r["unit"] for r in bom}
    want = sorted({r["part_number"] for r in bom if r["unit_price_usd"] == "" and r["part_number"] not in ("TBD", "")
                   and not r["part_number"].startswith("(")})
    rows = list(csv.DictReader(open(LINKS, encoding="utf-8-sig", newline="")))
    cols = list(rows[0].keys())
    by = {r["pn"]: r for r in rows}
    n = 0
    for pn in want:
        c, note = pick(pn, cat)
        if not c:
            continue
        price, per = c["price"], ""
        if unit.get(pn) == "m":   # vendor sells tubing and wire per foot; the BOM counts tubing in metres
            price, per = c["price"] * FT_PER_M, "; $%.2f per ft" % c["price"]
        r = by.get(pn)
        if r is None:
            r = {k: "" for k in cols}; r["pn"] = pn; rows.append(r); by[pn] = r
        r["buy_url"] = c["url"]
        r["unit_usd"] = "%.4f" % price if price < 0.1 else "%.2f" % price
        r["price_basis"] = "%s, %s%s%s" % (c["shop"], day, per, note)
        r["link_status"] = "vendor page read %s (products.json), in stock" % day
        n += 1
    w = csv.DictWriter(open(LINKS, "w", encoding="utf-8", newline=""), cols, lineterminator="\n")
    w.writeheader(); w.writerows(rows)
    print(n, "parts priced from vendor stores")


if __name__ == "__main__":
    main()
