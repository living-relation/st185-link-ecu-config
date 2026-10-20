"""Digi-Key Product Information v4 lookup for the project BOM (2-legged OAuth, client credentials).

Keys are read from ~/.secrets/digikey.env (DIGIKEY_CLIENT_ID / DIGIKEY_CLIENT_SECRET); they are never
printed, logged or stored in the repo. Usage:
    python docs/sourcing/digikey_price.py PN [PN ...]            # lookup, print a compact table
    python docs/sourcing/digikey_price.py --from-bom                    # every line of PROJECT-BOM.csv with a real PN and no real price (blank / est / seen)
Results go to _research/digikey-results.json (untracked) as {pn: {...}}; merge_digikey.py folds them into bom-links.csv.
"""
import csv, json, os, re, sys, time, urllib.parse, urllib.request, urllib.error

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ENV = os.path.join(os.path.expanduser("~"), ".secrets", "digikey.env")
OUT = os.path.join(ROOT, "_research", "digikey-results.json")
API = "https://api.digikey.com"


def keys():
    d = {}
    for line in open(ENV, encoding="utf-8"):
        k, _, v = line.strip().partition("=")
        d[k.strip()] = v.strip().strip('"\'')
    return d["DIGIKEY_CLIENT_ID"], d["DIGIKEY_CLIENT_SECRET"]


def token():
    cid, sec = keys()
    body = urllib.parse.urlencode({"client_id": cid, "client_secret": sec, "grant_type": "client_credentials"}).encode()
    with urllib.request.urlopen(urllib.request.Request(API + "/v1/oauth2/token", body)) as r:
        return json.load(r)["access_token"], cid


def search(tok, cid, kw):
    req = urllib.request.Request(API + "/products/v4/search/keyword", json.dumps({"Keywords": kw, "Limit": 5}).encode(), {
        "Authorization": "Bearer " + tok, "X-DIGIKEY-Client-Id": cid, "Content-Type": "application/json",
        "X-DIGIKEY-Locale-Site": "US", "X-DIGIKEY-Locale-Language": "en", "X-DIGIKEY-Locale-Currency": "USD"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(5 * (attempt + 1)); continue
            return {"error": "HTTP %d" % e.code}
    return {"error": "rate limited"}


# BOM part number -> (Digi-Key search text, Digi-Key MPN). Same part sold under another listing name (bulk pack, RoHS suffix)
# or a stock resistor of the stated value; every alias is noted in the BOM line's price basis.
ALIAS = {"ATM-2": "BK/ATM-2", "ATM-5": "BK/ATM-5", "ATM-10": "BK/ATM-10", "ATM-15": "BK/ATM-15", "ATM-20": "BK/ATM-20",
         "ATM-7-1/2": "BK/ATM-7-1/2", "114017": "114017-ZZ", "W8S": "W8S",
         "1k 1/4W": "CF14JT1K00", "1.8k 1/4W": "CF14JT1K80", "3.9k 1/4W": "CF14JT3K90", "10k 1/4W": "CF14JT10K0",
         "470R 1/4W": "CF14JT470R", "120R 1/4W": "RNMF14FTC120R", "2.2k 1/4W 1%": "MFR-25FBF52-2K20"}
SEARCH = {"W8S": "W8S Deutsch wedgelock"}


def norm(s):
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


def compact(pn, resp):
    """Pick the product whose manufacturer PN equals pn (exact, ignoring punctuation); else report the nearest."""
    if "error" in resp:
        return {"status": resp["error"]}
    prods = resp.get("Products") or []
    exact = [p for p in prods if norm(p.get("ManufacturerProductNumber")) == norm(pn)]
    if not exact:
        return {"status": "no exact match", "near": [p.get("ManufacturerProductNumber") for p in prods][:5]}
    p = exact[0]
    vs = p.get("ProductVariations") or []
    out = {"status": "ok", "mpn": p.get("ManufacturerProductNumber"), "maker": (p.get("Manufacturer") or {}).get("Name"),
           "url": p.get("ProductUrl"), "stock": p.get("QuantityAvailable"), "desc": (p.get("Description") or {}).get("ProductDescription"),
           "obsolete": p.get("Discontinued") or p.get("EndOfLife"), "variations": []}
    for v in vs:
        out["variations"].append({"dkpn": v.get("DigiKeyProductNumber"), "pkg": (v.get("PackageType") or {}).get("Name"),
                                  "min": v.get("MinimumOrderQuantity"), "stock": v.get("QuantityAvailableforPackageType"),
                                  "breaks": [(b["BreakQuantity"], b["UnitPrice"]) for b in v.get("StandardPricing") or []]})
    return out


def main(a):
    if "--from-bom" in a:
        pns = []
        for r in csv.DictReader(open(os.path.join(ROOT, "docs", "sourcing", "PROJECT-BOM.csv"), encoding="utf-8")):
            pn = r["part_number"]
            if pn and pn != "TBD" and r["price_basis"] in ("", "est", "seen") and not pn.startswith("(") and pn not in pns:
                pns.append(pn)
    else:
        pns = a
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    tok, cid = token()
    for pn in pns:
        if pn in res and res[pn].get("status") == "ok" or (pn in res and pn not in ALIAS):
            continue
        mpn = ALIAS.get(pn, pn)
        res[pn] = compact(mpn, search(tok, cid, SEARCH.get(pn, mpn)))
        if res[pn]["status"] == "ok" and mpn != pn:
            res[pn]["alias_of"] = mpn
        s = res[pn]
        print(pn, "->", s["status"], s.get("stock", ""), (s["variations"][0]["breaks"][:2] if s.get("variations") else s.get("near", "")))
        time.sleep(0.6)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        json.dump(res, open(OUT, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
