"""Build drawings/ST185-pin-chart.pdf from MASTER-wirelist.csv: every connector drawn as its cavity face, each cavity
coloured by its wire, and a table of what lands on each pin and where the other end goes (device + pin, fuse box + fuse,
relay + terminal; a splice lists where it leads). Faces: pin_chart/faces.json and faces2.json (sourced layouts) or the
DRB102 layout in build_drawings.py; a connector with no sourced layout is a numbered list, flagged.
Run: python docs/harness/tools/build_pin_chart.py   (needs playwright + chromium)"""
import csv, json, html, os, re, sys, tempfile, collections, importlib.util

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pin_chart")
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
spec = importlib.util.spec_from_file_location("bd", os.path.join(REPO, "docs/harness/tools/build_drawings.py"))
BD = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BD)

rows = list(csv.DictReader(open(os.path.join(REPO, "docs/harness/MASTER-wirelist.csv"), encoding="utf-8")))
FACES = json.load(open(os.path.join(HERE, "faces.json"), encoding="utf-8")) if os.path.exists(os.path.join(HERE, "faces.json")) else {}
ALIAS = {"354404": "13519047", "CONN-76270": "EV6", "D 261 205 358-01": "1-967616-1",
         "DT06-2S-CE05": "DT06-2S", "DT06-3S-CE05": "DT06-3S", "5-1393292-8": "V23074", "6-1419137-4": "V23074",
         "4-1904124-2": "V23074", "4-1904124-3": "V23074", "1-1414147-0": "V23134", "1-1393304-0": "V23134",
         "V23132-A2001-B200": "HCR150"}

WIRE = {"Red": "#c8312b", "Black": "#2b2b2b", "White": "#f4f4f2", "Blue": "#2a62c9", "Orange": "#e8781e",
        "Yellow": "#f0c419", "Green": "#2e8b43", "Shield": "#9a9a9a", "": "#d9d9d9"}
LIGHT = {"White", "Yellow", ""}
FRM = list(csv.DictReader(open(os.path.join(REPO, "sot/fuse-relay-map.csv"), encoding="utf-8")))
BOX = {"B1": "POWER fuse box", "B2": "LOGIC fuse box", "B3": "Trunk relay box", "B4": "beside the POWER fuse box"}
RELAY = {r["master_id"]: (r["bank"], r["position"], r["circuit"]) for r in FRM if r["kind"] == "relay" and r["master_id"].startswith("K-")}
FIX = {"BUS-5V": "+5 V bussed plug at the ECU, fed by ECU plug A pin 32 (BUS-5V)",
       "BUS-5V-2": "+5 V bussed plug 2 at the ECU, fed from BUS-5V pin 12 (BUS-5V-2)",
       "BUS-GNDOUT-A": "Sensor-ground bussed plug A at the ECU, to ECU plug A pin 24 (BUS-GNDOUT-A)",
       "BUS-GNDOUT-B": "Sensor-ground bussed plug B at the ECU, to ECU plug B pin 22 (BUS-GNDOUT-B)",
       "BUS-SW12": "Switched 12 V bussed plug in the glove box by the LOGIC fuse box, fed by LOGIC fuse BUS2-2 (BUS-SW12)",
       "DRB102-ENGINE": "DRB102 bulkhead, engine side", "DRB102-CABIN": "DRB102 bulkhead, cabin side",
       "ECU-A": "Link G4X plug A", "ECU-B": "Link G4X plug B",
       "IX-WS-F-P": "Front wheel-speed inline plug, sensor side (IX-WS-F)", "IX-WS-F-S": "Front wheel-speed inline plug, VRC side (IX-WS-F)",
       "IX-WS-R-P": "Rear wheel-speed inline plug, sensor side (IX-WS-R)", "IX-WS-R-S": "Rear wheel-speed inline plug, VRC side, dash above the ECU (IX-WS-R)",
       "IX-FUEL-P": "Fuel sender inline plug, harness side, trunk (IX-FUEL)", "IX-FUEL-S": "Fuel sender inline plug, sender side, trunk (IX-FUEL)",
       "R-CRUISE": "Cruise resistor on the CSB3", "R-TERM-ECU": "120 ohm CAN end resistor, ECU end",
       "R-TERM-END": "120 ohm CAN end resistor, Lambda end", "POWER": "POWER fuse box", "LOGIC": "LOGIC fuse box",
       "BATT-RELAY-BLOCK": "Trunk relay box", "POWER-STUDS": "POWER fuse box", "CSB3": "ECUMaster CSB3",
       "COIL-1": "Coil 1", "COIL-2": "Coil 2", "COIL-3": "Coil 3", "COIL-4": "Coil 4"}
FUSE = {}
for r in rows:
    for s in ("from", "to"):
        if r[s + "_id"] in ("POWER", "LOGIC"):
            m = re.findall(r"(?:AMI|LOGIC)\s+(\w+)\s+([\d.]+) A fuse", r["from_desc"] + " " + r["to_desc"])
            p = r[s + "_pin"]
            if m and not p.endswith(" IN") and p not in ("BUS1", "BUS2"):
                FUSE.setdefault((r[s + "_id"], p), "%s %s A" % (m[-1] if r[s + "_id"] == "LOGIC" or p.startswith("AMI") else m[0]))


def dev(i, name, typ):
    """Device name: the master name unless it is only a code; relays say their box and seat."""
    if typ == "cable screen":
        return "Shield, not connected at the device end"
    if i in RELAY:
        b, pos, circ = RELAY[i]
        return ("%s relay (%s)" % (circ[0].upper() + circ[1:], BOX[b])) if b == "B4" else "%s relay %s (%s)" % (BOX[b], pos, circ)
    if i in FIX:
        return FIX[i]
    return re.split(r" - ", name or i)[0].strip() or i


def where(i, name, typ, pin):
    """Goes-to text: device + pin, fuse box + fuse, or relay + terminal."""
    d = dev(i, name, typ)
    if not pin or typ in ("OEM", "cable screen", "terminal"):
        return d
    if i in RELAY:
        return d + " · terminal " + pin
    if i in ("POWER", "LOGIC"):
        if pin in ("BUS1", "BUS2"):
            return d + " · Bus %s feed" % pin[-1]
        side = " input" if pin.endswith(" IN") else ""
        p = pin[:-3] if side else pin
        f = FUSE.get((i, p))
        return d + " · fuse %s%s%s" % (p, " (%s)" % f if f else "", side)
    if i == "POWER-STUDS":
        return d + " · %s stud" % pin
    if i == "BATT-RELAY-BLOCK":
        return d + (" · FP fuse (40 A)" if pin == "FP" else " · battery + stud")
    return d + " · pin " + pin


ENDS = collections.defaultdict(list)
for r in rows:
    if r["wire_id"]:
        ENDS[r["from_id"]].append((r, "to"))
        ENDS[r["to_id"]].append((r, "from"))
TYPES = {}
for r in rows:
    TYPES[r["from_id"]] = r["from_type"]; TYPES[r["to_id"]] = r["to_type"]


def through(sp, came, seen=None):
    seen = seen or {sp}
    out = []
    for r, o in ENDS[sp]:
        if r["wire_id"] == came:
            continue
        oid = r[o + "_id"]
        if r[o + "_type"] == "splice" and oid not in seen:
            seen.add(oid)
            out += through(oid, r["wire_id"], seen)
        elif oid not in seen:
            out.append(where(oid, r[o + "_name"], r[o + "_type"], r[o + "_pin"]))
    return out


def goes_to(r, o):
    if r[o + "_type"] == "splice":
        t = list(dict.fromkeys(through(r[o + "_id"], r["wire_id"])))
        return "Splice to: " + "; ".join(t)
    return where(r[o + "_id"], r[o + "_name"], r[o + "_type"], r[o + "_pin"])


# ---- gather every connector end
con = collections.OrderedDict()
for r in rows:
    for s, o in (("from", "to"), ("to", "from")):
        if r[s + "_type"] != "connector":
            continue
        cid = r[s + "_id"]
        c = con.setdefault(cid, {"id": cid, "name": r[s + "_name"], "pn": r[s + "_housing_pn"], "extra": r[s + "_housing_extra"],
                                 "doc": r[s + "_pin_doc"], "harness": set(), "pins": collections.defaultdict(list)})
        c["harness"].add(r["harness"])
        other = goes_to(r, o) if (r[o + "_id"] or r[o + "_type"]) else ""
        c["pins"][r[s + "_pin"]].append({
            "wire": r["wire_id"], "awg": r["gauge_awg"], "colour": r["colour"],
            "desc": r[s + "_desc"] or r["circuit"], "other": other if r["wire_id"] else "", "term": r[s + "_terminal_pn"],
            "spare": not r["wire_id"]})


KEYMAP = {"4-1437290-0": "TE Superseal 1.0 34-pos 4-1437290-0 (code 1)", "4-1437290-1": "TE Superseal 1.0 34-pos 4-1437290-1 (code 2)",
          "90980-11400": "Toyota 90980-11400 (1-way starter)", "D 261 205 358-01": "TE MQS 6-pos 1-967616-1 (Bosch ETB 0 280 750 474)",
          "DT06-2S": "Deutsch DT06-2S (plug, sockets)", "DT06-2S-CE05": "Deutsch DT06-2S (plug, sockets)",
          "DT04-2P": "Deutsch DT04-2P (receptacle, pins)", "DT06-3S": "Deutsch DT06-3S (plug, sockets)", "DT06-3S-CE05": "Deutsch DT06-3S (plug, sockets)",
          "DT06-6S": "Deutsch DT06-6S (plug, sockets)", "DT06-08SA": "Deutsch DT06-08SA (plug, sockets)", "DT06-12SA": "Deutsch DT06-12SA (plug, sockets)",
          "DT04-6P": "Deutsch DT04-6P", "DTHD06-1-8S": "Deutsch DTHD06-1-8S", "HD36-24-33SE": "Deutsch HD36-24-33SE (HD30 shell 24, 24-33)",
          "LP-16-J05PE-02-001": "CNLINKO LP-16 5-pin female cable plug LP-16-J05PE-02-001",
          "1-1414147-0": "TE Power Relay F7 V23134 (1-1414147-0, 1-1393304-0)", "1-1393304-0": "TE Power Relay F7 V23134 (1-1414147-0, 1-1393304-0)"}
LETTER = {"A": "1", "B": "2", "C": "3"}
F2 = json.load(open(os.path.join(HERE, "faces2.json"), encoding="utf-8")) if os.path.exists(os.path.join(HERE, "faces2.json")) else {}
KEY2 = {"90980-11885": "Toyota 90980-11885", "90980-11062": "Toyota 90980-11062", "90980-11143": "Toyota 90980-11143",
        "90980-10947": "Toyota 90980-10947", "90980-11250": "Toyota 90980-11250", "90980-12068": "Toyota 90980-12068",
        "90980-10897": "Toyota 90980-10897", "90980-10942": "Toyota 90980-10942", "90980-10341": "Toyota 90980-10341",
        "DTM06-4S": "Deutsch DTM06-4S", "4-1904124-2": "TE micro ISO relay V23074", "4-1904124-3": "TE micro ISO relay V23074",
        "5-1393292-8": "TE micro ISO relay V23074", "6-1419137-4": "TE micro ISO relay V23074",
        "V23132-A2001-B200": "TE HCR150 V23132-A2001-B200"}


def face_for(c):
    if c["id"].startswith("DRB102"):
        return "DRB"
    k = KEYMAP.get(c["pn"])
    f = FACES.get(k) if k else None
    if not f and c["pn"] in KEY2:
        f = F2.get(KEY2[c["pn"]])
    if not f or not (f.get("rows") or f.get("xy")):
        return None
    f = dict(f)
    lm = f.get("label_map")
    if lm:
        f["rows"] = [[lm.get(str(x), x) if x is not None else None for x in r] for r in f["rows"]]
        f["flag"] = "Relay terminal numbers mapped to ISO 85 / 86 / 30 / 87 / 87a (%s)." % ", ".join("%s = %s" % kv for kv in lm.items())
    if any(str(x) in LETTER for r in f.get("rows") or [] for x in r if x is not None):
        f["rows"] = [[LETTER.get(str(x), x) if x is not None else None for x in r] for r in f["rows"]]
        f["flag"] = "Deutsch moulds this 3-way as A / B / C; the master numbers it 1 / 2 / 3, read here as A = 1, B = 2, C = 3."
    return f


def pin_key(p):
    m = re.match(r"(\D*)(\d+)(.*)", p)
    return (m.group(1), int(m.group(2)), m.group(3)) if m else (p, 0, "")


def cav_svg(cx, cy, r, num, entries, square=False):
    used = [e for e in entries if not e["spare"]]
    col = used[0]["colour"] if used else ""
    fill = WIRE.get(col, "#d9d9d9") if used else "var(--spare)"
    txt = "#111" if (not used or col in LIGHT) else "#fff"
    tip = html.escape("%s: %s" % (num, "; ".join("%s %s AWG %s - %s" % (e["wire"], e["awg"], e["colour"], e["desc"]) for e in used) or "spare"))
    shape = ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2"' % (cx - r, cy - r, 2 * r, 2 * r) if square
             else '<circle cx="%.1f" cy="%.1f" r="%.1f"' % (cx, cy, r))
    fs = max(7, min(12, r * 0.9))
    if not used:
        return ('<g class="cav sp" data-pin="%s"><title>%s</title>%s fill="var(--bg)" stroke="var(--dim)" stroke-width="1" stroke-dasharray="3 2"/>'
                '<text x="%.1f" y="%.1f" font-size="%.1f" fill="var(--dim)">%s</text></g>' % (
                    html.escape(num), tip, shape, cx, cy + fs * 0.35, fs, html.escape(num)))
    return ('<g class="cav" data-pin="%s"><title>%s</title>%s fill="%s" stroke="var(--ink)" stroke-width="2"/>'
            '<text x="%.1f" y="%.1f" font-size="%.1f" fill="%s">%s</text></g>' % (
                html.escape(num), tip, shape, fill, cx, cy + fs * 0.35, fs, txt, html.escape(num)))


def svg_xy(c, face):
    xy = face["xy"]
    R, pad = 150, 22
    W = 2 * (R + pad)
    out = ['<svg viewBox="0 0 %d %d" width="%d" height="%d" class="face" role="img" aria-label="cavity face">' % (W, W, W * 0.7, W * 0.7)]
    out.append('<circle cx="%d" cy="%d" r="%d" fill="var(--body)" stroke="var(--ink)" stroke-width="1.5"/>' % (W / 2, W / 2, R + pad - 4))
    span = max(max(abs(v[0]), abs(v[1])) for v in xy.values()) or 1
    for n, (x, y) in xy.items():
        out.append(cav_svg(W / 2 + x / span * (R - 14), W / 2 - y / span * (R - 14), 12, str(n), c["pins"].get(str(n), [])))
    out.append("</svg>")
    return "".join(out)


def svg_grid(c, face):
    if face.get("xy"):
        return svg_xy(c, face)
    rowsx = face["rows"]
    ncol = max(len(r) for r in rowsx)
    pitch, pad = 34, 18
    W = pad * 2 + ncol * pitch
    Hh = pad * 2 + len(rowsx) * pitch
    shape = face.get("shape", "rect")
    out = ['<svg viewBox="0 0 %d %d" width="%d" height="%d" class="face" role="img" aria-label="cavity face">' % (W, Hh + 16, W, Hh + 16)]
    rx = Hh / 2 if shape in ("round", "oval") else 8
    out.append('<rect x="2" y="2" width="%d" height="%d" rx="%.1f" fill="var(--body)" stroke="var(--ink)" stroke-width="1.5"/>' % (W - 4, Hh - 4, rx))
    latch = face.get("latch") if face.get("latch") in ("top", "bottom") else None
    if latch == "top":
        out.append('<rect x="%d" y="0" width="%d" height="6" rx="2" fill="var(--ink)"/>' % (W / 2 - 14, 28))
    elif latch == "bottom":
        out.append('<rect x="%d" y="%d" width="%d" height="6" rx="2" fill="var(--ink)"/>' % (W / 2 - 14, Hh - 6, 28))
    for ri, rr in enumerate(rowsx):
        off = (ncol - len(rr)) * pitch / 2
        for ci, n in enumerate(rr):
            if n is None:
                continue
            n = str(n)
            cx = pad + off + ci * pitch + pitch / 2
            cy = pad + ri * pitch + pitch / 2
            out.append(cav_svg(cx, cy, 12, n, c["pins"].get(n, []), square=face.get("cav") == "square"))
    if latch in ("top", "bottom"):
        out.append('<text x="%d" y="%d" class="cap">latch %s</text>' % (W / 2, Hh + 12, latch))
    out.append("</svg>")
    return "".join(out)


def svg_drb(c):
    xs = [30 + i * 46 for i in range(12)]
    step, mid = 30, 230
    W, Hh = 30 + 11 * 46 + 30, 470
    out = ['<svg viewBox="0 0 %d %d" width="%d" height="%d" class="face drb" role="img" aria-label="DRB102 insert face">' % (W, Hh, W, Hh)]
    out.append('<rect x="2" y="2" width="%d" height="%d" rx="18" fill="var(--body)" stroke="var(--ink)" stroke-width="1.5"/>' % (W - 4, Hh - 24))
    out.append('<line x1="%d" y1="10" x2="%d" y2="%d" stroke="var(--ink)" stroke-dasharray="4 4"/>' % (W / 2, W / 2, Hh - 30))
    for ci, col in enumerate(BD.DRB_COLS):
        top = mid - (len(col) - 1) * step / 2
        for k, n in enumerate(col):
            if n is None:
                continue
            r = {16: 9, 12: 11, 8: 13, 4: 15}[BD.DRB_SIZE.get(n, 16)]
            out.append(cav_svg(xs[ci], top + k * step, r, str(n), c["pins"].get(str(n), [])))
    out.append('<text x="%d" y="%d" class="cap">52-102 (left half)</text><text x="%d" y="%d" class="cap">1-51 (right half)</text>' % (
        W / 4, Hh - 8, 3 * W / 4, Hh - 8))
    out.append("</svg>")
    return "".join(out)


def svg_list(c):
    pins = sorted(c["pins"], key=pin_key)
    n = len(pins)
    per = min(n, 8)
    face = {"rows": [pins[i:i + per] for i in range(0, n, per)], "shape": "rect"}
    return svg_grid(c, face)



cards = []
sections = collections.OrderedDict()
ORDER = ["AB-cabin", "AB-engine", "CabinPower", "EngineRoom-C", "HeavyDC", "RearFuel", "CSB3", "ClusterLED", "AntiTheft", "CAN"]
counts = {"sourced": 0, "drb": 0, "unverified": 0}
for c in con.values():
    face = face_for(c)
    if face == "DRB":
        svg, status, view = svg_drb(c), "sourced", "TE drawing view, numbers moulded on the insert"
        counts["drb"] += 1
    elif face:
        svg, status = svg_grid(c, face), "sourced"
        view = "%s view%s" % ({"wire": "wire side (where the contacts go in)", "mating": "mating face"}.get(face.get("view"), face.get("view", "?")),
                              (". " + face["flag"]) if face.get("flag") else "")
        note = face.get("note") or ""
        counts["sourced"] += 1
    else:
        svg, status, view = svg_list(c), "unverified", "layout not sourced: numbered list only, match the moulded numbers"
        counts["unverified"] += 1
    src = (face.get("source") or "") if isinstance(face, dict) else ""
    note = (face.get("note") or "") if isinstance(face, dict) else ""
    trs = []
    for p in sorted(c["pins"], key=pin_key):
        for e in c["pins"][p]:
            if e["spare"]:
                trs.append('<tr class="sp"><td class="pin">%s</td><td colspan="5">spare</td></tr>' % html.escape(p))
                continue
            trs.append('<tr><td class="pin">%s</td><td><span class="sw" style="background:%s"></span>%s %s%s</td>'
                       '<td class="mono">%s</td><td>%s</td><td>%s</td><td class="mono dim">%s</td></tr>' % (
                           html.escape(p), WIRE.get(e["colour"], "#ccc"), html.escape(e["awg"]), html.escape(e["colour"]), "",
                           html.escape(e["wire"]), html.escape(e["desc"]), html.escape(e["other"]), html.escape(e["term"])))
    hs = sorted(c["harness"], key=lambda h: ORDER.index(h) if h in ORDER else 99)
    key = hs[0]
    pname = dev(c["id"], c["name"], "connector")
    hay = " ".join([c["id"], pname, c["name"], c["pn"]] + [e["other"] for v in c["pins"].values() for e in v] + [e["wire"] + " " + e["desc"] for v in c["pins"].values() for e in v]).lower()
    card = ('<article class="card" id="c-%s" data-hay="%s"><header><h3>%s</h3><span class="pn">%s · %s</span>'
            '<span class="chip %s">%s</span></header><p class="nm">%s</p>'
            '<div class="faceWrap">%s</div><p class="view">%s%s</p>%s'
            '<div class="tw"><table><thead><tr><th>Pin</th><th>Wire</th><th>Wire ID</th><th>What it does</th><th>Goes to</th><th>Contact</th></tr></thead>'
            '<tbody>%s</tbody></table></div><p class="doc">Pin numbers: %s · harness %s</p></article>') % (
        html.escape(c["id"]), html.escape(hay), html.escape(pname), html.escape(c["id"]), html.escape(c["pn"] + (" + " + c["extra"] if c["extra"] else "")),
        status, "face sourced" if status == "sourced" else "face not sourced",
        html.escape(c["name"]), svg, html.escape(view),
        (' · <a href="%s" target="_blank" rel="noopener">source</a>' % html.escape(src)) if src.startswith("http") else "",
        ('<details class="nt"><summary>Drawing notes</summary>%s</details>' % html.escape(note)) if note else "",
        "".join(trs), html.escape(c["doc"] or "TBD"), html.escape(", ".join(hs)))
    sections.setdefault(key, []).append(card)

nav = "".join('<a href="#s-%s">%s <b>%d</b></a>' % (k, k, len(v)) for k, v in sorted(sections.items(), key=lambda kv: ORDER.index(kv[0]) if kv[0] in ORDER else 99))
body = "".join('<section id="s-%s"><h2>%s</h2><div class="grid">%s</div></section>' % (k, k, "".join(v))
               for k, v in sorted(sections.items(), key=lambda kv: ORDER.index(kv[0]) if kv[0] in ORDER else 99))
tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
out = tpl.replace("{{NAV}}", nav).replace("{{BODY}}", body).replace("{{N}}", str(len(con))).replace(
    "{{SRC}}", str(counts["sourced"] + counts["drb"])).replace("{{UNV}}", str(counts["unverified"]))
PDF = os.path.join(REPO, "docs", "harness", "drawings", "ST185-pin-chart.pdf")
with tempfile.TemporaryDirectory() as tmp:
    page_html = os.path.join(tmp, "pin-chart.html")
    open(page_html, "w", encoding="utf-8").write(out)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page()
        pg.emulate_media(media="print", color_scheme="light")
        pg.goto("file://" + page_html)
        pg.pdf(path=PDF, format="Letter", landscape=True, print_background=True, prefer_css_page_size=True)
        b.close()
print("wrote", os.path.relpath(PDF, REPO), len(con), "connectors", counts)
