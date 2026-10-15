"""Short, literal names (DECISIONS R124 / R125, Dan 2026-10-15): the text the app builds a wire's Destination from
stays short and literal, so the wiring tables and layout "Show destinations" can be read.

harness.design builds the Destination column from "the component and cavity at the other
end of the conductor, followed by its signal in brackets"
(https://docs.harness.design/feature/wiring-tables); layout "Show destinations" shows the
component name and each cavity with its signal (https://docs.harness.design/feature/destinations).
So the fields that feed them are a connector's `label`, a cavity's `designation` and
`signal`, and a terminal's `signal` (a terminal has no label). Long explanations live in
full_text.json (the gates read them back through model.full_text), never in these fields.
A splice has no name field (the app shows S<n>), so it carries none.

  D1  connector label <= 12 characters ("ECU-A", "FB-LOGIC", "LOGIC M15")
  D2  label + designation, as the Destination prints it, <= 20 ("FB-LOGIC BUS2-13 IN")
  D3  cavity signal <= 20
  D4  a terminal has no name field (v1.2 schema), so its signal IS its visible name: every loose
      end reads "<what it is> -> <where it lands>" ("INJ 12V -> FB-LOGIC INJ 15A",
      "ACT cut -> A18-11", "Horn LH GND -> EA"), at most 32, and is unique in its drawing
  D5  no generic words in any visible name (DECISIONS R125): never "broken off", "continues on",
      "loose", "see other", "wire end"; never a bare "Splice", "Ground", "GND", "Signal",
      "Power", "Wire", "Coil", "Coil +", "Coil -", "+12V out", "Fused +12V in", "Switched 12V"

Run from anywhere:  python docs/harness/audit_destinations.py
Sample table:       python docs/harness/audit_destinations.py --table A-cabin ecu_a
(--raw on either shows the long text the drawings carried before.)
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model

LABEL, DEST, SIGNAL, TERM = 12, 20, 20, 32
BANNED = ("broken off", "broken-off", "continues on", "loose", "see other", "wire end")
GENERIC = {"splice", "ground", "gnd", "signal", "power", "wire", "terminal", "coil", "coil +",
           "coil -", "coil+", "coil-", "+12v out", "fused +12v in", "switched 12v", "12v", "+12v"}


def generic(text):
    t = (text or "").strip().lower()
    return t in GENERIC or next((w for w in BANNED if w in t), None)
RAW = "--raw" in sys.argv


def drawing(fn):
    with open(os.path.join(model.REB, fn), encoding="utf-8") as f:
        d = json.load(f)
    return model.full_text(d, fn) if RAW else d


def ends(d):
    for w, _, _ in model.conductors(d):
        if "source" in w and "target" in w:
            yield w["source"], w["target"]


def name(d, ref):
    """What the Destination column prints for one conductor end."""
    for c in d.get("connectors", []):
        if c["id"] == ref["id"]:
            cav = next((x for x in c["cavities"] if x["id"] == ref.get("handle")), {})
            sig = cav.get("signal")
            return "%s %s" % (c["label"], cav.get("designation", ref.get("handle"))) + (
                " (%s)" % sig if sig else "")
    for t in d.get("terminals", []):
        if t["id"] == ref["id"]:
            return t.get("signal") or t["id"]
    return ref["id"]


def table(h, cid):
    d = drawing(model.harness_files()[h])
    c = next(c for c in d["connectors"] if c["id"] == cid)
    print("%s  %s" % (h, c["label"]))
    print("%-6s %-22s %s" % ("Cavity", "Signal", "Destination"))
    for x in c["cavities"]:
        far = [b if a["id"] == cid and a.get("handle") == x["id"] else a
               for a, b in ends(d) if (cid, x["id"]) in ((a["id"], a.get("handle")), (b["id"], b.get("handle")))]
        for f in far or [None]:
            print("%-6s %-22s %s" % (x.get("designation", x["id"]), (x.get("signal") or "")[:60],
                                     name(d, f) if f else ""))


def audit():
    reg = model.registry()
    bad, n = [], 0
    for h, fn in model.harness_files(reg).items():
        d = drawing(fn)
        for c in d.get("connectors", []):
            lab = c.get("label", "")
            n += 1
            if len(lab) > LABEL:
                bad.append("D1 %s %s label %r is %d long (max %d)" % (h, c["id"], lab, len(lab), LABEL))
            if generic(lab):
                bad.append("D5 %s %s label %r is generic" % (h, c["id"], lab[:60]))
            for x in c.get("cavities", []):
                dest = "%s %s" % (lab, x.get("designation", x["id"]))
                if len(dest) > DEST:
                    bad.append("D2 %s %s.%s destination %r is %d long (max %d)" % (h, c["id"], x["id"], dest, len(dest), DEST))
                sig = x.get("signal") or ""
                if len(sig) > SIGNAL:
                    bad.append("D3 %s %s.%s signal %r is %d long (max %d)" % (h, c["id"], x["id"], sig[:60], len(sig), SIGNAL))
                if sig and generic(sig):
                    bad.append("D5 %s %s.%s signal %r is generic" % (h, c["id"], x["id"], sig[:60]))
        seen = {}
        for t in d.get("terminals", []):
            sig = t.get("signal") or ""
            n += 1
            what, _, where = sig.partition(" -> ")
            if not what.strip() or not where.strip() or len(sig) > TERM:
                bad.append("D4 %s %s %r: needs '<what> -> <where it lands>', max %d" % (h, t["id"], sig[:60], TERM))
            if generic(sig) or generic(what):
                bad.append("D5 %s %s %r is generic" % (h, t["id"], sig[:60]))
            if sig in seen:
                bad.append("D4 %s %s %r is the same name as %s" % (h, t["id"], sig, seen[sig]))
            seen.setdefault(sig, t["id"])
    for b in bad:
        print("  FAIL " + b)
    print("audit_destinations: %s (%d components, %d findings)" % ("FAIL" if bad else "PASS", n, len(bad)))
    return 1 if bad else 0

if __name__ == "__main__":
    if "--table" in sys.argv:
        i = sys.argv.index("--table")
        table(sys.argv[i + 1], sys.argv[i + 2])
    else:
        sys.exit(audit())
