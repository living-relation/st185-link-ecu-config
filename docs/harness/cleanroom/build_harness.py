"""Build one harness drawing from the master wire list (DECISIONS R201; Phase 2 tool).

    python docs/harness/cleanroom/build_harness.py <harness> [--geometry FILE] [--out FILE] [--check]

The wire list (docs/harness/wirelist/*-wirelist.csv) says every wire: from pin, to pin, what it is
for, colour, stripe, ident bands, gauge, cable and the notes at its ends. This script writes that
into the drawing, the same way for every file:
  - every connector table reads like a pinout: the row's description is the cavity signal at both
    ends (propagate off); a cavity with no wire carries no signal;
  - every wire is point to point; a wire whose other end is in another file keeps its drawn end
    there (the off-sheet end, R201), labelled with where it lands;
  - an end note (n_end_<terminal>) is the row's note for that end; nothing else is invented.
The geometry (parts, positions, the whole layout view, bundles) comes from the current drawing -
Dan's layout is kept (R202: pinout tables first). Labels, the title and the general notes come
from docs/harness/cleanroom/specs/<harness>.json when it exists, else from the drawing. Parts,
nodes and wires no row uses are dropped (R44). Title block initials: %USERPROFILE%\\.drawing-initials
(R200); with no file and no terminal the build stops.

--check (no file: every rebuilt file in wirelist.GATED - the check_all.py gate) rebuilds in memory on
top of the committed drawing and fails if what the list owns differs: wire ends, colours, stripes,
ident bands, wire parts, cavity texts, labels, end notes, title block. Positions, the layout view,
routing points and the schema version are not compared, so Dan's in-app layout moves and the app's
revision bump pass (R116); any other edit to a rebuilt drawing fails until the list says it.
"""
import argparse
import copy
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, HARNESS)
import model  # noqa: E402
import wirelist as WL  # noqa: E402


class Drawings:
    """The drawn halves of every wire across the files: a broken-off pair (interfaces.json
    `breaks`) is one physical wire drawn in two (or more) files."""

    def __init__(self):
        self.reg = model.registry()
        self.files = model.harness_files(self.reg)
        self.brk = model.break_ends(self.reg)
        self.cond, self.at = {}, {}
        for h, fn in self.files.items():
            for c, cable, scr in model.conductors(load(os.path.join(HARNESS, "rebuild", fn))):
                self.cond[(h, c["id"])] = c
                for side in ("source", "target"):
                    e = c.get(side) or {}
                    if e.get("id"):
                        self.at.setdefault((h, e["id"]), []).append((c["id"], side))

    def other_half(self, h, term):
        br = next(b for b in self.reg["breaks"] if b["id"] == self.brk[(h, term)])
        o = next(e for e in br["ends"] if (e["harness"], e["terminal"]) != (h, term))
        hits = self.at.get((o["harness"], o["terminal"]), [])
        if len(hits) != 1:
            raise SystemExit("break %s: %d conductors at %s on %s" % (br["id"], len(hits), o["terminal"], o["harness"]))
        return o["harness"], hits[0][0], hits[0][1]

    def chain(self, h, cid):
        """[(file, conductor id)] of every drawn half of the wire `cid` on `h`, in order."""
        halves = [(h, cid)]
        for side in ("source", "target"):
            hh, cc, sd, seen = h, cid, side, []
            while True:
                e = self.cond[(hh, cc)].get(sd) or {}
                if not (e.get("id") and (hh, e["id"]) in self.brk):
                    break
                hh, cc, sd2 = self.other_half(hh, e["id"])
                seen.append((hh, cc))
                sd = "target" if sd2 == "source" else "source"
            halves = (seen[::-1] + halves) if side == "source" else (halves + seen)
        return halves

FULL_TEXT = os.path.join(HARNESS, "full_text.json")


def initials():
    """R200: the requester's initials from the one per-computer file (env DRAWING_INITIALS wins)."""
    if os.environ.get("DRAWING_INITIALS"):
        return os.environ["DRAWING_INITIALS"].strip()
    path = os.path.join(os.path.expanduser("~"), ".drawing-initials")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            text = f.read().strip()
        if text:
            return text
    if sys.stdin.isatty():
        text = input("Your initials for drawing title blocks (R200): ").strip()
        if text:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text + "\n")
            return text
    raise SystemExit("no %s and no terminal: ask Dispatch / Dan for the requester's initials (R200)" % path)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def rows_for(h):
    """Every wire row drawn on `h`: the ones it owns and the ones that pass through it."""
    out = []
    for f in model.harness_files():
        if os.path.exists(WL.csv_path(f)):
            for r in WL.read_rows(f):
                if r["wire_id"] and (r["harness"] == h or h in r["passes_through"].split(" / ")):
                    out.append(r)
    return out


def build(h, geo, spec, who):
    dw = Drawings()
    reg = dw.reg
    out = copy.deepcopy(geo)
    rows = rows_for(h)
    conns = {c["id"]: c for c in out.get("connectors", [])}
    pins = {cid: dict(zip(WL.pin_names(c), (x["id"] for x in c["cavities"]))) for cid, c in conns.items()}
    fl_term = {(f["ewd"]["connector"], f["ewd"]["pin"]): f["terminal"] for f in reg["flyingLeads"] if f["harness"] == h}
    conductors = {c["id"]: (c, cable, scr) for c, cable, scr in model.conductors(out)}
    halves = {}   # row wire id -> this file's drawn halves (a wire can leave and come back)
    for cid in conductors:
        if (h, cid) in dw.cond:
            for hh, x in dw.chain(h, cid):
                halves.setdefault(x, [])
                if cid not in halves[x]:
                    halves[x].append(cid)
    brk = {t for (hh, t) in dw.brk if hh == h}
    problems = []

    def handle(r, s):
        """(node id, handle) of row end `s` when that end is in this file, else None."""
        t, conn, pin = r[s + "_type"], r[s + "_conn"], r[s + "_pin"]
        if t == "connector" and conn in conns:
            if pin not in pins[conn]:
                problems.append("%s: %s has no pin %s" % (r["wire_id"], conn, pin))
                return None
            return {"id": conn, "handle": pins[conn][pin]}
        if t == "splice" and any(x["id"] == conn for x in out.get("splices", [])):
            return {"id": conn, "handle": "Splice"}
        if t in ("resistor", "diode") and any(x["id"] == conn for x in out.get(t + "s", [])):
            return {"id": conn, "handle": {"1": "Left", "2": "Right"}.get(pin, pin)}
        if t == "OEM":
            term = fl_term.get((conn.replace(" (factory)", ""), pin))
            if term:
                return {"id": term, "handle": "Terminal"}
        if t == "terminal" and any(x["id"] == conn for x in out.get("terminals", [])):
            return {"id": conn, "handle": "Terminal"}
        return None

    signal, used, end_note, keep = {}, set(), {}, set()
    for r in rows:
        cids = halves.get(r["wire_id"])
        if not cids:
            problems.append("%s: no drawn half on %s (add it in the app, then rebuild)" % (r["wire_id"], h))
            continue
        ends = {s: handle(r, s) for s in ("from", "to")}
        placed = set()
        for cid in cids:
            cond, cable, scr = conductors[cid]
            keep.add(cid)
            # a drawn end that is a break terminal is the off-sheet end (R201): it stays, and it
            # stands for the row end that is not on this half
            fixed = {k for k in ("source", "target") if (cond.get(k) or {}).get("id") in brk}
            assign = {}
            for s in ("from", "to"):   # a row end already drawn on this half keeps its side
                for key in ("source", "target"):
                    if ends[s] and s not in placed and key not in assign.values() and                             (cond.get(key) or {}).get("id") == ends[s]["id"]:
                        assign[s] = key
                        break
            for s in ("from", "to"):   # a re-pinned end takes a free side that is not off-sheet
                free = [k for k in ("source", "target") if k not in assign.values() and k not in fixed]
                if s not in assign and ends[s] and s not in placed and free:
                    assign[s] = free[0]
            for s in ("from", "to"):   # what is left is the off-sheet / open end
                free = [k for k in ("source", "target") if k not in assign.values()]
                if s not in assign and free:
                    assign[s] = free[0]
            for side, key in assign.items():
                if ends[side] and key not in fixed and side not in placed:
                    cond[key] = ends[side]
                    placed.add(side)
                    if r[side + "_type"] == "connector":
                        signal[(ends[side]["id"], ends[side]["handle"])] = r[side + "_desc"]
                elif r[side + "_type"] == "cable screen" and key not in fixed:
                    cond.pop(key, None)
                node = (cond.get(key) or {}).get("id")
                if node:
                    used.add(node)
                    if r[side + "_note"] and (cond.get(key) or {}).get("handle") == "Terminal":
                        end_note[node] = r[side + "_note"]   # the end that terminal stands for
            if not scr:
                for k, col in (("color", "colour"), ("stripeColor", "stripe")):
                    if r[col]:
                        cond[k] = r[col]
                    else:
                        cond.pop(k, None)
                cond["identColors"] = r["ident_bands"].split("-") if r["ident_bands"] else []
                if not cond["identColors"]:
                    cond.pop("identColors")
            part = model.parts(out).get(cond.get("partId")) or {}
            drawn_g = str(((part.get("gauge") or {}).get("value")) or "")
            if drawn_g and r["gauge_awg"] and drawn_g != r["gauge_awg"]:
                problems.append("%s: drawn part %s is %s AWG, the list says %s AWG (change the part in the app)" % (
                    cid, cond.get("partId"), drawn_g, r["gauge_awg"]))
        for s in ("from", "to"):
            if ends[s] and s not in placed:
                problems.append("%s: its %s end %s %s is in %s but no drawn half can take it" % (
                    r["wire_id"], s, r[s + "_conn"], r[s + "_pin"], h))
    # conductors no row holds go (R44); a cable keeps only the cores and screen a row holds
    out["wires"] = [w for w in out.get("wires", []) if w["id"] in keep]
    for cb in out.get("cables", []):
        cb["cores"] = [c for c in cb["cores"] if c["id"] in keep]
        if cb.get("shield") and cb["shield"]["id"] not in keep:
            cb.pop("shield")
    if "cables" in out:
        out["cables"] = [cb for cb in out["cables"] if cb["cores"] or cb.get("shield")]

    # connectors: label + one description per wired pin, nothing on unwired pins
    labels = spec.get("connectors", {})
    for c in out.get("connectors", []):
        if c["id"] in labels:
            c["label"] = labels[c["id"]]
        cap = spec.get("bus_caps", {}).get(c["id"])
        for cav in c["cavities"]:
            text = cap if cap and not cav.get("notConnected") else signal.get((c["id"], cav["id"]))
            if text:
                cav["signal"], cav["propagate"] = text, False
            elif not cav.get("notConnected"):
                cav.pop("signal", None)
                cav.pop("propagate", None)
    # splices, resistors, terminals: the ones a row uses, labelled from the spec
    for kind in ("splices", "resistors", "diodes"):
        if kind in out:
            out[kind] = [x for x in out[kind] if x["id"] in used]
            for x in out[kind]:
                if x["id"] in spec.get(kind, {}):
                    x["label"] = spec[kind][x["id"]]
    out["terminals"] = [t for t in out.get("terminals", []) if t["id"] in used]
    for t in out["terminals"]:
        sp = spec.get("terminals", {}).get(t["id"])
        if sp:
            t["label"] = sp["label"]   # R156: a wire end has a label and no signal
            t.pop("signal", None)
            if spec.get("terminal_width"):
                t["width"] = spec["terminal_width"]
    # layout legs that ended at a removed node go, and so do branch points left as dead ends
    live = {x["id"] for k in ("connectors", "terminals", "splices", "resistors", "diodes") for x in out.get(k, [])}
    bps = {p["id"] for p in out.get("branchPoints", [])}
    out["bundles"] = [b for b in out.get("bundles", []) if b["sourceId"] in live | bps and b["targetId"] in live | bps]
    while out.get("branchPoints"):
        deg = {p["id"]: 0 for p in out["branchPoints"]}
        for b in out["bundles"]:
            for k in ("sourceId", "targetId"):
                if b[k] in deg:
                    deg[b[k]] += 1
        held = {x.get("locationId") for k in ("splices", "resistors", "diodes", "connectors", "terminals") for x in out.get(k, [])}
        dead = {k for k, v in deg.items() if v <= 1 and k not in held}
        if not dead:
            break
        out["bundles"] = [b for b in out["bundles"] if b["sourceId"] not in dead and b["targetId"] not in dead]
        out["branchPoints"] = [p for p in out["branchPoints"] if p["id"] not in dead]
    out["mates"] = [m for m in out.get("mates", []) if m["sourceId"] in live and m["targetId"] in live]

    # notes: the spec's one general block, the row notes at their ends, the spec's node notes;
    # without a spec the drawing's own non-end notes stay
    old = {n["id"]: n for n in geo.get("schematicNotes", [])}
    notes = []
    if spec.get("general_notes"):
        notes.append(dict(old.get("n_general", {}), id="n_general", text="\n".join(spec["general_notes"]), width=390))
    else:
        notes += [n for n in geo.get("schematicNotes", []) if not n["id"].startswith("n_end_")]
    for t in out["terminals"]:
        text = end_note.get(t["id"])
        if text:
            nid = "n_end_" + t["id"]
            notes.append(dict(old.get(nid, {}), id=nid, text=text, width=390 if len(text) > 200 else 270))
    for nid, n in spec.get("node_notes", {}).items():
        notes.append(dict(old.get(nid, {}), id=nid, text=n["text"], width=270))
    out["schematicNotes"] = notes

    # title block (R200: DRAWN = Rev A's person, never changes; BY = who asked for the change)
    tb = out.setdefault("titleBlock", {})
    if spec.get("title"):
        tb["title"] = spec["title"]
    if spec.get("rev"):
        tb["drawingNumber"] = "ST185-%s rev %s" % (h, spec["rev"])
        tb["drawnBy"] = tb.get("drawnBy") or who
        rest = re.sub(r"^Rev [A-Z0-9.]+, BY [^:]+: [^\n]*\n", "", geo.get("exportNotes", ""))
        out["exportNotes"] = "Rev %s, BY %s: %s\n%s" % (spec["rev"], spec.get("rev_by") or who, spec.get("rev_note", ""), rest)

    # parts no wire / cable uses any more go (R44)
    used_p = {w.get("partId") for w in out["wires"]}
    have = {p["id"] for p in out.get("wireParts", [])}
    lib = {p["id"]: p for p in load(os.path.join(HARNESS, "rebuild", "ST185.harnesslib")).get("wireParts", [])}
    out["wireParts"] = out.get("wireParts", []) + [copy.deepcopy(lib[i]) for i in sorted(used_p - have) if i in lib]   # the library is the master (R39)
    out["wireParts"] = [p for p in out["wireParts"] if p["id"] in used_p]
    used_p = {c.get("partId") for c in out.get("cables", [])}
    if "cableParts" in out:
        out["cableParts"] = [p for p in out["cableParts"] if p["id"] in used_p]
    return out, problems


def full_text(h, out, spec):
    """full_text.json entry of `h`: a mated connector shows the same text as its other half, so its
    long text is that half's (model.full_text); a spec'd terminal's long text is the spec's."""
    ft = load(FULL_TEXT)
    fn = model.harness_files()[h]
    rec = ft.setdefault(fn, {"connectors": {}, "terminals": {}})
    reg = model.registry()
    files = model.harness_files(reg)
    mates = {}
    for ix in reg["interfaces"]:
        a, b = ix["halves"]
        mates[a["connector"]], mates[b["connector"]] = (b["harness"], b["connector"]), (a["harness"], a["connector"])
    mates["bh_fw"], mates["bh_eng"] = ("ECU-engine", "bh_eng"), ("ECU-cabin", "bh_fw")   # the DRB102's two halves
    for c in out.get("connectors", []):
        if c["id"] not in mates or c["id"] not in rec.get("connectors", {}):
            continue
        oh, oc = mates[c["id"]]
        other = ft.get(files[oh], {}).get("connectors", {}).get(oc, {}).get("cavities", {})
        rec["connectors"][c["id"]] = {"cavities": {
            cav["id"]: [cav["signal"], other[cav["id"]][1]]
            for cav in c["cavities"] if cav.get("signal") and cav["id"] in other}}
    for tid, t in spec.get("terminals", {}).items():
        if t.get("long"):
            rec.setdefault("terminals", {})[tid] = ["", t["long"]]
    return ft


def owned(d):
    """What the wire list and spec own in a drawing - the part the gate compares. Positions, the
    layout view (bundles, branch points), routing points, note widths, part definitions and the
    schema version are NOT in it: Dan's layout moves in the desktop app and the app's own save /
    revision bump (R116) pass, and the builder keeps them (it starts from the committed file)."""
    conds = {}
    for c, cable, scr in model.conductors(d):
        conds[c["id"]] = [cable, (c.get("source") or {}).get("id"), (c.get("source") or {}).get("handle"),
                          (c.get("target") or {}).get("id"), (c.get("target") or {}).get("handle"),
                          c.get("color"), c.get("stripeColor"), c.get("identColors"), c.get("partId")]
    out = {"conductors": conds,
           "connectors": {c["id"]: {"label": c.get("label"), "cavities": {
               x["id"]: [x.get("signal"), x.get("propagate"), x.get("notConnected")] for x in c["cavities"]}}
               for c in d.get("connectors", [])},
           "notes": {n["id"]: n.get("text") for n in d.get("schematicNotes", [])},
           "title": [d.get("titleBlock", {}).get(k) for k in ("title", "drawingNumber", "drawnBy")],
           "exportNotes": (d.get("exportNotes") or "").split(chr(10))[0]}
    for k in ("splices", "resistors", "diodes", "terminals"):
        out[k] = {x["id"]: x.get("label") for x in d.get(k, [])}
    return out


def diff(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b), key=str):
            out += diff(a.get(k), b.get(k), "%s/%s" % (path, k)) if k in a and k in b else                 ["%s/%s %s" % (path, k, "added" if k in b else "removed")]
        return out
    return [] if a == b else ["%s: %r -> %r" % (path, a, b)]


def check(names):
    """The gate: every rebuilt (GATED) file, rebuilt in memory from its list on top of its committed
    self, must own the same content as the committed file."""
    bad = []
    for h in names:
        path = os.path.join(HARNESS, "rebuild", model.harness_files()[h])
        committed = load(path)
        sp_path = os.path.join(HERE, "specs", "%s.json" % h)
        spec = load(sp_path) if os.path.exists(sp_path) else {}
        # no initials asked here: DRAWN comes from the committed file and BY from the spec (a blank
        # one shows up as a difference); CI has no initials file and needs none (R200)
        out, problems = build(h, committed, spec, "")
        d = diff(owned(committed), owned(out)) + ["PROBLEM " + p for p in problems]
        ft = full_text(h, out, spec)
        if json.dumps(ft, indent=1, ensure_ascii=False) + chr(10) != open(FULL_TEXT, encoding="utf-8").read():
            d.append("full_text.json is not what the list gives")
        print("%s: %s" % (h, "matches its wire list" if not d else "%d difference(s) from its wire list" % len(d)))
        for x in d[:20]:
            print("   ", x)
        bad += d
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("harness", nargs="?")
    ap.add_argument("--geometry")
    ap.add_argument("--out")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    files = model.harness_files()
    if a.check and not a.harness:   # the check_all.py gate: every rebuilt file
        pending = [h for h in files if h not in WL.GATED]
        bad = check([h for h in files if h in WL.GATED])
        print("pending (not rebuilt yet, not gated): %s" % ", ".join(pending))
        print("build_harness --check: %s" % ("FAIL - a rebuilt drawing was edited outside its wire list: change the "
                                             "list (or spec) and rebuild, never the drawing" if bad else "OK"))
        return 1 if bad else 0
    if a.harness not in files:
        raise SystemExit("unknown harness %s (one of: %s)" % (a.harness, ", ".join(files)))
    if a.check:
        return 1 if check([a.harness]) else 0
    path = os.path.join(HARNESS, "rebuild", files[a.harness])
    geo = load(a.geometry or path)
    sp_path = os.path.join(HERE, "specs", "%s.json" % a.harness)
    spec = load(sp_path) if os.path.exists(sp_path) else {}
    out, problems = build(a.harness, geo, spec, initials() if spec.get("rev") else "")
    for p in problems:
        print("PROBLEM", p)
    if problems:
        raise SystemExit("not written: %d problem(s)" % len(problems))
    text = json.dumps(out, indent=2, ensure_ascii=False) + chr(10)
    ft_text = json.dumps(full_text(a.harness, out, spec), indent=1, ensure_ascii=False) + chr(10)
    target = a.out or path
    for p, t in ((target, text), (FULL_TEXT, ft_text)):
        tmp = p + ".tmp"
        crlf = os.path.exists(p) and b"\r\n" in open(p, "rb").read(4096)   # keep the file's own line ending: no whole-file diffs
        with open(tmp, "w", encoding="utf-8", newline=chr(13) + chr(10) if crlf else chr(10)) as f:
            f.write(t)
        os.replace(tmp, p)
    print("wrote %s: %d wires, %d cable conductors, %d connectors, %d splices, %d wire ends" % (
        target, len(out["wires"]), sum(len(c["cores"]) + bool(c.get("shield")) for c in out.get("cables", [])),
        len(out.get("connectors", [])), len(out.get("splices", [])), len(out.get("terminals", []))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
