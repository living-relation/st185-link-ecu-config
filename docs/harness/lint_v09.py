"""Check every rebuild file against the v0.9 rules we have learned by
rejection, so an upload is not a guess.

Each rule here cost a failed set_document_json at least once:
  - width is an enum, not a number
  - wire colour is an enum with no striped values; the stripe is its own field
  - wires take no 'signal'
  - cavities take no 'description'
  - connectors take no 'notes'
  - connectors take no 'shell' (6.27: no connector on this car has one)
  - a CablePart declares its screen with the boolean 'shielded'; the object
    form 'shield' belongs to the cable instance only
  - a cable's core count must match its CablePart's core count
  - every partId / contactPartId / cavityPlugPartId must resolve
  - every wire end must point at a node and a cavity that exist
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "rebuild")

WIDTHS = {60, 90, 150, 210, 270, 390}
COLORS = {"Black", "Brown", "Red", "Orange", "Yellow", "Green", "Blue",
          "Violet", "Gray", "White", "Pink", "Tan", "Maroon", "Light Yellow",
          "Light Green", "Light Blue", "Light Gray", "Transparent", "Shield"}


def check(fn):
    with open(os.path.join(SRC, fn), encoding="utf-8") as fh:
        d = json.load(fh)
    bad = []

    parts = set()
    for key in ("connectorParts", "contactParts", "resistorParts",
                "diodeParts", "cableParts", "wireParts", "bootParts",
                "spliceParts", "terminalParts", "tapeParts", "tubeParts",
                "lockParts", "cavityPlugParts", "cavitySealParts", "backshellParts",
                "mountParts", "dustCoverParts", "groupParts", "coveringParts"):
        for p in d.get(key, []):
            pid = p.get("id")
            # A part id listed twice is how a non-idempotent fix script quietly
            # doubles the BOM. Catch it here, not on the bench.
            if pid in parts:
                bad.append("duplicate part id %s in %s" % (pid, key))
            parts.add(pid)

    # A CablePart declares its screen with the BOOLEAN "shielded". Copying the
    # cable instance's {"shield": {...}} shape onto the part is rejected
    # outright - "Unrecognized key(s) in object: 'shield'". Cost one upload.
    cable_parts = {}
    for p in d.get("cableParts", []):
        cable_parts[p.get("id")] = p
        if "shield" in p:
            bad.append("cable part %s has a 'shield' key - the part takes the "
                       "boolean 'shielded'" % p.get("id"))

    # A part's own configuration references other parts. Those have to resolve
    # too - a connector part whose contact was trimmed out from under it still
    # looks fine on the connector, and the missing contact only shows up as a
    # short BOM.
    for p in d.get("connectorParts", []):
        for cfg in (p.get("configurations") or []):
            for k in ("lockPartId", "contactPartId", "cavityPlugPartId",
                      "bootPartId", "backshellPartId"):
                v = cfg.get(k)
                if v and v not in parts:
                    bad.append("part %s config %s -> missing part %s"
                               % (p.get("id"), k, v))

    # nodes and their cavity ids
    cav = {}
    for c in d.get("connectors", []):
        cav[c["id"]] = {x.get("id") for x in c.get("cavities", [])}
        if c.get("width") is not None and c["width"] not in WIDTHS:
            bad.append("connector %s width %s" % (c["id"], c["width"]))
        if "shell" in c:
            # 6.27: no connector on this car has a shield shell - except the VR
            # conditioner enclosures, where 6.35 says the shell IS the screen path.
            if not c["id"].startswith("vrc_"):
                bad.append("connector %s has a shell (6.27 says none do "
                           "except vrc_*)" % c["id"])
            cav[c["id"]].add(c["shell"].get("id"))
        if "notes" in c:
            bad.append("connector %s has a notes key" % c["id"])
        for x in c.get("cavities", []):
            if "description" in x:
                bad.append("cavity %s/%s has a description key"
                           % (c["id"], x.get("id")))
        for k in ("partId",):
            if c.get(k) and c[k] not in parts:
                bad.append("connector %s %s -> missing part %s"
                           % (c["id"], k, c[k]))
        for x in c.get("cavities", []):
            for k in ("contactPartId", "cavityPlugPartId"):
                if x.get(k) and x[k] not in parts:
                    bad.append("cavity %s/%s %s -> missing part %s"
                               % (c["id"], x.get("id"), k, x[k]))

    for s in d.get("splices", []):
        cav[s["id"]] = {"Splice"}
    for t in d.get("terminals", []):
        cav[t["id"]] = {"Terminal"}
        if t.get("width") is not None and t["width"] not in WIDTHS:
            bad.append("terminal %s width %s" % (t["id"], t["width"]))
    for r in d.get("resistors", []):
        cav[r["id"]] = {"Left", "Right"}
        if r.get("partId") and r["partId"] not in parts:
            bad.append("resistor %s -> missing part %s" % (r["id"], r["partId"]))
    # Diodes are two-terminal nodes exactly like resistors. Added 2026-09-22 when
    # ClusterLED went to individual LEDs and every one of them linted as unknown.
    for x in d.get("diodes", []):
        cav[x["id"]] = {"Left", "Right"}
        if x.get("partId") and x["partId"] not in parts:
            bad.append("diode %s -> missing part %s" % (x["id"], x["partId"]))

    for n in d.get("schematicNotes", []):
        if n.get("width") is not None and n["width"] not in WIDTHS:
            bad.append("note %s width %s" % (n.get("id"), n["width"]))

    # notConnected and a signal on the same cavity contradict each other, and
    # the app rejects a wire landing on a notConnected cavity.
    wired = set()
    parts_by_id = {}
    for p in d.get("connectorParts", []):
        parts_by_id[p.get("id")] = p
    for c in d.get("connectors", []):
        for x in c.get("cavities", []):
            if x.get("notConnected") and x.get("signal"):
                bad.append("cavity %s/%s is notConnected but has a signal"
                           % (c["id"], x.get("id")))
        p = parts_by_id.get(c.get("partId"))
        if p:
            n = p.get("numberOfCavities")
            if n is not None and n != len(c.get("cavities", [])):
                bad.append("connector %s has %d cavities but part %s says %s"
                           % (c["id"], len(c.get("cavities", [])), c["partId"], n))
            if bool(p.get("hasShell")) != ("shell" in c):
                bad.append("connector %s shell does not match part %s hasShell=%s"
                           % (c["id"], c["partId"], p.get("hasShell")))

    def check_conductor(kind, wid, obj):
        if "signal" in obj:
            bad.append("%s %s has a signal key" % (kind, wid))
        for k in ("color", "stripeColor"):
            if obj.get(k) and obj[k] not in COLORS:
                bad.append("%s %s %s %r" % (kind, wid, k, obj[k]))
        for end in ("source", "target"):
            e = obj.get(end)
            if not e:
                continue          # a shield core legitimately has one end
            nid, h = e.get("id"), e.get("handle")
            if nid not in cav:
                bad.append("%s %s %s -> unknown node %s" % (kind, wid, end, nid))
            elif h not in cav[nid]:
                bad.append("%s %s %s -> %s has no cavity %s"
                           % (kind, wid, end, nid, h))
            else:
                wired.add((nid, h))

    seen = set()
    for w in d.get("wires", []):
        wid = w.get("id")
        if wid in seen:
            bad.append("duplicate wire id %s" % wid)
        seen.add(wid)
        check_conductor("wire", wid, w)

    for cb in d.get("cables", []):
        cid = cb.get("id")
        if cid in seen:
            bad.append("duplicate id %s" % cid)
        seen.add(cid)
        if not cb.get("schematicPosition"):
            bad.append("cable %s has no schematicPosition (required)" % cid)
        if cb.get("partId") and cb["partId"] not in parts:
            bad.append("cable %s -> missing part %s" % (cid, cb["partId"]))
        cp = cable_parts.get(cb.get("partId"))
        if cp:
            # Cores align with the part's cores BY POSITION, so a count
            # mismatch means the wrong gauge and colour on real copper.
            n = len(cp.get("cores", []))
            if n != len(cb.get("cores", [])):
                bad.append("cable %s has %d cores but part %s has %d"
                           % (cid, len(cb.get("cores", [])), cb["partId"], n))
            if cb.get("shield") and not cp.get("shielded"):
                bad.append("cable %s has a shield but part %s is not shielded"
                           % (cid, cb["partId"]))
        for core in cb.get("cores", []):
            kid = core.get("id")
            if kid in seen:
                bad.append("duplicate id %s" % kid)
            seen.add(kid)
            check_conductor("core", kid, core)
        sh = cb.get("shield")
        if sh:
            if sh.get("color") != "Shield":
                bad.append("cable %s shield colour is %r, must be 'Shield'"
                           % (cid, sh.get("color")))
            check_conductor("shield", sh.get("id"), sh)

    for c in d.get("connectors", []):
        for x in c.get("cavities", []):
            if x.get("notConnected") and (c["id"], x.get("id")) in wired:
                bad.append("cavity %s/%s is notConnected but has a conductor on it"
                           % (c["id"], x.get("id")))
    return bad


def main():
    files = sys.argv[1:] or sorted(f for f in os.listdir(SRC)
                                   if f.endswith(".harness"))
    total = 0
    for fn in files:
        bad = check(fn)
        total += len(bad)
        print("%-30s %s" % (fn, "OK" if not bad else "%d PROBLEMS" % len(bad)))
        for b in bad:
            print("      " + b)
    print("\n%d problems total" % total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
