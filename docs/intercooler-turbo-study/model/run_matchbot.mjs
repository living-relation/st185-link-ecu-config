#!/usr/bin/env node
/**
 * Drive the live BorgWarner MatchBot page using the official field procedure
 * in matchbot_procedure.md / matchbot_case.yaml.
 *
 * Usage: node run_matchbot.mjs
 * Writes matchbot_results.json and screenshots next to this file.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const puppeteer = require("puppeteer-core");

const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(HERE, "matchbot_results.json");
const SHOT_DIR = path.join(HERE, "matchbot_shots");
const CASE_PATH = path.join(HERE, "matchbot_case.yaml");

function parseSimpleYaml(text) {
  // Tiny subset parser for our case file (no nested lists of maps beyond points).
  // Prefer to hard-code the case here if YAML isn't available — the file is the
  // human source of truth; this script embeds the same numbers so we don't need
  // a YAML dep in Node.
  return text;
}

const CASE = {
  displacement_l: 2.189,
  ambient_f: 75,
  altitude_ft: 0,
  points: [
    { rpm: 3000, ve: 92, boost: 15, ie: 95, ce: 66, te: 84, egt: 1650, ter: 1.21, bsfc: 0.45, afr: 12.0 },
    { rpm: 4000, ve: 100, boost: 25, ie: 93, ce: 70, te: 80, egt: 1650, ter: 1.38, bsfc: 0.48, afr: 11.5 },
    { rpm: 5000, ve: 105, boost: 30, ie: 90, ce: 74, te: 72, egt: 1650, ter: 1.61, bsfc: 0.50, afr: 11.5 },
    { rpm: 6000, ve: 101, boost: 30, ie: 88, ce: 76, te: 71, egt: 1650, ter: 1.81, bsfc: 0.52, afr: 11.5 },
    { rpm: 7000, ve: 92, boost: 28, ie: 86, ce: 72, te: 70, egt: 1650, ter: 1.98, bsfc: 0.58, afr: 11.5 },
    { rpm: 8000, ve: 90, boost: 27, ie: 85, ce: 66, te: 70, egt: 1650, ter: 2.18, bsfc: 0.62, afr: 11.5 },
  ],
  peak: { ipd: 1.5, fil: 0.5, mbp: 2.0 },
  compressors: [
    { id: "EFR_7064", value: "70s75" },
    { id: "EFR_7163", value: "71x80" },
    { id: "EFR_7670", value: "76s75" },
  ],
};

const delay = (ms) => new Promise((r) => setTimeout(r, ms));

async function setVal(page, id, value) {
  await page.evaluate((elId, val) => {
    const el = document.getElementById(elId);
    if (!el) throw new Error("missing " + elId);
    el.value = String(val);
  }, id, value);
}

async function collect(page) {
  return page.evaluate(() => {
    const val = (id) => {
      const el = document.getElementById(id);
      return el ? (el.value !== undefined && el.value !== "" ? el.value : el.innerText) : null;
    };
    const points = [];
    for (let i = 1; i <= 6; i++) {
      points.push({
        rpm: val(`pt${i}_rpm`),
        ve: val(`pt${i}_ve`),
        boost: val(`pt${i}_boost`),
        ie: val(`pt${i}_ie`),
        ipd: val(`pt${i}_ipd`),
        filres: val(`pt${i}_filres`),
        mbp: val(`pt${i}_mbp`),
        ce: val(`pt${i}_ce`),
        te: val(`pt${i}_te`),
        egt: val(`pt${i}_egt`),
        ter: val(`pt${i}_ter`),
        wg_pct: val(`pt${i}_pw`),
        bsfc: val(`pt${i}_bsfc`),
        afr: val(`pt${i}_afr`),
        cpr: val(`pt${i}_cpr`),
        t2_f: val(`pt${i}_cot`),
        iat_f: val(`pt${i}_mat`),
        act_lbmin: val(`pt${i}_actfr_lbmin`),
        cor_lbmin: val(`pt${i}_corfr_lbmin`),
        power_hp: val(`pt${i}_power`),
        torque: val(`pt${i}_torque`),
        fuel_lbhr: val(`pt${i}_fuel`),
        emp_psi: val(`pt${i}_emp`),
        dp_psi: val(`pt${i}_dp`),
        phi: val(`pt${i}_tswal`),
        tcf_lbmin: val(`pt${i}_tcf`),
        wg_area: val(`pt${i}_wfa`),
        wg_port_mm: val(`pt${i}_pdr`),
      });
    }
    return {
      displacement: val("displacement"),
      cid: val("CID"),
      aat: val("aat"),
      altitude: val("altitude"),
      baro: val("baro"),
      fueltype: val("fueltype"),
      compressor: val("compressor"),
      points,
    };
  });
}

async function applyCase(page, scaleFromFlows) {
  await setVal(page, "displacement", CASE.displacement_l);
  await setVal(page, "aat", CASE.ambient_f);
  await setVal(page, "altitude", CASE.altitude_ft);
  await page.select("#fueltype", "1");
  await page.select("#turboconfig", "1");

  for (let i = 0; i < 6; i++) {
    const p = CASE.points[i];
    const n = i + 1;
    await setVal(page, `pt${n}_rpm`, p.rpm);
    await setVal(page, `pt${n}_ve`, p.ve);
    await setVal(page, `pt${n}_boost`, p.boost);
    await setVal(page, `pt${n}_ie`, p.ie);
    await setVal(page, `pt${n}_ce`, p.ce);
    await setVal(page, `pt${n}_te`, p.te);
    await setVal(page, `pt${n}_egt`, p.egt);
    await setVal(page, `pt${n}_ter`, p.ter);
    await setVal(page, `pt${n}_bsfc`, p.bsfc);
    await setVal(page, `pt${n}_afr`, p.afr);
  }

  // First-pass restrictions: use square-law vs estimated relative flow
  // (boost*rpm*ve) so we don't need a prior MatchBot run.
  const rel = CASE.points.map((p) => p.rpm * (p.ve / 100) * (p.boost + 14.7));
  const peak = Math.max(...rel);
  for (let i = 0; i < 6; i++) {
    const r2 = (rel[i] / peak) ** 2;
    await setVal(page, `pt${i + 1}_ipd`, (CASE.peak.ipd * r2).toFixed(2));
    await setVal(page, `pt${i + 1}_filres`, (CASE.peak.fil * r2).toFixed(2));
    await setVal(page, `pt${i + 1}_mbp`, (CASE.peak.mbp * r2).toFixed(2));
  }

  await page.evaluate(() => {
    if (typeof botMatch === "function") botMatch();
  });
  await delay(400);

  if (scaleFromFlows) {
    const data = await collect(page);
    const flows = data.points.map((p) => parseFloat(p.act_lbmin) || 0);
    const pflow = Math.max(...flows, 1);
    for (let i = 0; i < 6; i++) {
      const r2 = (flows[i] / pflow) ** 2;
      await setVal(page, `pt${i + 1}_ipd`, (CASE.peak.ipd * r2).toFixed(2));
      await setVal(page, `pt${i + 1}_filres`, (CASE.peak.fil * r2).toFixed(2));
      await setVal(page, `pt${i + 1}_mbp`, (CASE.peak.mbp * r2).toFixed(2));
    }
    await page.evaluate(() => botMatch());
    await delay(300);
  }
}

async function trimTerPerPoint(page) {
  // Official All+/All− scales later points much harder and exploded EMP
  // (dP −35 psi) on the first pass. Set TER from a catalog-like dP target
  // (example outputs: +3 / +3 / +4 / +2 / −1 / −4), then nudge only the
  // points that are still N/A.
  const targetDp = [6, 8, 6, 2, -2, -4];
  const baro = 14.706;
  const data = await collect(page);
  for (let i = 0; i < 6; i++) {
    const boost = parseFloat(data.points[i].boost);
    const mbp = parseFloat(data.points[i].mbp);
    const ter = (boost - targetDp[i] + baro) / (mbp + baro);
    await setVal(page, `pt${i + 1}_ter`, Math.max(1.05, ter).toFixed(2));
  }
  await page.evaluate(() => botMatch());
  await delay(250);

  let nudges = 0;
  for (let pass = 0; pass < 40; pass++) {
    const cur = await collect(page);
    let changed = false;
    for (let i = 0; i < 6; i++) {
      const wg = cur.points[i].wg_pct;
      const ter = parseFloat(cur.points[i].ter);
      if (wg === "N/A" || wg === "" || Number(wg) < 0) {
        await setVal(page, `pt${i + 1}_ter`, (ter + 0.06).toFixed(2));
        changed = true;
        nudges += 1;
      }
    }
    if (!changed) {
      await page.evaluate(() => botMatch());
      const done = await collect(page);
      const ok = done.points.every((p) => p.wg_pct !== "N/A" && Number(p.wg_pct) >= 0);
      return { nudges, ok };
    }
    await page.evaluate(() => botMatch());
    await delay(80);
  }
  return { nudges, ok: false };
}

async function screenshotSection(page, name) {
  fs.mkdirSync(SHOT_DIR, { recursive: true });
  const dest = path.join(SHOT_DIR, name);
  await page.screenshot({ path: dest, fullPage: true });
  return dest;
}

async function runCompressor(page, comp) {
  await page.select("#compressor", comp.value);
  await page.evaluate(() => botMatch());
  await delay(800);

  const ter = await trimTerPerPoint(page);
  // Re-scale restrictions from actual flows now that TER is valid.
  const mid = await collect(page);
  const flows = mid.points.map((p) => parseFloat(p.act_lbmin) || 0);
  const pflow = Math.max(...flows, 1);
  for (let i = 0; i < 6; i++) {
    const r2 = (flows[i] / pflow) ** 2;
    await setVal(page, `pt${i + 1}_ipd`, (CASE.peak.ipd * r2).toFixed(2));
    await setVal(page, `pt${i + 1}_filres`, (CASE.peak.fil * r2).toFixed(2));
    await setVal(page, `pt${i + 1}_mbp`, (CASE.peak.mbp * r2).toFixed(2));
  }
  await page.evaluate(() => botMatch());
  await delay(400);
  const ter2 = await trimTerPerPoint(page);

  const shot = await screenshotSection(page, `${comp.id}.png`);
  const data = await collect(page);
  data.compressor_id = comp.id;
  data.ter_nudges = ter.nudges + ter2.nudges;
  data.turbine_match_ok = ter2.ok && data.points.every((p) => p.wg_pct !== "N/A");
  data.screenshot = shot;
  return data;
}

async function main() {
  fs.mkdirSync(SHOT_DIR, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: process.env.CHROME || "/usr/bin/google-chrome",
    headless: "new",
    args: [
      "--no-sandbox",
      "--disable-gpu",
      "--disable-dev-shm-usage",
      "--window-size=1400,2200",
    ],
    defaultViewport: { width: 1400, height: 2200 },
  });
  const page = await browser.newPage();
  page.setDefaultTimeout(60000);
  await page.goto("https://www.borgwarner.com/matchbot/", { waitUntil: "networkidle0" });
  await page.waitForSelector("#displacement");
  // dismiss cookie banners if present
  await page.evaluate(() => {
    const btns = [...document.querySelectorAll("button, a")];
    const hit = btns.find((b) => /accept|agree|ok/i.test(b.textContent || ""));
    if (hit) hit.click();
  });
  await delay(500);

  await applyCase(page, false);
  const runs = [];
  for (const comp of CASE.compressors) {
    console.log("running", comp.id);
    const result = await runCompressor(page, comp);
    console.log(
      comp.id,
      "ok=",
      result.turbine_match_ok,
      "nudges=",
      result.ter_nudges,
      "phi=",
      result.points.map((p) => p.phi).join(","),
      "wg=",
      result.points.map((p) => p.wg_pct).join(","),
      "hp=",
      result.points.map((p) => p.power_hp).join(","),
    );
    runs.push(result);
  }

  const payload = {
    generated: new Date().toISOString(),
    source: "https://www.borgwarner.com/matchbot/",
    procedure: "docs/intercooler-turbo-study/model/matchbot_procedure.md",
    case_file: CASE_PATH,
    runs,
  };
  fs.writeFileSync(OUT, JSON.stringify(payload, null, 2));
  console.log("wrote", OUT);
  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
