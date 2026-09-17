import json, os, re, collections, datetime
R = os.path.dirname(os.path.abspath(__file__))
F = ("ST185-Signal.harness","ST185-Power.harness","ST185-CAN.harness","ST185-EngineRoom-C.harness")

ONHAND = {  # from TE_BOM_with_screenshots.xlsx + the three TE invoices in Drive
 "0460-202-1631":130,"0460-215-1631":60,"0462-201-1631":118,"0462-209-1631":51,
 "0462-221-1631":25,"0460-220-1231":20,"0462-210-1231":20,"0460-204-08141":5,
 "0462-203-08141":9,"0460-204-0490":5,"5960-203-04141":5,"0462-203-04141":9,
 "5962-203-04141":5,"HDP24-24-47PE":1,"HDP24-24-47PE-L017":1,"HDP24-24-47SE-L017":1,
 "HDP26-24-47SE-L015":1,"HDP26-24-47PE-L015":1,"HDP24-24-21PN":1,"HDP26-24-21SN":1,
 "HDP24-24-9PE":2,"HDP26-24-9SE":2,"5-1393292-8":2,"4-1904124-2":2,"4-1904124-3":2,
 "6-1419137-4":2,"1416010-1":2,"1-1393304-0":2,"1-1414147-0":3,"2141029-1":1,
 "0413-214-1205":10,"114018-ZZ":10,"114019-ZZ":10,"4-1437290-0":2,"4-1437290-1":2,
 "3-1447221-3":68,"3-1447221-4":68,"0462-201-16141":12,"DT06-2S":2,"DT06-3S":2,
 "DTM06-4S":1,"DTM06-6S":1,"12084200":6,"15326427":5,"42281-1":20,"60249-1":21,
 "1928403970":2,"GT150-2":1,"FLEX-3":1,"TSPD-3":1,"1 928 403 874":1,
 "13519047":1,"D 261 205 358-01":1,"12052641":1,
 # MRS EPS pump connectors - Toyota/Sumitomo TS090, on hand (not from TE invoices)
 "90980-12068":1,"90980-10897":1,"90980-10942":1,
}
EXTRA = [  # harness hardware the .harness schema cannot attach to a connector
 ("1-1904045-6","TE Connectivity","Micro ISO relay connector kit (harness-side socket for the V23074 relays)",6,0),
 ("VCF7-1000 / 1393310-4","TE Connectivity","Maxi relay mounting block",1,1),
 ("280756-4","TE Connectivity","250-series terminal 12-10 AWG, for VCF7 power legs",4,0),
 ("HCR 150 mating hardware","TE Connectivity","Receptacle / terminals for V23132-A2001-B200 - CONFIRM with supplier",1,0),
 ("2 AWG welding cable red/black","generic","Trunk battery +/−, RADLOK charge/start, jump post. Length TBD on the car.",1,0),
 ("Jump lugs 2 AWG / 1/0","generic","Trunk +, trunk −, PDB, starter B+, engine block, engine-bay jump post",8,0),
 ("8 AWG TXL red/black","generic","EPS pump 12V/GND (passenger ABS trough) and uprated fan 12V/GND (core support)",1,0),
 ("ANL 150A + holder","generic","PMU-16 M6 input fuse at the glove-box PDB (or PMU's own input fuse)",1,0),
 ("2428-011-2405","TE DEUTSCH","Backshell 24SZ right-angle L017",1,1),
 ("M902-2243","TE DEUTSCH","Backshell 24SZ straight L015",1,1),
 ("16-04477","TE DEUTSCH","Gasket 24SZ",6,4),
 ("2411-001-2405","TE DEUTSCH","Panel nut size 24",3,4),
]

req, meta = collections.Counter(), {}
seen_conn = set()
for f in F:
    d = json.load(open(os.path.join(R,f), encoding="utf-8"))
    parts = {}
    for k in [x for x in d if x.endswith("Parts")]:
        for q in d[k]: parts[q["id"]] = q
    for c in d.get("connectors", []):
        if c["id"] in seen_conn: continue
        seen_conn.add(c["id"])
        if c.get("partId") and c["partId"] in parts:
            q = parts[c["partId"]]; req[q["partNumber"]] += 1; meta[q["partNumber"]] = q
        for cv in c.get("cavities", []):
            for key in ("contactPartId","cavityPlugPartId"):
                pid = cv.get(key)
                if pid and pid in parts:
                    q = parts[pid]; req[q["partNumber"]] += 1; meta[q["partNumber"]] = q
    for coll, pk in (("resistors","resistorParts"),("branchPoints","bootParts")):
        for n in d.get(coll, []):
            pid = n.get("partId") or n.get("bootPartId")
            if pid and pid in parts:
                q = parts[pid]; req[q["partNumber"]] += 1; meta[q["partNumber"]] = q

# things that are modelled as blocks but are not parts anyone buys for this harness:
# OEM items already on the car, or device-side terminals that come with the device.
NOT_A_PART = re.compile(r"^\(|^TBD\b")
rows_buy, rows_ok, rows_na = [], [], []
for pn, n in sorted(req.items()):
    have = ONHAND.get(pn, 0); short = max(0, n - have)
    d_ = meta[pn]
    r = (pn, d_.get("manufacturer",""), (d_.get("description") or "").split(" - OWNED")[0][:62], n, have, short)
    if NOT_A_PART.match(pn): rows_na.append(r)
    else: (rows_buy if short else rows_ok).append(r)
for pn, mf, desc, n, have in EXTRA:
    short = max(0, n - have)
    (rows_buy if short else rows_ok).append((pn, mf, desc, n, have, short))

out = ["# Harness — need to buy",
 "",
 "Generated from `ST185-Signal.harness`, `ST185-Power.harness`, `ST185-CAN.harness` and `ST185-EngineRoom-C.harness` on %s."
 % datetime.date.today().isoformat(),
 "On-hand comes from `TE_BOM_with_screenshots.xlsx` plus the three TE invoices in Drive.",
 "Regenerate with `docs/harness/buylist.py` after any harness change — do not hand-edit.",
 "", "## Short — order these", "",
 "| Part number | Mfr | Description | Need | Have | **Buy** |", "|---|---|---|---:|---:|---:|"]
for r in sorted(rows_buy, key=lambda x: -x[5]):
    out.append("| `%s` | %s | %s | %d | %d | **%d** |" % r)
out += ["", "## Covered by stock", "",
        "| Part number | Description | Need | Have |", "|---|---|---:|---:|"]
for r in sorted(rows_ok):
    out.append("| `%s` | %s | %d | %d |" % (r[0], r[2], r[3], r[4]))
out += ["", "## Not purchased — already on the car, or supplied with the device", "",
        "| Modelled as | What it really is | Qty |", "|---|---|---:|"]
for r in sorted(rows_na):
    out.append("| `%s` | %s | %d |" % (r[0], r[2], r[3]))
out += ["", "## Still unspecified", "",
 "- **Moulded breakout boots** for the branch points — `boot_breakout` is a placeholder. "
 "Needs a real dash number per branch OD once the trunk diameters are known.",
 "- **HCR 150 mating hardware** — confirm the receptacle and terminal part numbers for "
 "`V23132-A2001-B200` with the supplier before ordering.", ""]
p = os.path.join(R, "NEED-TO-BUY.md")
open(p, "w", encoding="utf-8").write("\n".join(out))
print("wrote", p)
print("to buy: %d lines, covered: %d lines" % (len(rows_buy), len(rows_ok)))
for r in sorted(rows_buy, key=lambda x: -x[5]):
    print("   BUY %-32s need %-4d have %-4d short %d" % (r[0], r[3], r[4], r[5]))
