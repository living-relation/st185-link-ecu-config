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
                  'tank_top','tank_ctr','tank_side','fit_plan','fit_front'];
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

  finish();
}, 900);

function finish() {
  console.log('\n=================================');
  if (errs.length === 0) console.log('ALL CHECKS PASSED');
  else { console.log('FAILURES (' + errs.length + '):'); errs.forEach(e => console.log('  - ' + e)); }
  console.log('=================================');
}
