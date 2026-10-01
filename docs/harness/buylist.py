import json, os, re, collections

import model

R = model.REB
# Every harness in interfaces.json - the registry is the list, so a new or
# retired drawing can never silently drop off the buy list again.
FILES = model.harness_files()
F = tuple(FILES.values())

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
 "DT06-12SA":2,"DT04-12PA":2,"W12P":2,"W12S":2,
 # MRS EPS pump connectors - Toyota/Sumitomo TS090, on hand (not from TE invoices)
 "90980-12068":1,"90980-10897":1,"90980-10942":1,
 # 2026-09-25 from docs/sourcing/te-on-hand-bom.csv (not in the older xlsx pull)
 "1393310-4":1,"282080-1":2,"282110-1":10,"281934-2":10,
}
EXTRA = [  # harness hardware the .harness schema cannot attach to a connector
 # 2026-09-25: the relays now sit in VCF7 sockets drawn as mount parts, so the
 # socket and its 280755-4 / 280756-4 / 42281-1 terminals come off the drawings.
 ("282080-1","TE Connectivity","HOUSING, PLUG, SUPERSEAL 1.5, 2 POS",1,2),
 ("281934-2","TE Connectivity","SEAL, WIRE, SUPERSEAL 1.5",2,10),
 ("AMI-50","Eaton Bussmann","FUSE, AMI, 50 A, M5 BOLT-DOWN",1,0),
 ("AMI-40","Eaton Bussmann","FUSE, AMI, 40 A, M5 BOLT-DOWN",1,0),
 ("AMI-30","Eaton Bussmann","FUSE, AMI, 30 A, M5 BOLT-DOWN",1,0),
 ("AMI-60","Eaton Bussmann","FUSE, AMI, 60 A, M5 BOLT-DOWN",1,0),
 ("RL9080-301-F1RE","Amphenol","RECEPTACLE, FEED-THROUGH, RADLOK 8.0, PANEL MOUNT, 200 A, 1 KV, RED, MATES RL00801-50RE",1,0),
 ("RL9080-301-F1","Amphenol","RECEPTACLE, FEED-THROUGH, RADLOK 8.0, PANEL MOUNT, 200 A, 1 KV, BLACK, MATES RL00801-50BK",1,0),
 ("1/0 AWG welding cable red/black","generic","CABLE, WELDING, 1/0 AWG, RED AND BLACK, APPROX 45 FT EACH COLOUR",1,0),
 ("2 AWG welding cable","generic","CABLE, WELDING, 2 AWG",1,0),
 ("Jump lugs 1/0","generic","LUG, RING, COPPER, 1/0 AWG",8,0),
 ("8 AWG TXL red/black","generic","WIRE, ELECTRICAL, 8 AWG, RED AND BLACK, SAE J1128 TXL",1,0),

 ("Micro ISO relays x4","TE Connectivity","RELAY, PLUG-IN, MICRO ISO, 1 FORM A, 12 VDC COIL",4,4),
 ("2nd fuse block 12-16 way","generic","FUSE BLOCK, BLADE, 12-16 WAY",1,0),
 ("ANL 100A + holder","generic","FUSE, ANL, 100 A, WITH HOLDER",1,0),
 ("2127","Blue Sea Systems","BUSBAR, POWERBAR, 250 A, FOUR 5/16-18 STUDS",1,0),
 ("2719","Blue Sea Systems","COVER, INSULATING, MAXIBUS, FITS 2127",1,0),
 ("ANL/MEGA 300A + holder","generic","FUSE, ANL OR MEGA, 300 A, WITH HOLDER",1,0),
 ("Alternator protection 175A","generic","FUSIBLE LINK OR INLINE FUSE / CIRCUIT BREAKER, 175 A",1,0),
 ("Longacre 4-terminal kill switch","Longacre","SWITCH, BATTERY DISCONNECT, 4 TERMINAL, 2 POLE",1,0),
 ("generic","generic","CABLE, SHIELDED, 1 CONDUCTOR, 22 AWG, WHITE, ETFE (TEFZEL), TINNED COPPER BRAID",1,1),
 # 2026-09-29: HDP24 shell A/B bulkheads and their backshells/gasket/panel nuts
 # are retired - replaced by the shared DRB102 (see docs/harness/redesign/DECISIONS.md).
 # The DRB's own wedgelocks take their place; the .harness schema only holds one
 # lockPartId per connector configuration, but the DRB102 needs two per shell
 # (left + right), so all four are tracked here instead of in a lockParts config.
 ("WB-51PAL","TE DEUTSCH","WEDGELOCK, DRB 102/128, RECEPTACLE, LEFT",1,0),
 ("WB-51PAR","TE DEUTSCH","WEDGELOCK, DRB 102/128, RECEPTACLE, RIGHT",1,0),
 ("WB-51SAL","TE DEUTSCH","WEDGELOCK, DRB 102/128, PLUG, LEFT",1,0),
 ("WB-51SAR","TE DEUTSCH","WEDGELOCK, DRB 102/128, PLUG, RIGHT",1,0),
]

# Pin-side mates crimped onto device flying leads. Device side, so not drawn on
# any loom (harness.design rule: the drawing ends at the harness connector).
DEVICE_SIDE = [
 ("DT04-12PA","TE DEUTSCH","CONN RECP DT 12-WAY PIN SEALED A-KEY",1),
 ("W12P","TE DEUTSCH","WEDGELOCK, DT, 12-WAY RECEPTACLE",1),
 ("DT04-2P","TE DEUTSCH","CONN RECP DT 2-WAY PIN SEALED",3),
 ("W2P","TE DEUTSCH","WEDGELOCK, DT, 2-WAY RECEPTACLE",3),
 ("DT04-3P","TE DEUTSCH","CONN RECP DT 3-WAY PIN SEALED",1),
 ("W3P","TE DEUTSCH","WEDGELOCK, DT, 3-WAY RECEPTACLE",1),
 ("0460-202-1631","TE DEUTSCH","CONTACT, PIN, SOLID, SIZE 16, 20-16 AWG, 13A, GOLD",21),
]

req, meta = collections.Counter(), {}
WIRED = {}   # loom -> {(node id, handle)} every conductor end, to resolve default contacts
READ = [model.REGISTRY]
wire_used = collections.Counter()   # (loom, part number) -> conductor count
# A connector that appears in more than one loom is ONE physical part - bulkhead A
# lives in three files, bulkhead B in two.  Count the first copy and skip the rest.
# The dedupe keys on the component id, so it is only safe while the same id always
# means the same item: SHARED below records what got skipped, and the run aborts if
# two files disagree about a shared connector's part or contact stamps.
copies = collections.OrderedDict()   # connector id -> [(loom, connector, parts), ...]
for loom, f in FILES.items():
    path = os.path.join(R, f)
    READ.append(path)
    d = json.load(open(path, encoding="utf-8"))
    parts = {}
    for k in [x for x in d if x.endswith("Parts")]:
        for q in d[k]: parts[q["id"]] = q
    w = set()
    for x in d.get("wires", []):
        for e in (x.get("source"), x.get("target")):
            if e: w.add((e.get("id"), e.get("handle")))
    for cb in d.get("cables", []) + d.get("twistedWires", []):
        for x in cb.get("cores", []) + cb.get("wires", []) + ([cb["shield"]] if cb.get("shield") else []):
            for e in (x.get("source"), x.get("target")):
                if e: w.add((e.get("id"), e.get("handle")))
    WIRED[loom] = w
    for cond, _cable, _screen in model.conductors(d):
        q = parts.get(cond.get("partId")) or {}
        pn = q.get("partNumber")
        if pn:
            wire_used[(loom, pn)] += 1
            meta.setdefault(pn, q)
    for c in d.get("connectors", []):
        copies.setdefault(c["id"], []).append((loom, c, parts))
    for coll in ("resistors", "diodes", "terminals", "splices", "branchPoints"):
        for n in d.get(coll, []):
            if n.get("excludeFromBom"):
                continue
            pid = n.get("partId") or n.get("bootPartId")
            if pid and pid in parts:
                q = parts[pid]; req[q["partNumber"]] += 1; meta[q["partNumber"]] = q

def stamp(c, parts):
    """What this copy claims: its part number and every contact/plug it names.
    A cross-reference dummy claims nothing, so it stamps empty and never wins.
    2026-09-25: neither does a copy marked excludeFromBom - every non-owner copy
    of a shared connector is excluded, so it is counted once, on its owner loom."""
    if c.get("excludeFromBom"):
        return None, ()
    pn = (parts.get(c.get("partId")) or {}).get("partNumber")
    ct = tuple(sorted((cv["id"], cv.get("contactPartId"), cv.get("cavityPlugPartId"))
                      for cv in c.get("cavities", []) if cv.get("contactPartId")
                      or cv.get("cavityPlugPartId")))
    return pn, ct

SHARED, clash = {}, []
# physicalPartGroup: two or more DIFFERENT connector ids that are documentation
# halves of ONE physical part - e.g. the DRB102 bulkhead's A-half and B-half,
# split so the A/B ECU-letter gate still works (docs/harness/redesign/DECISIONS.md,
# 2026-09-29). This is a different problem from SHARED above: SHARED is the SAME
# id copied into more than one loom (always identical cavities, asserted by the
# clash check); a physicalPartGroup is different ids with different, non-overlapping
# cavities that nonetheless share one housing. So only the housing part number and
# its configuration hardware (lock/boot/backshell/mount/dustCover) are counted once
# per group below - each half's own cavities are real and stay per-id, uncoditionally.
# Owner = alphabetically-first id in the group, so it never depends on the order
# harness_files() happens to return.
group_members = collections.OrderedDict()
for cid, cc in copies.items():
    pg = cc[0][1].get("physicalPartGroup")
    if pg:
        group_members.setdefault(pg, []).append(cid)
group_owner = {pg: min(ids) for pg, ids in group_members.items()}

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
    pg = c.get("physicalPartGroup")
    is_owner = (group_owner.get(pg) == cid) if pg else True
    if is_owner and c.get("partId") and c["partId"] in parts:
        q = parts[c["partId"]]; req[q["partNumber"]] += 1; meta[q["partNumber"]] = q
    # The part's configuration supplies the lock/boot/backshell and the DEFAULT
    # contact (wired cavity) or plug (unwired cavity). Before 2026-09-24 only
    # explicitly stamped cavities were counted, so every config-default contact
    # and every wedgelock was missing from the buy list.
    cfgs = (parts.get(c.get("partId")) or {}).get("configurations") or []
    cfg = next((x for x in cfgs if x.get("id") == c.get("configurationId")), cfgs[0] if cfgs else {})
    if is_owner:
        for key in ("lockPartId","bootPartId","backshellPartId","mountPartId","dustCoverPartId"):
            pid = cfg.get(key)
            if pid and pid in parts:
                q = parts[pid]; req[q["partNumber"]] += 1; meta[q["partNumber"]] = q
    for cv in c.get("cavities", []):
        if cv.get("notConnected"):
            continue
        if "contactPartId" in cv or "cavityPlugPartId" in cv:
            pids = [cv.get("contactPartId"), cv.get("cavityPlugPartId")]
        elif any((cid, cv["id"]) in WIRED[l] for l, _, _ in cc):
            pids = [cfg.get("contactPartId")]
        else:
            pids = [cfg.get("cavityPlugPartId")]
        for pid in pids:
            if pid and pid in parts:
                q = parts[pid]; req[q["partNumber"]] += 1; meta[q["partNumber"]] = q
if clash:
    raise SystemExit("Shared connectors are inconsistent between looms:\n  "
                     + "\n  ".join(clash))

for pn, mf, desc, n in DEVICE_SIDE:
    req[pn] += n
    meta.setdefault(pn, {"partNumber": pn, "manufacturer": mf, "description": desc})

# things that are modelled as blocks but are not parts anyone buys for this harness:
# OEM items already on the car, or device-side terminals that come with the device.
NOT_A_PART = re.compile(r"^\(|^TBD\b")
rows_buy, rows_ok, rows_na = [], [], []
for pn, n in sorted(req.items()):
    have = ONHAND.get(pn, 0); short = max(0, n - have)
    d_ = meta[pn]
    r = (pn, d_.get("manufacturer",""), d_.get("description") or "", n, have, short)
    if NOT_A_PART.match(pn): rows_na.append(r)
    else: (rows_buy if short else rows_ok).append(r)
for pn, mf, desc, n, have in EXTRA:
    short = max(0, n - have)
    (rows_buy if short else rows_ok).append((pn, mf, desc, n, have, short))

DIGEST = model.files_sha256(READ)
out = ["# Harness — need to buy",
 "",
 "Generated from SHA-256 `%s` of the %d `.harness` files actually read in `docs/harness/rebuild/` plus `interfaces.json`:"
 % (DIGEST, len(F)),
 "`" + "`, `".join(FILES) + "`.",
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
out += ["", "## One housing, drawn as two logical halves", "",
 "These connector ids are DIFFERENT nodes with different, non-overlapping cavities, not",
 "copies of the same node - but they are still one physical housing, split across an",
 "A-half and a B-half so the A/B ECU-letter gate applies to each side's own signals.",
 "The housing part number and its wedgelock/mount/backshell hardware are counted once,",
 "on the alphabetically-first half; every cavity's own contacts and plugs are still",
 "counted on both halves, since those are real and separate.", "",
 "| Group | Halves | Counted in |", "|---|---|---|"]
for pg, ids in sorted(group_members.items()):
    out.append("| `%s` | %s | `%s` |" % (pg, ", ".join(sorted(ids)), group_owner[pg]))
REG = model.registry()
out += ["", "## Inline interfaces - one connector pair per harness boundary", "",
 "Each half is counted once, on the harness that owns it (the receiving harness owns the",
 "mating half). Contacts and wedgelocks come from each half's part configuration above.", "",
 "| Interface | Family | Source half | Receiving half |", "|---|---|---|---|"]
for ix in REG.get("interfaces", []):
    s = next(h for h in ix["halves"] if h["role"] == "source")
    r = next(h for h in ix["halves"] if h["role"] == "receiving")
    out.append("| `%s` | %s | `%s` on %s | `%s` on %s |"
               % (ix["id"], ix.get("family", ""), s["connector"], s["harness"], r["connector"], r["harness"]))
fl_by = collections.Counter(f["harness"] for f in REG.get("flyingLeads", []))
out += ["", "## OEM flying leads - splice material only, no OEM housing", "",
 "Each lead is one solder sleeve (`GENERIC FLYING LEAD` above). The EWD locator for every lead",
 "is in `interfaces.json` and in the build list's EWD column.", "",
 "| Harness | Flying leads |", "|---|---:|"]
for h, n in sorted(fl_by.items()):
    out.append("| %s | %d |" % (h, n))
cab = collections.Counter()
for loom, fn in model.harness_files(REG).items():
    d = model.load(fn)
    cp = {p["id"]: p for p in d.get("cableParts", [])}
    for cb in d.get("cables", []):
        p = cp.get(cb.get("partId")) or {}
        cab[(loom, p.get("partNumber", cb.get("partId")))] += 1
out += ["", "## Screened cable pieces by owning harness", "",
 "Cut lengths are in the build list (`Est mm`). Device endpoints (VRC) claim no connector.", "",
 "| Harness | Cable | Pieces |", "|---|---|---:|"]
for (loom, pn), n in sorted(cab.items()):
    out.append("| %s | `%s` | %d |" % (loom, pn, n))
out += ["", "## Wire part numbers on numbered drawings", "",
 "Taken from each conductor's wire part on the numbered `.harness` files actually read.",
 "A drawing that now uses an M22759/16 part is listed under that part, not under EW-1C.",
 "",
 "| Harness | Part number | Description | Conductors |", "|---|---|---|---:|"]
for (loom, pn), n in sorted(wire_used.items()):
    q = meta.get(pn) or {}
    out.append("| %s | `%s` | %s | %d |" % (loom, pn, q.get("description") or "", n))
out += ["", "## Still unspecified", "",
 "- **Moulded breakout boots** for the branch points — `boot_breakout` is a placeholder. "
 "Needs a real dash number per branch OD once the trunk diameters are known.",
 ""]
p = os.path.join(os.path.dirname(R), "NEED-TO-BUY.md")
open(p, "w", encoding="utf-8").write("\n".join(out))
print("wrote", p)
print("to buy: %d lines, covered: %d lines" % (len(rows_buy), len(rows_ok)))
for r in sorted(rows_buy, key=lambda x: -x[5]):
    print("   BUY %-32s need %-4d have %-4d short %d" % (r[0], r[3], r[4], r[5]))
