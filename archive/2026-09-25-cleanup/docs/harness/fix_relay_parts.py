"""One relay, one part number.

Two defects the shared-connector check in buylist.py turned up on 2026-09-22:

1. A-ECU drew all six relays as the generic "(OEM block, 5-way)" placeholder.
   B-ECU had already been given the real TE micro ISO parts.  A-ECU is read
   first, so the buy list took the placeholder and the relays fell out of the
   count entirely (they were being hand-patched back in through EXTRA).

2. EngineRoom-C and B-ECU both define a part called cp_rly_cod but give it
   different part numbers - EngineRoom-C had 5-1393292-8, which is the MAKE
   contact relay, under the id used for the CHANGEOVER one.

Verified against te.com 2026-09-22:
   5-1393292-8   Micro Relay A, 1 Form A (NO),   12 V, 25 A, diode
   6-1419137-4   Micro Relay A, 1 Form C (SPDT), 12 V, 25 A, diode
   4-1904124-2   Micro Relay A, 1 Form A (NO),   12 V, 25 A, coil 119R 1.42W
                 (TE's page does not state diode vs resistor - UNVERIFIED)
"""
import json, os

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")

PARTS = {
    "cp_rly_nod": {"id": "cp_rly_nod", "partNumber": "5-1393292-8",
                   "manufacturer": "TE Connectivity",
                   "description": "Micro ISO relay V23074, 1 Form A make, 12V coil, 25A, diode suppressed"},
    "cp_rly_cod": {"id": "cp_rly_cod", "partNumber": "6-1419137-4",
                   "manufacturer": "TE Connectivity",
                   "description": "Micro ISO relay V23074, 1 Form C changeover, 12V coil, 25A, diode suppressed"},
    "cp_rly_nor": {"id": "cp_rly_nor", "partNumber": "4-1904124-2",
                   "manufacturer": "TE Connectivity",
                   "description": "Micro ISO relay V23074, 1 Form A make, 12V coil 119R, 25A - suppression UNVERIFIED"},
}
# which relay is which, from the B-ECU drawing (the one that was already right)
ASSIGN = {"k_efi": "cp_rly_nod", "k_etb": "cp_rly_nor", "k_fp": "cp_rly_nod",
          "k_fan": "cp_rly_cod", "k_fan2": "cp_rly_cod", "k_str": "cp_rly_nor"}


def load(n):
    p = os.path.join(R, "ST185-%s.harness" % n)
    return p, json.load(open(p, encoding="utf-8"))


def save(p, d):
    json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


for loom in ("A-ECU", "B-ECU", "EngineRoom-C"):
    p, d = load(loom)
    lib = d.setdefault("connectorParts", [])
    by_id = {q["id"]: q for q in lib}
    for cid, pid in ASSIGN.items():
        c = next((x for x in d.get("connectors", []) if x["id"] == cid), None)
        if c is None:
            continue
        if c.get("partId") != pid:
            print("%-14s %-8s %s -> %s" % (loom, cid, c.get("partId"), pid))
            c["partId"] = pid
        if pid not in by_id:
            lib.append(dict(PARTS[pid]))
            by_id[pid] = lib[-1]
    # align any relay part already present with the verified numbers
    for pid, want in PARTS.items():
        q = by_id.get(pid)
        if q and (q.get("partNumber") != want["partNumber"]
                  or q.get("description") != want["description"]):
            print("%-14s part %s  %s -> %s" % (loom, pid, q.get("partNumber"),
                                               want["partNumber"]))
            q.update(want)
    # drop parts nothing points at any more.  connectorParts also holds the
    # sealing plugs and wedgelocks, which cavities reference - not just the
    # housings - so collect EVERY part reference, not only connector.partId.
    used = set()
    for x in d.get("connectors", []):
        used.add(x.get("partId"))
        for cv in x.get("cavities", []) + ([x["shell"]] if x.get("shell") else []):
            used.add(cv.get("contactPartId"))
            used.add(cv.get("cavityPlugPartId"))
        for a in x.get("coveringIds", []) or []:
            used.add(a)
    # a part's configurations name accessories (wedgelock, boot, backshell) that
    # live in connectorParts too and are referenced by nothing else
    for q in lib:
        for cfg in q.get("configurations", []) or []:
            for v in cfg.values():
                if isinstance(v, str):
                    used.add(v)
    for q in lib:
        if q["id"] not in used:
            print("%-14s drop unused part %s (%s)" % (loom, q["id"], q.get("partNumber")))
    d["connectorParts"] = [q for q in lib if q["id"] in used]
    save(p, d)
