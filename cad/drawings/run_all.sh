#!/bin/bash
# PY = the st185 CAD Python (handbuilt-cad .venv: ~/projects/handbuilt-cad/.venv/bin/python, same versions of every package st185 imports); HANDBUILT_CAD = handbuilt-cad checkout (default ~/projects/handbuilt-cad)
# Usage: ST185_WORK=/path/to/workdir (containing src/<job>/*.step) ./run_all.sh
set -e; HERE=$(cd "$(dirname "$0")" && pwd)
: "${PY:=python}"; : "${ST185_WORK:?set ST185_WORK}"; export ST185_WORK
cd "$ST185_WORK"; mkdir -p logs
keys=$($PY -c "import sys;sys.path[:0]=['$HERE','${HANDBUILT_CAD:-$HOME/projects/handbuilt-cad}/drawing'];import specs;print(' '.join(specs.PARTS))")
echo $keys | tr ' ' '\n' | xargs -P ${JOBS:-6} -I{} sh -c "timeout 1500 $PY $HERE/run_one.py {} > logs/{}.log 2>&1; echo \"{} exit \$?\" >> logs/_status.txt"
echo ALLDONE >> logs/_status.txt
