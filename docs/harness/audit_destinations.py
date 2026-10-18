"""Wire-end labels (DECISIONS R156, Dan 2026-10-17, which replaces the terminal parts of R124 / R125) and
short, literal connector names (R124): every wire end says where THAT end lands in the car, and the
text the app builds a wire's Destination from stays readable.

harness.design builds the Destination column from "the component and cavity at the other
end of the conductor, followed by its signal in brackets"
(https://docs.harness.design/feature/wiring-tables); layout "Show destinations" shows the
component name and each cavity with its signal (https://docs.harness.design/feature/destinations).
So the fields that feed them are a connector's `label`, a cavity's `designation` and
`signal`, and a terminal's `signal` (a terminal has no label). Long explanations live in
full_text.json (the gates read them back through model.full_text), never in these fields.
A splice has no name field (the app shows S<n>), so it carries none.

  D1  connector label <= 48 characters, so it can say what the connector is and where
      ("IX-WS-F inline to front VRC (dash above ECU)"); R156 lifted R124's 12
  D2  label + designation, as the Destination prints it, <= 60 (was 20 under R124)
  D3  cavity signal <= 20
  D4  a terminal has no name field (v1.2 schema), so its signal IS its visible name: every loose
      end reads "<what it is> -> <where it lands>" ("INJ 12V -> FB-LOGIC INJ 15A",
      "ACT cut -> A18-11", "Horn LH GND -> EA"), at most 32, and is unique in its drawing
  D5  no generic words in any visible name (DECISIONS R125): never "broken off", "continues on",
      "loose", "see other", "wire end"; never a bare "Splice", "Ground", "GND", "Signal",
      "Power", "Wire", "Coil", "Coil +", "Coil -", "+12V out", "Fused +12V in", "Switched 12V"

R156 (Dan 2026-10-17: "I NEED TO KNOW WHAT THIS END OF THE WIRE CONNECTS TO"). A terminal or
splice carries a `label`: "the user's name for the component ... shown in place of the display
id wherever the component is named" (https://docs.harness.design/files/harness/document-format.md),
so it is what the canvas, the connection table From / To and every Destination print. In a
drawing that is not in PENDING_R156, D4 is replaced by:
  L1  every terminal and splice has a label; a terminal has no signal (the label already says what
      the wire is, and a second text on the node is what Dan read as the far end)
  L2  a terminal label reads "<where this end lands> - <what it is>" (R156 formats), at most 90, and
      its landing names a pin / stud / lug / bar / ground point / splice / lead; a splice label says what
      it joins
  L3  no arrow tail ("->", "<-") in any label or signal, no bare pin code ("C11-12", "IE1-14",
      "1F-1": write "C11 pin 12"), no internal id (anything with "_", e.g. sp_led_gnd)
  L4  labels are unique in the drawing, and the two ends of one wire never print the same name
  L5  every schematic note is at least 270 wide, and 390 once its text passes 200 characters
      (Dan: "make notes wider!!"; 390 is the widest NodeWidth the v1.2 schema allows)

Run from anywhere:  python docs/harness/audit_destinations.py
Sample table:       python docs/harness/audit_destinations.py --table A-cabin ecu_a
Wire ends:          python docs/harness/audit_destinations.py --ends ClusterLED  (both printed ends of every wire)
(--raw on either shows the long text the drawings carried before.)
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model

LABEL, DEST, SIGNAL, TERM = 48, 60, 20, 32   # R156 lifted LABEL 12 -> 48, DEST 20 -> 60
END = 90
# Drawings not yet relabelled to R156: they keep the R125 D4 check until their group ships
# (2026-10-17 task split: G2 A-cabin, B-cabin; G3 A-engine, B-engine; G4 EngineRoom-C,
# HeavyDC, CAN, WheelSpeed-Front, WheelSpeed-Rear; G1 the rest). Remove a name when its
# drawing is relabelled; the list only ever shrinks.
PENDING_R156 = {"A-cabin", "B-cabin"}
LANDS = re.compile(r"\b(pins?|stud|lug|bar|ground point|splice|terminal post|lead|anode|cathode)\b", re.I)
ARROW = re.compile("->|<-|\u2192|\u2190")
PINCODE = re.compile(r"\b[A-Z0-9/]*[A-Z][A-Z0-9/]*-\d+\b")
INTERNAL = re.compile(r"\b[a-z0-9]+_[a-z0-9_]+\b", re.I)
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
    for t in d.get("terminals", []) + d.get("splices", []):
        if t["id"] == ref["id"]:
            if not t.get("label"):
                return t.get("signal") or t["id"]
            return t["label"] + (" (%s)" % t["signal"] if t.get("signal") else "")
    for t in d.get("diodes", []) + d.get("resistors", []):
        if t["id"] == ref["id"]:
            return "%s %s" % (t.get("label") or t["id"], ref.get("handle"))
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


def code_faults(text):
    out = []
    if ARROW.search(text):
        out.append("an arrow tail")
    m = PINCODE.search(text)
    if m:
        out.append("bare pin code %r (write '<conn> pin <n>')" % m.group(0))
    m = INTERNAL.search(text)
    if m:
        out.append("internal id %r" % m.group(0))
    return out


def r156(h, d):
    """The R156 wire-end checks for one relabelled drawing."""
    bad, seen = [], {}
    for kind, items in (("terminal", d.get("terminals", [])), ("splice", d.get("splices", []))):
        for t in items:
            lab = (t.get("label") or "").strip()
            if not lab:
                bad.append("L1 %s %s %s has no label (where this end lands)" % (h, kind, t["id"]))
                continue
            if kind == "terminal" and t.get("signal"):
                bad.append("L1 %s %s carries a signal %r besides its label" % (h, t["id"], t["signal"][:40]))
            where, sep, what = lab.partition(" - ")
            if not sep or not where.strip() or not what.strip() or len(lab) > END:
                bad.append("L2 %s %s %r: needs '<where it lands> - <what it is>', max %d" % (h, t["id"], lab[:60], END))
            elif kind == "terminal" and not LANDS.search(where):
                bad.append("L2 %s %s %r: the landing names no pin / stud / lug / bar / ground point / splice"
                           % (h, t["id"], lab[:60]))
            if generic(lab) or generic(where) or generic(what):
                bad.append("D5 %s %s %r is generic" % (h, t["id"], lab[:60]))
            for f in code_faults(lab):
                bad.append("L3 %s %s %r has %s" % (h, t["id"], lab[:60], f))
            if lab in seen:
                bad.append("L4 %s %s %r is the same label as %s" % (h, t["id"], lab[:60], seen[lab]))
            seen.setdefault(lab, t["id"])
    for c in d.get("connectors", []):
        for txt in [c.get("label") or ""] + [x.get("signal") or "" for x in c.get("cavities", [])]:
            if ARROW.search(txt):
                bad.append("L3 %s %s %r has an arrow tail" % (h, c["id"], txt[:60]))
    for a, b in ends(d):
        na, nb = name(d, a), name(d, b)
        if na == nb:
            bad.append("L4 %s both ends of the wire at %s print %r" % (h, a["id"], na[:60]))
    for x in d.get("schematicNotes", []):
        txt = x.get("text") or ""
        w, need = x.get("width") or 150, 390 if len(txt) > 200 else 270
        if w < need:
            bad.append("L5 %s note %s is %d wide (needs %d for %d characters)" % (h, x["id"], w, need, len(txt)))
    return bad


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
        if h in PENDING_R156:
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
        else:
            bad += r156(h, d)
            n += len(d.get("terminals", [])) + len(d.get("splices", []))
    for b in bad:
        print("  FAIL " + b)
    print("audit_destinations: %s (%d components, %d findings)" % ("FAIL" if bad else "PASS", n, len(bad)))
    return 1 if bad else 0

if __name__ == "__main__":
    if "--ends" in sys.argv:
        dd = drawing(model.harness_files()[sys.argv[sys.argv.index("--ends") + 1]])
        for w, _, _ in model.conductors(dd):
            if "source" in w and "target" in w:
                print("%-18s %s\n%-18s   to %s" % (w["id"], name(dd, w["source"]), "", name(dd, w["target"])))
    elif "--table" in sys.argv:
        i = sys.argv.index("--table")
        table(sys.argv[i + 1], sys.argv[i + 2])
    else:
        sys.exit(audit())
