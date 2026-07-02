#!/usr/bin/env bash
#
# ttg-pass-feature_finish_demo.bash
#
# demo: Feature Finish merge (feature/x into develop) staging two
# files — a.py with a STEADY "# Todo steady marker" comment and
# b.py with a QUIET "# todo quiet marker" comment (no Loud tags
# anywhere)
# expected result: pass

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCENARIO="feature_finish_pass"

if [ -x "$REPO_ROOT/venv/bin/python3" ]; then
    PYTHON="$REPO_ROOT/venv/bin/python3"
else
    PYTHON="python3"
    export PYTHONPATH="$REPO_ROOT:${PYTHONPATH:-}"
fi

DEMO_SCRIPT="$(basename "${BASH_SOURCE[0]}")"

"$PYTHON" -m hupy.kamilog lp c "$DEMO_SCRIPT" "#"
printf "scenario:\tFeature Finish, multiple files (steady + quiet, no loud)\n"
printf "expected:\tPASS\n"
echo

"$PYTHON" -m hupy.kamilog lp c "TTG" "="
DEMO_REPO_1="$("$PYTHON" "$REPO_ROOT/tests/ttg/prep_repo.py" --scenario "$SCENARIO")"
cd "$DEMO_REPO_1"
"$PYTHON" -m hupy triage_tag_gating || true
cd - >/dev/null
echo

"$PYTHON" -m hupy.kamilog lp c "TTG" "="
DEMO_REPO_2="$("$PYTHON" "$REPO_ROOT/tests/ttg/prep_repo.py" --scenario "$SCENARIO")"
cd "$DEMO_REPO_2"
"$PYTHON" -m hupy triage_tag_gating -v || true
cd - >/dev/null
echo

"$PYTHON" -m hupy.kamilog lp c "TTG" "="
DEMO_REPO_3="$("$PYTHON" "$REPO_ROOT/tests/ttg/prep_repo.py" --scenario "$SCENARIO")"
cd "$DEMO_REPO_3"
"$PYTHON" -m hupy triage_tag_gating -vvv || true
cd - >/dev/null
