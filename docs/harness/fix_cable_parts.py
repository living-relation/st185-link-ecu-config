"""Cable parts must declare a shield and match their core count.

Two problems the upload warnings and the guide between them expose:

1. A cable that has a shield needs its CablePart to declare one, the same way a
   connector with a shell needs hasShell. harness.design warned on all six
   WheelSpeed cables for this.
2. Cores align with the part's cores BY POSITION, so a 1-core cable pointed at a
   2-core part is a mismatch. cab_crank and cab_cam are single-core; cab_knock1
   is a twisted pair.

So: one part per core count, each declaring its screen.

Also trims every file's part catalogue down to what it actually references. The
A files were still carrying all 30 parts, most of them unused, which bloats each
upload and puts parts in the BOM that the loom does not contain.
"""
import json, glob, os

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")

CABLE_PARTS = {
    1: {"id": "cab_sh_1c", "partNumber": "(generic)", "manufacturer": "generic",
        "description": "1-core shielded sensor cable, overall foil + braid screen, "
                       "20 AWG. Cable is generic in BOMs per 6.24.",
        "cores": [{"id": "k1", "color": "Blue"}],
        "shield": {"id": "sh", "color": "Shield"}},
    2: {"id": "cab_sh_2c", "partNumber": "(generic)", "manufacturer": "generic",
        "description": "2-core twisted shielded cable, overall foil + braid screen, "
                       "20 AWG. Cable is generic in BOMs per 6.24.",
        "cores": [{"id": "k1", "color": "White"}, {"id": "k2", "color": "Green"}],
        "shield": {"id": "sh", "color": "Shield"}},
    4: {"id": "cab_sh_4c", "partNumber": "(generic)", "manufacturer": "generic",
        "description": "4-core shielded cable, overall foil + braid screen, 20 AWG. "
                       "Conditioner to ECU. Cable is generic in BOMs per 6.24.",
        "cores": [{"id": "k1", "color": "Orange"}, {"id": "k2", "color": "Black"},
                  {"id": "k3", "color": "Blue"}, {"id": "k4", "color": "Violet"}],
        "shield": {"id": "sh", "color": "Shield"}},
}


def used_part_ids(d):
    used = set()
    for c in d.get("connectors", []):
        used.add(c.get("partId"))
        for x in c.get("cavities", []):
            used.add(x.get("contactPartId"))
            used.add(x.get("cavityPlugPartId"))
        for cfg in (c.get("configurations") or []):
            used.add(cfg.get("lockPartId"))
            used.add(cfg.get("contactPartId"))
    for key in ("resistors", "terminals", "cables", "splices", "diodes"):
        for e in d.get(key, []):
            used.add(e.get("partId"))
    # Some parts are in the file ON PURPOSE without being wired to anything -
    # the mating half of a connector still has to reach the buy list. Trimming
    # them out silently loses them from the BOM.
    #
    # This has to come BEFORE the configuration walk below. Adding it after left
    # cp_dt2p_abs in the file but trimmed its own contact ct_dt16p out from
    # under it, because nothing else referenced that contact.
    used |= KEEP_UNREFERENCED

    # A connector part's own configuration pulls in contacts and locks. Repeat
    # until it settles, so a kept part's contacts are kept too.
    for _ in range(4):
        grew = False
        for p in d.get("connectorParts", []):
            if p.get("id") not in used:
                continue
            for cfg in (p.get("configurations") or []):
                for k in ("lockPartId", "contactPartId", "cavityPlugPartId",
                          "bootPartId", "backshellPartId"):
                    v = cfg.get(k)
                    if v and v not in used:
                        used.add(v)
                        grew = True
        if not grew:
            break
    used.discard(None)
    return used


KEEP_UNREFERENCED = {
    "cp_dt2p_abs",   # DT04-2P, the ABS sensor-side half. Never wired on the
    "lp_w2p",        # drawing, always bought.
}


total_cables = 0
for path in sorted(glob.glob(os.path.join(SRC, "*.harness"))):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    name = os.path.basename(path)

    # 1 + 2: point each cable at a part with the right core count and a screen.
    needed = set()
    for cb in d.get("cables", []):
        n = len(cb.get("cores", []))
        spec = CABLE_PARTS.get(n)
        if spec is None:
            print("  ! %s: %s has %d cores, no matching part" % (name, cb["id"], n))
            continue
        cb["partId"] = spec["id"]
        needed.add(n)
        total_cables += 1
    if needed:
        d["cableParts"] = [CABLE_PARTS[n] for n in sorted(needed)]
    elif "cableParts" in d:
        del d["cableParts"]

    # 3: drop parts nothing references.
    used = used_part_ids(d)
    before = after = 0
    for key in ("connectorParts", "contactParts", "resistorParts",
                "bootParts", "spliceParts", "terminalParts"):
        if key not in d:
            continue
        before += len(d[key])
        d[key] = [p for p in d[key] if p.get("id") in used]
        after += len(d[key])
        if not d[key]:
            del d[key]

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2)
    print("%-30s parts %2d -> %2d" % (name, before, after))

print("\n%d cables repointed at a part that declares its screen" % total_cables)
