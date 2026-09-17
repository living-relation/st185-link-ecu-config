/* Round-four verification.
   Loads the report in jsdom, checks every chart mounts, every round-four table is
   populated, both calculators compute, zero console errors, the document is
   self-contained, and the on-page numbers agree with unified_model_r4.py. */
const fs = require("fs");
const path = require("path");
const { JSDOM, VirtualConsole } = require("jsdom");

const FILE = path.join(__dirname, "intercooler-report.html");
const html = fs.readFileSync(FILE, "utf8");

let fail = 0, warn = 0;
const bad = (m) => { console.log("  FAIL  " + m); fail++; };
const ok  = (m) => console.log("  ok    " + m);
const wrn = (m) => { console.log("  warn  " + m); warn++; };
const hr  = (t) => { console.log(""); console.log("=".repeat(78)); console.log(t);
                     console.log("=".repeat(78)); };

hr("SELF-CONTAINMENT");
[
  [/<script[^>]+src=/i, "external <script src>"],
  [/<link[^>]+rel=["']?stylesheet/i, "external stylesheet"],
  [/@import\s+url/i, "css @import"],
  [/<img[^>]+src=["']https?:/i, "remote <img>"],
  [/url\(\s*["']?https?:/i, "remote css url()"],
  [/<iframe/i, "iframe"],
].forEach(([re, name]) => re.test(html) ? bad("contains " + name) : ok("no " + name));
ok(`${(html.match(/href="https?:[^"]+"/g) || []).length} outbound <a href> citations (not loaded)`);
ok(`document is ${(html.length / 1024).toFixed(0)} KB`);

hr("RENDER + RUNTIME");
const errors = [], warns = [], logs = [];
const vc = new VirtualConsole();
vc.on("error", (m) => errors.push(String(m)));
vc.on("warn",  (m) => warns.push(String(m)));
vc.on("log",   (m) => logs.push(String(m)));
vc.on("jsdomError", (e) => errors.push("jsdomError: " + (e && e.message)));

const dom = new JSDOM(html, { runScripts: "dangerously", virtualConsole: vc,
                              pretendToBeVisual: true, url: "file:///report.html" });
const { window } = dom;
const doc = window.document;

setTimeout(() => {
  const charts = [
    "ch_face","ch_vol","ch_pipe","ch_dp","ch_soak","ch_fpi",
    "tank_top","tank_ctr","tank_side","fit_plan","fit_front","duct_svg",
    "ch_ve","ch_pwr_rpm","ch_spool_pwr","ch_inertia_flow","ch_boost_rpm","ch_coretrade",
    "ch_r3_power","ch_r3_ladder","ch_r3_sens","ch_r3_ve","ch_r3_turbo","ch_r3_core",
    "ch_pulse","ch_bp",
    "ch_r4_rpm","ch_r4_map","ch_r4_dyno","ch_r4_drive","ch_r4_stack",
  ];
  let mounted = 0;
  charts.forEach((id) => {
    const el = doc.getElementById(id);
    if (!el) { bad(`#${id} - container missing from the DOM`); return; }
    const svg = el.querySelector("svg");
    if (!svg) { bad(`#${id} - no <svg> mounted`); return; }
    const n = svg.querySelectorAll("path,rect,circle,line,text,polygon").length;
    if (n < 6) { bad(`#${id} - svg has only ${n} elements`); return; }
    mounted++;
    ok(`#${id.padEnd(14)} rendered, ${String(n).padStart(4)} svg elements`);
  });
  console.log(`  -> ${mounted}/${charts.length} charts rendered`);
  if (doc.getElementById("ch_spoolpair"))
    bad("ch_spoolpair still present - the mis-paired spool chart should be deleted");
  else ok("ch_spoolpair correctly removed (the mis-pairing penalty no longer applies)");

  hr("ROUND-FOUR TABLES POPULATED");
  const wantRows = { "t-r4rpm": 9, "t-r4surge": 11, "t-r4dyno": 9, "t-r4drive": 4,
                     "t-r4duty": 3, "t-r4core": 7, "t-r4tb": 6, "t-r4cold": 4,
                     "t-r4hot": 4, "t-r4pipes": 5, "t-r4route": 4 };
  Object.entries(wantRows).forEach(([id, n]) => {
    const t = doc.getElementById(id);
    if (!t) { bad(`#${id} missing`); return; }
    const rows = t.querySelectorAll("tbody tr").length;
    if (rows < n) bad(`#${id} has ${rows} rows, expected ${n}`);
    else ok(`#${id.padEnd(12)} ${rows} rows`);
    if (/NaN|undefined|Infinity/.test(t.textContent))
      bad(`#${id} contains NaN / undefined / Infinity`);
  });

  hr("CALCULATORS");
  const txt = (e) => (e ? e.textContent.replace(/\s+/g, " ").trim() : "");
  const outCore = doc.getElementById("out_core");
  const outDp   = doc.getElementById("out_dp");
  if (!txt(outCore)) bad("core calculator produced no output");
  else ok("core calculator computed: " + txt(outCore).slice(0, 120) + " ...");
  if (!txt(outDp)) bad("pressure-drop calculator produced no output");
  else ok("dP calculator computed: " + txt(outDp).slice(0, 110) + " ...");
  const pipeRows = doc.querySelectorAll("#tb_pipe tbody tr").length;
  if (pipeRows < 3) bad(`pipe table only has ${pipeRows} rows`); else ok(`pipe table: ${pipeRows} rows`);
  if ([outCore, outDp].some((e) => /NaN|Infinity|undefined/.test(txt(e))))
    bad("calculator output contains NaN/Infinity/undefined");
  else ok("no NaN / Infinity / undefined in calculator output");

  const before = txt(outCore);
  const sl = doc.getElementById("i_boost");
  sl.value = "22"; sl.dispatchEvent(new window.Event("input", { bubbles: true }));
  if (before === txt(outCore)) bad("moving the boost slider did not change the output");
  else ok("boost slider 30 -> 22 psi recomputes the core calculator");
  sl.value = "30"; sl.dispatchEvent(new window.Event("input", { bubbles: true }));

  const sl2 = doc.getElementById("i_ct");
  const b2 = txt(outCore);
  sl2.value = "76"; sl2.dispatchEvent(new window.Event("input", { bubbles: true }));
  if (b2 === txt(outCore)) bad("core thickness slider did not change the output");
  else ok("core thickness slider 102 -> 76 mm recomputes");
  sl2.value = "102"; sl2.dispatchEvent(new window.Event("input", { bubbles: true }));

  const slR = doc.getElementById("i_rpm");
  const b3 = txt(outCore);
  slR.value = "8000"; slR.dispatchEvent(new window.Event("input", { bubbles: true }));
  if (b3 === txt(outCore)) bad("rpm slider did not change the output");
  else ok("rpm slider 7500 -> 8000 recomputes (the range in section 24 is live)");
  slR.value = "7500"; slR.dispatchEvent(new window.Event("input", { bubbles: true }));

  hr("CALCULATOR DEFAULTS");
  const want = { i_boost: "30", i_rpm: "7500", i_ve: "0.94", i_eta: "0.71",
                 i_disp: "2.19", i_cw: "610", i_ch: "305", i_ct: "102",
                 i_dh: "2.5", i_dc: "2.5", i_lh: "1.1", i_lc: "1.5" };
  Object.entries(want).forEach(([id, v]) => {
    const got = doc.getElementById(id).value;
    if (String(got) !== v) bad(`${id}: expected ${v}, got ${got}`);
    else ok(`${id.padEnd(9)} = ${v}`);
  });

  hr("CROSS-CHECK: page vs unified_model_r4.py");
  const R4 = window.R4;
  if (!R4) { bad("R4 data block did not load"); }
  else {
    const py = JSON.parse(fs.readFileSync(path.join(__dirname, "data", "unified_model_r4.json"), "utf8"));
    const cmp = (label, a, b, tol) => {
      if (!Number.isFinite(a) || !Number.isFinite(b)) {
        bad(`${label.padEnd(30)} NOT A NUMBER  page ${a}   python ${b}`);
        return;
      }
      const d = Math.abs(a - b);
      const s = `${label.padEnd(30)} page ${String(a).padStart(9)}   python ${String(b).padStart(9)}   diff ${d.toFixed(3)}`;
      if (d > tol) bad(s + `  (> ${tol})`); else ok(s);
    };
    cmp("hero whp",            R4.hero.whp,        py.hero.whp,        0.001);
    cmp("hero lb/min",         R4.hero.lb,         py.hero.lb,         0.001);
    cmp("hero charge temp C",  R4.hero.iat,        py.hero.iat,        0.001);
    cmp("hero pressure ratio", R4.hero.pr,         py.hero.pr,         0.001);
    cmp("throttle body bore",  R4.tb.bore,         74.5,               0.001);
    cmp("throttle body Mach",  R4.tb.mach,         py.tb.mach,         0.001);
    cmp("throttle body dP psi",R4.tb.dp_psi,       py.tb.dp_psi,       0.0001);
    cmp("both steps, psi",     R4.tb.step_psi,     py.tb.step_psi,     0.0001);
    cmp("total dP budget psi", R4.budget.total,    py.budget.total,    0.001);
    cmp("system volume L",     R4.budget.sysL,     py.budget.sysL,     0.001);
    cmp("official eta fit RMS",R4.etaRms,          py.eta_rms,         0.0001);
    cmp("radiator penalty C",  R4.radPenalty.d_rad_in, py.rad_penalty.d_rad_in, 0.001);

    // internal consistency of the numbers the prose quotes
    const r7000 = R4.rpmRange.find((r) => r.rpm === 7000);
    const r7200 = R4.rpmRange.find((r) => r.rpm === 7200);
    const r7500 = R4.rpmRange.find((r) => r.rpm === 7500);
    const r8000 = R4.rpmRange.find((r) => r.rpm === 8000);
    cmp("prose: 7000->7200 = 8 whp",  r7200.whp_mid - r7000.whp_mid, 8, 0.5);
    cmp("prose: 7200->7500 = 3 whp",  r7500.whp_mid - r7200.whp_mid, 3, 0.5);
    cmp("prose: 7500->8000 = 4 whp",  r8000.whp_mid - r7500.whp_mid, 4, 0.5);
    cmp("prose: whole band = 15 whp", r8000.whp_mid - r7000.whp_mid, 15, 0.5);
    cmp("prose: band at 7500 = 401",  r7500.whp_lo, 401, 0.5);
    cmp("prose: band at 7500 = 427",  r7500.whp_hi, 427, 0.5);
    cmp("prose: band at 7000 = 390",  r7000.whp_lo, 390, 0.5);
    cmp("prose: band at 7000 = 415",  r7000.whp_hi, 415, 0.5);
    cmp("prose: driveline band = 26",
        R4.driveline.band[3].whp - R4.driveline.band[0].whp, 26, 0.5);

    // core comparison quoted in section 28
    const c76  = R4.cores.find((c) => c.k === "610x305x76");
    const c102 = R4.cores.find((c) => c.k === "610x305x102");
    const c114 = R4.cores.find((c) => c.k === "610x305x114");
    cmp("prose: 76->102 charge -9.2 C", +(c76.iat - c102.iat).toFixed(1), 9.2, 0.15);
    cmp("prose: 76->102 rad +7.2 C",  +(c102.t_rad_in - c76.t_rad_in).toFixed(1), 7.2, 0.15);
    cmp("prose: 102->114 charge 3.0 C", +(c102.iat - c114.iat).toFixed(1), 3.0, 0.15);
    cmp("prose: 102->114 rad 3.0 C",  +(c114.t_rad_in - c102.t_rad_in).toFixed(1), 3.0, 0.15);
    cmp("prose: 76mm core whp 404",   c76.whp,  404, 0.5);
    cmp("prose: 102mm core whp 411",  c102.whp, 411, 0.5);

    // surge finding
    const surgeBad = R4.surgeSweep.filter((r) => r.margin < 0).map((r) => r.rpm);
    if (surgeBad.length && Math.max(...surgeBad) === 2500)
      ok(`surge finding: inside surge at ${surgeBad.join(", ")} rpm, marginal at 2750`);
    else bad("surge sweep does not reproduce the 2,750 rpm crossover quoted in 25.4");

    // pipe recommendation - 2.5 in both sides, welded cone to the bought 3 in adapter
    const byLab = {};
    R4.coldLayouts.forEach((r) => { byLab[r.lab.slice(0, 4)] = r; });
    const c25 = byLab["2.50"], c30 = byLab["3.00"], c275 = byLab["2.75"], c225 = byLab["2.25"];
    cmp("prose: 2.5in cold dP 0.591",  c25.dp,  0.591, 0.002);
    cmp("prose: 3.0in cold dP 0.247",  c30.dp,  0.247, 0.002);
    cmp("prose: 2.5 vs 3.0 dP = 0.34", +(c25.dp - c30.dp).toFixed(3), 0.344, 0.004);
    cmp("prose: 2.5 vs 3.0 fill 25 ms", c30.fill_ms - c25.fill_ms, 25, 1);
    cmp("prose: 2.5 vs 3.0 volume 1.79 L", +(c30.sysL - c25.sysL).toFixed(2), 1.79, 0.02);
    cmp("prose: 2.5in system 14.0 L",  c25.sysL, 14.01, 0.02);
    cmp("prose: 2.5in system 6.4x",    c25.sysX, 6.40, 0.02);
    cmp("prose: 2.5in fill 191 ms",    c25.fill_ms, 191, 1);
    cmp("prose: 2.25in is 181 ft/s",   c225.vmax, 181, 1);
    cmp("prose: 2.75in dP 0.376",      c275.dp, 0.376, 0.002);
    cmp("prose: welded cone 0.035 psi", R4.coldTransitions.cone, 0.0352, 0.001);
    cmp("prose: sudden step 0.044 psi", R4.coldTransitions.sudden, 0.0443, 0.001);
    // routing envelope
    const rt = {}; R4.routing.forEach((r) => { rt[r.od.toFixed(2)] = r; });
    cmp("prose: 2.5in real ID 60.2 mm", rt["2.50"].id_mm, 60.2, 0.1);
    cmp("prose: 2.75in real ID 66.5 mm", rt["2.75"].id_mm, 66.5, 0.1);
    cmp("prose: 3.0in real ID 72.9 mm", rt["3.00"].id_mm, 72.9, 0.1);
    cmp("prose: 2.5in bend box 127 mm", rt["2.50"].box, 127, 0.5);
    cmp("prose: 3.0in bend box 152 mm", rt["3.00"].box, 152, 0.5);
    cmp("prose: 25 mm more corner room", R4.routingDeltaBox, 25, 0.5);
    cmp("prose: clamped joint adds 18 mm",
        +(rt["2.50"].clamped - rt["2.50"].bare).toFixed(1), 18.0, 0.1);
    // the dP penalty, in the units the prose quotes
    cmp("prose: 2.5in build dP 1.757",  R4.budget.total, 1.757, 0.002);
    cmp("prose: dP costs 1.3 C at compressor", R4.budget.vs3in.dtc, 1.34, 0.05);
    cmp("prose: dP costs 0.28 C at valve",     R4.budget.vs3in.diat, 0.28, 0.02);
    cmp("prose: dP costs 0.1 whp",             R4.budget.vs3in.dwhp, 0.10, 0.02);
    const hot25 = R4.hotLayouts.find((r) => r.od === 2.5);
    cmp("prose: hot 2.5in = 201 ft/s", hot25.fts, 201, 0.5);
    if (hot25.band === "in band") ok("hot 2.5 in is the only option inside Garrett's 200-300 ft/s band");
    else bad("hot 2.5 in is not reported as in band");
    const inBand = R4.hotLayouts.filter((r) => r.band === "in band").length;
    if (inBand === 2) ok("two hot-side options are in band, which is what the prose now says");
    else bad(`${inBand} hot-side options in band, prose says two`);

    // duty cycle
    cmp("prose: WOT loses 56% of radiator", R4.duty[0].lost_pct, 55.8, 0.3);
    cmp("prose: recovery loses 9%",         R4.duty[1].lost_pct,  9.2, 0.3);
  }

  hr("ROUND-FOUR CONTENT PRESENT");
  [["r4","23 round four"],["rpmrange","24 rev range"],["officialmap","25 official map"],
   ["dynocheck","26 dyno check"],["driveline","27 drivetrain"],["packaging","28 packaging"],
   ["audit","29 file audit"],["sources","30 sources"],["open","31 open questions"],
   ["recon","21 reconciliation"],["manifold","22 manifold"],["pipes","10 charge pipes"],
   ["fitment","13 fitment"]].forEach(([id, n]) => {
    doc.getElementById(id) ? ok("section " + n + " present") : bad("section " + n + " MISSING");
  });

  hr("WITHDRAWN CLAIMS ARE GONE");
  const manSec = doc.getElementById("manifold");
  const manH2 = manSec.querySelector("h2").textContent;
  if (/paired correctly/i.test(manH2)) ok("section 22 heading: '" + manH2.trim() + "'");
  else bad("section 22 heading still asserts a fault: " + manH2.trim());
  const recHeads = Array.from(manSec.querySelectorAll(".rec h3")).map((e) => e.textContent.trim());
  if (recHeads.some((t) => /^Re-make the manifold/i.test(t)))
    bad("section 22 still carries a 'Re-make the manifold' recommendation block");
  else ok("no 're-make the manifold' recommendation block: " + JSON.stringify(recHeads));
  const man = manSec.textContent;
  [[/withdrawn/i, "an explicit withdrawal of the round-three claim"],
   [/1\+4\s*\/\s*2\+3/, "the correct pairing stated"],
   [/96&?deg|96\u00b0|96 deg/i, "the 96 degree clear gap"]]
   .forEach(([re, n]) => re.test(man) ? ok("section 22 contains " + n)
                                      : bad("section 22 is missing " + n));
  const sum = doc.getElementById("summary").textContent;
  if (/costs roughly 7 whp and 400 rpm of spool/i.test(sum))
    bad("summary still states the 7 whp / 400 rpm spool penalty");
  else ok("summary no longer states the manifold penalty");
  const p = doc.getElementById("pipes").textContent;
  [[/2\.5 in, with a welded cone to 3\.0 in at the throttle/i, "the 2.5 in cold recommendation"],
   [/Hot side: 2\.5 in/i, "the 2.5 in hot recommendation"],
   [/routing clearance/i, "routing treated as a constraint"],
   [/0\.065/, "the real 0.065 in wall thickness"],
   [/Weld 2\.5 in ports/i, "the intercooler port recommendation"]]
   .forEach(([re, n]) => re.test(p) ? ok("section 10 states " + n)
                                    : bad("section 10 is missing " + n));
  if (/fixed by the bought 3 in throttle adapter/i.test(doc.body.textContent))
    bad("the withdrawn '3 in cold side is fixed' claim is still in the document");
  else ok("the withdrawn '3 in cold side is fixed' claim is gone");
  if (/74 mm throttle body/i.test(doc.body.textContent) && !/74\.5/.test(p))
    bad("throttle bore not updated to 74.5 mm");
  else ok("throttle bore stated as 74.5 mm");

  hr("ESTIMATE LABELLING");
  const body = doc.body.textContent;
  [/never been (run )?on a dynamometer|no dyno/i, /estimate/i]
    .forEach((re, i) => re.test(body) ? ok("report labels its power figures as estimates (" + (i + 1) + ")")
                                      : bad("missing estimate labelling " + (i + 1)));
  const opens = doc.querySelectorAll("#open li").length;
  ok(`open-questions list: ${opens} items`);

  hr("CONSOLE");
  const realErrors = errors.filter((e) => !/Could not parse CSS|Error: Not implemented/i.test(e));
  if (realErrors.length) realErrors.forEach((e) => bad("console.error: " + e.slice(0, 220)));
  else ok("zero console errors");
  const cssNoise = errors.length - realErrors.length;
  if (cssNoise) console.log(`  note  ${cssNoise} jsdom CSS-parser messages suppressed (jsdom limitation)`);
  logs.forEach((l) => console.log("  log   " + l));

  console.log("");
  console.log("=".repeat(78));
  console.log(fail === 0 ? `PASS - 0 failures, ${warn} warnings` : `FAIL - ${fail} failures, ${warn} warnings`);
  console.log("=".repeat(78));
  process.exit(fail === 0 ? 0 : 1);
}, 3000);
