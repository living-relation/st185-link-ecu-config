"""ECU looms follow the ECU connector letter (docs/RECONCILIATION-RULES.md Rule 3).

ECU connector A -> cabin A -> bulkhead A -> engine A; connector B the same. A pin's
letter is its conn column in sot/channels.csv. A device's letter is the set of
signal-class ECU pins its cavities reach through splices, bulkheads and inline
interfaces (rails, grounds and screens do not give a device a letter).

  L1  a conductor on an ECU pin is on the ECU loom file of that pin's letter
  L2  a conductor on a bulkhead cavity is on the file of that bulkhead's letter
  L3  a conductor on a device cavity with a letter is on that letter's file (a cavity
      with no letter of its own - a supply or ground - takes the device's letter, and
      is free when the device has both)
  L4  a bulkhead cavity only serves its own letter: on the cabin side it reaches
      signal ECU pins of that connector only, on the engine side every device it feeds
      has that letter
  L5  a sensor rail of one connector (+5V, +8V, Gnd Out) reaches the other letter's file
      only where crossover (a) allows it
  L6  a broken-off stub is legal only in matched pairs: every cross-reference dummy (a
      cp_xref connector - dm_<element>_<cavity>, dm_<splice>_Splice, or a named dummy
      such as CAN's csb3io) names an element that really exists on the file registered
      as its owner, with that cavity, and that element's text on the owner file names
      the stub's harness back (ST185-<harness>). One side missing fails. Inline
      connectors between files are the other legal break; validate_interfaces I7 checks
      their pins pair up.

The allow-list is the rule's three crossovers and nothing else:
  (a) +5V (A32) and sensor Gnd Out (A24, B22) splice at ECU A in the cabin, one leg to
      cabin bulkhead A for A sensors, one to cabin bulkhead B for B sensors
  (b) ETB: trigger A20 on the ETB relay, H-bridge supply B5 from that relay's output
  (c) APS pedal: channel 1 on A14, channel 2 on B33 (by ECU pin design). The A and B
      pedal wires break off A-cabin / B-cabin at the female half of IX_APS (drawn on both,
      alsoDrawnOn) and one pedal harness runs from the male half to the pedal

PENDING entries are deviations Daniel has not yet ruled on. They are printed on
every run and do not fail it; each names the open question in
redesign/DECISIONS.md. Resolve the question, then delete the entry.

Exit 1 on any finding.
"""
import collections
import sys

import model

ECU_LOOMS = {"A-cabin": "A", "B-cabin": "B", "A-engine": "A", "B-engine": "B"}
BH_LETTER = {"bh_a_fw": "A", "bh_a_eng": "A", "bh_b_fw": "B", "bh_b_eng": "B"}

ALLOW = {
    "a": {"nets": {"P5V", "GNDOUT"}},
    "b": {"conductors": {("k_etb", "c4", "ecu_b", "b5")}},
    "c": {"devices": {"ix_aps_r"}},
}
PENDING = {
    "Q-RAIL": {
        "why": "injector rail (F11 15A) and COP rail (F10 20A) feed A devices across bulkhead B "
               "size-12 contacts; bulkhead A has no size-12 cavity and its size-16 contacts are 13 A",
        "conductors": {"w_inj_pwr_c", "w_cop_pwr_c", "w_inj_pwr_e", "w_cop_pwr_e",
                       "w211", "w212", "w213", "w214", "w112", "w113", "w114", "w115"},
        "cavities": {("B", "c1"), ("B", "c2")},
    },
}
PENDING_CONDS = set().union(*(p["conductors"] for p in PENDING.values()))
PENDING_CAVS = set().union(*(p["cavities"] for p in PENDING.values()))

reg = model.registry()
g = model.Graph(reg)
sot = {(r["conn"], r["pin"]): r for r in model.sot_rows() if r["owner"] == "ECU"}
bad, pending_hits = [], collections.Counter()

missing = sorted(set(ECU_LOOMS) - set(g.docs))
for m in missing:
    bad.append("L0 ECU loom %s is not registered in interfaces.json" % m)


def ecu_end(e):
    nid, h = e.get("id", ""), e.get("handle")
    if nid in ("ecu_a", "ecu_b"):
        return nid, h
    if nid.startswith(("dm_ecu_a_", "dm_ecu_b_")):
        p = nid.split("_")
        return "ecu_" + p[2], p[3]
    return None


def bh_end(e):
    nid, h = e.get("id", ""), e.get("handle")
    if nid in BH_LETTER:
        return nid, h
    if nid.startswith("dm_bh_"):
        bh, cav = nid[3:].rsplit("_", 1)
        if bh in BH_LETTER:
            return bh, cav
    return None


def letters(n):
    out = set()
    for m in g.reach(n, stop=lambda x: x[0] not in ("SP", "BH", "IX")):
        if m[0] == "ECU" and m[1] in ("ecu_a", "ecu_b"):
            r = sot.get((m[1], m[2]))
            if r and r["class"] == "signal":
                out.add(m[1][-1].upper())
    return out


cav_letter, dev_letter = {}, collections.defaultdict(set)
for n in list(g.adj):
    if n[0] == "C":
        cav_letter[(n[1], n[2])] = letters(n)
        dev_letter[n[1]] |= cav_letter[(n[1], n[2])]


def device_letter(loom, e):
    n = g.node(loom, e)
    if n[0] != "C":
        return None, None
    own = cav_letter.get((n[1], n[2])) or set()
    return n[1], (own or dev_letter.get(n[1]) or set())


# L1 - L3: every conductor on an ECU loom file sits on its letter
for loom, L in ECU_LOOMS.items():
    d = g.docs.get(loom)
    if not d:
        continue
    for cond, cable, screen in model.conductors(d):
        ends = [cond.get("source") or {}, cond.get("target") or {}]
        if cond["id"] in PENDING_CONDS:
            pending_hits["Q-RAIL"] += 1
            continue
        ecu = [ecu_end(e) for e in ends if ecu_end(e)]
        for conn, pin in ecu:
            if conn[-1].upper() != L:
                bad.append("L1 %s: %s lands on %s.%s but is drawn on a %s file"
                           % (loom, cond["id"], conn, pin, L))
        for bh, cav in [bh_end(e) for e in ends if bh_end(e)]:
            if BH_LETTER[bh] != L:
                bad.append("L2 %s: %s lands on %s %s but is drawn on a %s file"
                           % (loom, cond["id"], bh, cav, L))
        for e in ends:
            dev, S = device_letter(loom, e)
            if not dev or not S or L in S:
                continue
            key = (dev, e.get("handle")) + (ecu[0] if ecu else ("", ""))
            if key in ALLOW["b"]["conductors"]:
                continue
            bad.append("L3 %s: %s wires %s.%s (letter %s) on a %s file"
                       % (loom, cond["id"], dev, e.get("handle"), "/".join(sorted(S)), L))

# L4 - a bulkhead cavity serves its own letter only
land = collections.defaultdict(list)  # (bulkhead, cavity) -> [(loom, far end)]
for loom, d in g.docs.items():
    for cond, cable, screen in model.conductors(d):
        s, t = cond.get("source") or {}, cond.get("target") or {}
        for a, b in ((s, t), (t, s)):
            k = bh_end(a)
            if k and b.get("id"):
                land[k].append((loom, b))

for (bh, cav), fars in sorted(land.items()):
    L = BH_LETTER[bh]
    if (L, cav) in PENDING_CAVS:
        continue
    for loom, far in fars:
        start = g.node(loom, far)
        net = {start} | g.reach(start, stop=lambda x: x[0] not in ("SP",))
        for m in net:
            if bh.endswith("_fw") and m[0] == "ECU" and m[1] in ("ecu_a", "ecu_b"):
                r = sot.get((m[1], m[2]))
                if r and r["class"] == "signal" and m[1][-1].upper() != L:
                    bad.append("L4 %s %s reaches %s.%s %s - bulkhead %s carries connector %s only"
                               % (bh, cav, m[1], m[2], r["net"], L, L))
            if bh.endswith("_eng") and m[0] == "C":
                S = cav_letter.get((m[1], m[2])) or dev_letter.get(m[1]) or set()
                if S and L not in S:
                    bad.append("L4 %s %s feeds %s.%s (letter %s) - it must cross on bulkhead %s"
                               % (bh, cav, m[1], m[2], "/".join(sorted(S)), "/".join(sorted(S))))

# L5 - a connector's sensor rail reaches the other letter's file only under (a)
rails = {k: r for k, r in sot.items() if r["class"] == "rail"}
for loom, L in ECU_LOOMS.items():
    d = g.docs.get(loom)
    if not d:
        continue
    for cond, cable, screen in model.conductors(d):
        ends = [g.node(loom, e) for e in (cond.get("source") or {}, cond.get("target") or {}) if e.get("id")]
        net = set()
        for n in ends:
            net |= {n} | g.reach(n, stop=lambda x: x[0] not in ("SP",))
        for m in net:
            if m[0] == "ECU" and (m[1], m[2]) in rails and m[1][-1].upper() != L:
                r = rails[(m[1], m[2])]
                if r["net"] not in ALLOW["a"]["nets"]:
                    bad.append("L5 %s: %s is on %s (%s.%s) - only +5V and Gnd Out cross letters"
                               % (loom, cond["id"], r["net"], m[1], m[2]))

# L6 - broken-off stubs come in matched pairs
def owner_text(d, eid, cav):
    """Text on the owner file that belongs to this element: the cavity signal, the
    connector label, and any cavity-note line that starts with the element's label."""
    out, keys = [], {eid}
    for c in d.get("connectors", []) + d.get("terminals", []):
        if c["id"] == eid:
            lb = c.get("label") or ""
            out.append(lb)
            out += [(x.get("signal") or "") for x in c.get("cavities", []) if cav is None or x["id"] == cav]
            out.append(c.get("signal") or "")
            if lb:
                keys |= {lb[:30], lb.split(" - ")[0][:30]}
    for n in d.get("schematicNotes", []):
        for line in (n.get("text") or "").split("\n"):
            if any(line.startswith(k) for k in keys if k) or ("%s " % eid) in line or ("(%s)" % eid) in line:
                out.append(line)
    return out


for ref in reg.get("references", []):
    stub_loom, dm = ref["harness"], ref["connector"]
    owner = g.docs.get(ref.get("realOn"))
    if owner is None:
        bad.append("L6 %s/%s names owner %s, which is not drawn" % (stub_loom, dm, ref.get("realOn")))
        continue
    body = dm[3:] if dm.startswith("dm_") else dm
    if body.endswith("_Splice"):
        eid, cav = body[:-7], None
        ok = any(s["id"] == eid for s in owner.get("splices", []))
    elif dm.startswith("dm_"):
        if body.startswith(("ecu_a_", "ecu_b_")):
            eid, cav = body[:5], body[6:]
        else:
            eid, _, cav = body.rpartition("_")
        c = next((x for x in owner.get("connectors", []) + owner.get("terminals", [])
                  if x["id"] == eid and not x.get("excludeFromBom")), None)
        ok = c is not None and (cav is None or any(x["id"] == cav for x in c.get("cavities", [])))
    else:
        eid, cav = dm, None
        ok = any(x["id"] == eid and not x.get("excludeFromBom") for x in owner.get("connectors", []))
    if not ok:
        bad.append("L6 %s/%s: the other end (%s%s) is missing on %s"
                   % (stub_loom, dm, eid, "." + cav if cav else "", ref["realOn"]))
        continue
    back = "ST185-%s" % stub_loom
    if not any(back in t for t in owner_text(owner, eid, cav)):
        bad.append("L6 %s/%s: %s%s on %s has no note naming %s - the broken-off end must be "
                   "marked on both sides" % (stub_loom, dm, eid, "." + cav if cav else "",
                                             ref["realOn"], back))

for q, n in sorted(pending_hits.items()):
    print("PENDING %s: %d conductor(s) exempt - %s" % (q, n, PENDING[q]["why"]))
print("ECU letter looms checked: %s" % ", ".join(k for k in ECU_LOOMS if k in g.docs))
for line in sorted(set(bad)):
    print(line)
print("\n%d bulkhead-letter finding(s)." % len(set(bad)))
sys.exit(1 if bad else 0)
