"""Two hard rules Daniel set on 2026-09-23.  Both fail the build.

RULE 1 - NOTHING BUT A DRAIN ON A SHIELD GROUND. EVER.
    "No signals or power may flow over any shield ground ever! Never!"
    "If any 5v return or power ground or signal output touches a shield
     ground, it's wrong."
    A shield ground pin (A7, B17) may carry screens and nothing else.  Not a
    sensor return, not a 5V return, not a power ground, not a signal.

    Link says either pin works electrically - Adamw, Link staff, forum topic
    17263: "Either is fine. The 'Gnd Out' and 'Shield/Gnd' pins are both sensor
    ground."  So there is no reason NOT to keep the shield reference clean, and
    every reason to: any return current on it appears as noise on the screen.

RULE 2 - A BULKHEAD CAVITY HAS ONE NAME ON BOTH HALVES.
    "Bh connector pins must be named exactly the same across a mating pair.
     A cabin = A engine bay, B cabin = B engine bay.
     No pins should get different names on any two mating connectors."
    Same cavity, same signal text, in every file that draws either half.
"""
import json, glob, os, sys, collections

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild")
SHIELD_PINS = {("ecu_a", "a7"), ("ecu_b", "b17")}
PAIRS = {"bh_a_fw": "bh_a_eng", "bh_b_fw": "bh_b_eng"}

docs = {os.path.basename(f)[6:-8]: json.load(open(f, encoding="utf-8"))
        for f in sorted(glob.glob(os.path.join(R, "*.harness")))}


def conductors(d):
    """(wire, is_screen) for everything that carries current or signal."""
    for w in d.get("wires", []):
        tail = w["id"].rsplit("_", 1)[-1]
        screen = (w.get("color") == "Shield" or tail in ("sh", "shield", "drain")
                  or w["id"].startswith("w_drain"))
        yield w, screen
    for cb in d.get("cables", []):
        for co in cb.get("cores", []):
            yield co, False
        if cb.get("shield"):
            yield cb["shield"], True


bad = []

# ---- RULE 1 -----------------------------------------------------------------
for loom, d in docs.items():
    for w, screen in conductors(d):
        if screen:
            continue
        for e in (w.get("source"), w.get("target")):
            if e and (e.get("id"), e.get("handle")) in SHIELD_PINS:
                bad.append("R1 %s/%s is not a screen but lands on %s %s - "
                           "NOTHING but a drain may touch a shield ground"
                           % (loom, w["id"], e["id"], e["handle"]))

# ---- RULE 2 -----------------------------------------------------------------
# collect every signal text seen for (connector, cavity), across all files
sig = collections.defaultdict(dict)   # connector -> cavity -> {text: [looms]}
for loom, d in docs.items():
    for c in d.get("connectors", []):
        if c["id"] not in PAIRS and c["id"] not in PAIRS.values():
            continue
        for cv in c.get("cavities", []):
            t = (cv.get("signal") or "").strip()
            sig[c["id"]].setdefault(cv["id"], collections.defaultdict(list))
            sig[c["id"]][cv["id"]][t].append(loom)

# a) the same half must not disagree with itself between files
for conn, cavs in sorted(sig.items()):
    for cav, texts in sorted(cavs.items()):
        if len(texts) > 1:
            bad.append("R2 %s %s has %d different names across looms: %s"
                       % (conn, cav, len(texts),
                          " | ".join("%r in %s" % (t, ",".join(l))
                                     for t, l in texts.items())))

# b) the two halves of a mating pair must agree
for a, b in PAIRS.items():
    for cav in sorted(set(sig.get(a, {})) | set(sig.get(b, {})),
                      key=lambda x: int(x[1:]) if x[1:].isdigit() else 0):
        ta = sorted(sig.get(a, {}).get(cav, {}))
        tb = sorted(sig.get(b, {}).get(cav, {}))
        if ta and tb and ta != tb:
            bad.append("R2 %s %s is %r but %s %s is %r - a mating pair shares "
                       "one name" % (a, cav, ta[0], b, cav, tb[0]))

for line in bad:
    print(line)
print()
print("%d pin-name / shield-ground violations." % len(bad))
sys.exit(1 if bad else 0)
