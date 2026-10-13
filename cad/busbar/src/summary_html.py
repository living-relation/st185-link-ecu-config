"""Build ST185-busbar-designs.html: all three saved versions side by side (single file, images embedded).
Claude Code, 2026-10-13.  A rev 2 | B rev 1 (frozen, as built) | B rev 2 (universal bus).
"""
import os, json, base64, sys
import fitz
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# key, spec, folder, file prefix, Fusion document, short label
VERSIONS = [
    ("A", spec.A, "design-A", "A", "ST185_busbar_A", "A rev 2"),
    ("B", spec.B, "design-B", "B", "ST185_busbar_B", "B rev 1"),
    ("B_rev2", spec.B2, "design-B-rev2", "B_rev2", "ST185_busbar_B_rev2", "B rev 2"),
    ("A_rev3", spec.A3, "design-A-rev3", "A_rev3", "ST185_busbar_A_rev3", "A rev 3"),
    ("B_rev3", spec.B3, "design-B-rev3", "B_rev3", "ST185_busbar_B_rev3", "B rev 3"),
]


def img(path, w=1100):
    pm = fitz.Pixmap(path)
    if pm.alpha:
        pm = fitz.Pixmap(pm, 0)
    if pm.width > w:
        pm = fitz.Pixmap(pm, w, int(pm.height * w / pm.width))
    return "data:image/jpeg;base64," + base64.b64encode(pm.tobytes("jpeg", jpg_quality=80)).decode()


def pdf_img(path):
    d = fitz.open(path)
    pm = d[0].get_pixmap(dpi=90)
    return "data:image/jpeg;base64," + base64.b64encode(pm.tobytes("jpeg", jpg_quality=78)).decode()


def f(v, name):
    return os.path.join(ROOT, v[2], v[3] + "_" + name)


def rows(d):
    out = []
    for (x, y, lug, ex, pole, label) in d["studs"]:
        w, h = spec.notch(d, stud=(x, y, lug, ex, pole, label))
        out.append((pole, label, spec.LUGS[lug]["stud"] + " stud", "Klauke " + lug, "%.0fx%.0f" % (w, h), "front" if ex < 0 else "rear"))
    for (x, fy, dr, pole, label) in d["ports"]:
        w, h = spec.notch(d, port=(x, fy, dr, pole, label))
        out.append((pole, label, "port D13.5", "H50,0/25 ferrule", "%.0fx%.0f" % (w, h), "front" if dr > 0 else "rear"))
    for (x, y, lp, ll) in d.get("links", []):
        out.append((lp, ll + " (link strap)", "M8 link stud", "6 x 20 Al strap", "-", "-"))
    order = {"POS": 0, "NEG": 1, "UNI": 2}
    out.sort(key=lambda r: (order[r[0]], "SPARE" in r[1], "LINK" in r[1]))
    return out


def table(d):
    h = ['<table><tr><th>pole</th><th>connection</th><th>stud / port</th><th>lug</th><th>exit WxH</th><th>exits</th></tr>']
    for r in rows(d):
        cls = "sp" if "SPARE" in r[1] else {"POS": "pos", "NEG": "neg", "UNI": "uni"}[r[0]]
        h.append('<tr class="%s"><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                 % ((cls, {"POS": "+", "NEG": "&minus;", "UNI": "U"}[r[0]]) + r[1:]))
    h.append("</table>")
    return "".join(h)


rep = {v[0]: json.load(open(f(v, "report.json"))) for v in VERSIONS}


def mass(k, key):
    return sum(p["mass_g"] * p.get("qty", 1) for n, p in rep[k]["parts"].items() if key in n)


def counts(d):
    c = {}
    for s_ in d["studs"]:
        c.setdefault(s_[4], [0, 0])[1 if "SPARE" in s_[5] else 0] += 1
    for p_ in d["ports"]:
        c.setdefault(p_[3], [0, 0])[1 if "SPARE" in p_[4] else 0] += 1
    return c


def cnt_txt(d):
    c = counts(d)
    t = "+ %d used / %d spare &middot; &minus; %d / %d" % (c["POS"][0], c["POS"][1], c["NEG"][0], c["NEG"][1])
    if "UNI" in c:
        t += " &middot; U %d studs (+ or &minus;)" % (c["UNI"][0] + c["UNI"][1])
    return t


FACTS = {
    "A_rev3": dict(tag="LATEST A", pockets="milled in Al", hold="7&times; M4 into blind inserts (+ 4, &minus; 3), spread end to end",
                   term="lugs on every connection (M10 for 1/0)", uni="&mdash;", note="A rev 2 with 7 well-spread hold-down screws; &minus; bar 12 mm longer."),
    "B_rev3": dict(tag="LATEST B", pockets="milled in Al", hold="10&times; M4 into blind inserts (+ 4, &minus; 3, U 3)",
                   term="1/0 in set-screw ports; M8 lug studs", uni="3&times; M8; strap <b>or AMG fuse</b> (50.8 mm studs)",
                   note="B rev 2 + more hold-downs + fuse-ready link (strap or AMG/MEGA fuse)."),
    "A": dict(tag="A rev 2", pockets="milled in Al", hold="2&times; M4 per bar into blind inserts", term="lugs on every connection (M10 for 1/0)",
              uni="&mdash;", note="Inline poles, two stepped rows; wires leave front and rear."),
    "B": dict(tag="SAVED AS BUILT", pockets="printed locator plates (rev 1)", hold="plate tabs + 4&times; M4 into blind inserts",
              term="1/0 in set-screw ports; M8 lug studs", uni="&mdash;", note="Back-to-back poles; + leaves front, &minus; leaves rear."),
    "B_rev2": dict(tag="B rev 2", pockets="milled in Al", hold="2&times; M4 per bar into blind inserts (6)", term="1/0 in set-screw ports; M8 lug studs",
                   uni="3&times; M8, one strap to + or &minus;", note="B with rev 2 upgrades plus a universal bus next to &minus;."),
}

CSS = """
:root{--bg:#fafaf8;--fg:#1d1d1b;--mut:#6b6b66;--card:#fff;--line:#e3e2dd;--pos:#c62828;--neg:#1565c0;--uni:#7b3fa0;--ok:#2e7d32;--new:#7b3fa0;--old:#8a6d1d}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161615;--fg:#ecebe6;--mut:#a3a29c;--card:#1f1f1d;--line:#34332f;--pos:#ef6b6b;--neg:#6aa8f0;--uni:#c39be0;--ok:#6cc070;--new:#c39be0;--old:#d8b65a}}
:root[data-theme="dark"]{--bg:#161615;--fg:#ecebe6;--mut:#a3a29c;--card:#1f1f1d;--line:#34332f;--pos:#ef6b6b;--neg:#6aa8f0;--uni:#c39be0;--ok:#6cc070;--new:#c39be0;--old:#d8b65a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:1200px;margin:0 auto;padding:16px}h1{font-size:1.45rem;margin:.2em 0}h2{font-size:1.2rem;margin:1.4em 0 .4em}
h3{font-size:1rem;margin:1em 0 .3em}.mut{color:var(--mut)}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin:12px 0}
.rec{border:2px solid var(--ok)}.tag{display:inline-block;color:#fff;border-radius:4px;padding:1px 7px;font-size:.78rem;font-weight:600;background:var(--ok)}
.tag.old{background:var(--old)}.tag.new{background:var(--new)}
img{width:100%;height:auto;border-radius:8px;border:1px solid var(--line);background:#fff}
.three{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:12px}.two{display:grid;grid-template-columns:1fr 1fr;gap:10px}
@media(max-width:560px){.three{grid-template-columns:1fr}}@media(max-width:640px){.two{grid-template-columns:1fr}}
.three .card{margin:0}
table{border-collapse:collapse;width:100%;font-size:.85rem;display:block;overflow-x:auto}td,th{border-bottom:1px solid var(--line);padding:4px 6px;text-align:left;vertical-align:top}
.cmp td,.cmp th{white-space:normal;min-width:120px}.st td{white-space:nowrap}
tr.pos td{color:var(--pos)}tr.neg td{color:var(--neg)}tr.uni td{color:var(--uni)}tr.sp td{color:var(--mut)}ul{padding-left:1.2em}li{margin:.2em 0}code{font-size:.85em;word-break:break-all}
.kv td:first-child{color:var(--mut)}
"""

html = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>ST185 Bus Bar Designs</title><style>%s</style></head><body><main>' % CSS]
html.append('''<h1>ST185 glove-box combined +/&minus; bus bar &mdash; all saved versions</h1>
<p class="mut">Built in Fusion by Claude Code, 2026-10-13. Nothing is overwritten: each version has its own folder in
<code>cad\\busbar\\</code> (.f3d, STL for the printed parts and renders in git; STEP for every part and the assembly and the A3 drawing PDF kept local, gitignored with an isolation
sheet, renders) and its own Fusion document in Default Project.</p>''')

# ---- side-by-side cards
html.append('<div class="three">')
for v in VERSIONS:
    k, d, folder, pre, doc, lab = v
    fa = FACTS[k]
    ov = rep[k]["overall_mm"]
    cls = {"A": "tag old", "B": "tag old", "B_rev2": "tag old", "A_rev3": "tag", "B_rev3": "tag new"}[k]
    html.append('<div class="card%s"><span class="%s">%s</span><h3 style="margin-top:.4em">%s</h3>' % (" rec" if k == "A_rev3" else "", cls, fa["tag"], lab))
    html.append('<p class="mut" style="margin:.2em 0 .6em">%s</p>' % fa["note"])
    html.append('<img alt="%s with the cover on" src="%s"><div style="height:8px"></div>' % (lab, img(f(v, "render_iso_cover.png"), 800)))
    html.append('<img alt="%s with the cover off, showing the lug pockets" src="%s">' % (lab, img(f(v, "render_pockets.png"), 800)))
    html.append('<table class="kv"><tr><td>size</td><td><b>%.0f &times; %.0f &times; %.0f mm</b></td></tr>' % tuple(ov))
    html.append('<tr><td>studs / ports</td><td>%s</td></tr>' % cnt_txt(d))
    html.append('<tr><td>aluminium</td><td>%.0f g</td></tr><tr><td>printed ASA</td><td>%.0f g</td></tr>' % (mass(k, "Bar_") + mass(k, "LinkStrap"), mass(k, "_ASA")))
    html.append('<tr><td>folder</td><td><code>%s\\</code></td></tr><tr><td>Fusion</td><td><code>%s</code></td></tr></table></div>' % (folder, doc))
html.append('</div>')

# ---- comparison table
html.append('<h2>Side-by-side</h2><div class="card"><table class="cmp"><tr><th></th>' + "".join("<th>%s</th>" % v[5] for v in VERSIONS) + "</tr>")
cmp_rows = [
    ("Overall (incl. flanges)", lambda k, d: "%.0f &times; %.0f &times; %.0f mm" % tuple(rep[k]["overall_mm"])),
    ("Layout", lambda k, d: FACTS[k]["note"]),
    ("1/0 termination", lambda k, d: FACTS[k]["term"]),
    ("Studs / ports", lambda k, d: cnt_txt(d)),
    ("Anti-rotation lug pockets", lambda k, d: FACTS[k]["pockets"]),
    ("Bar hold-down", lambda k, d: FACTS[k]["hold"]),
    ("Universal bus", lambda k, d: FACTS[k]["uni"]),
    ("Isolation to the mounting face", lambda k, d: "%.1f mm solid ASA; %.1f mm to the M6 screws" % (rep[k]["isolation"]["min_to_mount_face"], rep[k]["isolation"]["min_to_mount_screw"])),
    ("Aluminium / printed", lambda k, d: "%.0f g / %.0f g" % (mass(k, "Bar_") + mass(k, "LinkStrap"), mass(k, "_ASA"))),
]
for (lab, fn) in cmp_rows:
    html.append("<tr><td><b>%s</b></td>%s</tr>" % (lab, "".join("<td>%s</td>" % fn(v[0], v[1]) for v in VERSIONS)))
html.append("</table></div>")

# ---- per-version detail
DETAIL = {
    "A_rev3": """<ul>
<li><b>Hold-down (Dan: 2 per bar was not enough, and some pairs were too close):</b> 7 counterbored ISO 7380 M4&times;10 screws into blind brass inserts in printed bosses under the bars.
<ul><li>+ bar: 4 screws, one in every column gap (x &minus;99.5, &minus;75.5, &minus;54, &minus;34).</li>
<li>&minus; bar: 3 screws (36.5, 61.5 and 94). The bar is 12 mm longer at its outer end to fit the third one.</li></ul></li>
<li>Everything else is as in A rev 2: lug pockets milled in the aluminium, 4 mm solid floor, same isolation (4.0 mm / 8.0 mm).</li>
<li>Close-up below with the screws hidden, showing the counterbored holes on the step line of the + bar.</li></ul>""",
    "B_rev3": """<ul>
<li><b>Hold-down:</b> 10 counterbored M4 screws.
<ul><li>+ bar: 4 (&minus;110, &minus;56, 73, 137).</li>
<li>&minus; bar: 3 (&minus;110, &minus;55, 46.5).</li>
<li>U: 3 (87, 108, 174).</li>
<li>The bars are 10 mm longer at the ends to fit the end screws. Screws in the tall port blocks are counterbored down to the stud-field level, clear of the port bores.</li></ul></li>
<li><b>Fuse-ready link:</b> the link studs moved from 50.0 to 50.8 mm pitch, which is exactly the Bussmann AMG (MEGA-type) bolt-in fuse pitch. The strap or an AMG fuse bolts onto the same M8 studs.
<ul><li>The notches are 14.8 mm deep and the U bar has a relief, so the fuse body clears. Clash-checked in Fusion: 0.46 mm clearance under the body, and the terminals touch only their own two bars.</li></ul></li>
<li>Everything else is as in B rev 2: universal bus, one link only, plugs, stow slot, 4 mm solid floor.</li></ul>""",
    "A": """<ul>
<li>Poles sit end to end: + bar on the left, &minus; bar on the right, with a 4 mm printed wall that runs up to the cover (24 mm metal gap).</li>
<li>Each pole has two rows, stepped 6 mm: front-row wires leave forward and rear-row wires leave rearward, so no wires cross.</li>
<li>Lug pockets are milled 3 mm deep into the aluminium. Each lug sits flat on bare aluminium, and the metal walls stop it turning.</li>
<li>Hold-down: 2 counterbored ISO 7380 M4&times;10 screws per bar into blind brass inserts in printed bosses under the bar.</li>
<li>+ Standard lugs everywhere, matching the harness drawings. Nothing to re-torque. Shortest of the three.</li>
<li>&minus; Wires leave on both sides, so it needs about 45 mm of free space in front and behind.</li></ul>""",
    "B": """<ul>
<li>Saved exactly as built before the rev 2 changes. The files were restored from the untouched copy, and the Fusion document <code>ST185_busbar_B</code> was put back to this version (v4, promoted to v7; all versions kept).</li>
<li>Poles sit back to back: + bar at the front (wires leave forward), &minus; bar at the back (wires leave rearward), with a barrier wall between them.</li>
<li>1/0 cables go into set-screw ports (Weidm&uuml;ller H50,0/25 ferrule, two M8 cup-point set screws in coil inserts). 4/8 AWG lugs go on M8 studs.</li>
<li>Lug pockets are in printed locator plates. Bars are clamped by plate tabs into blind inserts in printed ledges.</li></ul>""",
    "B_rev2": """<ul>
<li>B brought to the rev 2 standard: lug pockets milled into the aluminium, and 2 counterbored M4 screws per bar into blind inserts in printed bosses.</li>
<li><b>Universal bus U:</b> a separate 6061 bar next to the &minus; bar. It has its own 4 mm wall to &minus; (26 mm metal gap) and the main barrier to + (32 mm). It has 3 &times; M8 studs (Klauke 4R8 keep-out, up to 4 AWG) exiting rearward.</li>
<li><b>One</b> bolted aluminium strap (6 &times; 20, &oslash;8.5 holes at 50 mm pitch) ties U to &minus; (through notch N) or to + (through notch P), landing on M8 link studs on bare aluminium. The unused notch takes a printed plug that the cover holds down; the spare plug sits in a park socket. With U floating, the strap goes in an insulated stow slot. There is only one strap, so it can never bridge + to &minus;. The model shows it tied to &minus;.</li>
<li>The + bar keeps 2 spares (1 &times; M8 + the 1/0 port); U adds 3 studs to whichever pole it is tied to.</li>
<li>&minus; Longest of the three (325 mm) and the heaviest.</li></ul>""",
}
for v in VERSIONS[::-1]:
    k, d, folder, pre, doc, lab = v
    html.append('<h2>%s &mdash; %s</h2><div class="card%s">' % (lab, d["title"].split(" - ", 1)[-1], " rec" if k == "A_rev3" else ""))
    html.append(DETAIL[k])
    html.append('<div class="two"><img alt="%s, cover off with lug keep-outs" src="%s"><img alt="%s drawing sheet 1" src="%s"></div>'
                % (lab, img(f(v, "render_iso_open.png")), lab, pdf_img(f(v, "drawing.pdf"))))
    html.append('<p class="mut">Drawing: <code>%s\\%s_drawing.pdf</code> (A3, 1:1; sheet 2 = isolation sections)</p>' % (folder, pre))
    if os.path.exists(f(v, "holddown_holes.png")):
        html.append('<h3>Hold-down holes (screws hidden)</h3><img alt="%s close-up of the counterbored hold-down holes with the screws hidden" src="%s">' % (lab, img(f(v, "holddown_holes.png"))))
    html.append("<h3>Stud map</h3>" + table(d) + "</div>")

# ---- fuse / fusible link question
html.append('''<h2>Fuse or fusible link in place of the strap?</h2><div class="card"><ul>
<li><b>Yes: a bolt-in fuse can replace the strap</b> and makes U a <i>protected</i> section of the + bus. The best fit is the <b>Bussmann AMG</b> (MEGA-type) fuse: M8 studs on <b>2.00 in (50.8 mm) centres</b>, 100&ndash;300 A, 32 VDC, 1,000 A interrupt rating. B rev 3's link studs are set to 50.8 mm, so the strap or the fuse fits the same studs.</li>
<li><b>Size compared with the strap.</b> Strap: 70.8 &times; 20 &times; 6 mm aluminium. AMG: 68.4 mm long, copper terminals 15.4 wide &times; 1.52 thick with &oslash;8.6 holes, and a 29.2 mm-long, 9 mm-tall plastic body in the middle. So the footprint is nearly the same, but the body hangs below the terminals. That is why B rev 3 has deeper notches and a relief in the U bar.</li>
<li><b>Other flat fuses don't drop in.</b> ANL fuses use about 2.43 in (~62 mm) stud centres (distributor listings, no maker drawing found), so they would need a different stud spacing and more room. MIDI/AMI (30&ndash;150 A) uses smaller &oslash;5.5 mm holes, and I couldn't confirm its hole spacing from the datasheet, so it isn't designed in. A Toyota-style fusible link is a plug-in cartridge in its own holder (or a length of fusible wire), not a bolt-down part, so it doesn't fit here.</li>
<li><b>How to use it:</b>
<ul><li>Fuse only the U&rarr;+ position. The ground (U&rarr;&minus;) side stays a plain strap.</li>
<li>Rate the fuse to protect the thinnest wire on U. AMG starts at 100 A, which only suits heavy wire. With 8 AWG (60 A per the harness gauge rule) on a U stud, that circuit still needs its own downstream fuse.</li>
<li>Check the 1,000 A interrupt rating against the battery's short-circuit current; the trunk MEGA 300 A upstream is the main protection.</li></ul></li>
<li>Sources: Bussmann AMG catalogue pages (<a href="https://static.chipdip.ru/lib/421/DOC029421297.pdf">bolt-in fuse protection p.35</a>, <a href="https://static.chipdip.ru/lib/420/DOC029420210.pdf">AMG series p.20</a>); ANL stud centres from <a href="https://shop.boeing.com/cpd/bdi_anl225=3c">a distributor listing</a>; Bussmann AMI datasheet (<a href="https://static.chipdip.ru/lib/665/DOC011665675.pdf">chipdip copy</a>).</li>
</ul></div>''')

# ---- isolation
html.append('''<h2>Electrical isolation from the car body (all versions)</h2><div class="card"><ul>
<li>Every conductor (bars, stud heads, set screws, the link strap) sits on a <b>solid printed floor at least 4.0 mm thick</b>, with no holes through it under any conductor.</li>
<li>Bars are held down from the top into <b>blind</b> brass heat-set inserts that end inside plastic. The M6 mounting screws pass only through the plastic end flanges and never touch a conductor.</li>
<li>Measured in Fusion for each version: conductor &rarr; mounting face <b>4.0 mm solid ASA</b>; conductor &rarr; M6 screw/washer <b>8.0 mm</b> (straight line, cover off, wall in between).</li>
<li>Creepage &ge; 15 mm to the mounting face and &ge; 13 mm to the screw washer. IEC 60664-1 asks for about 1.9 mm at &le;50 V, pollution degree 3.</li></ul>
<div class="three">''')
for v in VERSIONS:
    html.append('<div><img alt="%s section through the bar hold-down" src="%s"><p class="mut">%s: hold-down section</p></div>' % (v[5], img(f(v, "section_clamp.png"), 800), v[5]))
html.append('</div></div>')

html.append('''<h2>Engineering notes (all versions)</h2><div class="card"><ul>
<li><b>Lugs</b> (Klauke R-series, tin-plated Cu): 1/0 &rarr; 6R10 (M10, b 20, l 39); 4 AWG &rarr; 4R8 (M8, b 16, l 32); 8 AWG &rarr; 2R8 (M8, b 15, l 25). Lugs are at least 4 mm apart, with no stacking.</li>
<li><b>Pole barrier:</b> a 4 mm printed wall up to the cover, with a 24&ndash;32 mm metal gap. That is a big margin for a dropped spanner or a loose lug, not just to meet the standard.</li>
<li><b>Current:</b> 6061-T6 at 250 A runs 0.3&ndash;0.7 A/mm&sup2;, a few kelvin rise inside the cover. Bolted joints dominate, so check under 5 mV drop per joint at 250 A. 6101-T6 cuts the losses by about 25%. The B rev 2 link strap is 120 mm&sup2;.</li>
<li><b>Plastic:</b> ASA, stiff to about 95 &deg;C and UV-stable. No PA-CF, because carbon fibre is partly conductive.</li>
<li><b>Aluminium to copper:</b> tin-plated lugs and ferrules; bare (not anodized), scuffed faces with anti-oxidant paste; stainless conical washers to hold clamp load.</li>
</ul></div>
<h2>Check before cutting metal</h2><div class="card"><ul>
<li>Glove-box space (with flanges): A rev 3 274 &times; 96, B rev 3 345 &times; 120 mm (older versions: A rev 2 262, B rev 1 261, B rev 2 325 mm long), plus about 45 mm wire room where wires exit.</li>
<li>Test-crimp a 6R10 on the real 1/0 cable (bore 10.0 mm), and caliper a 6R10 / 4R8 / 2R8 tongue against the 3 mm pocket depth.</li>
<li>Pocket corners: pick an end mill (6 mm or smaller) and the corner radii get added to the model.</li>
<li>Check the wire-exit openings (W&times;H, etched on each cover) against your cable insulation OD.</li>
</ul></div>
<p class="mut">Sources: Klauke "Tubular cable lugs, Cu, standard type" (R series); Weidm&uuml;ller H50,0/25 datasheet 1988780000; ISO 4017 / 4032 / 7089 / 7380, DIN 6796; IEC 60664-1;
st185-link-ecu-config ENGINE-ROOM-POWER-REDISTRIBUTION.md &sect;5.1/&sect;8.1 and the harness files. Scripts: <code>src\\</code> (<code>spec.py</code> = every dimension; <code>build_fusion.py</code>, <code>drawings.py</code>, <code>summary_html.py</code>).</p>
</main></body></html>''')

out = os.path.join(ROOT, "ST185-busbar-designs.html")
s = "".join(html)
open(out, "w", encoding="utf-8").write(s)
print(out, len(s) // 1024, "KB")
