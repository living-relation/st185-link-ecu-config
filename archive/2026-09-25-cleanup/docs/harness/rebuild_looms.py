"""Rebuild the ST185 looms into the 6-file structure of plan doc 6.14.

Reads the current Signal / Power / EngineRoom-C / CAN files, applies every
change settled 2026-09-17, and writes a new set into docs/harness/rebuild/.

NOTHING IS OVERWRITTEN. The originals stay put until Daniel OKs the rebuild.

    python docs/harness/rebuild_looms.py            report only
    python docs/harness/rebuild_looms.py --write    also write rebuild/

Changes applied, each traceable to a plan section:

  6.1   delete bulkhead C (bh_c_fw / bh_c_eng) and everything hanging off it
  6.16  delete w_mrs_relay_req; the pump does not switch its own relay
  6.16  add the ECU-driven EPS relay trigger on Ign 6 / ecu_b.b12
  6.17  move all EPS wiring - K7 relay and all three pump connectors - to loom C
  6.17  move the radiator and condenser fan motors to loom C
  6.14  pull the wheel-speed sensors and both VR conditioners into their own loom
  cam   move the 1.8k cam pull-up to the ECU side, bridging 8V to Trigger 2
"""
import json, io, os, sys, collections, copy

R = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(R, "rebuild")

CABIN_BH = {"bh_a_fw", "bh_b_fw"}
ENGINE_BH = {"bh_a_eng", "bh_b_eng"}
BH = CABIN_BH | ENGINE_BH
KILL_NODES = {"bh_c_fw", "bh_c_eng"}
KILL_WIRES = {"w_mrs_relay_req"}

# Nodes that leave for another loom.
TO_LOOM_C = {"k_eps", "mrs_pwr", "mrs_en", "mrs_ctrl", "rad_fan", "fan2"}
TO_WHEELSPEED = {"wss_fl", "wss_fr", "wss_rl", "wss_rr",
                 "vr1_ch1n", "vr1_ch1p", "vr1_ch2n", "vr1_ch2p",
                 "vr1_out1", "vr1_out2", "vr1_gnd", "vr1_5v",
                 "vr2_ch1n", "vr2_ch1p", "vr2_ch2n", "vr2_ch2p",
                 "vr2_out1", "vr2_out2", "vr2_gnd", "vr2_5v",
                 "sp_shield_rear"}

# Which side of the firewall a node sits on when the graph cannot say.
SIDE_FIX = {
    "t_batt_pos": "ECU", "t_batt_neg": "ECU",
    "rl_pos_fw": "ECU", "rl_neg_fw": "ECU",
    "rl_pos_eng": "engine", "rl_neg_eng": "engine",
    "t_starter_b": "engine", "t_alt_b": "engine", "t_eng_block": "engine",
    "fuelpump": "ECU", "fuellvl": "ECU", "starter_trigger": "engine",
    "batt_ring": "ECU", "chassis_ring": "ECU",
}
# Wires that cross with no bulkhead pin yet - cut so the fill does not smear.
SIDE_CUT = {"w_strl"}

NODE_KEYS = ["connectors", "splices", "terminals", "diodes", "resistors",
             "groups", "branchPoints"]
PART_KEYS = ["connectorParts", "contactParts", "wireParts", "cableParts",
             "bootParts", "coveringParts", "spliceParts", "terminalParts",
             "otherParts"]
WIRE_KEYS = ["wires", "cables", "twistedWires"]


def ends(w):
    return ((w.get("source") or {}).get("id"), (w.get("target") or {}).get("id"))


def load(fn):
    return json.load(io.open(os.path.join(R, fn), encoding="utf-8"))


def node_ids(doc):
    out = set()
    for k in NODE_KEYS:
        out |= {e.get("id") for e in doc.get(k, [])}
    return out


def drop_nodes(doc, kill):
    """Remove nodes and cascade to the wires, bundles and mates on them."""
    for k in NODE_KEYS:
        if k in doc:
            doc[k] = [e for e in doc[k] if e.get("id") not in kill]
    for k in WIRE_KEYS:
        if k in doc:
            doc[k] = [w for w in doc[k] if not (set(ends(w)) & kill)]
    if "bundles" in doc:
        doc["bundles"] = [b for b in doc["bundles"]
                          if b.get("sourceId") not in kill
                          and b.get("targetId") not in kill]
    if "mates" in doc:
        doc["mates"] = [m for m in doc["mates"]
                        if m.get("sourceId") not in kill
                        and m.get("targetId") not in kill]


def take_nodes(doc, take):
    """Pull nodes and their wholly-internal wiring out of doc into a new doc."""
    sub = {k: doc[k] for k in ("$schema", "$docs", "version", "lengthUnit")
           if k in doc}
    for k in NODE_KEYS:
        keep = [e for e in doc.get(k, []) if e.get("id") in take]
        if keep:
            sub[k] = keep
    for k in WIRE_KEYS:
        keep = [w for w in doc.get(k, []) if set(ends(w)) <= take]
        if keep:
            sub[k] = keep
    if doc.get("bundles"):
        b = [x for x in doc["bundles"]
             if x.get("sourceId") in take and x.get("targetId") in take]
        if b:
            sub["bundles"] = b
    for k in PART_KEYS:
        if doc.get(k):
            sub[k] = copy.deepcopy(doc[k])
    return sub


def main():
    write = "--write" in sys.argv
    sig, pwr = load("ST185-Signal.harness"), load("ST185-Power.harness")
    can, room = load("ST185-CAN.harness"), load("ST185-EngineRoom-C.harness")
    # w_rlp is used twice across the repo: the rear-left wheel-speed wire in
    # Signal and the RADLOK positive pair in EngineRoom-C. Same id, different
    # wires - any cross-file tool silently keeps one. Rename the RADLOK one;
    # w_rlp belongs with w_flp / w_frp / w_rrp.
    for w in room.get("wires", []):
        if w.get("id") == "w_rlp":
            w["id"] = "w_rl_pos"
    originals = {w["id"]: copy.deepcopy(w)
                 for d in (sig, pwr) for w in d.get("wires", [])}
    report = []

    for name, d in (("Signal", sig), ("Power", pwr)):
        before = len(d.get("wires", []))
        drop_nodes(d, KILL_NODES)
        for k in WIRE_KEYS:
            if k in d:
                d[k] = [w for w in d[k] if w.get("id") not in KILL_WIRES]
        report.append("%-8s %3d -> %3d wires after deleting bulkhead C and "
                      "w_mrs_relay_req" % (name, before, len(d.get("wires", []))))

    # 6.12 - shields. Daniel's rules, 2026-09-19:
    #   a shield is NEVER connected at the device end, only at the ECU;
    #   none of his connectors have a shell for a shield;
    #   a shield is cable only until it terminates at the ECU;
    #   it passes THROUGH the bulkhead on its own pin, not on the shell.
    # So: strip every shell, and delete every drain that lands on a device.
    shells = 0
    for d in (sig, pwr, can, room):
        for c in d.get("connectors", []):
            if c.pop("shell", None) is not None:
                shells += 1
    dropped = []
    for d in (sig, pwr, can, room):
        keep = []
        for w in d.get("wires", []):
            s, t = w.get("source") or {}, w.get("target") or {}
            device_end = (s.get("handle") == "shield" or t.get("handle") == "shield")
            if device_end:
                dropped.append(w.get("id"))
                continue
            keep.append(w)
        d["wires"] = keep
    # place_crossings works from `originals`, which still holds these, so without
    # this they get resurrected as cross-loom wires later in the run.
    KILL_WIRES.update(dropped)
    report.append("shields: stripped %d connector shells, dropped %d device-end "
                  "drains (%s)" % (shells, len(dropped), ", ".join(sorted(dropped))))

    # 6.16 - ECU-driven EPS relay trigger, Ign 6 / ecu_b.b12 low-side to K7 coil.
    eps_trig = {
        "id": "w_eps_trig", "color": "Violet",
        "source": {"id": "ecu_b", "handle": "b12"},
        "target": {"id": "k_eps", "handle": "c2"},
    }
    sig.setdefault("wires", []).append(eps_trig)
    # K7 lives on loom C, the ECU does not - so this is itself a cross-loom
    # wire and has to go through place_crossings like the rest.
    originals["w_eps_trig"] = copy.deepcopy(eps_trig)
    report.append("added w_eps_trig  ecu_b.b12 (Ign 6) -> k_eps.c2")

    # Cam pull-up: bridge ECU 8V (a6) to Trigger 2 (a9) instead of sitting in
    # series in the trigger line. Rename for readability.
    for r in sig.get("resistors", []):
        if r.get("id") == "r_cam":
            r["id"] = "cam_pullup"
            r["locationId"] = "ecu_a"
    fixed = 0
    for w in sig.get("wires", []):
        s, t = ends(w)
        if w.get("id") == "w23":          # cam.c2 -> r_cam.Left
            w["source"] = {"id": "ecu_a", "handle": "a6"}
            w["target"] = {"id": "cam_pullup", "handle": "Left"}
            w["id"] = "w_cam_pullup_8v"
            fixed += 1
        elif w.get("id") == "w20_e":      # r_cam.Right -> bh_a_eng.c32
            w["source"] = {"id": "cam_pullup", "handle": "Right"}
            w["target"] = {"id": "ecu_a", "handle": "a9"}
            w["id"] = "w_cam_pullup_sig"
            fixed += 1
        elif s == "r_cam" or t == "r_cam":
            fixed += 1
    # The straight-through cam signal already exists on bulkhead A pin 29
    # (w_cam_sig_e / w_cam_sig_c, added in Pass A), so the old resistor-in-series
    # leg on pin 32 is a second, parallel path to the same ECU pin. Drop its
    # cabin half too - w23 and w20_e are rewired above, w20_c just goes.
    sig["wires"] = [w for w in sig["wires"] if w.get("id") != "w20_c"]
    report.append("cam pull-up rewired ECU-side (8V a6 -> resistor -> Trig2 a9), "
                  "%d wires touched" % fixed)

    # Pull the wheel-speed loom out of Signal and Power.
    ws_parts = []
    for d in (sig, pwr):
        ws_parts.append(take_nodes(d, TO_WHEELSPEED))
        drop_nodes(d, TO_WHEELSPEED)
    wheel = ws_parts[0]
    for k in NODE_KEYS + WIRE_KEYS + ["bundles"]:
        if ws_parts[1].get(k):
            wheel.setdefault(k, []).extend(ws_parts[1][k])
    report.append("WheelSpeed loom: %d wires, %d connectors, %d terminals"
                  % (len(wheel.get("wires", [])), len(wheel.get("connectors", [])),
                     len(wheel.get("terminals", []))))

    # Move EPS and both fan motors into loom C.
    for d in (sig, pwr):
        moved = take_nodes(d, TO_LOOM_C)
        for k in NODE_KEYS + WIRE_KEYS:
            for e in moved.get(k, []):
                if e.get("id") not in {x.get("id") for x in room.get(k, [])}:
                    room.setdefault(k, []).append(e)
        drop_nodes(d, TO_LOOM_C)
    report.append("EngineRoom-C now %d wires, %d connectors"
                  % (len(room.get("wires", [])), len(room.get("connectors", []))))

    # Split what is left at the firewall.
    outputs = {"ST185-WheelSpeed": wheel, "ST185-EngineRoom-C": room,
               "ST185-CAN": can}
    for loom, d in (("A", sig), ("B", pwr)):
        side = classify(d)
        for want in ("ECU", "engine"):
            outputs["ST185-%s-%s" % (loom, want)] = slice_side(d, side, want)

    cross = place_crossings(outputs, originals)
    print("\n".join(report))
    print("-" * 66)
    print("cross-loom wires given a home plus a 6.15 dummy far end:")
    print("\n".join(cross) if cross else "  none")
    print("-" * 66)
    start = len(originals) + len(can.get("wires", [])) + 33
    total = sum(len(v.get("wires", [])) for v in outputs.values())
    # Deleted: KILL_WIRES plus w20_c (the duplicate cam leg). Added: w_eps_trig,
    # which is already counted in originals, so nothing to add here.
    # KILL_WIRES has already absorbed the device-end drains, so only w20_c is extra.
    deleted = len(KILL_WIRES) + 1
    expect = start - deleted
    print("accounting: %d in, %d deleted, %d out%s"
          % (start, deleted, total,
             "  OK - nothing lost" if total == expect else "  <-- MISMATCH"))
    for k in sorted(outputs):
        v = outputs[k]
        n = len(v.get("wires", []))
        flag = "  <-- OVER 100 CAP" if n > 100 else ""
        print("%-24s wires %3d  connectors %3d  splices %2d%s"
              % (k, n, len(v.get("connectors", [])), len(v.get("splices", [])), flag))
    if write:
        os.makedirs(OUT, exist_ok=True)
        for k, v in outputs.items():
            p = os.path.join(OUT, k + ".harness")
            with io.open(p, "w", encoding="utf-8", newline="\n") as f:
                json.dump(v, f, indent=2, ensure_ascii=False)
        print("\nwrote %d files to %s" % (len(outputs), OUT))
    else:
        print("\nreport only - pass --write to create docs/harness/rebuild/")


_DUMMY_N = {}


def dummy(node_id, pin, label, owner="x"):
    """A connection block standing in for a component owned by another file.

    Per 6.15 it carries no part number and no contacts, so it adds nothing to
    this drawing's BOM. Shape taken from Grok's rework.py, which had this right.
    """
    # v0.9 schema: connectors take no `notes` key, so the explanation rides in
    # the cavity signal text instead.
    return {"id": "dm_%s_%s" % (node_id, pin),
            "label": "%s-%s" % (label, pin),
            "width": 150,
            "cavities": [{"id": "c1", "designation": "1",
                          "signal": "Dummy - real part on the owning drawing, 6.15"}],
            "schematicPosition": _dummy_pos(owner),
            "layoutPosition": _dummy_pos(owner, bump=False)}


def _dummy_pos(owner, bump=True):
    """Stack dummies down the right-hand edge instead of piling them at 0,0."""
    n = _DUMMY_N.get(owner, 0)
    if bump:
        _DUMMY_N[owner] = n + 1
    return {"x": 4200, "y": 120 + n * 240}


# Which output file owns a wire that crosses between looms, and therefore which
# end becomes a dummy. A wire belongs to the loom that physically carries it.
OWNER_OF = [
    (TO_WHEELSPEED, "ST185-WheelSpeed"),
    (TO_LOOM_C, "ST185-EngineRoom-C"),
]
# Crossings where neither end moved - name the owner outright.
OWNER_FIX = {"w_strl": "ST185-B-engine"}
# Human labels for the far end, per 6.15's component ID table.
LABEL = {"k_efi": "K1", "k_etb": "K2", "k_fp": "K3", "k_fan": "K4",
         "k_fan2": "K5", "k_str": "K6", "k_eps": "K7",
         "bh_a_fw": "BH-A", "bh_a_eng": "BH-A", "bh_b_fw": "BH-B",
         "bh_b_eng": "BH-B", "fusebox": "FB1",
         "ecu_a": "ECU-A", "ecu_b": "ECU-B"}


def place_crossings(outputs, originals):
    """Give every wire that fell between looms a home plus a dummy far end."""
    placed = set()
    for doc in outputs.values():
        placed |= {w.get("id") for w in doc.get("wires", [])}
    # Wires renamed earlier in the run - they are placed under the new id.
    renamed = {"w23", "w20_e"}
    report = []
    for wid, w in originals.items():
        if wid in placed or wid in KILL_WIRES or wid in renamed:
            continue
        s, t = ends(w)
        owner = OWNER_FIX.get(wid)
        near = None
        if not owner:
            for group, name in OWNER_OF:
                if s in group:
                    owner, near = name, "source"
                    break
                if t in group:
                    owner, near = name, "target"
                    break
        if not owner:
            report.append("  UNASSIGNED %-20s %s -> %s" % (wid, s, t))
            continue
        doc = outputs[owner]
        far = "target" if near == "source" else "source"
        if near is None:                      # OWNER_FIX case - dummy the cabin end
            far = "source" if t not in outputs[owner].get("_ids", ()) else "target"
        fid = (w.get(far) or {}).get("id")
        fpin = (w.get(far) or {}).get("handle")
        lbl = LABEL.get(fid, fid)
        blk = dummy(fid, fpin, lbl, owner)
        if blk["id"] not in {c.get("id") for c in doc.get("connectors", [])}:
            doc.setdefault("connectors", []).append(blk)
        nw = copy.deepcopy(w)
        nw[far] = {"id": blk["id"], "handle": "c1"}
        doc.setdefault("wires", []).append(nw)
        report.append("  %-20s -> %-20s dummy %s" % (wid, owner, blk["label"]))
    return report


def classify(doc):
    adj = collections.defaultdict(set)
    for w in doc.get("wires", []):
        if w.get("id") in SIDE_CUT:
            continue
        s, t = ends(w)
        if s in BH or t in BH or not (s and t):
            continue
        adj[s].add(t); adj[t].add(s)
    side = {n: {v} for n, v in SIDE_FIX.items()}
    for w in doc.get("wires", []):
        if w.get("id") in SIDE_CUT:
            continue
        s, t = ends(w)
        for a, b in ((s, t), (t, s)):
            if not b or b in BH or b in SIDE_FIX:
                continue
            if a in CABIN_BH:
                side.setdefault(b, set()).add("ECU")
            elif a in ENGINE_BH:
                side.setdefault(b, set()).add("engine")
    changed = True
    while changed:
        changed = False
        for n in list(adj):
            if n in SIDE_FIX:
                continue
            cur = side.get(n, set()); new = set(cur)
            for m in adj[n]:
                new |= side.get(m, set())
            if new != cur:
                side[n] = new; changed = True
    out = {n: next(iter(v)) for n, v in side.items() if len(v) == 1}
    for n in CABIN_BH:
        out[n] = "ECU"
    for n in ENGINE_BH:
        out[n] = "engine"
    return out


def slice_side(doc, side, want):
    sub = {k: doc[k] for k in ("$schema", "$docs", "version", "lengthUnit")
           if k in doc}
    keep = set()
    for k in NODE_KEYS:
        got = [e for e in doc.get(k, []) if side.get(e.get("id")) == want]
        if got:
            sub[k] = got
        keep |= {e.get("id") for e in got}
    for k in WIRE_KEYS:
        got = [w for w in doc.get(k, [])
               if w.get("id") not in SIDE_CUT and set(ends(w)) <= keep]
        if got:
            sub[k] = got
    if doc.get("bundles"):
        b = [x for x in doc["bundles"]
             if x.get("sourceId") in keep and x.get("targetId") in keep]
        if b:
            sub["bundles"] = b
    for k in PART_KEYS:
        if doc.get(k):
            sub[k] = copy.deepcopy(doc[k])
    return sub


if __name__ == "__main__":
    main()
