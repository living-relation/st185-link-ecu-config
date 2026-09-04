// Verify the report: parse HTML, run its JS in jsdom, check charts render & calcs are right.
const fs = require('fs');
const path = 'C:\\projects\\5sgte-intercooler-research\\intercooler-report.html';
const html = fs.readFileSync(path, 'utf8');

// --- structural checks ---
const errs = [], warns = [];
function count(re) { return (html.match(re) || []).length; }
const openDiv = count(/<div\b/g), closeDiv = count(/<\/div>/g);
const openSec = count(/<section\b/g), closeSec = count(/<\/section>/g);
const openTab = count(/<table\b/g), closeTab = count(/<\/table>/g);
const openTr = count(/<tr\b/g), closeTr = count(/<\/tr>/g);
console.log('div  open/close:', openDiv, closeDiv, openDiv === closeDiv ? 'OK' : 'MISMATCH');
console.log('sect open/close:', openSec, closeSec, openSec === closeSec ? 'OK' : 'MISMATCH');
console.log('table open/close:', openTab, closeTab, openTab === closeTab ? 'OK' : 'MISMATCH');
console.log('tr   open/close:', openTr, closeTr, openTr === closeTr ? 'OK' : 'MISMATCH');
if (openDiv !== closeDiv) errs.push('div mismatch');
if (openSec !== closeSec) errs.push('section mismatch');
if (openTab !== closeTab) errs.push('table mismatch');

// no external resources
const ext = html.match(/(src|href)\s*=\s*"(https?:)?\/\//g) || [];
const extLinks = html.match(/<(script|link)[^>]*(src|href)\s*=\s*"[^"]*"/g) || [];
console.log('external <script>/<link> tags:', extLinks.length, extLinks.length === 0 ? 'OK (self-contained)' : extLinks);
if (extLinks.length) errs.push('external resource dependency');

// all nav anchors resolve
const anchors = [...html.matchAll(/href="#([a-z0-9\-]+)"/g)].map(m => m[1]);
const ids = new Set([...html.matchAll(/id="([a-zA-Z0-9_\-]+)"/g)].map(m => m[1]));
const dead = anchors.filter(a => !ids.has(a));
console.log('nav anchors:', anchors.length, 'dead:', dead.length ? dead : 'none');
if (dead.length) errs.push('dead anchors: ' + dead.join(','));

// JS syntax check
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
console.log('inline <script> blocks:', scripts.length);
scripts.forEach((s, i) => {
  try { new Function(s); console.log('  script[' + i + '] syntax OK (' + s.length + ' chars)'); }
  catch (e) { console.log('  script[' + i + '] SYNTAX ERROR: ' + e.message); errs.push('js syntax: ' + e.message); }
});

// --- run in jsdom ---
let JSDOM;
try { ({ JSDOM } = require('jsdom')); } catch (e) {
  console.log('\njsdom not installed; skipping runtime test');
  finish(); process.exit(0);
}
const logs = [], jserr = [];
const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  virtualConsole: new (require('jsdom').VirtualConsole)()
    .on('log', m => logs.push(String(m)))
    .on('error', m => jserr.push(String(m)))
    .on('jsdomError', m => jserr.push(String(m && m.message || m)))
});
setTimeout(() => {
  const d = dom.window.document;
  console.log('\n--- runtime ---');
  console.log('console.log output:', logs.length ? logs : '(none)');
  if (jserr.length) { console.log('CONSOLE ERRORS:', jserr); errs.push('runtime errors'); }
  else console.log('console errors: NONE  OK');

  const charts = ['ch_face','ch_vol','ch_pipe','ch_dp','ch_soak','ch_fpi','duct_svg',
                  'tank_top','tank_ctr','tank_side','fit_plan','fit_front',
                  // round two
                  'ch_ve','ch_pwr_rpm','ch_spool_pwr','ch_inertia_flow',
                  'ch_boost_rpm','ch_coretrade'];
  let bad = 0;
  charts.forEach(id => {
    const c = d.getElementById(id);
    const svgs = c ? c.querySelectorAll('svg').length : 0;
    const kids = c && c.firstChild ? c.firstChild.querySelectorAll('*').length : 0;
    const ok = svgs === 1 && kids > 5;
    if (!ok) { bad++; errs.push('chart empty: ' + id); }
    console.log('  ' + (ok ? 'OK  ' : 'FAIL') + '  #' + id + '  svg=' + svgs + ' nodes=' + kids);
  });

  // calculator outputs populated
  ['out_core','out_dp'].forEach(id => {
    const e = d.getElementById(id);
    const n = e ? e.innerHTML.length : 0;
    console.log('  ' + (n > 200 ? 'OK  ' : 'FAIL') + '  #' + id + ' -> ' + n + ' chars');
    if (n <= 200) errs.push('calc empty: ' + id);
  });
  const rows = d.querySelectorAll('#tb_pipe tbody tr').length;
  console.log('  ' + (rows === 6 ? 'OK  ' : 'FAIL') + '  #tb_pipe rows = ' + rows);
  if (rows !== 6) errs.push('pipe table rows=' + rows);

  // --- numeric verification against the Python model ---
  console.log('\n--- numeric cross-check vs Python model ---');
  const S = dom.window.S;
  const expect = [
    ['mass flow lb/min', S.lbmin, 44.7, 1.5],
    ['pressure ratio',   S.pr,     2.92, 0.03],
    ['compressor out C', S.tc,     180,  3],
    ['effectiveness',    S.eps,    0.855,0.03],
    ['outlet IAT C',     S.iat,    53.5, 3],
    ['site pressure kPa',S.pamb,   93.9, 0.3],
    ['CFM',              S.cfm,    350,  20]
  ];
  expect.forEach(([n, got, exp, tol]) => {
    const ok = Math.abs(got - exp) <= tol;
    if (!ok) errs.push('numeric ' + n + ': got ' + got.toFixed(3) + ' expected ~' + exp);
    console.log('  ' + (ok ? 'OK  ' : 'FAIL') + '  ' + n.padEnd(20) +
      ' got ' + got.toFixed(3) + '  expected ~' + exp + ' (±' + tol + ')');
  });

  // interactive test: change boost, confirm outputs move sensibly
  console.log('\n--- interactivity test ---');
  const before = { iat: S.iat, m: S.lbmin, tc: S.tc };
  const inp = d.getElementById('i_boost');
  inp.value = 15;
  inp.dispatchEvent(new dom.window.Event('input', { bubbles: true }));
  const S2 = dom.window.S;
  const ok1 = S2.lbmin < before.m && S2.tc < before.tc && S2.iat < before.iat;
  console.log('  boost 25 -> 15 psi: mdot ' + before.m.toFixed(1) + ' -> ' + S2.lbmin.toFixed(1) +
    ', Tcomp ' + before.tc.toFixed(0) + ' -> ' + S2.tc.toFixed(0) +
    ', IAT ' + before.iat.toFixed(1) + ' -> ' + S2.iat.toFixed(1) + '  ' + (ok1 ? 'OK' : 'FAIL'));
  if (!ok1) errs.push('boost slider did not respond correctly');

  const vf = d.getElementById('i_vf');
  const iatA = dom.window.S.iat;
  vf.value = 4;
  vf.dispatchEvent(new dom.window.Event('input', { bubbles: true }));
  const ok2 = dom.window.S.iat > iatA && dom.window.S.eps < 0.8;
  console.log('  face vel 12 -> 4 m/s: IAT ' + iatA.toFixed(1) + ' -> ' + dom.window.S.iat.toFixed(1) +
    ', eps -> ' + dom.window.S.eps.toFixed(3) + '  ' + (ok2 ? 'OK' : 'FAIL'));
  if (!ok2) errs.push('face velocity slider did not respond correctly');

  // reset and check dP tab
  d.getElementById('i_boost').value = 25;
  d.getElementById('i_boost').dispatchEvent(new dom.window.Event('input', { bubbles: true }));
  d.getElementById('i_vf').value = 12;
  d.getElementById('i_vf').dispatchEvent(new dom.window.Event('input', { bubbles: true }));
  const dpTxt = d.getElementById('out_dp').textContent;
  const mtot = dpTxt.match(/TOTAL ΔP\s*([\d.]+) psi/);
  console.log('  dP budget total: ' + (mtot ? mtot[1] + ' psi' : 'NOT FOUND'));
  if (mtot) {
    const v = parseFloat(mtot[1]);
    const ok3 = v > 0.6 && v < 2.5;
    console.log('  ' + (ok3 ? 'OK  ' : 'FAIL') + '  total dP in plausible 0.6–2.5 psi band');
    if (!ok3) errs.push('dP total implausible: ' + v);
  } else errs.push('dP total not rendered');

  // ---------- ROUND TWO checks ----------
  console.log('\n--- round two: tables ---');
  [['tb_rpm', 12], ['tb_gain', 12]].forEach(([id, want]) => {
    const n = d.querySelectorAll('#' + id + ' tbody tr').length;
    const ok = n === want;
    if (!ok) errs.push(id + ' rows=' + n + ' expected ' + want);
    console.log('  ' + (ok ? 'OK  ' : 'FAIL') + '  #' + id + ' rows = ' + n);
  });
  const lg = d.getElementById('lg_pwr');
  const lgn = lg ? lg.querySelectorAll('span').length : 0;
  console.log('  ' + (lgn === 12 ? 'OK  ' : 'FAIL') + '  #lg_pwr legend entries = ' + lgn);
  if (lgn !== 12) errs.push('lg_pwr entries=' + lgn);

  console.log('\n--- round two: data block sanity vs Python ---');
  const TD = dom.window.TD;
  if (!TD) { errs.push('TD data block missing'); console.log('  FAIL  TD undefined'); }
  else {
    const g = TD.turbos.find(t => t.n.indexOf('G25-770') >= 0);
    const e7 = TD.turbos.find(t => t.n.indexOf('7163') >= 0);
    const r2 = [
      ['candidate count',        TD.turbos.length,   12,   0],
      ['site pressure kPa',      TD.pamb,            93.87, 0.05],
      ['G25-770 whp @7200',      g.r[7200].whp,      542,  2],
      ['G25-770 spool rpm',      g.spool,            4307, 0],
      ['G25-770 J with comp',    g.j2,               0.769, 0.005],
      ['G25-770 choke lb/min',   g.choke,            73,   0],
      ['EFR 7163 whp @6650',     e7.r[6650].whp,     451,  2],
      ['EFR 7163 whp @7200',     e7.r[7200].whp,     467,  2],
      ['EFR 7163 crossover rpm', e7.cross,           6925, 0],
      ['EFR 7163 boost @6650',   e7.r[6650].b,       33.9, 0.15],
      ['VE round-1 @7200',       TD.ve.r1[TD.ve.rpm.indexOf(7200)], 0.835, 0.005],
      ['VE round-2 @7200',       TD.ve.m16[TD.ve.rpm.indexOf(7200)], 0.945, 0.005],
      ['Mach index Z @7200',     TD.ve.Z[TD.ve.rpm.indexOf(7200)],  0.517, 0.005],
      ['boost for 600whp @7200', TD.boost[600].find(p => p[0] === 7200)[1], 46.3, 0.3],
      ['boost for 500whp @7200', TD.boost[500].find(p => p[0] === 7200)[1], 36.4, 0.3]
    ];
    r2.forEach(([n, got, exp, tol]) => {
      const ok = Math.abs(got - exp) <= tol;
      if (!ok) errs.push('R2 ' + n + ': got ' + got + ' expected ' + exp);
      console.log('  ' + (ok ? 'OK  ' : 'FAIL') + '  ' + n.padEnd(24) +
        ' got ' + got + '  expected ' + exp);
    });
    // internal consistency: 7163 must be choke-limited at and above its crossover
    const c1 = e7.r[7200].lim === 'choke' && e7.r[6650].lim === 'PR';
    console.log('  ' + (c1 ? 'OK  ' : 'FAIL') + '  EFR 7163 limit flips PR -> choke between 6650 and 7200');
    if (!c1) errs.push('7163 limit flag wrong');
    // gain from 6650 -> 7200 must be positive for every turbo (the headline correction)
    const neg = TD.turbos.filter(t => t.r[7200].whp <= t.r[6650].whp);
    console.log('  ' + (neg.length === 0 ? 'OK  ' : 'FAIL') +
      '  every turbo gains power from 6650 -> 7200 rpm (' + neg.length + ' exceptions)');
    if (neg.length) errs.push('turbos losing power with rpm: ' + neg.map(t => t.n).join(','));
    // 600 whp must be unreachable: required PR above every candidate's ceiling
    const maxPR = Math.max.apply(null, TD.turbos.map(t => t.pr));
    const need600 = TD.boost[600].find(p => p[0] === 7200)[1];
    const prNeed = (93.87 + need600 * 6.89476) / (93.87 * 0.97);
    const ok600 = prNeed > maxPR;
    console.log('  ' + (ok600 ? 'OK  ' : 'FAIL') + '  600 whp needs PR ' + prNeed.toFixed(2) +
      ' vs best candidate ceiling ' + maxPR.toFixed(1) + ' -> unreachable');
    if (!ok600) errs.push('600 whp claim not supported by data');
  }

  console.log('\n--- round two: prose / numbers agree ---');
  const claims = [
    ['SS-850 price',            /\$524\.68/],
    ['TR1245 price',            /\$549\.00/],
    ['G25-770 price',           /\$1,850/],
    ['+28 whp headline',        /\+28&nbsp;wheel horsepower|\+28 whp/],
    ['307 rpm spool delta',     /307 rpm/],
    ['12.1 machine-hours',      /12\.1 machine-hours/],
    ['billet no-go',            /NO-GO on machining billet/],
    ['600 whp verdict',         /600 whp is not realistic/],
    ['7200 rpm recommendation', /7,200 rpm/],
    ['76 C outlet',             /76\.1 &deg;C|76 &deg;C/]
  ];
  claims.forEach(([n, re]) => {
    const ok = re.test(html);
    if (!ok) errs.push('claim missing from prose: ' + n);
    console.log('  ' + (ok ? 'OK  ' : 'FAIL') + '  ' + n);
  });

  finish();
}, 900);

function finish() {
  console.log('\n=================================');
  if (errs.length === 0) console.log('ALL CHECKS PASSED');
  else { console.log('FAILURES (' + errs.length + '):'); errs.forEach(e => console.log('  - ' + e)); }
  console.log('=================================');
}
