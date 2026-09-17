import io, sys, math
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
exec(open(r"C:\projects\5sgte-intercooler-research\rpm_sensitivity.py").read().split("# ================================================================== REPORT")[0])
VE = lambda r: ve_mach(r, 50.0, 6200.0, 1.6)

print("HEADLINE VE (backpressure 1.6) - boost required, psi")
print("  whp   lb/min   6650    7200    7800")
vals = {}
for whp in [400,450,500,550,600,650]:
    lb = whp/0.82/10.0
    row = {r: boost_for_flow(lb, r, VE) for r in (6650,7200,7800)}
    vals[whp] = (lb, row)
    print("  %3d   %5.1f   %5.1f   %5.1f   %5.1f  (PR %.2f/%.2f/%.2f)"
          % (whp, lb, row[6650], row[7200], row[7800],
             pressure_ratio(row[6650]), pressure_ratio(row[7200]), pressure_ratio(row[7800])))
print()
print("EFR 7163 at 6650 rpm on the headline VE:")
ve = VE(6650); b = boost_for_pr(3.6); f,_ = flow_lbmin(6650,b,ve)
print("  VE %.3f  boost %.1f psi  flow %.1f lb/min  %.0f whp  (%.0f%% of 60 lb/min choke)"
      % (ve, b, f, f*10*0.82, f/60*100))
print()
print("Boost to hold 500 whp as redline rises (headline VE):")
for r in (6000,6650,7200,7800,8400):
    bb = boost_for_flow(500/0.82/10.0, r, VE)
    print("  %d rpm -> %.1f psi (PR %.2f)" % (r, bb, pressure_ratio(bb)))

# ------------------------------------------------- patch the HTML
P = r"C:\projects\5sgte-intercooler-research\intercooler-report.html"
h = io.open(P, encoding="utf-8").read()
n0 = len(h)

def f1(x): return "%.1f" % x

# --- 17.6 table rows: replace the three boost cells per row
old_rows = [
 ('450 whp</td><td class="num">54.9 lb/min</td><td class="num">32.4 psi</td><td class="num">30.0 psi</td><td class="num">29.3 psi</td>', 450),
 ('500 whp</td><td class="num">61.0 lb/min</td><td class="num">37.6 psi</td><td class="num">34.9 psi</td><td class="num">34.1 psi</td>', 500),
 ('550 whp</td><td class="num">67.1 lb/min</td><td class="num">42.7 psi</td><td class="num">39.7 psi</td><td class="num">38.9 psi</td>', 550),
 ('600 whp</td><td class="num">73.2 lb/min</td><td class="num">47.8 psi</td><td class="num">44.5 psi</td><td class="num">43.6 psi</td>', 600),
 ('650 whp</td><td class="num">79.3 lb/min</td><td class="num">52.9 psi</td><td class="num">49.4 psi</td><td class="num">48.4 psi</td>', 650),
]
for old, whp in old_rows:
    assert old in h, "row not found: %d" % whp
    lb, row = vals[whp]
    new = ('%d whp</td><td class="num">%.1f lb/min</td><td class="num">%s psi</td>'
           '<td class="num">%s psi</td><td class="num">%s psi</td>'
           % (whp, lb, f1(row[6650]), f1(row[7200]), f1(row[7800])))
    h = h.replace(old, new, 1)
    print("patched %d whp row" % whp)

# --- 17.6 prose: the 44.5 psi figure and the pressure ratio band
b600_72 = vals[600][1][7200]
pr600_72 = pressure_ratio(b600_72)
b600_66 = vals[600][1][6650]
pr600_78 = pressure_ratio(vals[600][1][7800])
h = h.replace(
 "600 whp is 73.2 lb/min. A 2.19 L engine at 7,200 rpm\nand VE 0.95 moves 73.2 lb/min only at a manifold pressure of about 4.4 bar absolute &mdash; 44.5 psi of boost.",
 "600 whp is %.1f lb/min. A 2.19 L engine at 7,200 rpm\nand VE 0.945 moves that only at a manifold pressure of about %.1f bar absolute &mdash; <b>%.1f psi</b> of boost."
 % (vals[600][0], (P_AMB + b600_72*PSI)/100.0, b600_72))
h = h.replace("Pressure ratio 4.4&ndash;4.7. Above every candidate's usable map.",
              "Pressure ratio %.1f&ndash;%.1f. Above every candidate's usable map (best is 4.3)."
              % (pr600_78, pressure_ratio(b600_66)))
h = h.replace("44 psi on a 1.52 rod ratio 2.19 L is a grenade with a timer.",
              "%.0f psi on a 1.52 rod ratio 2.19 L is a grenade with a timer." % b600_72)

# --- 17.4 boost-vs-rpm caption
b500 = {r: boost_for_flow(500/0.82/10.0, r, VE) for r in (6000,6650,7200)}
h = h.replace(
 "Holding 500 whp costs 43 psi at 6,000 rpm, 37.6 at 6,650 and 34.9 at 7,200 &mdash;",
 "Holding 500 whp costs %.0f psi at 6,000 rpm, %.1f at 6,650 and %.1f at 7,200 &mdash;"
 % (b500[6000], b500[6650], b500[7200]))

# --- 17.2 KPI block: the EFR 7163 at its PR ceiling, on the headline VE
ve66 = VE(6650); b66 = boost_for_pr(3.6); f66,_ = flow_lbmin(6650,b66,ve66)
h = h.replace('<div class="val">56.6 lb/min</div>', '<div class="val">%.1f lb/min</div>' % f66)
h = h.replace('<div class="note">out of a 60 lb/min choke line &mdash; 94% used</div>',
              '<div class="note">out of a 60 lb/min choke line &mdash; %.0f%% used</div>' % (f66/60*100))
h = h.replace('<div class="val">451 whp</div>', '<div class="val">%.0f whp</div>' % (f66*10*0.82))
h = h.replace('<div class="note">550 crank at 10 hp per lb/min</div>',
              '<div class="note">%.0f crank at 10 hp per lb/min</div>' % (f66*10))
h = h.replace("it is within 6% of its choke line",
              "it is within %.0f%% of its choke line" % (100-f66/60*100))
h = h.replace("550 crank hp on E85 needs about 358 lb/hr,",
              "%.0f crank hp on E85 needs about %.0f lb/hr," % (f66*10, f66*10*0.65))
h = h.replace("which is 64% duty on 1400 cc injectors",
              "which is %.0f%% duty on 1400 cc injectors" % (f66*10*0.65/4/(1400/10.5)*100))

io.open(P, "w", encoding="utf-8", newline="").write(h)
print("\nreport: %d -> %d bytes" % (n0, len(h)))
