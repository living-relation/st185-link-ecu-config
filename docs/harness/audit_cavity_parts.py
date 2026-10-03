"""Contacts: one part per cavity, the right part for the use, and a contact that fits.

  1. (2026-09-22) no cavity claims BOTH a contact and a cavity plug - only possible in
     hand-edited JSON; harness.design itself clears one when you set the other.
  2. (2026-09-25) a bulkhead cavity wired in any loom has a contact, an unused one a plug.
  3. (2026-10-03) contact fit, K1-K4 - see the block at the end of this file: contact
     present, gender match, wire gauge (combined gauge for several wires in one cavity)
     inside the contact's rated range, and contact part listed for the connector in the
     maker's datasheet (docs/harness/contact_compat.json). Missing datasheet or gauge data
     is listed as a GAP, never guessed.

Original note for check 1:

The harness.design editing guide is explicit: a cavity holds exactly one part,
a contact OR a cavity plug, never both ("assigning one clears the other in the
app").  The app silently resolves it in favour of the contact, so the drawings
look fine - but our buylist.py counts whatever the JSON says, so every cavity
carrying both adds a plug nobody will ever fit.  Added 2026-09-22.
"""
import json, glob, os, collections, sys

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
tot = 0
for f in sorted(glob.glob(os.path.join(R, "*.harness"))):
    d = json.load(open(f, encoding="utf-8"))
    hits = collections.Counter()
    for c in d.get("connectors", []):
        for cv in c.get("cavities", []):
            if cv.get("contactPartId") and cv.get("cavityPlugPartId"):
                hits[c["id"]] += 1
    if hits:
        print(os.path.basename(f)[6:-8])
        for cid, n in sorted(hits.items()):
            print("      %-16s %d cavities with a contact AND a plug" % (cid, n))
        tot += sum(hits.values())
print()
print("%d cavities double-booked." % tot)

# ---- 2026-09-25: parts rule 1, second half ---------------------------------
# A bulkhead cavity wired in ANY loom gets a contact, in every copy of that
# half; a cavity wired in NO loom gets a sealing plug. Found 11 wired cavities
# (knock c16-c18, VSS c15, screens c33/c34, MRS c36, MRS enable A c35) carrying
# plugs and 10 spares carrying contacts - the buy list was counting both wrong.
BH = ("bh_a_fw", "bh_a_eng", "bh_b_fw", "bh_b_eng")
used = collections.defaultdict(set)
docs = {os.path.basename(f)[6:-8]: json.load(open(f, encoding="utf-8"))
        for f in sorted(glob.glob(os.path.join(R, "*.harness")))}
for d in docs.values():
    conds = list(d.get("wires", []))
    for cb in d.get("cables", []):
        conds += cb.get("cores", [])
        if cb.get("shield"):
            conds.append(cb["shield"])
    for w in conds:
        for e in (w.get("source"), w.get("target")):
            if not e:
                continue
            if e["id"].startswith("dm_bh_"):
                b, c = e["id"][3:].rsplit("_", 1)
                used[b].add(c)
            elif e["id"] in BH:
                used[e["id"]].add(e.get("handle"))
wrong = 0
for loom, d in docs.items():
    for c in d.get("connectors", []):
        if c["id"] not in BH:
            continue
        for cv in c.get("cavities", []):
            wired = cv["id"] in used[c["id"]]
            if wired and not cv.get("contactPartId"):
                print("  %-12s %s %s is wired but has no contact" % (loom, c["id"], cv["id"]))
                wrong += 1
            elif not wired and not cv.get("cavityPlugPartId"):
                print("  %-12s %s %s is unused but has no sealing plug" % (loom, c["id"], cv["id"]))
                wrong += 1
print("%d bulkhead cavities with the wrong part for their use." % wrong)
OLD_FAIL = bool(tot or wrong)

# ---- 2026-10-03: contact fit (Daniel) ---------------------------------------
# Double-booking cannot happen in harness.design itself (the app clears one when you set
# the other), so the old check above only guards hand-edited JSON. The real question is
# whether each contact FITS:
#   K1  every wired cavity has a contact (cavity part or the connector's default config)
#   K2  the contact's gender matches the connector's (Male housing - Pin, Female - Socket)
#   K3  the wire gauge is inside the contact's rated range (minGauge..maxGauge from the
#       part library). Several conductors in ONE cavity are checked as their COMBINED
#       gauge - standing splice rule, Wire Barn Combined Wire Gauge Calculator
#       (circular-mil sum, docs/RECONCILIATION-RULES.md Rule 3). Terminals (ring lugs,
#       flying-lead terminals) and splices with a rated range are checked the same way.
#   K4  the contact part number is one the maker lists for that connector part number -
#       from docs/harness/contact_compat.json (datasheet-sourced; never guessed). A pair
#       not in that file is listed as a GAP, not failed.
# Gaps (no gauge on a wire/contact, no datasheet compatibility entry) are listed and do
# not fail the run - they need datasheet data, not a guess.
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model as _model

COMPAT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contact_compat.json")
compat = json.load(open(COMPAT_FILE, encoding="utf-8")).get("connectors", {}) \
    if os.path.exists(COMPAT_FILE) else {}


def cmil(awg):
    d = 5.0 * 92 ** ((36.0 - awg) / 39.0)          # diameter in mils
    return d * d


def awg_of(cm):
    return 36.0 - 39.0 * math.log((math.sqrt(cm) / 5.0), 92)


def combined_awg(gauges):
    """Wire Barn combined gauge: sum the circular mils, back to the nearest AWG."""
    return int(round(awg_of(sum(cmil(g) for g in gauges))))


def gauge(v):
    v = v or {}
    return v.get("value") if v.get("unit", "AWG") == "AWG" else None


reg = _model.registry()
ds = _model.docs(reg)
fit_bad, gaps_gauge, gaps_compat = [], set(), {}
land = collections.defaultdict(list)   # (component id, handle) -> [(loom, conductor id, awg or None)]
comp_ids = {}
for loom, d in ds.items():
    for k in ("connectors", "terminals", "splices"):
        for c in d.get(k, []):
            comp_ids.setdefault(c["id"], k)
for loom, d in ds.items():
    P = _model.parts(d)
    for cb in d.get("cables", []):
        cores = (P.get(cb.get("partId")) or {}).get("cores") or []
        for i, co in enumerate(cb.get("cores", [])):
            co["_awg"] = gauge(cores[i].get("gauge")) if i < len(cores) else None
    for cond, cable, screen in _model.conductors(d):
        awg = cond.get("_awg") if cable else gauge((P.get(cond.get("partId")) or {}).get("gauge"))
        for e in (cond.get("source") or {}, cond.get("target") or {}):
            nid, h = e.get("id", ""), e.get("handle")
            if nid.startswith("dm_") and not nid.endswith("_Splice"):
                comp, _, cav = nid[3:].rpartition("_")
                if comp in comp_ids:
                    nid, h = comp, cav
            if nid in comp_ids:
                land[(nid, h if comp_ids[nid] == "connectors" else "-")].append((loom, cond["id"], awg))

seen_cav = set()
for loom, d in ds.items():
    P = _model.parts(d)
    for c in d.get("connectors", []):
        if _model.is_xref(c) or not c.get("partId") or c.get("excludeFromBom"):
            continue
        cp = P.get(c["partId"]) or {}
        cfg = (cp.get("configurations") or [{}])[0]
        cpn = cp.get("partNumber", c["partId"])
        for cv in c.get("cavities", []):
            key = (c["id"], cv["id"])
            if key in seen_cav or key not in land:
                continue
            seen_cav.add(key)
            ctid = cv.get("contactPartId") or (cfg.get("contactPartId") if "cavityPlugPartId" not in cv else None)
            ct = P.get(ctid)
            where = "%s/%s %s" % (loom, c["id"], cv["id"])
            if not ct:
                if str(cpn).upper().startswith(("TBD", "(")):
                    gaps_gauge.add("%s: housing is %r - no contact can be chosen until the part is" % (where, cpn))
                else:
                    fit_bad.append("K1 %s is wired but has no contact" % where)
                continue
            if cp.get("gender") and ct.get("gender") and \
                    {"Male": "Pin", "Female": "Socket"}.get(cp["gender"]) != ct["gender"]:
                fit_bad.append("K2 %s: %s housing with a %s contact (%s)"
                               % (where, cp["gender"], ct["gender"], ct.get("partNumber")))
            gs = [x[2] for x in land[key]]
            lo, hi = gauge(ct.get("maxGauge")), gauge(ct.get("minGauge"))   # lo = thickest AWG
            if None in gs or lo is None or hi is None:
                gaps_gauge.add("%s: %s" % (where, "contact %s has no gauge range" % ct.get("partNumber")
                                          if lo is None or hi is None else
                                          "conductor gauge unknown (%s)" % ", ".join(x[1] for x in land[key] if x[2] is None)))
            else:
                eff = gs[0] if len(gs) == 1 else combined_awg(gs)
                if not lo <= eff <= hi:
                    fit_bad.append("K3 %s: %s AWG%s outside contact %s range %s-%s AWG"
                                   % (where, eff, "" if len(gs) == 1 else " combined (%s)" % "+".join(map(str, gs)),
                                      ct.get("partNumber"), lo, hi))
            ok = compat.get(cpn, {}).get("contacts")
            if ok is None:
                gaps_compat.setdefault(cpn, set()).add(ct.get("partNumber"))
            elif ct.get("partNumber") not in ok:
                fit_bad.append("K4 %s: contact %s is not listed for %s in contact_compat.json (%s)"
                               % (where, ct.get("partNumber"), cpn, compat[cpn].get("source", "")))
    for k in ("terminals", "splices"):
        for t in d.get(k, []):
            tp = P.get(t.get("partId"))
            if not tp or (t["id"], "-") not in land:
                continue
            gs = [x[2] for x in land[(t["id"], "-")]]
            lo, hi = gauge(tp.get("maxGauge")), gauge(tp.get("minGauge"))
            if lo is None or hi is None or None in gs:
                if lo is not None and hi is not None:
                    gaps_gauge.add("%s/%s: conductor gauge unknown" % (loom, t["id"]))
                continue
            eff = gs[0] if len(gs) == 1 else combined_awg(gs)
            if not lo <= eff <= hi:
                fit_bad.append("K3 %s/%s: %s AWG%s outside %s range %s-%s AWG"
                               % (loom, t["id"], eff, "" if len(gs) == 1 else " combined (%s)" % "+".join(map(str, gs)),
                                  tp.get("partNumber"), lo, hi))

print()
for line in fit_bad:
    print("  " + line)
print("%d contact-fit problem(s) (K1-K4)." % len(fit_bad))
print("GAP - gauge data missing (%d):" % len(gaps_gauge))
for line in sorted(gaps_gauge):
    print("    " + line)
print("GAP - no datasheet contact list in contact_compat.json for %d connector part number(s):" % len(gaps_compat))
for cpn, cts in sorted(gaps_compat.items()):
    print("    %-26s contacts used: %s" % (cpn, ", ".join(sorted(x or "?" for x in cts))))
if fit_bad:
    sys.exit(1)
sys.exit(1 if OLD_FAIL else 0)
