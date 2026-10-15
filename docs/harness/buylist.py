import json, os, re, csv, collections, sys, difflib

import model

R = model.REB
# Every harness in interfaces.json - the registry is the list, so a new or
# retired drawing can never silently drop off the buy list again.
F = tuple(model.harness_files().values())

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
 # 2026-10-14 fuse boxes: AMP MCP 2.8K receptacle, te-on-hand-bom.csv
 "1241388-2":10,
 # 2026-10-15 rear lamp ends (R113): 40 mm cuts of ATUM-4/1-0, from te-on-hand-bom.csv NB11014001
 # ATUM-4/1-0-SP qty_ordered 2 (sold by the metre, so read as 2 m = 50 cuts; an upper bound, check the shelf)
 "ATUM-4/1-0":50,
}
EXTRA = [  # harness hardware the .harness schema cannot attach to a connector
 # 2026-09-25: the relays now sit in VCF7 sockets drawn as mount parts, so the
 # socket and its 280755-4 / 280756-4 / 42281-1 terminals come off the drawings.
 ("282080-1","TE Connectivity","HOUSING, PLUG, SUPERSEAL 1.5, 2 POS",1,2),
 ("281934-2","TE Connectivity","SEAL, WIRE, SUPERSEAL 1.5",2,10),
 # 2026-10-14: the Option B AMI fuses (AMI-30/40/50/60) and the LMI bus bars B109-7046-x are gone from this list: the custom POWER / LOGIC /
 # battery boxes (R70, R75) replace them and their fuses are counted from cad/fusebox/fusebox-parts-*.csv below.
 # 2026-10-12: Option B bus bars are not drawable; RL9080 radlok receptacles below stay.
 ("RL9080-301-F1RE","Amphenol","RECEPTACLE, FEED-THROUGH, RADLOK 8.0, PANEL MOUNT, 200 A, 1 KV, RED, MATES RL00801-50RE",1,0),
 ("RL9080-301-F1","Amphenol","RECEPTACLE, FEED-THROUGH, RADLOK 8.0, PANEL MOUNT, 200 A, 1 KV, BLACK, MATES RL00801-50BK",1,0),
 ("1/0 AWG welding cable red/black","generic","CABLE, WELDING, 1/0 AWG, RED AND BLACK, APPROX 45 FT EACH COLOUR",1,0),
 ("2 AWG welding cable","generic","CABLE, WELDING, 2 AWG",1,0),
 ("Jump lugs 1/0","generic","LUG, RING, COPPER, 1/0 AWG",8,0),
 ("8 AWG TXL red/black","generic","WIRE, ELECTRICAL, 8 AWG, RED AND BLACK, SAE J1128 TXL",1,0),

 ("Micro ISO relays x4","TE Connectivity","RELAY, PLUG-IN, MICRO ISO, 1 FORM A, 12 VDC COIL",4,4),
 ("ANL/MEGA 300A + holder","generic","FUSE, ANL OR MEGA, 300 A, WITH HOLDER",1,0),
 ("Alternator protection 175A","generic","FUSIBLE LINK OR INLINE FUSE / CIRCUIT BREAKER, 175 A",1,0),
 ("generic","generic","CABLE, SHIELDED, 1 CONDUCTOR, 22 AWG, WHITE, ETFE (TEFZEL), TINNED COPPER BRAID",1,1),
 # 2026-09-29: HDP24 shell A/B bulkheads and their backshells/gasket/panel nuts
 # are retired - replaced by the shared DRB102 (see docs/harness/redesign/DECISIONS.md).
 # The DRB's own wedgelocks take their place; the v0.9 .harness schema only held one
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
    w = set()
    for x in d.get("wires", []):
        for e in (x.get("source"), x.get("target")):
            if e: w.add((e.get("id"), e.get("handle")))
    for cb in d.get("cables", []) + d.get("twistedWires", []):
        for x in cb.get("cores", []) + cb.get("wires", []) + ([cb["shield"]] if cb.get("shield") else []):
            for e in (x.get("source"), x.get("target")):
                if e: w.add((e.get("id"), e.get("handle")))
    WIRED[loom] = w
    for c in d.get("connectors", []):
        copies.setdefault(c["id"], []).append((loom, c, parts))
    for coll in ("resistors", "diodes", "terminals", "splices", "branchPoints"):
        for n in d.get(coll, []):
            if n.get("excludeFromBom"):
                continue
            pid = n.get("partId") or n.get("bootPartId")
            if pid and pid in parts:
                q = parts[pid]; req[q["partNumber"]] += 1; meta[q["partNumber"]] = q
            # coverings on a node are one each
            for cid in n.get("coveringIds", []):
                q = next((x for x in d.get("coveringParts", []) if x["id"] == cid), None)
                if q:
                    req[q["partNumber"]] += 1; meta[q["partNumber"]] = q

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
# physical part groups: two or more DIFFERENT connector ids that are drawings of ONE
# physical part - e.g. the DRB102 bulkhead, drawn whole on the A and B looms with the
# other section's cavities N/C (shared-connector rule, DECISIONS S10/S11, 2026-10-12).
# This is a different problem from SHARED above: SHARED is the SAME
# id copied into more than one loom (always identical cavities, asserted by the
# clash check); a physical part group is different ids whose live cavities do not
# overlap but that share one housing. So only the housing part number and
# its configuration hardware (lock/boot/backshell/mount/dustCover) are counted once
# per group below - each file's live cavities stay per-id; N/C cavities are skipped.
# Owner = alphabetically-first id in the group, so it never depends on the order
# harness_files() happens to return.
# The groups live in interfaces.json "physicalPartGroups" (harness.design rejects unknown
# connector keys, so they cannot sit on the connector itself).
PART_GROUP = {m["connector"]: pg for pg, ms in model.registry().get("physicalPartGroups", {}).items()
              if not pg.startswith("_") for m in ms}
group_members = collections.OrderedDict()
for cid, cc in copies.items():
    pg = PART_GROUP.get(cid)
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
    pg = PART_GROUP.get(cid)
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
        # housing accessories (lock, boot, backshell, mount, dust cover, and coverings such
        # as the VRC-IN / VRC-OUT plug labels and colour bands, row 71): each listed entry
        # counts once. Contacts and plugs are per cavity, below.
        for typ, pid, _ in model.cfg_accessories(cfg):
            if typ not in model.CAVITY_TYPES and pid in parts:
                q = parts[pid]; req[q["partNumber"]] += 1; meta[q["partNumber"]] = q
    for cv in c.get("cavities", []):
        if cv.get("notConnected") and not cv.get("cavityPlugPartId"):
            continue          # another loom's cavity - counted there
        if "contactPartId" in cv or "cavityPlugPartId" in cv:
            pids = [cv.get("contactPartId"), cv.get("cavityPlugPartId")]
        elif any((cid, cv["id"]) in WIRED[l] for l, _, _ in cc):
            pids = [model.cfg_default(cfg, "ContactPart")]
        else:
            pids = [model.cfg_default(cfg, "CavityPlugPart")]
        for pid in pids:
            if pid and pid in parts:
                q = parts[pid]; req[q["partNumber"]] += 1; meta[q["partNumber"]] = q
if clash:
    raise SystemExit("Shared connectors are inconsistent between looms:\n  "
                     + "\n  ".join(clash))

for pn, mf, desc, n in DEVICE_SIDE:
    req[pn] += n
    meta.setdefault(pn, {"partNumber": pn, "manufacturer": mf, "description": desc})

# 2026-10-14 (DECISIONS R87): ident bands. harness.design draws a wire's identColors as bands
# but they carry no part, so they are counted here: every band is fitted at BOTH ends of the
# wire, cut BAND_MM long from an RNF-100 stick sized to the wire (audit_ident_bands.SIZES).
# Wire labels are bundle coverings (fixed-length TMS-SCE markers in a bundle's partIds), one each.
import audit_ident_bands as IB
LIBP = {q["partNumber"]: q for k, v in json.load(open(os.path.join(R, "ST185.harnesslib"), encoding="utf-8")).items()
        if k.endswith("Parts") for q in v}
BANDS = collections.Counter()
for f in F:
    d = json.load(open(os.path.join(R, f), encoding="utf-8"))
    parts = {q["id"]: q for k in d if k.endswith("Parts") for q in d[k]}
    for w, _, _ in model.conductors(d):
        size = IB.band_size(w, parts)
        for c in w.get("identColors") or []:
            BANDS[IB.band_part(c, size)] += 2
    for b in d.get("bundles", []):
        for pid in b.get("partIds", []):
            q = parts.get(pid)
            if q:
                req[q["partNumber"]] += 1; meta[q["partNumber"]] = q
for pn, n in BANDS.items():
    req[pn] += -(-n // IB.BANDS_PER_STICK)
    meta[pn] = LIBP[pn]

# 2026-10-14: the custom POWER / LOGIC / battery relay boxes (cad/fusebox, R70 / R75). One CSV per box, written by
# cad/fusebox/src/parts_lists.py from the box spec; each line's qty_need + qty_spare is the order quantity. A part number
# the harness drawings already count (the F7 relays, 42281-1, ...) is NOT added again: it is the same physical part, so
# the drawn count already covers it, and once the CabinPower redraw (OPEN-ITEMS row 108) removes it from the drawings the
# next regeneration picks it up from here. Lines with no real part number (TBD / none / cut from stock) are listed
# under "Still unspecified" instead.
FB_DIR = os.path.join(os.path.dirname(R), "..", "..", "cad", "fusebox")
FB_ADDED, FB_DRAWN, FB_OPEN = collections.OrderedDict(), [], []
DRAWN = set(req)      # parts the harness files count; the box lines below must not be tested against their own additions
for fn in ("fusebox-parts-power.csv", "fusebox-parts-logic.csv", "fusebox-parts-battrelay.csv"):
    fp = os.path.join(FB_DIR, fn)
    if not os.path.exists(fp):
        continue
    for r in csv.DictReader(open(fp, encoding="utf-8", newline="")):
        n = int(r["qty_need"]) + int(r["qty_spare"])
        pn = r["part_number"]
        if n == 0 or re.match(r"^(TBD|none$|not designed|cut from)", pn):
            if re.match(r"^(TBD|not designed)", pn):
                FB_OPEN.append((r["box"], r["item"], r["note"] or r["checked_against"]))
            continue
        if pn in DRAWN:
            FB_DRAWN.append((r["box"], pn, n))
            continue
        req[pn] += n
        meta.setdefault(pn, {"partNumber": pn, "manufacturer": r["maker"], "description": r["description"].upper()})
        FB_ADDED.setdefault(pn, []).append(r["box"])

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

out = ["# Harness — need to buy",
 "",
 "Generated from the %d `.harness` files in `docs/harness/rebuild/`:"
 % len(F),
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
out += ["", "## One housing, drawn whole in several files", "",
 "These connector ids are the SAME physical connector drawn whole in more than one file",
 "(shared-connector rule, Daniel 2026-10-12): each file wires its own section and marks",
 "the other files' cavities N/C. The housing part number and its wedgelock/mount/backshell",
 "hardware are counted once, on the alphabetically-first id; each live cavity's contact or",
 "plug is counted in the file that owns it, N/C cavities never.", "",
 "| Group | Drawn as | Counted in |", "|---|---|---|"]
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
 "Each lead is one `GENERIC FLYING LEAD` splice above; the rear lamp leads are soldered to the factory",
 "bulb-socket pigtails under a 40 mm `ATUM-4/1-0` cut (DECISIONS R113). The EWD locator for every lead",
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
out += ["", "## Custom fuse + relay boxes (cad/fusebox)", "",
 "The POWER, LOGIC and battery relay boxes have one parts list each, `cad/fusebox/fusebox-parts-*.csv`",
 "(table on `cad/fusebox/ST185-fusebox-summary.html`). Their lines are counted in the tables above, with these",
 "exceptions: a part number a harness drawing already counts is the same physical part and is not added a",
 "second time. When the CabinPower redraw (OPEN-ITEMS row 108) takes it off the drawing, it moves here.", "",
 "| Part number | Box | Qty (incl. spares) | Counted by |", "|---|---|---:|---|"]
for box, pn, n in FB_DRAWN:
    out.append("| `%s` | %s | %d | the harness drawings |" % (pn, box, n))
for pn, boxes in FB_ADDED.items():
    out.append("| `%s` | %s | %d | this section's CSVs |" % (pn, ", ".join(sorted(set(boxes))), req[pn]))
out += ["", "Fuse-box lines with no part number yet:", ""]
for box, item, why in FB_OPEN:
    out.append("- %s: %s - %s" % (box, item, why))
out += ["", "## Ident bands (DECISIONS R87)", "",
 "Counted from each wire's `identColors`: one %d mm band per colour at BOTH ends of the wire, cut from a" % IB.BAND_MM,
 "%.1f m RNF-100 stick (%d bands per stick after cut loss). 20-14 AWG takes 3/32, 12-8 AWG takes 3/16;" % (IB.STICK_MM / 1000.0, IB.BANDS_PER_STICK),
 "6 AWG and heavier carry no band. The Buy column above is in sticks.", "",
 "| Part number | Bands | Sticks |", "|---|---:|---:|"]
for pn, n in sorted(BANDS.items()):
    out.append("| `%s` | %d | %d |" % (pn, n, -(-n // IB.BANDS_PER_STICK)))
out += ["", "## Still unspecified", "",
 "- **Moulded breakout boots** for the branch points — `boot_breakout` is a placeholder. "
 "Needs a real dash number per branch OD once the trunk diameters are known.",
 ""]
p = os.path.join(os.path.dirname(R), "NEED-TO-BUY.md")
new = "\n".join(out)
# No date stamp in the file: the content alone decides whether it changed, so
# regenerating an up-to-date list is a no-op and git status stays clean.
# --check (check_all.py / CI): compare against the committed file, never write.
# Default / --write: write it, always LF (git stores it LF; text mode on
# Windows used to turn every line into a CRLF diff).
if "--check" in sys.argv[1:]:
    old = open(p, encoding="utf-8", newline="").read() if os.path.exists(p) else ""
    if old.replace("\r\n", "\n") != new:
        print("STALE: %s does not match the drawings." % p)
        print("Fix: python docs/harness/buylist.py, then commit the result.")
        for ln in list(difflib.unified_diff(old.replace("\r\n", "\n").splitlines(), new.splitlines(),
                                            "committed", "regenerated", lineterm=""))[:20]:
            print("   " + ln)
        sys.exit(1)
    print("up to date:", p)
else:
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(new)
    print("wrote", p)
print("to buy: %d lines, covered: %d lines" % (len(rows_buy), len(rows_ok)))
for r in sorted(rows_buy, key=lambda x: -x[5]):
    print("   BUY %-32s need %-4d have %-4d short %d" % (r[0], r[3], r[4], r[5]))
