"""One-time migration: the current drawings -> master wire list rows (DECISIONS R201, Phase 1).

The A-cabin list was written by hand in the pilot. The other 14 files are read here from their
current drawings: every wire, core and screen becomes ONE row from a real end to a real end, with
the drawing's broken-off pairs (interfaces.json `breaks`) joined back into one physical wire.
A wire drawn in two files is one row, owned by the file with the longer drawn half (Dispatch
for Dan, 2026-10-19: ties and unknown lengths go to the file listed first in interfaces.json),
`passes_through` names the other file.

The drawing is only where the rows come FROM. wirelist.py then checks every row against the
live SoT (sot/channels.csv, interfaces.json, the DRB102 cavity map, the fuse-box wiring plan),
and from then on the CSV is the source: build_harness.py builds the drawing from it.

Never overwrites a list that exists (A-cabin, or a file already migrated) unless --force.

    python docs/harness/cleanroom/extract_wirelist.py            # every file without a list
    python docs/harness/cleanroom/extract_wirelist.py --force CAN
"""
import csv
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
from descriptions import DESC, describe  # noqa: E402


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def short(text):
    """The drawn label's name part: before a double space or ' - '."""
    return re.split(r"  | - ", text or "")[0].strip()


class Drawings:
    def __init__(self):
        self.reg = model.registry()
        self.files = model.harness_files(self.reg)
        self.order = list(self.files)
        self.raw = {h: load_json(os.path.join(HARNESS, "rebuild", fn)) for h, fn in self.files.items()}
        self.brk = model.break_ends(self.reg)
        self.fl = {(f["harness"], f["terminal"]): f for f in self.reg["flyingLeads"]}
        self.circuit = {}
        for h, cs in self.reg["identBands"].items():
            for name, c in cs.items():
                if isinstance(c, dict):
                    for w in c.get("wires", []):
                        self.circuit[(h, w)] = name
        with open(os.path.join(HARNESS, "HARNESS-BUILD-LIST.csv"), encoding="utf-8") as f:
            self.est = {(r["File"], r["Wire"]): r["Est mm"] for r in csv.DictReader(f)}
        self.cond = {}      # (h, id) -> (conductor, cable, screen)
        self.at = {}        # (h, end id) -> [(conductor id, side)]
        for h, d in self.raw.items():
            for c, cable, scr in model.conductors(d):
                self.cond[(h, c["id"])] = (c, cable, scr)
                for side in ("source", "target"):
                    e = c.get(side) or {}
                    if e.get("id"):
                        self.at.setdefault((h, e["id"]), []).append((c["id"], side))
        self.node = {}
        for h, d in self.raw.items():
            for k in ("connectors", "splices", "resistors", "diodes", "terminals"):
                for x in d.get(k, []):
                    self.node[(h, x["id"])] = (k, x)
        self.parts = {h: model.parts(d) for h, d in self.raw.items()}
        self.end_note = {(h, n["id"][len("n_end_"):]): n["text"] for h, d in self.raw.items()
                         for n in d.get("schematicNotes", []) if n["id"].startswith("n_end_")}

    def gauge(self, h, cid):
        c, cable, _ = self.cond[(h, cid)]
        g = ((self.parts[h].get(c.get("partId")) or {}).get("gauge") or {}).get("value", "")
        if not g and cable:
            cb = next(x for x in self.raw[h]["cables"] if x["id"] == cable)
            cores = (self.parts[h].get(cb.get("partId")) or {}).get("cores") or []
            for i, core in enumerate(cb["cores"]):
                if core["id"] == cid and i < len(cores):
                    g = (cores[i].get("gauge") or {}).get("value", "")
            if not g and cb.get("shield", {}).get("id") == cid:
                g = ""
        return str(g)

    def other_half(self, h, term):
        """(h2, conductor id, side at the break) of the other drawn half of break end `term`."""
        bid = self.brk[(h, term)]
        br = next(b for b in self.reg["breaks"] if b["id"] == bid)
        o = next(e for e in br["ends"] if (e["harness"], e["terminal"]) != (h, term))
        hits = self.at.get((o["harness"], o["terminal"]), [])
        if len(hits) != 1:
            raise SystemExit("break %s: %d conductors at %s on %s" % (bid, len(hits), o["terminal"], o["harness"]))
        return o["harness"], hits[0][0], hits[0][1], bid

    def chain(self, h, cid):
        """Every drawn half of the physical wire `cid` on `h`, in order, and its two real ends:
        ([(h, id)], end_from, end_to) with each end = (h, endpoint dict, conductor id)."""
        halves = [(h, cid)]
        ends = []
        for side, other in (("source", "target"), ("target", "source")):
            hh, cc, sd = h, cid, side
            seen = []
            while True:
                c = self.cond[(hh, cc)][0]
                e = c.get(sd) or {}
                if e.get("id") and (hh, e["id"]) in self.brk:
                    h2, c2, sd2, _ = self.other_half(hh, e["id"])
                    seen.append((h2, c2))
                    hh, cc = h2, c2
                    sd = "target" if sd2 == "source" else "source"
                    continue
                ends.append((hh, e, cc))
                break
            halves = (seen[::-1] + halves) if side == "source" else (halves + seen)
        return halves, ends[0], ends[1]

    def endpoint(self, h, e, cid):
        """A drawn end -> wire-list endpoint (type, conn, name, pin, harness, extra)."""
        nid, hd = e.get("id"), e.get("handle")
        if not nid:  # an open cable screen: floats at this end
            cable = self.cond[(h, cid)][1]
            return dict(type="cable screen", conn=cable or cid, name="cable screen (one end only)", pin="", harness=h)
        kind, x = self.node[(h, nid)]
        if kind == "connectors":
            for cav, pin in zip(x["cavities"], WL.pin_names(x)):
                if cav["id"] == hd:
                    return dict(type="connector", conn=nid, name=short(x.get("label", nid)),
                                pin=pin, harness=h, signal=cav.get("signal") or "", cav_id=cav["id"])
            raise SystemExit("%s %s: no cavity %s" % (h, nid, hd))
        if kind == "splices":
            return dict(type="splice", conn=nid, name="splice %s (%s)" % (nid, (x.get("label") or "").split(" - ")[0]),
                        pin="", harness=h, label=x.get("label") or "")
        if kind in ("resistors", "diodes"):
            pin = {"Left": "1", "Right": "2"}.get(hd, hd)
            return dict(type=kind[:-1], conn=nid, name=x.get("label") or nid, pin=pin, harness=h)
        # terminals
        if (h, nid) in self.fl:
            ew = self.fl[(h, nid)]["ewd"]
            return dict(type="OEM", conn="%s (factory)" % ew["connector"], name=short(x.get("label")) or "OEM %s" % ew["connector"],
                        pin=ew["pin"], harness=h, ewd=ew, term=nid, label=x.get("label") or "")
        return dict(type="terminal", conn=nid, name=(x.get("label") or nid).split(" - ")[0], pin="", harness=h,
                    label=x.get("label") or "", term=nid)


def rows_for(dw, h, consumed):
    """Wire-list rows for every conductor drawn on `h` that no earlier row holds."""
    out = []
    for (hh, cid), (c, cable, scr) in dw.cond.items():
        if hh != h or (h, cid) in consumed:
            continue
        halves, a, b = dw.chain(h, cid)
        for x in halves:
            consumed.add(x)
        lens = {x: dw.est.get(x, "") for x in halves}
        owner = halves[0]
        known = [x for x in halves if lens[x]]
        if len(known) == len(halves) and len(halves) > 1:
            best = max(float(lens[x]) for x in halves)
            owner = min((x for x in halves if float(lens[x]) == best), key=lambda x: dw.order.index(x[0]))
        elif len(halves) > 1:
            owner = min(halves, key=lambda x: dw.order.index(x[0]))
        oh, oid = owner
        oc, ocable, oscr = dw.cond[owner]
        ea, eb = dw.endpoint(*a), dw.endpoint(*b)
        notes = []
        if len(halves) > 1:
            drawn = "; ".join("%s on %s, %s mm" % (x[1], x[0], lens[x] or "?") for x in halves)
            notes.append(("owner proposed: longer half" if len(known) == len(halves) else
                          "owner TBD: a half has no length estimate") + " (drawn today as %s)" % drawn)
        gauges = {dw.gauge(*x) for x in halves} - {""}
        if len(gauges) > 1:
            notes.append("halves drawn with different gauges: %s" % ", ".join(
                "%s %s AWG" % (x[1], dw.gauge(*x)) for x in halves))
        cols = {dw.cond[x][0].get("color", "") for x in halves}
        if len(cols) > 1:
            notes.append("halves drawn in different colours: %s" % ", ".join(
                "%s %s" % (x[1], dw.cond[x][0].get("color", "")) for x in halves))
        circuit = next((dw.circuit[x] for x in halves if x in dw.circuit), "")
        oems = [e for e in (ea, eb) if e.get("ewd")]

        def note(e):
            return dw.end_note.get((e["harness"], e.get("term", "")), "")

        def oem_where(e):
            return note(e) or e.get("label", "")

        row = {
            "circuit_id": circuit, "wire_id": oid, "harness": oh,
            "passes_through": " / ".join(x for x in dict.fromkeys(x[0] for x in halves) if x != oh),
            "splice": next((e["conn"] for e in (ea, eb) if e["type"] == "splice"), ""),
            "cable": ocable or "", "gauge_awg": dw.gauge(*owner),
            "colour": "Shield" if oscr else oc.get("color", ""), "stripe": oc.get("stripeColor", ""),
            "ident_bands": "-".join(oc.get("identColors", [])),
            "oem_location": " / ".join(oem_where(e) for e in oems),
            "oem_wire_colour": " / ".join(e["ewd"].get("color", "") for e in oems),
            "oem_ewd_page": " / ".join(e["ewd"].get("page", "") for e in oems),
            "oem_method": " / ".join(e["ewd"].get("method", "") for e in oems),
            "route_branch": "", "est_length_mm": lens[owner],
            "notes": "; ".join(notes), "_ends": (ea, eb), "_halves": halves,
        }
        if oscr and (ea["type"] == "cable screen" or eb["type"] == "cable screen"):
            row["notes"] = "; ".join(x for x in ("screen floats at the far end", row["notes"]) if x)
        for s, e in (("from", ea), ("to", eb)):
            row.update({s + "_type": e["type"], s + "_conn": e["conn"], s + "_conn_name": e["name"],
                        s + "_pin": e["pin"], s + "_note": note(e) if e["type"] in ("OEM", "terminal") else ""})
        out.append(row)
    return out


def spare_rows(dw, h, rows_all):
    """Unwired cavities of this file's own connectors: 'spare' rows with no wire (R201)."""
    wired = {(r[s + "_conn"], r[s + "_pin"]) for r in rows_all for s in ("from", "to")}
    caps = {b["receptacle"] for b in dw.reg["bussedSplices"]["buses"]}
    out = []
    drb = WL.drb_map()
    for c in dw.raw[h].get("connectors", []):
        if c["id"] in caps:
            continue
        part = (dw.parts[h].get(c.get("partId")) or {}).get("partNumber", "")
        sealed = part.upper().startswith(("DT", "DRB", "HD", "AT", "DTM"))
        for cav, des in zip(c["cavities"], WL.pin_names(c)):
            if (c["id"], des) in wired:
                continue
            if c["id"] in WL.DRB102:
                sec = drb.get(des, ("?",))[0]
                if sec != WL.DRB102[c["id"]]:
                    continue  # the other section of the shared DRB102
            out.append(dict({k: "" for k in WL.COLUMNS}, harness=h, from_type="connector", from_conn=c["id"],
                            from_conn_name=short(c.get("label", c["id"])), from_pin=des,
                            from_desc="spare, sealing plug" if sealed else "spare, not used"))
    return out


def main(argv):
    force = set(argv[argv.index("--force") + 1:]) if "--force" in argv else set()
    dw = Drawings()
    have = {h for h in dw.order if os.path.exists(WL.csv_path(h)) and h not in force}
    consumed = set()
    lists = {h: WL.read_rows(h) for h in have}
    # the halves the existing lists already hold
    for h in have:
        for r in lists[h]:
            if r["wire_id"]:
                hh = r["harness"] if (r["harness"], r["wire_id"]) in dw.cond else h
                if (hh, r["wire_id"]) not in dw.cond:
                    hh = next((x for x in dw.order if (x, r["wire_id"]) in dw.cond), None)
                if hh:
                    for x in dw.chain(hh, r["wire_id"])[0]:
                        consumed.add(x)
    new = {}
    for h in dw.order:
        if h in have:
            continue
        new.setdefault(h, [])
        for r in rows_for(dw, h, consumed):
            new.setdefault(r["harness"], []).append(r)
    allrows = [r for v in lists.values() for r in v] + [r for v in new.values() for r in v]
    describe(allrows, dw)
    # rows of an existing list that another file owns move to that file's list
    moved = []
    for h in list(have):
        keep = []
        for r in lists[h]:
            if r["wire_id"] and r["harness"] != h:
                new.setdefault(r["harness"], []).append(r)
                moved.append("%s %s -> %s" % (h, r["wire_id"], r["harness"]))
            else:
                keep.append(r)
        if moved:
            lists[h] = keep
            WL.write_rows(h, keep)
    for h, rows in new.items():
        if h in have:
            lists[h].extend(rows)
            WL.write_rows(h, lists[h])
            continue
        rows = sorted(rows, key=lambda r: (r["from_type"] != "connector", r["from_conn"], WL.pin_key(r["from_pin"]),
                                           r["to_conn"], WL.pin_key(r["to_pin"]), r["wire_id"]))
        rows += spare_rows(dw, h, allrows)
        WL.write_rows(h, rows)
        print("%s: %d rows (%d wires)" % (h, len(rows), sum(bool(r["wire_id"]) for r in rows)))
    for m in moved:
        print("moved", m)
    unused = sorted(set(DESC) - {r["wire_id"] for r in allrows})
    if unused:
        print("description overrides with no row:", ", ".join(unused))


if __name__ == "__main__":
    main(sys.argv[1:])
