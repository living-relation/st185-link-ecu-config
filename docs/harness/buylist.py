import json, os, re, collections, datetime
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
# The eight current looms. Repointed 2026-09-22 - this used to read the
# pre-split Signal/Power/CAN/EngineRoom-C files, so every buy list generated
# before that date missed everything the rebuild added (the CSB3 HD30
# connector and its size-20 contacts among them).
F = ("ST185-A-ECU.harness", "ST185-A-engine.harness",
     "ST185-B-ECU.harness", "ST185-B-engine.harness",
     "ST185-CAN.harness", "ST185-EngineRoom-C.harness",
     "ST185-ClusterLED.harness", "ST185-WheelSpeed.harness",
     "ST185-AntiTheft.harness")

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
 ("RL9080-301-F1RE","Amphenol","RADLOK 8.0 feed-through receptacle, panel mount, 200A/1kV, RED - firewall POSITIVE. Mates RL00801-50RE each side.",1,0),
 ("RL9080-301-F1","Amphenol","RADLOK 8.0 feed-through receptacle, panel mount, 200A/1kV, BLACK - firewall NEGATIVE. Mates RL00801-50BK each side.",1,0),
 ("1/0 AWG welding cable red/black","generic","Trunk battery +/−, firewall crossing, engine ground. Sized on voltage drop over a ~36 ft round trip: 1.06V cranking, 0.57V at 160A charge. 2 AWG was 13% cranking drop - too much. ~45 ft each colour.",1,0),
 ("2 AWG welding cable","generic","Alternator B+ to starter post only. Short engine-bay jumper, never crosses the firewall.",1,0),
 ("Jump lugs 1/0","generic","Trunk +, trunk −, PDB, starter B+, engine block, engine-bay jump post",8,0),
 ("8 AWG TXL red/black","generic","EPS pump 12V/GND (passenger ABS trough) and uprated fan 12V/GND (core support)",1,0),

 ("Micro ISO relays x4","TE Connectivity","HEAD LH, HEAD RH, RTR, device-hold and alternator-excite relays replacing the PMU (plan 6.48). 8 owned, 6 already assigned to k_efi/k_etb/k_fp/k_fan/k_fan2/k_str.",4,0),
 ("2nd fuse block 12-16 way","generic","Glove box, for the ex-J/B2 body circuits: HEAD LH 15, HEAD RH 15, HAZ-HORN 15, DOME 20, RTR 30, CSB3 5, cluster 10, Pi 15, alt excite 5. TE 2141029-1 is full at F1-F13. Plan 6.48.",1,0),
 ("ANL 100A + holder","generic","Feed for the second fuse block off the PDB stud. Plan 6.48 / redistribution 8.",1,0),
 ("2127","Blue Sea Systems","PDB1 glove-box distribution block, 250A, four 5/16\"-18 studs. Starter is fed direct from the main cable per OEM (plan 6.20), so PDB1 carries accessories only.",1,0),
 ("2719","Blue Sea Systems","MaxiBus insulating cover for PDB1 / 2127. Not optional - PDB1 is inside the cabin.",1,0),
 ("ANL/MEGA 300A + holder","generic","MAIN battery fuse, within ~18in of the trunk battery positive. Protects the whole cabin run - OEM leaves the starter lead unfused but its battery is 2ft away, ours is 12ft. See plan 6.20.",1,0),
 ("ANL 175A + holder","generic","Alternator B+ protection. OEM uses 100A FL ALT for the stock alternator; scaled for the 160A unit. See plan 6.20.",1,0),
 ("Battery master cutoff","generic","Trunk, alongside the main fuse. Motorsport requirement and the sane place for it.",1,0),
 ("generic","generic","22 AWG WHITE TEFZEL, SINGLE CONDUCTOR, SHIELDED (tinned copper braid). EPS speed pulse Aux 7 -> pump conn B, and any other screened single signal. Shield grounded at the ECU end only. IN STOCK.",1,1),
 ("2428-011-2405","TE DEUTSCH","Backshell 24SZ right-angle L017",1,1),
 ("M902-2243","TE DEUTSCH","Backshell 24SZ straight L015",1,1),
 ("16-04477","TE DEUTSCH","Gasket 24SZ",6,4),
 ("2411-001-2405","TE DEUTSCH","Panel nut size 24",3,4),
]

req, meta = collections.Counter(), {}
# A connector that appears in more than one loom is ONE physical part - bulkhead A
# lives in three files, bulkhead B in two.  Count the first copy and skip the rest.
# The dedupe keys on the component id, so it is only safe while the same id always
# means the same item: SHARED below records what got skipped, and the run aborts if
# two files disagree about a shared connector's part or contact stamps.
copies = collections.OrderedDict()   # connector id -> [(loom, connector, parts), ...]
for f in F:
    loom = f[6:-8]
    d = json.load(open(os.path.join(R,f), encoding="utf-8"))
    parts = {}
    for k in [x for x in d if x.endswith("Parts")]:
        for q in d[k]: parts[q["id"]] = q
    for c in d.get("connectors", []):
        copies.setdefault(c["id"], []).append((loom, c, parts))
    for coll in ("resistors", "diodes", "terminals", "branchPoints"):
        for n in d.get(coll, []):
            pid = n.get("partId") or n.get("bootPartId")
            if pid and pid in parts:
                q = parts[pid]; req[q["partNumber"]] += 1; meta[q["partNumber"]] = q

def stamp(c, parts):
    """What this copy claims: its part number and every contact/plug it names.
    A cross-reference dummy claims nothing, so it stamps empty and never wins."""
    pn = (parts.get(c.get("partId")) or {}).get("partNumber")
    ct = tuple(sorted((cv["id"], cv.get("contactPartId"), cv.get("cavityPlugPartId"))
                      for cv in c.get("cavities", []) if cv.get("contactPartId")
                      or cv.get("cavityPlugPartId")))
    return pn, ct

SHARED, clash = {}, []
for cid, cc in copies.items():
    stamps = [(loom, stamp(c, p)) for loom, c, p in cc]
    real = [s for s in stamps if s[1][0] or s[1][1]]   # copies that claim a part
    if not real:
        continue                                        # partless everywhere - nothing to buy
    # every copy that claims anything must claim the SAME thing, or the dedupe
    # below would silently pick one of two different items.
    for loom, s in real[1:]:
        if s != real[0][1]:
            clash.append("%s: %s disagrees with %s" % (cid, loom, real[0][0]))
    if len(cc) > 1:
        SHARED[cid] = ([loom for loom, _, _ in cc], real[0][0])
    # count the copy that actually carries the parts, not whichever file came first
    loom0 = real[0][0]
    c, parts = next((c, p) for l, c, p in cc if l == loom0)
    if c.get("partId") and c["partId"] in parts:
        q = parts[c["partId"]]; req[q["partNumber"]] += 1; meta[q["partNumber"]] = q
    for cv in c.get("cavities", []):
        for key in ("contactPartId","cavityPlugPartId"):
            pid = cv.get(key)
            if pid and pid in parts:
                q = parts[pid]; req[q["partNumber"]] += 1; meta[q["partNumber"]] = q
if clash:
    raise SystemExit("Shared connectors are inconsistent between looms:\n  "
                     + "\n  ".join(clash))

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
 "Generated on %s from the eight `.harness` files in `docs/harness/rebuild/`:"
 % datetime.date.today().isoformat(),
 "`" + "`, `".join(x[6:-8] for x in F) + "`.",
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
out += ["", "## Counted once, drawn more than once", "",
 "These connectors are one physical part that appears on several drawings — a bulkhead",
 "has to be on both looms that pass through it. The buy list counts the first copy and",
 "skips the rest. If you add up the parts lists off the individual drawings by hand you",
 "will over-order these; use this list, not the drawings.", "",
 "| Connector | One part, drawn on | Counted in |", "|---|---|---|"]
for cid, (looms, owner) in sorted(SHARED.items()):
    out.append("| `%s` | %s | %s |" % (cid, ", ".join(looms), owner))
out += ["", "## Still unspecified", "",
 "- **Moulded breakout boots** for the branch points — `boot_breakout` is a placeholder. "
 "Needs a real dash number per branch OD once the trunk diameters are known.",
 "- **HCR 150 mating hardware** — confirm the receptacle and terminal part numbers for "
 "`V23132-A2001-B200` with the supplier before ordering.", ""]
p = os.path.join(os.path.dirname(R), "NEED-TO-BUY.md")
open(p, "w", encoding="utf-8").write("\n".join(out))
print("wrote", p)
print("to buy: %d lines, covered: %d lines" % (len(rows_buy), len(rows_ok)))
for r in sorted(rows_buy, key=lambda x: -x[5]):
    print("   BUY %-32s need %-4d have %-4d short %d" % (r[0], r[3], r[4], r[5]))
