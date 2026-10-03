"""Every assigned ECU signal reaches a real far end, across every harness boundary.

Replaces verify_rebuild.py's comparison against the frozen legacy baseline. That
baseline cannot follow an intentional change of ownership or boundary; this check
works from the SoT instead, on the one electrical graph model.py builds (bulkhead
halves, inline interface halves, cross-reference dummies and VRC enclosures all
collapse to one node each).

  C1  every sot/channels.csv ECU row with class=signal and status=set is wired on
      some drawing
  C2  from that pin the net reaches a far end - a device cavity, a terminal, a
      resistor or a device enclosure - not only splices, bulkhead cavities, interface
      pins or another ECU pin
  C3  every cross-reference dummy resolves to a component drawn somewhere; an
      unresolved one is a conductor that stops at another drawing's boundary with
      nothing on the other side
  C4  every far end that C2 accepts is LABELLED: a connector cavity needs signal text
      (it is the harness plug that mates to an undrawn device), a terminal (flying lead,
      device endpoint lead, ring/stud) needs signal or label text, a resistor needs a
      label or part. Unlabelled far ends
      fail - a builder could not tell what plugs in there.

What counts as a far end (C2): a connector cavity that is not a bulkhead, an inline
interface or the ECU (the harness plug that mates to an undrawn device - sensors,
modules, the CSB3), a Loose terminal (OEM flying lead or device endpoint lead), a
resistor, or a device enclosure (VRC). A drawn device is never required - devices are
never drawn (harness-wiring-conventions).

Exit 1 on any finding.
"""
import sys

import model

g = model.Graph()
bad = []
THROUGH = ("SP", "BH", "IX", "BRK", "ECU")

rows = [r for r in model.sot_rows()
        if r["owner"] == "ECU" and r["class"] == "signal" and r["status"] == "set"]
checked = 0
for r in rows:
    n = ("ECU", r["conn"], r["pin"])
    if n not in g.adj:
        bad.append("C1 %s.%s %s is set in the SoT but wired on no drawing"
                   % (r["conn"], r["pin"], r["net"]))
        continue
    checked += 1
    net = g.reach(n, stop=lambda m: m[0] not in THROUGH or (m[0] == "ECU" and m != n))
    far = [m for m in net if m[0] in ("C", "T", "ENC")]
    if not far:
        bad.append("C2 %s.%s %s never reaches a device: %s"
                   % (r["conn"], r["pin"], r["net"], ", ".join(sorted(model.fmt(m) for m in net))))

# C4: label lookup for every connector cavity and terminal, per drawing
cav_label, term_label = {}, {}
for loom, d in g.docs.items():
    for c in d.get("connectors", []):
        for cv in c.get("cavities", []):
            if (cv.get("signal") or "").strip():
                cav_label[(c["id"], cv["id"])] = cv["signal"]
    for rs in d.get("resistors", []) + d.get("diodes", []):
        if (rs.get("label") or rs.get("partId") or "").strip():   # a resistor is labelled by its part
            for side in ("Left", "Right"):
                cav_label[(rs["id"], side)] = rs.get("label") or rs.get("partId")
    for tm in d.get("terminals", []):
        txt = (tm.get("signal") or tm.get("label") or "").strip()
        if txt:
            term_label[(loom, tm["id"])] = txt
unlabelled = set()
for r in rows:
    n = ("ECU", r["conn"], r["pin"])
    if n not in g.adj:
        continue
    net = g.reach(n, stop=lambda m: m[0] not in THROUGH or (m[0] == "ECU" and m != n))
    for m in net:
        if m[0] == "C" and (m[1], m[2]) not in cav_label:
            unlabelled.add(("C4 %s.%s %s ends at connector %s cavity %s, which has no signal label"
                            % (r["conn"], r["pin"], r["net"], m[1], m[2])))
        if m[0] == "T" and (m[1], m[2]) not in term_label:
            unlabelled.add(("C4 %s.%s %s ends at terminal %s/%s, which has no signal or label"
                            % (r["conn"], r["pin"], r["net"], m[1], m[2])))
bad.extend(sorted(unlabelled))

for n in g.adj:
    if n[0] == "DM":
        bad.append("C3 %s resolves to nothing drawn (used by %s)"
                   % (n[1], ", ".join("%s/%s" % x for x in g.where[n])))

print("ECU signal pins traced: %d of %d" % (checked, len(rows)))
for line in bad:
    print(line)
print("\n%d connectivity finding(s)." % len(bad))
sys.exit(1 if bad else 0)
