# ST185 drawing jobs (cad/drawings)

Job specs and run scripts for the st185 shop drawings. The drawing engine itself (`part`, `asm`, `dwg`, `revs`, checks, smooth renders) lives in **handbuilt-cad** (`drawing/`, `tools/checks/`, `tools/render/`); these scripts find it through `HANDBUILT_CAD` (default `~/projects/handbuilt-cad`) by `sys.path`, and run on handbuilt-cad's `.venv` (`~/projects/handbuilt-cad/.venv/bin/python`; the same versions of every package st185 imports as the old handbuilt-models env, repointed 2026-10-17). Ported from the local `stevecad-tools/examples/st185` on 2026-10-17.

- **Every model change regenerates its drawing in the same PR, and a wrong drawing is fixed in the model** (DECISIONS R183). After a drawing is regenerated and copied beside its model: `python cad/check_drawings_current.py --update <part no> ...` (records the rev, the PDF and the model fingerprints in `cad/drawing-models.json`; it refuses a model change without a new letter). The gate runs in `check_all.py`.
- **Drawings are NOT auto-updating** (Daniel's rule). They are generated from exported STEP files and have no link to the Fusion models. After any model change, re-export the STEP and re-run the drawing script; check the rev block.
- Edge breaks are not modeled; they are a drawing note (GEN_M in specs.py).
- Run: make a work dir containing `src/<job>/<file>.step` (copy or symlink the repo's `cad/...` STEP files; never edit the repo from here), then:
  `ST185_WORK=<work dir> HANDBUILT_CAD=~/projects/handbuilt-cad ~/projects/handbuilt-cad/.venv/bin/python cad/drawings/run_one.py csb3_body` -> `out/<job>/<PN>.pdf/.dxf`, `previews/<PN>_shN.png`.
- `run_asm.py <key>` = an assembly drawing from `aspecs.py` (`fb_power`, `fb_logic`, `fb_br`, `vrc`, `csb3`, `drb`, `fuel_hanger`; DECISIONS R182), work dir as above with `src/st185_fusebox_1015/`, `src/csv/` and the enclosure / DRB assembly STEPs.
- `specs.py` = per-part drawing specs (dims, notes, threads); `aspecs.py` = assembly specs + BOM; `run_B.py` = rev-B reissue; `run_all.sh` = all parts in parallel.
- `fix_*.py`, `build_assemblies.py`, `render_fixes.py` are 2026-10-16 job scripts kept for reference (paths relative to a work dir).
- `specs_1017.py` / `run_one_1017.py` / `run_1017.sh` = the 2026-10-17 drawing set (`bash cad/drawings/run_1017.sh`; work dir defaults to `_research/drawings_1017/work`, untracked).
- `run_fb117.py` = ST185-FB-117, the POWER output copper C-strap (R155, N14 = B): the Fusion strap + its flat blank (build123d, from `spec.strap_blank()`) in one drawing model; `run_n14.py` = the FB-101 / -102 / -112 reissue that goes with it (changes in `specs_1017.py`). Both: `ST185_WORK=<work dir> ~/projects/handbuilt-cad/.venv/bin/python cad/drawings/<script>.py`.
- Title block project / drawn-by are set at the bottom of `specs.py`, `aspecs.py` and `specs_1017.py`.
- Work dirs and outputs stay out of git; finished PDFs and `_sh1.png` previews go beside their model in `cad/` by PR.
