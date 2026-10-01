#!/usr/bin/env node
/** Runtime filter checks for the generated research hub. Requires jsdom. */

"use strict";

const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const HTML = path.join(__dirname, "research-hub.html");

function loadHtml() {
  let html = fs.existsSync(HTML) ? fs.readFileSync(HTML, "utf8") : "";
  if (!html.includes("function applyFilters")) {
    const built = spawnSync("python3", [path.join(__dirname, "build-research-hub.py")], {
      stdio: "inherit",
    });
    if (built.status !== 0) process.exit(built.status || 1);
    html = fs.readFileSync(HTML, "utf8");
  }
  return html;
}

function visible(document, sel) {
  return [...document.querySelectorAll(sel)].filter((el) => !el.classList.contains("hidden"));
}

function click(document, id) {
  document.getElementById(id).click();
}

function search(window, document, q) {
  const inp = document.getElementById("q");
  inp.value = q;
  inp.dispatchEvent(new window.Event("input"));
}

function main() {
  const dom = new JSDOM(loadHtml(), {
    runScripts: "dangerously",
    url: "file://" + HTML,
  });
  const { window } = dom;
  const { document } = window;

  const startCards = visible(document, "#out .card[data-filter-item]").length;
  if (startCards < 10) throw new Error("expected cards on load, got " + startCards);

  click(document, "t-deliverable");
  const delivLeft = visible(document, "#out .card[data-filter-item]")
    .filter((el) => el.dataset.kind === "deliverable").length;
  if (delivLeft) throw new Error("deliverable cards still visible");
  click(document, "t-deliverable");

  search(window, document, "matchbot_case");
  const matchCards = visible(document, "#out .card[data-filter-item]");
  if (!matchCards.length) throw new Error("research title search found no cards");
  const openWrap = matchCards.some((el) => {
    const wrap = el.closest("details.support-wrap");
    return wrap && wrap.open && !wrap.classList.contains("hidden");
  });
  if (!openWrap) throw new Error("matching research group stayed collapsed");

  search(window, document, "fl_acamp_act");
  const rowCard = visible(document, "#out .card[data-filter-item]")
    .find((el) => (el.dataset.hay || "").includes("fl_acamp_act"));
  if (!rowCard) throw new Error("embedded table row search hid the card");

  search(window, document, "0413-214-1205");
  const parts = document.getElementById("parts");
  if (!parts || parts.classList.contains("hidden")) {
    throw new Error("on-hand-only PN hid the parts board");
  }
  const onhandTab = parts.querySelector('[data-tab="onhand"]');
  if (!onhandTab || onhandTab.getAttribute("aria-selected") !== "true") {
    throw new Error("search did not switch to the on-hand tab");
  }
  const pnRow = [...parts.querySelectorAll("tbody tr")].find((tr) =>
    (tr.dataset.hay || "").includes("0413-214-1205") && !tr.classList.contains("hidden"));
  if (!pnRow) throw new Error("on-hand PN row is not visible");

  const tfilter = parts.querySelector(".tfilter");
  tfilter.value = "0413";
  tfilter.dispatchEvent(new window.Event("input"));
  const leaked = [...parts.querySelectorAll("tbody tr:not(.hidden)")]
    .filter((tr) => !(tr.dataset.hay || "").includes("0413-214-1205")
      && !(tr.dataset.hay || "").includes("0413"));
  if (leaked.length) throw new Error("local table filter dropped the global search");

  search(window, document, "frozen records");
  const notesTile = document.querySelector('.topic-tile[data-topic="notes"]');
  const notesSec = document.getElementById("topic-notes");
  if (!notesTile.classList.contains("hidden")) {
    throw new Error("topic tile stayed visible with no matching documents");
  }
  if (!notesSec.classList.contains("hidden")) {
    throw new Error("notes section stayed visible with no matching documents");
  }

  search(window, document, "");
  if (!visible(document, "#out .card[data-filter-item]").length) {
    throw new Error("clearing search hid every card");
  }

  console.log("ok filter runtime");
}

main();
