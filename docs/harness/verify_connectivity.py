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

for n in g.adj:
    if n[0] == "DM":
        bad.append("C3 %s resolves to nothing drawn (used by %s)"
                   % (n[1], ", ".join("%s/%s" % x for x in g.where[n])))

print("ECU signal pins traced: %d of %d" % (checked, len(rows)))
for line in bad:
    print(line)
print("\n%d connectivity finding(s)." % len(bad))
sys.exit(1 if bad else 0)
