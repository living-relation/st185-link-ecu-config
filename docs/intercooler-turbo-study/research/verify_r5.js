/* Round-five verification.
   Loads the report in jsdom and checks: self-contained, zero console errors,
   every chart mounts an <svg>, both calculators compute and react to input,
   the tabs work, and no anchor points at a section that no longer exists. */
const fs = require("fs");
const path = require("path");
const { JSDOM, VirtualConsole } = require("jsdom");

const FILE = path.join(__dirname, "intercooler-report.html");
const html = fs.readFileSync(FILE, "utf8");

let fail = 0, warn = 0;
const bad = (m) => { console.log("  FAIL  " + m); fail++; };
const ok  = (m) => console.log("  ok    " + m);
const wrn = (m) => { console.log("  warn  " + m); warn++; };
const hr  = (t) => { console.log(""); console.log("=".repeat(74)); console.log(t);
                     console.log("=".repeat(74)); };

hr("SELF-CONTAINMENT");
[
  [/<script[^>]+src=/i, "external <script src>"],
  [/<link[^>]+rel=["']?stylesheet/i, "external stylesheet"],
  [/@import\s+url/i, "css @import"],
  [/<img[^>]+src=["']https?:/i, "remote <img>"],
  [/url\(\s*["']?https?:/i, "remote css url()"],
  [/<iframe/i, "iframe"],
].forEach(([re, name]) => re.test(html) ? bad("contains " + name) : ok("no " + name));
ok(`${(html.match(/href="https?:[^"]+"/g) || []).length} outbound citation links (never fetched)`);
ok(`document is ${(html.length / 1024).toFixed(0)} KB`);

hr("CONSOLE");
const vc = new VirtualConsole();
const errors = [], logs = [];
vc.on("jsdomError", (e) => errors.push("jsdomError: " + (e.stack || e.message)));
vc.on("error", (...a) => errors.push("console.error: " + a.join(" ")));
vc.on("warn",  (...a) => wrn("console.warn: " + a.join(" ")));
vc.on("log",   (...a) => logs.push(a.join(" ")));

const dom = new JSDOM(html, { runScripts: "dangerously", virtualConsole: vc,
                              pretendToBeVisual: true });
const doc = dom.window.document;

/* the report defers its init to DOMContentLoaded, so wait for the document to
   finish loading before inspecting anything it drew */
main();
async function main() {
await new Promise((r) => {
  if (doc.readyState === "complete") return r();
  dom.window.addEventListener("load", r);
  setTimeout(r, 5000);
});
await new Promise((r) => setTimeout(r, 50));

if (errors.length) errors.forEach(bad); else ok("zero console errors");
logs.forEach((l) => ok("log: " + l));

hr("CHARTS");
const mounts = [...html.matchAll(/mount\("([^"]+)"/g)].map((m) => m[1]);
const extra  = ["tank_top", "tank_ctr", "tank_side"];
[...new Set(mounts.concat(extra))].sort().forEach((id) => {
  const el = doc.getElementById(id);
  if (!el) return bad(`#${id} — container missing from the document`);
  const svg = el.querySelector("svg");
  if (!svg) return bad(`#${id} — no <svg> rendered`);
  const kids = svg.querySelectorAll("*").length;
  if (kids < 8) return bad(`#${id} — svg has only ${kids} elements`);
  ok(`#${id} — svg with ${kids} elements`);
});

hr("CALCULATORS");
const outCore = doc.getElementById("out_core");
const outDp   = doc.getElementById("out_dp");
const pipeTb  = doc.querySelector("#tb_pipe tbody");
outCore && outCore.textContent.trim().length > 80
  ? ok(`core calculator populated (${outCore.querySelectorAll(".calcrow").length} rows)`)
  : bad("core calculator empty");
outDp && outDp.textContent.trim().length > 40
  ? ok(`ΔP calculator populated (${outDp.querySelectorAll(".calcrow").length} rows)`)
  : bad("ΔP calculator empty");
pipeTb && pipeTb.rows.length >= 5
  ? ok(`pipe velocity table populated (${pipeTb.rows.length} rows)`)
  : bad("pipe velocity table empty");

function iatOf() {
  const r = [...outCore.querySelectorAll(".calcrow")]
    .find((x) => /Intercooler outlet IAT/.test(x.textContent));
  return r ? parseFloat(r.querySelector(".v").textContent) : NaN;
}
const before = iatOf();
const boost = doc.getElementById("i_boost");
boost.value = "36";
boost.dispatchEvent(new dom.window.Event("input", { bubbles: true }));
const after = iatOf();
Number.isFinite(before) && Number.isFinite(after) && Math.abs(after - before) > 1
  ? ok(`core calculator reacts to input (IAT ${before.toFixed(1)} → ${after.toFixed(1)} °C at 36 psi)`)
  : bad(`core calculator did not react (${before} → ${after})`);
boost.value = "30";
boost.dispatchEvent(new dom.window.Event("input", { bubbles: true }));

const dpBefore = outDp.textContent;
const dh = doc.getElementById("i_dh");
dh.value = "3.5";
dh.dispatchEvent(new dom.window.Event("input", { bubbles: true }));
outDp.textContent !== dpBefore ? ok("ΔP calculator reacts to input")
                               : bad("ΔP calculator did not react");
dh.value = "2.5";
dh.dispatchEvent(new dom.window.Event("input", { bubbles: true }));

hr("TABS");
const btns = [...doc.querySelectorAll(".tabbar button")];
ok(`${btns.length} tab buttons`);
btns[2].dispatchEvent(new dom.window.Event("click", { bubbles: true }));
doc.getElementById("t-dp").classList.contains("on") &&
  !doc.getElementById("t-core").classList.contains("on")
  ? ok("tab switching works") : bad("tab switching broken");
btns[0].dispatchEvent(new dom.window.Event("click", { bubbles: true }));

hr("STRUCTURE AND DEAD REFERENCES");
const ids   = [...doc.querySelectorAll("section[id]")].map((s) => s.id);
const navs  = [...doc.querySelectorAll("nav.toc a")].map((a) => a.getAttribute("href").slice(1));
const anchors = [...doc.querySelectorAll('a[href^="#"]')].map((a) => a.getAttribute("href").slice(1));
ok(`${ids.length} sections`);
const orphan = anchors.filter((h) => !ids.includes(h) && !doc.getElementById(h));
orphan.length ? bad("anchors with no target: " + orphan.join(", ")) : ok("no dead anchors");
const uncovered = ids.filter((i) => !navs.includes(i));
uncovered.length ? bad("sections missing from nav: " + uncovered.join(", "))
                 : ok("every section is in the nav");
const navOrder = navs.join(",") === ids.join(",");
navOrder ? ok("nav order matches document order") : bad("nav order does not match document order");

// section numbers must run 01..N in order
const nums = [...doc.querySelectorAll("h2 .num")].map((n) => n.textContent.trim());
const want = ids.map((_, i) => String(i + 1).padStart(2, "0"));
nums.join(",") === want.join(",") ? ok(`section numbers run ${nums[0]}–${nums[nums.length - 1]} in order`)
                                  : bad("section numbering is wrong: " + nums.join(","));

// every §NN reference must resolve to a real section
const bodyText = doc.body.innerHTML;
const refs = [...bodyText.matchAll(/&sect;(\d+)|§(\d+)/g)].map((m) => parseInt(m[1] || m[2], 10));
const badRefs = [...new Set(refs)].filter((n) => n < 1 || n > ids.length);
badRefs.length ? bad("§ references outside 1–" + ids.length + ": " + badRefs.join(", "))
               : ok(`${refs.length} § cross-references, all inside 1–${ids.length}`);

hr("WITHDRAWN CONTENT MUST BE GONE");
/* the rejected section names each dropped item on purpose, so it is excluded */
const live = [...doc.querySelectorAll("section")]
  .filter((s) => s.id !== "rejected").map((s) => s.innerHTML).join("\n");
[
  [/24\s*Pa/i,                             "the 24 Pa joint-step figure"],
  [/concentricity/i,                       "coupler concentricity note"],
  [/SpeedFactory|SS-850/i,                 "SpeedFactory SS-850 as a constraint"],
  [/taper cone angle/i,                    "taper cone angle optimisation"],
  [/1\.7\s*mm step/i,                      "the 1.7 mm step analysis"],
  [/welded cone to 3\.0/i,                 "the welded 2.5-to-3.0 cold-side cone"],
  [/coupler outside diameter/i,            "coupler OD as a packaging argument"],
].forEach(([re, name]) => re.test(live) ? bad("still live outside §17: " + name)
                                        : ok("removed from the live text: " + name));

// the Garrett survey may only appear inside the "considered and rejected" section
const rej = doc.getElementById("rejected");
const g25 = [...doc.querySelectorAll("section")].filter((s) => /G25-770/.test(s.innerHTML))
  .map((s) => s.id);
g25.every((id) => id === "rejected")
  ? ok("G25-770 appears only in the rejected section" + (g25.length ? "" : " (absent)"))
  : bad("G25-770 appears in: " + g25.join(", "));
/no turbo change is recommended/i.test(html)
  ? ok("report states plainly that no turbo change is recommended")
  : bad("missing the explicit 'no turbo change' statement");

hr(fail ? `RESULT: ${fail} FAILURE(S), ${warn} warning(s)`
        : `RESULT: PASS — 0 failures, ${warn} warning(s)`);
process.exit(fail ? 1 : 0);
}
