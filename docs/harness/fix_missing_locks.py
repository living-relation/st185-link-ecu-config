"""Define the wedgelocks and contacts that connector configurations reference.

The new lint check on part-configuration references found seven dangling ids.
They were all pre-existing: a connector part named its wedgelock in a
configuration, but the wedgelock itself was never defined anywhere, so it never
reached a BOM.

Every Deutsch DT and DTM connector needs its wedgelock. A loom built from a BOM
missing them does not assemble.

Deutsch wedgelock naming:
  DT  socket housing, n ways -> W<n>S     (DT06-2S -> W2S)
  DT  pin    housing, n ways -> W<n>P
  DTM socket housing, n ways -> WM-<n>S   (DTM06-6S -> WM-6S)
  DTM pin    housing, n ways -> WM-<n>P
"""
import json, glob, os

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")

MISSING = {
    "lp_dtm6wl": {"id": "lp_dtm6wl", "partNumber": "WM-6S",
                  "manufacturer": "Deutsch (TE)",
                  "description": "Wedgelock for DTM06-6S, 6-way socket housing"},
    "lp_dtm4wl": {"id": "lp_dtm4wl", "partNumber": "WM-4S",
                  "manufacturer": "Deutsch (TE)",
                  "description": "Wedgelock for DTM06-4S, 4-way socket housing"},
    "lp_dt2wl": {"id": "lp_dt2wl", "partNumber": "W2S",
                 "manufacturer": "Deutsch (TE)",
                 "description": "Wedgelock for DT06-2S, 2-way socket housing"},
    "lp_dt3wl": {"id": "lp_dt3wl", "partNumber": "W3S",
                 "manufacturer": "Deutsch (TE)",
                 "description": "Wedgelock for DT06-3S, 3-way socket housing"},
}

CONTACTS = {
    "ct_dtm_skt": {"id": "ct_dtm_skt", "partNumber": "0462-201-16141",
                   "manufacturer": "Deutsch (TE)", "gender": "Socket",
                   "type": "Crimp",
                   "maxGauge": {"unit": "AWG", "value": 16},
                   "minGauge": {"unit": "AWG", "value": 20},
                   "description": "DT/DTM size 16 solid socket, 16-20 AWG"},
    "ct_generic_skt": {"id": "ct_generic_skt", "partNumber": "(generic)",
                       "manufacturer": "Generic", "gender": "Socket",
                       "type": "Crimp",
                       "description": "Generic machined socket for a board-level "
                                      "or unspecified housing - confirm before "
                                      "ordering"},
}

added = 0
for path in sorted(glob.glob(os.path.join(SRC, "*.harness"))):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)

    have = set()
    for key in ("connectorParts", "contactParts", "resistorParts", "cableParts"):
        for p in d.get(key, []):
            have.add(p.get("id"))

    wanted = set()
    for p in d.get("connectorParts", []):
        for cfg in (p.get("configurations") or []):
            for k in ("lockPartId", "contactPartId", "cavityPlugPartId"):
                v = cfg.get(k)
                if v and v not in have:
                    wanted.add(v)

    if not wanted:
        continue

    for wid in sorted(wanted):
        if wid in MISSING:
            d.setdefault("connectorParts", []).append(MISSING[wid])
        elif wid in CONTACTS:
            d.setdefault("contactParts", []).append(CONTACTS[wid])
        else:
            print("  ! %s references %s and I have no definition for it"
                  % (os.path.basename(path), wid))
            continue
        added += 1
        print("  %-30s + %s" % (os.path.basename(path), wid))

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2)

print("\n%d part definitions added" % added)
