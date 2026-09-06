#!/usr/bin/env python3
"""Generate docs/research-hub.html - a single navigable index of the repo's research.

Run from anywhere:  python docs/build-research-hub.py
Output is self-contained and opens from file:// with no server.
"""

from __future__ import annotations

import html
import json
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import md5
from pathlib import Path

DOCS = Path(__file__).resolve().parent
REPO = DOCS.parent
OUT = DOCS / "research-hub.html"

# Topic order and framing. Directories not listed here are still picked up,
# appended in sorted order with a generic blurb.
TOPICS: list[dict] = [
    {
        "dir": "intercooler-turbo-study",
        "title": "Intercooler, Turbo & Charge Piping",
        "blurb": "Cold-side hardware study: core selection, turbo/redline choice, "
                 "manifold pairing, ducting, and charge-pipe sizing. Mechanical/thermal "
                 "scope, separate from the CAN/ECU config.",
    },
    {
        "dir": "harness",
        "title": "Harness & Wiring",
        "blurb": "Harness wiring diagram for the ECU/cluster/switchboard install.",
    },
]

# Files matching these are working artifacts, not things you read.
SUPPORTING_SUFFIXES = {".py", ".js", ".json", ".csv", ".css", ".txt"}
ASSET_SUFFIXES = {".png", ".svg", ".webp", ".jpg", ".jpeg", ".pdf", ".ico"}
SKIP_NAMES = {"package-lock.json", "package.json"}
SKIP_PATTERNS = [re.compile(r"\.bak\.html$"), re.compile(r"^__pycache__$")]

# A readable file sitting directly in a topic folder is a deliverable; anything
# deeper (research/, data/) is the working trail behind it. These two lists
# override that inference where the layout lies.
FORCE_RESEARCH = {  # readable, but an intermediate rather than something to read
    "docs/intercooler-turbo-study/research/data/report-splice-scripts/_new_sections.html",
}
FORCE_DELIVERABLE: set[str] = set()


@dataclass
class Doc:
    path: Path
    rel: str
    kind: str              # "read" | "support" | "asset"
    title: str
    summary: str = ""
    sections: list[str] = field(default_factory=list)
    size: int = 0
    modified: str = ""
    digest: str = ""


def git_date(rel: str) -> str:
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", rel],
            cwd=REPO, capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip()
    except Exception:
        return ""


def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


def read_html(p: Path) -> tuple[str, str, list[str]]:
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<title>(.*?)</title>", text, re.S | re.I)
    title = strip_tags(m.group(1)) if m else p.stem
    # Numbered sections: <section id="pipes"> ... <h2><span class="num">07</span>Title</h2>
    # Carry the enclosing section id so the hub can deep-link with a real anchor.
    secs = []
    anchors = [(m.start(), m.group(1))
               for m in re.finditer(r'<section[^>]*\bid="([^"]+)"', text, re.I)]
    for hm in re.finditer(r"<h2[^>]*>(.*?)</h2>", text, re.S | re.I):
        inner = hm.group(1)
        num = re.search(r'class="num"[^>]*>(.*?)</span>', inner, re.S | re.I)
        label = strip_tags(re.sub(r'<span class="num".*?</span>', "", inner, flags=re.S | re.I))
        if not label:
            continue
        prior = [a for pos, a in anchors if pos < hm.start()]
        secs.append({
            "label": f"{strip_tags(num.group(1))} {label}".strip() if num else label,
            "id": prior[-1] if prior else "",
        })
    # First real paragraph as summary
    pm = re.search(r"<p[^>]*>(.*?)</p>", text, re.S | re.I)
    summary = strip_tags(pm.group(1))[:280] if pm else ""
    return title, summary, secs


def read_md(p: Path) -> tuple[str, str, list[str]]:
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    title, summary, secs = p.stem, "", []
    body_start = 0
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            title = ln[2:].strip()
            body_start = i + 1
            break
    para: list[str] = []
    for ln in lines[body_start:]:
        s = ln.strip()
        if not s:
            if para:
                break
            continue
        if s.startswith(("#", "|", ">", "-", "*", "```")):
            if para:
                break
            continue
        para.append(s)
    summary = " ".join(para)[:280]
    for ln in lines:
        if ln.startswith("## "):
            secs.append({"label": ln[3:].strip(), "id": ""})
    return title, summary, secs


def classify(p: Path, topic_dir: Path, rel: str) -> str:
    if p.suffix.lower() in ASSET_SUFFIXES:
        return "asset"
    if p.suffix.lower() in SUPPORTING_SUFFIXES:
        return "support"
    if rel in FORCE_DELIVERABLE:
        return "deliverable"
    if rel in FORCE_RESEARCH:
        return "research"
    return "deliverable" if p.parent == topic_dir else "research"


def collect(topic_dir: Path) -> list[Doc]:
    docs: list[Doc] = []
    for p in sorted(topic_dir.rglob("*")):
        if not p.is_file():
            continue
        if p.name in SKIP_NAMES:
            continue
        if any(pat.search(p.name) or pat.search(p.parent.name) for pat in SKIP_PATTERNS):
            continue
        rel = p.relative_to(REPO).as_posix()
        kind = classify(p, topic_dir, rel)
        title, summary, secs = p.stem, "", []
        if kind in ("deliverable", "research"):
            try:
                if p.suffix.lower() in {".html", ".htm"}:
                    title, summary, secs = read_html(p)
                elif p.suffix.lower() == ".md":
                    title, summary, secs = read_md(p)
            except Exception:
                pass
        stat = p.stat()
        docs.append(Doc(
            path=p, rel=rel, kind=kind, title=title, summary=summary, sections=secs,
            size=stat.st_size,
            modified=git_date(rel) or datetime.fromtimestamp(
                stat.st_mtime, timezone.utc).strftime("%Y-%m-%d"),
            digest=md5(p.read_bytes()).hexdigest()
            if kind in ("deliverable", "research") else "",
        ))
    return docs


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} MB"


def build() -> dict:
    topics = []
    seen_dirs = {t["dir"] for t in TOPICS}
    extra = sorted(
        d.name for d in DOCS.iterdir()
        if d.is_dir() and d.name not in seen_dirs and not d.name.startswith(".")
    )
    spec = TOPICS + [{"dir": d, "title": d.replace("-", " ").title(), "blurb": ""} for d in extra]

    digests: dict[str, list[str]] = {}
    for t in spec:
        tdir = DOCS / t["dir"]
        if not tdir.is_dir():
            continue
        docs = collect(tdir)
        for d in docs:
            if d.digest:
                digests.setdefault(d.digest, []).append(d.rel)
        # A deeper copy of a file that already appears higher up is a mirror,
        # not a second document - link it back instead of repeating the card.
        canonical: dict[str, str] = {}
        for d in sorted(docs, key=lambda x: x.rel.count("/")):
            if d.digest and d.digest not in canonical:
                canonical[d.digest] = d.rel
        rows = []
        for d in docs:
            row = d.__dict__ | {"path": None}
            row["mirror_of"] = (canonical.get(d.digest)
                                if d.digest and canonical.get(d.digest) != d.rel else None)
            rows.append(row)
        topics.append({
            "dir": t["dir"], "title": t["title"], "blurb": t["blurb"], "docs": rows,
            "counts": {
                k: sum(1 for r in rows if r["kind"] == k and not r["mirror_of"])
                for k in ("deliverable", "research", "support", "asset")
            },
        })
    dupes = {k: v for k, v in digests.items() if len(v) > 1}
    return {"topics": topics, "dupes": dupes}


def render(data: dict) -> str:
    # Derived from the sources, not the clock: regenerating without changing any
    # research must produce a byte-identical file, or the committed output churns
    # on every run and collides between concurrent sessions.
    dates = [d["modified"] for t in data["topics"] for d in t["docs"] if d.get("modified")]
    latest = max(dates) if dates else "unknown"
    payload = json.dumps(data, default=str, sort_keys=True)
    total_read = sum(t["counts"]["deliverable"] + t["counts"]["research"]
                     for t in data["topics"])
    total_all = sum(len(t["docs"]) for t in data["topics"])

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ST185 Research Hub</title>
<style>
  :root {{
    --bg:#f7f7f5; --panel:#fff; --ink:#16171a; --muted:#6a6d75; --line:#e2e2df;
    --accent:#b4451f; --accent-soft:#fbeee8; --chip:#eeeeeb;
  }}
  :root:not([data-theme="light"]) {{ }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg:#131417; --panel:#1b1c20; --ink:#e9e9ea; --muted:#9a9da5; --line:#2c2e34;
      --accent:#e8825a; --accent-soft:#2a1c16; --chip:#26282e;
    }}
  }}
  :root[data-theme="dark"] {{
    --bg:#131417; --panel:#1b1c20; --ink:#e9e9ea; --muted:#9a9da5; --line:#2c2e34;
    --accent:#e8825a; --accent-soft:#2a1c16; --chip:#26282e;
  }}
  * {{ box-sizing:border-box; }}
  body {{ background:var(--bg); color:var(--ink); margin:0;
    font:15px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }}
  .wrap {{ max-width:1080px; margin:0 auto; padding:32px 20px 80px; }}
  header h1 {{ font-size:26px; margin:0 0 6px; letter-spacing:-.02em; }}
  .sub {{ color:var(--muted); font-size:14px; margin:0 0 22px; }}
  .bar {{ display:flex; gap:10px; flex-wrap:wrap; align-items:center;
    position:sticky; top:0; background:var(--bg); padding:12px 0; z-index:5;
    border-bottom:1px solid var(--line); margin-bottom:22px; }}
  #q {{ flex:1; min-width:220px; padding:9px 12px; border:1px solid var(--line);
    border-radius:8px; background:var(--panel); color:var(--ink); font-size:14px; }}
  #q:focus {{ outline:2px solid var(--accent); outline-offset:-1px; }}
  .toggle {{ display:flex; gap:4px; }}
  .toggle button {{ padding:8px 11px; border:1px solid var(--line); background:var(--panel);
    color:var(--muted); border-radius:7px; cursor:pointer; font-size:13px; }}
  .toggle button[aria-pressed="true"] {{ background:var(--accent-soft);
    border-color:var(--accent); color:var(--accent); font-weight:600; }}
  .topic {{ margin:0 0 30px; }}
  .topic > h2 {{ font-size:19px; margin:0 0 4px; letter-spacing:-.01em; }}
  .blurb {{ color:var(--muted); font-size:13.5px; margin:0 0 12px; max-width:74ch; }}
  .counts {{ font-size:12px; color:var(--muted); margin-bottom:12px; }}
  .counts b {{ color:var(--ink); font-weight:600; }}
  .card {{ background:var(--panel); border:1px solid var(--line); border-radius:10px;
    padding:14px 16px; margin-bottom:9px; }}
  .card h3 {{ margin:0 0 4px; font-size:15px; font-weight:600; }}
  .card h3 a {{ color:var(--ink); text-decoration:none; }}
  .card h3 a:hover {{ color:var(--accent); text-decoration:underline; }}
  .meta {{ font-size:11.5px; color:var(--muted); display:flex; gap:9px;
    flex-wrap:wrap; margin-bottom:6px; }}
  .chip {{ background:var(--chip); padding:1.5px 7px; border-radius:20px;
    font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:11px; }}
  .summary {{ font-size:13.5px; color:var(--muted); margin:0; max-width:78ch; }}
  details.secs {{ margin-top:9px; }}
  details.secs summary {{ cursor:pointer; font-size:12.5px; color:var(--accent);
    font-weight:600; user-select:none; }}
  .seclist {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr));
    gap:2px 14px; margin:9px 0 0; padding:0; list-style:none; }}
  .seclist a {{ font-size:12.5px; color:var(--muted); text-decoration:none;
    display:block; padding:2.5px 0; border-bottom:1px solid transparent; }}
  .seclist a:hover {{ color:var(--accent); border-bottom-color:var(--line); }}
  .support-wrap summary {{ cursor:pointer; font-size:13px; color:var(--muted); }}
  .support-list {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr));
    gap:1px 14px; margin:10px 0 0; padding:0; list-style:none; }}
  .support-list a {{ font-size:12px; color:var(--muted); text-decoration:none;
    font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }}
  .support-list a:hover {{ color:var(--accent); }}
  .warn {{ background:var(--accent-soft); border:1px solid var(--accent);
    border-radius:9px; padding:12px 15px; margin-bottom:24px; font-size:13px; }}
  .warn h3 {{ margin:0 0 6px; font-size:13.5px; color:var(--accent); }}
  .warn ul {{ margin:0; padding-left:18px; }}
  .warn code {{ font-size:11.5px; }}
  footer {{ margin-top:44px; padding-top:16px; border-top:1px solid var(--line);
    color:var(--muted); font-size:12px; }}
  .hidden {{ display:none !important; }}
  mark {{ background:var(--accent-soft); color:var(--accent); padding:0 1px; }}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>ST185 Research Hub</h1>
  <p class="sub">Sources last updated {latest} &middot; {total_read} readable documents of
     {total_all} files across {len(data["topics"])} topics &middot; regenerate with
     <code>python docs/build-research-hub.py</code></p>
</header>

<div class="bar">
  <input id="q" type="search" placeholder="Filter by title, section, or filename&hellip;"
         autocomplete="off">
  <div class="toggle">
    <button id="t-deliverable" aria-pressed="true">Deliverables</button>
    <button id="t-research" aria-pressed="false">Research trail</button>
    <button id="t-support" aria-pressed="false">Working files</button>
  </div>
</div>

<div id="dupes"></div>
<main id="out"></main>

<footer>
  Built from <code>docs/</code> by <code>build-research-hub.py</code>.
  Section links use the source document's own anchors where it has them, and a
  text fragment otherwise.
</footer>
</div>

<script>
const DATA = {payload};

const esc = s => String(s ?? "").replace(/[&<>"]/g,
  c => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]));

function docCard(d) {{
  const secs = (d.sections || []).filter(s => s && s.label);
  // Real #anchor when the source document has one; text fragment otherwise.
  const target = s => s.id
    ? `#${{encodeURIComponent(s.id)}}`
    : `#:~:text=${{encodeURIComponent(s.label.replace(/^\\d+\\s+/, ""))}}`;
  return `
  <article class="card" data-hay="${{esc(
      (d.title + " " + d.rel + " " + secs.map(s => s.label).join(" ")).toLowerCase())}}">
    <h3><a href="../${{esc(d.rel)}}">${{esc(d.title)}}</a></h3>
    <div class="meta">
      <span class="chip">${{esc(d.rel.split("/").slice(1).join("/"))}}</span>
      <span>${{esc(d.modified)}}</span>
      <span>${{esc(d.human_size)}}</span>
      ${{secs.length ? `<span>${{secs.length}} sections</span>` : ""}}
    </div>
    ${{d.summary ? `<p class="summary">${{esc(d.summary)}}</p>` : ""}}
    ${{secs.length ? `<details class="secs"><summary>${{secs.length}} sections</summary>
      <ul class="seclist">${{secs.map(s =>
        `<li><a href="../${{esc(d.rel)}}${{target(s)}}">${{esc(s.label)}}</a></li>`
      ).join("")}}</ul></details>` : ""}}
  </article>`;
}}

const on = id => document.getElementById(id).getAttribute("aria-pressed") === "true";

function render() {{
  const show = {{
    deliverable: on("t-deliverable"),
    research: on("t-research"),
    support: on("t-support"),
  }};

  document.getElementById("out").innerHTML = DATA.topics.map(t => {{
    const live = t.docs.filter(d => !d.mirror_of);
    const deliverables = live.filter(d => d.kind === "deliverable");
    const research = live.filter(d => d.kind === "research");
    const support = t.docs.filter(d => d.kind === "support" || d.kind === "asset");
    const mirrors = t.docs.filter(d => d.mirror_of);
    return `
    <section class="topic" data-topic="${{esc(t.dir)}}">
      <h2>${{esc(t.title)}}</h2>
      ${{t.blurb ? `<p class="blurb">${{esc(t.blurb)}}</p>` : ""}}
      <p class="counts"><b>${{t.counts.deliverable}}</b> deliverables &middot;
         <b>${{t.counts.research}}</b> research notes &middot;
         <b>${{t.counts.support + t.counts.asset}}</b> scripts &amp; assets${{
         mirrors.length ? ` &middot; <b>${{mirrors.length}}</b> mirrored` : ""}}</p>
      ${{show.deliverable ? deliverables.map(docCard).join("") : ""}}
      ${{show.research && research.length ? `
        <details class="support-wrap" open>
          <summary>${{research.length}} research notes</summary>
          <div>${{research.map(docCard).join("")}}</div>
        </details>` : ""}}
      ${{show.support && support.length ? `
        <details class="support-wrap" open>
          <summary>${{support.length}} working files</summary>
          <ul class="support-list">${{support.map(d =>
            `<li data-hay="${{esc(d.rel.toLowerCase())}}"><a href="../${{esc(d.rel)}}">${{
              esc(d.rel.split("/").slice(2).join("/"))}}</a></li>`
          ).join("")}}</ul>
        </details>` : ""}}
    </section>`;
  }}).join("");
  filter();
}}

function filter() {{
  const q = document.getElementById("q").value.trim().toLowerCase();
  document.querySelectorAll("[data-hay]").forEach(el => {{
    el.classList.toggle("hidden", q && !el.dataset.hay.includes(q));
  }});
  document.querySelectorAll(".topic").forEach(sec => {{
    const anyVisible = sec.querySelector("[data-hay]:not(.hidden)");
    sec.classList.toggle("hidden", !!q && !anyVisible);
  }});
}}

function renderDupes() {{
  const entries = Object.entries(DATA.dupes || {{}});
  if (!entries.length) return;
  document.getElementById("dupes").innerHTML = `
    <div class="warn">
      <h3>${{entries.length}} document${{entries.length > 1 ? "s exist" : " exists"}} in more than one place</h3>
      <ul>${{entries.map(([, paths]) =>
        `<li>${{paths.map(p => `<code>${{esc(p)}}</code>`).join(" = ")}}</li>`).join("")}}</ul>
    </div>`;
}}

document.getElementById("q").addEventListener("input", filter);
["t-deliverable", "t-research", "t-support"].forEach(id => {{
  document.getElementById(id).addEventListener("click", e => {{
    const b = e.currentTarget;
    b.setAttribute("aria-pressed", b.getAttribute("aria-pressed") === "true" ? "false" : "true");
    render();
  }});
}});

renderDupes();
render();
</script>
</body>
</html>
"""


def main() -> None:
    data = build()
    for t in data["topics"]:
        for d in t["docs"]:
            d["human_size"] = human_size(d["size"])
    OUT.write_text(render(data), encoding="utf-8")
    deliv = sum(t["counts"]["deliverable"] for t in data["topics"])
    research = sum(t["counts"]["research"] for t in data["topics"])
    total = sum(len(t["docs"]) for t in data["topics"])
    print(f"wrote {OUT.relative_to(REPO)}  "
          f"({len(data['topics'])} topics, {deliv} deliverables, "
          f"{research} research notes, {total} files, "
          f"{len(data['dupes'])} duplicate groups)")


if __name__ == "__main__":
    main()
