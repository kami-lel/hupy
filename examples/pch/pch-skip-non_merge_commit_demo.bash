#!/usr/bin/env bash
#
# pch-skip-non_merge_commit_demo.bash
#
# demo: a regular (non-merge) commit stages two files — a.py with a
# LOUD "# TODO loud marker" comment and b.py with no tags at all
# expected result: skip (PCH only rewrites in-progress merge commits)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCENARIO="non_merge_commit"

if [ -x "$REPO_ROOT/venv/bin/python3" ]; then
    PYTHON="$REPO_ROOT/venv/bin/python3"
else
    PYTHON="python3"
    export PYTHONPATH="$REPO_ROOT:${PYTHONPATH:-}"
fi

DEMO_SCRIPT="$(basename "${BASH_SOURCE[0]}")"

printf "%s\n" "$DEMO_SCRIPT" | "$PYTHON" -m hupy.kamilog cb0
printf "scenario:\tNon-merge commit, multiple files (loud + clean)\n"
printf "expected:\tSKIP\n"
echo

printf "PCH" | "$PYTHON" -m hupy.kamilog cb c "#"
DEMO_REPO_1="$("$PYTHON" "$REPO_ROOT/tests/ttg/prep_repo.py" --scenario "$SCENARIO")"
cd "$DEMO_REPO_1"
"$PYTHON" -m hupy prepare-commit-msg prepend-commit-header || true
cd - >/dev/null
echo

printf "PCH w/ -v" | "$PYTHON" -m hupy.kamilog cb c "#"
DEMO_REPO_2="$("$PYTHON" "$REPO_ROOT/tests/ttg/prep_repo.py" --scenario "$SCENARIO")"
cd "$DEMO_REPO_2"
"$PYTHON" -m hupy prepare-commit-msg prepend-commit-header -v || true
cd - >/dev/null
echo

printf "PCH w/ -vvv" | "$PYTHON" -m hupy.kamilog cb c "#"
DEMO_REPO_3="$("$PYTHON" "$REPO_ROOT/tests/ttg/prep_repo.py" --scenario "$SCENARIO")"
cd "$DEMO_REPO_3"
"$PYTHON" -m hupy prepare-commit-msg prepend-commit-header -vvv || true
cd - >/dev/null
