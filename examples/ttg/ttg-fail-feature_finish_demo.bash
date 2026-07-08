#!/usr/bin/env bash
#
# ttg-fail-feature_finish_demo.bash
#
# demo: Feature Finish merge (add-user-authentication into develop) staging three
# files — a.py with 1 LOUD tag, b.py with 2 LOUD tags (multiple TT
# in a single file), and c.py with a QUIET tag
# expected result: fail (Feature Finish gates the Loud tier; both
# a.py and b.py's Loud tags are reported, c.py's Quiet tag is not)

# BUG fix bad demos

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

printf "%s\n" "$DEMO_SCRIPT" | "$PYTHON" -m hupy.kamilog cb0
printf "scenario:\tFeature Finish, multiple files with multiple Loud TT\n"
printf "expected:\tFAIL\n"
printf "reason:\tLoud tags in both a.py and b.py (multiple files, multiple TT)\n"
echo

printf "TTG" | "$PYTHON" -m hupy.kamilog cb c "#"
DEMO_REPO_1="$("$PYTHON" "$REPO_ROOT/tests/ttg/prep_repo.py" --scenario "$SCENARIO")"
cd "$DEMO_REPO_1"
"$PYTHON" -m hupy pre-commit triage-tag-gating || true
cd - >/dev/null
echo

printf "TTG w/ -v" | "$PYTHON" -m hupy.kamilog cb c "#"
DEMO_REPO_2="$("$PYTHON" "$REPO_ROOT/tests/ttg/prep_repo.py" --scenario "$SCENARIO")"
cd "$DEMO_REPO_2"
"$PYTHON" -m hupy pre-commit triage-tag-gating -v || true
cd - >/dev/null
echo

printf "TTG w/ -vvv" | "$PYTHON" -m hupy.kamilog cb c "#"
DEMO_REPO_3="$("$PYTHON" "$REPO_ROOT/tests/ttg/prep_repo.py" --scenario "$SCENARIO")"
cd "$DEMO_REPO_3"
"$PYTHON" -m hupy pre-commit triage-tag-gating -vvv || true
cd - >/dev/null
