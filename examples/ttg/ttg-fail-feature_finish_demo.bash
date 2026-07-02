#!/usr/bin/env bash
#
# ttg-fail-feature_finish_demo.bash
#
# demo: Feature Finish merge (feature/x into develop) staging three
# files — a.py with a LOUD "# TODO loud marker" comment, b.py with
# no tags, and c.py with a STEADY "# Todo steady marker" comment
# expected result: fail (Feature Finish gates the Loud tier; only
# a.py's Loud tag is reported, c.py's Steady tag is not)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCENARIO="feature_finish_fail"

if [ -x "$REPO_ROOT/venv/bin/python3" ]; then
    PYTHON="$REPO_ROOT/venv/bin/python3"
else
    PYTHON="python3"
    export PYTHONPATH="$REPO_ROOT:${PYTHONPATH:-}"
fi

DEMO_SCRIPT="$(basename "${BASH_SOURCE[0]}")"

"$PYTHON" -m hupy.kamilog lp c "$DEMO_SCRIPT" "#"
printf "scenario:\tFeature Finish, multiple files (loud + clean + steady)\n"
printf "expected:\tFAIL\n"
printf "reason:\tLoud \"# TODO loud marker\" comment in a.py\n"
echo

"$PYTHON" -m hupy.kamilog lp c "TTG" "="
DEMO_REPO_1="$("$PYTHON" "$REPO_ROOT/tests/ttg/prep_repo.py" --scenario "$SCENARIO")"
cd "$DEMO_REPO_1"
"$PYTHON" -m hupy triage_tag_gating || true
cd - >/dev/null
echo

"$PYTHON" -m hupy.kamilog lp c "TTG w/ -v" "="
DEMO_REPO_2="$("$PYTHON" "$REPO_ROOT/tests/ttg/prep_repo.py" --scenario "$SCENARIO")"
cd "$DEMO_REPO_2"
"$PYTHON" -m hupy triage_tag_gating -v || true
cd - >/dev/null
echo

"$PYTHON" -m hupy.kamilog lp c "TTG w/ -vvv" "="
DEMO_REPO_3="$("$PYTHON" "$REPO_ROOT/tests/ttg/prep_repo.py" --scenario "$SCENARIO")"
cd "$DEMO_REPO_3"
"$PYTHON" -m hupy triage_tag_gating -vvv || true
cd - >/dev/null
