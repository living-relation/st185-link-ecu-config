# ST185 drawing jobs (cad/drawings)

Job specs and run scripts for the st185 shop drawings. The drawing engine itself (`part`, `asm`, `dwg`, `revs`, checks, smooth renders) lives in **handbuilt-cad** (`drawing/`, `tools/checks/`, `tools/render/`); these scripts find it through `HANDBUILT_CAD` (default `~/projects/handbuilt-cad`) by `sys.path`, so st185's own Python environment is unchanged (frozen, AGENTS.md). Ported from the local `stevecad-tools/examples/st185` on 2026-10-17.

- **Drawings are NOT auto-updating** (Daniel's rule). They are generated from exported STEP files and have no link to the Fusion models. After any model change, re-export the STEP and re-run the drawing script; check the rev block.
- Edge breaks are not modeled; they are a drawing note (GEN_M in specs.py).
- Run: make a work dir containing `src/<job>/<file>.step` (copy or symlink the repo's `cad/...` STEP files; never edit the repo from here), then:
  `ST185_WORK=<work dir> HANDBUILT_CAD=~/projects/handbuilt-cad <st185 CAD python> cad/drawings/run_one.py csb3_body` -> `out/<job>/<PN>.pdf/.dxf`, `previews/<PN>_shN.png`.
- `specs.py` = per-part drawing specs (dims, notes, threads); `aspecs.py` = assembly specs + BOM; `run_B.py` = rev-B reissue; `run_all.sh` = all parts in parallel.
- `fix_*.py`, `build_assemblies.py`, `render_fixes.py` are 2026-10-16 job scripts kept for reference (paths relative to a work dir).
- `specs_1017.py` / `run_one_1017.py` / `run_1017.sh` = the 2026-10-17 drawing set (`bash cad/drawings/run_1017.sh`; work dir defaults to `_research/drawings_1017/work`, untracked).
- Title block project / drawn-by are set at the bottom of `specs.py`, `aspecs.py` and `specs_1017.py`.
- Work dirs and outputs stay out of git; finished PDFs and `_sh1.png` previews go beside their model in `cad/` by PR.
