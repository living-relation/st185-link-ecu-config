import io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\projects\5sgte-intercooler-research\intercooler-report.html"
h = io.open(P, encoding="utf-8").read(); n0=len(h)

# --- reconcile the two halves of the report -------------------------------
anchor = '<h3 id="t177">17.7 &nbsp;Spool, inertia, and the driveability question</h3>'
assert anchor in h
NOTE = '''<div class="callout c-warn"><b>Where &sect;17 and &sect;19 have to be read together.</b>
The turbo model above assumes a 50&nbsp;&deg;C charge temperature at the intake valve. The intercooler
model in &sect;19 says the real figure at this design point is about <b>76&nbsp;&deg;C</b>. Hotter air is
less dense, so the engine swallows less mass at the same boost:
<div class="eq">at 30 psi and 7,200 rpm, charge at 50 &deg;C   &rarr;  53.5 lb/min  &rarr;  439 whp
at 30 psi and 7,200 rpm, charge at 76 &deg;C   &rarr;  50.2 lb/min  &rarr;  412 whp   <span class="cm">a 6% loss</span></div>
<b>Every power figure in &sect;17 is therefore about 6&ndash;7% optimistic</b> unless the intercooler
actually holds 50&nbsp;&deg;C, which it will not at 30 psi. The numbers in &sect;19 are the ones to build
against. This also means the intercooler is worth roughly 27&nbsp;whp on its own at this design point,
and the ducting is most of that.</div>

''' + anchor
h = h.replace(anchor, NOTE, 1)

# --- the 450 whp verdict cell now reads oddly given 33.9 psi at 6650 -------
h = h.replace(
 '<span class="pill p-ok">Yes</span> Street and track. This is the number to build for.',
 '<span class="pill p-ok">Yes</span> Street and track at 7,200 rpm. This is the number to build for. '
 'Note it needs 31 psi, not 25.')

io.open(P,"w",encoding="utf-8",newline="").write(h)
print("report: %d -> %d" % (n0, len(h)))
