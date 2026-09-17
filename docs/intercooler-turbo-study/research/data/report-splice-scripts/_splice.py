import io, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\projects\5sgte-intercooler-research\intercooler-report.html"
h = io.open(P, encoding="utf-8").read()
orig_len = len(h)

new_html = io.open(r"C:\projects\5sgte-intercooler-research\_new_sections.html", encoding="utf-8").read()
new_js   = io.open(r"C:\projects\5sgte-intercooler-research\_new_js.js",         encoding="utf-8").read()
chartdat = io.open(r"C:\projects\5sgte-intercooler-research\data\chartdata.js",  encoding="utf-8").read()

# ---------------------------------------------------------------- 1. renumber 16 -> 20, 17 -> 21
assert h.count('<span class="num">16</span>') == 1
assert h.count('<span class="num">17</span>') == 1
h = h.replace('<span class="num">16</span>', '<span class="num">20</span>')
h = h.replace('<span class="num">17</span>', '<span class="num">21</span>')
# section-17 cross references in the body text
h = h.replace('listed in &sect;17', 'listed in &sect;21')
h = h.replace('&sect;17 ', '&sect;21 ')

# ---------------------------------------------------------------- 2. insert new sections before <!-- ============ 16
marker = '<!-- ============ 16 SOURCES'
i = h.find(marker)
if i < 0:
    i = h.find('<section id="sources">')
    assert i > 0, "cannot find sources section"
h = h[:i] + new_html + "\n\n" + h[i:]

# ---------------------------------------------------------------- 3. TOC
old_toc = '<a href="#sources">Sources</a><a href="#open">Open Questions</a>'
assert old_toc in h, "TOC anchor block not found"
new_toc = ('<a href="#round2">Round Two</a><a href="#turbo">Turbo &amp; Redline</a>'
           '<a href="#tanks2">Tank Manufacture</a><a href="#ots">Off-the-shelf</a>\n'
           + old_toc)
h = h.replace(old_toc, new_toc, 1)

# ---------------------------------------------------------------- 4. banner in the executive summary
anchor = '<section id="summary">\n<h2><span class="num">01</span>Executive summary</h2>'
assert anchor in h, "summary anchor not found"
banner = anchor + '''
<div class="callout c-bad" style="margin-top:14px"><b>Round two, August 2026 &mdash; read &sect;16 first.</b>
Three findings below have been superseded.
<b>(1)</b> You were told raising the rev limit would not help. That is true only for the EFR 7163 you own;
on any larger compressor 6,650 &rarr; 7,200 rpm is worth about +28 whp. <a href="#turbo">&sect;17</a>
<b>(2)</b> The design point moves from 25 psi to 30 psi, so the predicted intercooler outlet moves from
about 55 &deg;C to about 76 &deg;C. <a href="#ots">&sect;19</a>
<b>(3)</b> The end tank recommendation changes from "fabricate" to "buy the assembled SpeedFactory SS-850",
and machining billet tanks at work is a <b>no-go</b>. <a href="#tanks2">&sect;18</a></div>'''
h = h.replace(anchor, banner, 1)

# ---------------------------------------------------------------- 5. inject JS before </script>
k = h.rfind('</script>')
assert k > 0
inject = "\n\n/* ==== round-two data ==== */\n" + chartdat + "\n" + new_js + "\n"
h = h[:k] + inject + h[k:]

# ---------------------------------------------------------------- 6. call initRound2 on load
cands = ['window.addEventListener("load"', 'window.onload', 'document.addEventListener("DOMContentLoaded"']
hooked = False
for c in cands:
    if c in h:
        print("found existing load hook:", c)
        hooked = True
        break
h = h[:h.rfind('</script>')] + "\ntry{initRound2();}catch(e){if(window.console)console.error(e);}\n" + h[h.rfind('</script>'):]

io.open(P, "w", encoding="utf-8", newline="").write(h)
print("report: %d -> %d bytes (+%d)" % (orig_len, len(h), len(h)-orig_len))
for s in ["round2","turbo","tanks2","ots","sources","open"]:
    print("  section #%-8s present: %s" % (s, ('id="%s"' % s) in h))
for c in ["ch_ve","ch_pwr_rpm","ch_spool_pwr","ch_inertia_flow","ch_boost_rpm","ch_coretrade"]:
    print("  chart  %-16s div:%s  fn:%s" % (c, ('id="%s"'%c) in h, ('mount("%s"'%c) in h))
