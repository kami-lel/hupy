#!/usr/bin/env bash
#
# ttg-fail-version_release_demo.bash
#
# demo: Version Release merge (develop into main) staging three
# files — a.py with 1 LOUD tag, b.py with 1 LOUD and 2 STEADY tags
# (multiple TT in a single file), and c.py with a QUIET tag
# expected result: fail (Version Release gates Loud and Steady tiers;
# both a.py and b.py's gating tags are reported, c.py's Quiet tag is not)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCENARIO="version_release_fail"

if [ -x "$REPO_ROOT/venv/bin/python3" ]; then
    PYTHON="$REPO_ROOT/venv/bin/python3"
else
    PYTHON="python3"
    export PYTHONPATH="$REPO_ROOT:${PYTHONPATH:-}"
fi

DEMO_SCRIPT="$(basename "${BASH_SOURCE[0]}")"

"$PYTHON" -m hupy.kamilog lp c "$DEMO_SCRIPT" "#"
printf "scenario:\tVersion Release, multiple files with multiple gating TT\n"
printf "expected:\tFAIL\n"
printf "reason:\tLoud/Steady tags in both a.py and b.py (multiple files, multiple TT)\n"
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
