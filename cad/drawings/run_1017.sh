#!/bin/bash
# Usage: bash cad/drawings/run_1017.sh   (writes only under $ST185_WORK, default <repo>/_research/drawings_1017/work, untracked per R67)
# PY = the st185 CAD Python (frozen env, see AGENTS.md). HANDBUILT_CAD = handbuilt-cad checkout (drawing engine + renders).
# ST185_CAD = the main checkout's cad/ tree (heavy STEP files are local-only there; a worktree has none).
set -u
HERE=$(cd "$(dirname "$0")" && pwd); REPO=$(cd "$HERE/../.." && pwd)
HB=${HANDBUILT_CAD:-$HOME/projects/handbuilt-cad}; export HANDBUILT_CAD=$HB
PY=${PY:-$HOME/projects/handbuilt-models/.venv/bin/python}
W=${ST185_WORK:-$REPO/_research/drawings_1017/work}; export ST185_WORK=$W
R=${ST185_CAD:-/mnt/c/projects/active/st185-link-ecu-config/cad}
mkdir -p $W/src/{st185_csb3_1017,st185_vrc_1017,st185_drb102_1017,st185_fusebox_1017} $W/logs $W/renders
cp $R/enclosures/csb3/CSB3_part_CSB3-Body.step $R/enclosures/csb3/CSB3_part_CSB3-Lid.step $W/src/st185_csb3_1017/
cp $R/enclosures/vrc/print/ST185_VRC_board_holder_PA12.step $R/enclosures/vrc/VRC_part_VRC-Body.step $R/enclosures/vrc/VRC_part_VRC-Lid.step $W/src/st185_vrc_1017/
cp $R/drb102-plate/DRB102-firewall-plate.step $W/src/st185_drb102_1017/
cp $R/fusebox/rev7/*.step $W/src/st185_fusebox_1017/; rm -f $W/src/st185_fusebox_1017/ST185_fusebox_rev7_assembly.step
cd $W; : > logs/_status.txt
keys=$(cd $HERE && $PY -c "import specs_1017;print(' '.join(specs_1017.ORDER))")
echo $keys | tr ' ' '\n' | xargs -P ${JOBS:-6} -I{} sh -c "timeout 1500 $PY $HERE/run_one_1017.py {} > logs/{}.log 2>&1; echo \"{} exit \$?\" >> logs/_status.txt"
[ -n "${SKIP_RENDERS:-}" ] && { echo ALLDONE >> logs/_status.txt; exit 0; }
# smooth-shaded renders (no mesh lines), one per model file
for f in $W/src/*/*.step; do b=$(basename $f .step); timeout 600 $PY $HB/tools/render/smooth_render.py $f $W/renders/$b.png --view iso --edges > logs/render_$b.log 2>&1 || echo "render $b fail" >> logs/_status.txt; done
echo ALLDONE >> logs/_status.txt
