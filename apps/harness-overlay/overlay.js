(function () {
  const DATA = window.HARNESS_DATA;
  if (!DATA || !DATA.harnesses) {
    document.getElementById("status").textContent =
      "Missing data.js — run build_data.py";
    return;
  }

  const DEVICE_GROUPS = [
    {
      key: "ecu",
      label: "ECU",
      test: (d) => /^ecu/i.test(d.id) || /\becu\b/i.test(d.label),
    },
    {
      key: "sensors",
      label: "Sensors",
      test: (d) => {
        if (/^ecu/i.test(d.id)) return false;
        return /sensor|aps|map|knock|lambda|flex|fuellvl|wss_|vss_|clutch_sw|brake_sw|reverse_sw|cruise|start_req|oilp|fuelp|clntp|ect|iat|cpiat|oilt|crank|cam|turbospd/i.test(
          d.id + " " + d.label
        );
      },
    },
    {
      key: "inj_coil",
      label: "Injectors / coils",
      test: (d) =>
        /^(inj|cop)\d/i.test(d.id) || /injector|\bcop\b|coil/i.test(d.label),
    },
    {
      key: "power",
      label: "Power / PDB / RADLOK",
      test: (d) =>
        /^(pdb|pmu|fusebox|rl_|k_|fuelpump|rad_fan|fan2|mrs_|jump_|batt_|chassis_|sp_12v|sp_sw)/i.test(
          d.id
        ) ||
        /pdb|pmu|radlok|relay|fuse|fan motor|fuel pump|jump|battery|power/i.test(
          d.label
        ),
    },
    {
      key: "can",
      label: "CAN nodes",
      test: (d) =>
        /can|csb|realdash|cluster_can|r_term/i.test(d.id + " " + d.label),
    },
    {
      key: "bulkhead_oem",
      label: "Bulkhead / OEM",
      test: (d) =>
        /^(bh_|oem_|ign_sw)/i.test(d.id) ||
        /bulkhead|\boem\b|j\/b|r\/b/i.test(d.label),
    },
    {
      key: "splice_term",
      label: "Splices / terminals",
      test: (d) =>
        d.kind === "splice" ||
        d.kind === "terminal" ||
        d.kind === "resistor" ||
        /^(sp_|t_|r_|vr)/i.test(d.id),
    },
    { key: "other", label: "Other", test: () => true },
  ];

  function classify(d) {
    for (const g of DEVICE_GROUPS) {
      if (g.key === "other") continue;
      if (g.test(d)) return g.key;
    }
    return "other";
  }

  const harnessOn = Object.fromEntries(
    DATA.harnesses.map((h) => [h.key, true])
  );
  const dtypeOn = Object.fromEntries(
    DEVICE_GROUPS.map((g) => [g.key, true])
  );

  const BOX_W = 150;
  const BOX_H = 36;
  const STUB_LEN = 48;

  const stageWrap = document.getElementById("stage-wrap");
  const stage = document.getElementById("stage");
  const svg = document.getElementById("canvas");
  const empty = document.getElementById("empty");
  const status = document.getElementById("status");

  let scale = 0.35;
  let tx = 40;
  let ty = 40;
  let panning = false;
  let pan0 = null;

  function applyTransform() {
    stage.style.transform = `translate(${tx}px,${ty}px) scale(${scale})`;
  }

  function fitView() {
    let minX = Infinity,
      minY = Infinity,
      maxX = -Infinity,
      maxY = -Infinity;
    let any = false;
    for (const h of DATA.harnesses) {
      if (!harnessOn[h.key]) continue;
      for (const d of h.devices) {
        if (!dtypeOn[classify(d)]) continue;
        any = true;
        minX = Math.min(minX, d.x);
        minY = Math.min(minY, d.y);
        maxX = Math.max(maxX, d.x + BOX_W);
        maxY = Math.max(maxY, d.y + BOX_H);
      }
    }
    if (!any) return;
    const pad = 80;
    const w = stageWrap.clientWidth;
    const hgt = stageWrap.clientHeight;
    const bw = maxX - minX + pad * 2;
    const bh = maxY - minY + pad * 2;
    scale = Math.min(w / bw, hgt / bh, 1.2);
    tx = (w - bw * scale) / 2 - (minX - pad) * scale;
    ty = (hgt - bh * scale) / 2 - (minY - pad) * scale;
    applyTransform();
  }

  function deviceVisible(hKey, d) {
    return harnessOn[hKey] && dtypeOn[classify(d)];
  }

  function findDevice(h, endId) {
    if (!endId) return null;
    return h.devices.find((x) => x.id === endId) || null;
  }

  function endpointVisible(h, endId) {
    const d = findDevice(h, endId);
    if (!d) return false;
    return deviceVisible(h.key, d);
  }

  function deviceCenter(d) {
    return { x: d.x + BOX_W / 2, y: d.y + BOX_H / 2 };
  }

  function truncate(s, n) {
    s = String(s || "");
    return s.length > n ? s.slice(0, n - 1) + "…" : s;
  }

  function unitToward(from, to) {
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const len = Math.hypot(dx, dy) || 1;
    return { x: dx / len, y: dy / len };
  }

  /**
   * Wire visibility (council lock):
   * - both ends visible → full wire
   * - one end visible → short stub + label toward hidden mate
   * - both ends hidden → hide
   */
  function wireMode(h, w) {
    const srcId = w.source && w.source.id;
    const tgtId = w.target && w.target.id;
    const srcVis = endpointVisible(h, srcId);
    const tgtVis = endpointVisible(h, tgtId);
    if (!srcVis && !tgtVis) return { mode: "hide" };
    if (srcVis && tgtVis) return { mode: "full" };
    if (srcVis) {
      return {
        mode: "stub",
        visibleEnd: "source",
        hiddenId: tgtId,
        hiddenHandle: w.target && w.target.handle,
      };
    }
    return {
      mode: "stub",
      visibleEnd: "target",
      hiddenId: srcId,
      hiddenHandle: w.source && w.source.handle,
    };
  }

  function buildSidebar() {
    const hList = document.getElementById("harness-list");
    const legend = document.getElementById("legend");
    hList.innerHTML = "";
    legend.innerHTML = "";
    for (const h of DATA.harnesses) {
      const row = document.createElement("label");
      row.className = "layer" + (harnessOn[h.key] ? "" : " off");
      row.innerHTML = `<input type="checkbox" ${
        harnessOn[h.key] ? "checked" : ""
      } data-h="${h.key}">
        <span class="sw" style="background:${h.color}"></span>
        <span class="nm">${h.key}</span>
        <span class="ct">${h.counts.devices}/${h.counts.wires}</span>`;
      row.querySelector("input").addEventListener("change", (e) => {
        harnessOn[h.key] = e.target.checked;
        row.classList.toggle("off", !e.target.checked);
        render();
      });
      hList.appendChild(row);
      const leg = document.createElement("span");
      leg.innerHTML = `<i style="background:${h.color}"></i>${h.key}`;
      legend.appendChild(leg);
    }

    const dList = document.getElementById("dtype-list");
    dList.innerHTML = "";
    const counts = Object.fromEntries(
      DEVICE_GROUPS.map((g) => [g.key, 0])
    );
    for (const h of DATA.harnesses) {
      for (const d of h.devices) counts[classify(d)]++;
    }
    for (const g of DEVICE_GROUPS) {
      const row = document.createElement("label");
      row.className = "layer" + (dtypeOn[g.key] ? "" : " off");
      row.innerHTML = `<input type="checkbox" ${
        dtypeOn[g.key] ? "checked" : ""
      } data-d="${g.key}">
        <span class="nm">${g.label}</span>
        <span class="ct">${counts[g.key]}</span>`;
      row.querySelector("input").addEventListener("change", (e) => {
        dtypeOn[g.key] = e.target.checked;
        row.classList.toggle("off", !e.target.checked);
        render();
      });
      dList.appendChild(row);
    }
  }

  function render() {
    const NS = "http://www.w3.org/2000/svg";
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    let minX = Infinity,
      minY = Infinity,
      maxX = -Infinity,
      maxY = -Infinity;
    let nDev = 0,
      nWire = 0,
      nDevVis = 0,
      nWireVis = 0,
      nStub = 0;

    for (const h of DATA.harnesses) {
      for (const d of h.devices) {
        minX = Math.min(minX, d.x);
        minY = Math.min(minY, d.y);
        maxX = Math.max(maxX, d.x + BOX_W);
        maxY = Math.max(maxY, d.y + BOX_H);
      }
      for (const w of h.wires) {
        for (const p of w.layoutPoints || []) {
          minX = Math.min(minX, p.x);
          minY = Math.min(minY, p.y);
          maxX = Math.max(maxX, p.x);
          maxY = Math.max(maxY, p.y);
        }
      }
    }
    if (!isFinite(minX)) {
      minX = 0;
      minY = 0;
      maxX = 1000;
      maxY = 1000;
    }
    const pad = 100;
    const vbX = minX - pad;
    const vbY = minY - pad;
    const vbW = maxX - minX + pad * 2;
    const vbH = maxY - minY + pad * 2;
    svg.setAttribute("width", vbW);
    svg.setAttribute("height", vbH);
    svg.setAttribute("viewBox", `${vbX} ${vbY} ${vbW} ${vbH}`);

    const defs = document.createElementNS(NS, "defs");
    defs.innerHTML = `<pattern id="dots" width="30" height="30" patternUnits="userSpaceOnUse">
      <circle cx="1" cy="1" r="1" fill="#1a1a20"/></pattern>`;
    svg.appendChild(defs);
    const bg = document.createElementNS(NS, "rect");
    bg.setAttribute("x", vbX);
    bg.setAttribute("y", vbY);
    bg.setAttribute("width", vbW);
    bg.setAttribute("height", vbH);
    bg.setAttribute("fill", "url(#dots)");
    svg.appendChild(bg);

    const gWires = document.createElementNS(NS, "g");
    const gStubs = document.createElementNS(NS, "g");
    const gDevs = document.createElementNS(NS, "g");
    svg.appendChild(gWires);
    svg.appendChild(gStubs);
    svg.appendChild(gDevs);

    for (const h of DATA.harnesses) {
      const byId = Object.fromEntries(h.devices.map((d) => [d.id, d]));

      for (const w of h.wires) {
        nWire++;
        const wm = wireMode(h, w);
        if (wm.mode === "hide") continue;
        nWireVis++;

        const src = byId[w.source && w.source.id];
        const tgt = byId[w.target && w.target.id];

        if (wm.mode === "full") {
          const pts = [];
          if (src) pts.push(deviceCenter(src));
          for (const p of w.layoutPoints || []) pts.push(p);
          if (tgt) pts.push(deviceCenter(tgt));
          if (pts.length < 2) continue;
          const dpath = pts
            .map((p, i) => `${i ? "L" : "M"}${p.x},${p.y}`)
            .join(" ");
          const el = document.createElementNS(NS, "path");
          el.setAttribute("d", dpath);
          el.setAttribute("class", "wire");
          el.setAttribute("stroke", h.color);
          el.setAttribute("fill", "none");
          el.setAttribute("data-h", h.key);
          el.setAttribute("data-id", w.id);
          gWires.appendChild(el);
          continue;
        }

        // stub + label toward hidden mate
        nStub++;
        const visDev = wm.visibleEnd === "source" ? src : tgt;
        if (!visDev) continue;
        const from = deviceCenter(visDev);
        const hidDev = byId[wm.hiddenId];
        let toward;
        const lps = w.layoutPoints || [];
        if (hidDev) {
          toward = deviceCenter(hidDev);
        } else if (lps.length) {
          toward =
            wm.visibleEnd === "source" ? lps[lps.length - 1] : lps[0];
        } else {
          toward = { x: from.x + STUB_LEN, y: from.y };
        }
        const u = unitToward(from, toward);
        const to = {
          x: from.x + u.x * STUB_LEN,
          y: from.y + u.y * STUB_LEN,
        };

        const el = document.createElementNS(NS, "path");
        el.setAttribute("d", `M${from.x},${from.y} L${to.x},${to.y}`);
        el.setAttribute("class", "wire stub");
        el.setAttribute("stroke", h.color);
        el.setAttribute("fill", "none");
        el.setAttribute("stroke-dasharray", "5 4");
        el.setAttribute("data-h", h.key);
        el.setAttribute("data-id", w.id);
        gStubs.appendChild(el);

        const tip = document.createElementNS(NS, "circle");
        tip.setAttribute("cx", to.x);
        tip.setAttribute("cy", to.y);
        tip.setAttribute("r", "3");
        tip.setAttribute("fill", h.color);
        gStubs.appendChild(tip);

        const label = document.createElementNS(NS, "text");
        label.setAttribute("x", to.x + u.x * 8);
        label.setAttribute("y", to.y + u.y * 8 + 3);
        label.setAttribute("fill", h.color);
        label.setAttribute("font-size", "10");
        label.setAttribute(
          "font-family",
          "IBM Plex Mono, ui-monospace, monospace"
        );
        label.setAttribute("paint-order", "stroke");
        label.setAttribute("stroke", "#0b0b0d");
        label.setAttribute("stroke-width", "3");
        const handle = wm.hiddenHandle ? `:${wm.hiddenHandle}` : "";
        label.textContent = `→ ${wm.hiddenId || "?"}${handle}`;
        gStubs.appendChild(label);
      }

      for (const d of h.devices) {
        nDev++;
        const vis = deviceVisible(h.key, d);
        if (vis) nDevVis++;
        const g = document.createElementNS(NS, "g");
        g.setAttribute("class", "comp" + (vis ? "" : " hidden"));
        g.setAttribute("transform", `translate(${d.x},${d.y})`);
        const body = document.createElementNS(NS, "rect");
        body.setAttribute("class", "comp-body");
        body.setAttribute("width", BOX_W);
        body.setAttribute("height", BOX_H);
        body.setAttribute("rx", "5");
        body.setAttribute("stroke", h.color);
        body.setAttribute("stroke-width", "1.6");
        const title = document.createElementNS(NS, "text");
        title.setAttribute("class", "comp-title");
        title.setAttribute("x", "8");
        title.setAttribute("y", "15");
        title.textContent = truncate(d.label, 22);
        const idt = document.createElementNS(NS, "text");
        idt.setAttribute("class", "comp-id");
        idt.setAttribute("x", "8");
        idt.setAttribute("y", "28");
        idt.textContent = `${d.id} · ${h.key}`;
        g.appendChild(body);
        g.appendChild(title);
        g.appendChild(idt);
        gDevs.appendChild(g);
      }
    }

    empty.classList.toggle("on", nDevVis === 0);
    status.textContent = `${nDevVis}/${nDev} devices · ${nWireVis}/${nWire} wires (${nStub} stubs)`;
  }

  stageWrap.addEventListener("pointerdown", (e) => {
    if (e.button !== 0) return;
    panning = true;
    stageWrap.classList.add("panning");
    pan0 = { x: e.clientX, y: e.clientY, tx, ty };
    stageWrap.setPointerCapture(e.pointerId);
  });
  stageWrap.addEventListener("pointermove", (e) => {
    if (!panning || !pan0) return;
    tx = pan0.tx + (e.clientX - pan0.x);
    ty = pan0.ty + (e.clientY - pan0.y);
    applyTransform();
  });
  function endPan() {
    panning = false;
    pan0 = null;
    stageWrap.classList.remove("panning");
  }
  stageWrap.addEventListener("pointerup", endPan);
  stageWrap.addEventListener("pointercancel", endPan);

  stageWrap.addEventListener(
    "wheel",
    (e) => {
      e.preventDefault();
      const rect = stageWrap.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const before = 1 / scale;
      const factor = e.deltaY < 0 ? 1.12 : 1 / 1.12;
      const next = Math.min(4, Math.max(0.05, scale * factor));
      const wx = (mx - tx) * before;
      const wy = (my - ty) * before;
      scale = next;
      tx = mx - wx * scale;
      ty = my - wy * scale;
      applyTransform();
    },
    { passive: false }
  );

  document.getElementById("btn-fit").addEventListener("click", fitView);
  document.getElementById("btn-reset").addEventListener("click", () => {
    scale = 0.35;
    tx = 40;
    ty = 40;
    applyTransform();
  });
  document.getElementById("btn-h-all").addEventListener("click", () => {
    for (const k of Object.keys(harnessOn)) harnessOn[k] = true;
    buildSidebar();
    render();
  });
  document.getElementById("btn-h-none").addEventListener("click", () => {
    for (const k of Object.keys(harnessOn)) harnessOn[k] = false;
    buildSidebar();
    render();
  });
  document.getElementById("btn-d-all").addEventListener("click", () => {
    for (const k of Object.keys(dtypeOn)) dtypeOn[k] = true;
    buildSidebar();
    render();
  });
  document.getElementById("btn-d-none").addEventListener("click", () => {
    for (const k of Object.keys(dtypeOn)) dtypeOn[k] = false;
    buildSidebar();
    render();
  });

  buildSidebar();
  render();
  applyTransform();
  requestAnimationFrame(() => fitView());
})();
