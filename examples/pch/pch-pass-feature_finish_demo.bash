#!/usr/bin/env bash
#
# pch-pass-feature_finish_demo.bash
#
# demo: Feature Finish merge (add-user-authentication into develop) with the
# in-progress merge message copied into COMMIT_EDITMSG (mirroring
# what git itself does before invoking the commit-msg hook)
# expected result: header prepended to COMMIT_EDITMSG

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

printf "%s\n" "$DEMO_SCRIPT" | "$PYTHON" -m hupy.kamilog cb0
printf "scenario:\tFeature Finish merge (add-user-authentication into develop)\n"
printf "expected:\tPASS, header prepended to COMMIT_EDITMSG\n"
echo

printf "print out" | "$PYTHON" -m hupy.kamilog cb c "#"
echo

printf "PCH" | "$PYTHON" -m hupy.kamilog cb c "="
DEMO_REPO_1="$("$PYTHON" "$REPO_ROOT/tests/ttg/prep_repo.py" --scenario "$SCENARIO")"
BEFORE_FILE_1="$DEMO_REPO_1/.git/COMMIT_EDITMSG.before"
cp "$DEMO_REPO_1/.git/MERGE_MSG" "$DEMO_REPO_1/.git/COMMIT_EDITMSG"
cp "$DEMO_REPO_1/.git/COMMIT_EDITMSG" "$BEFORE_FILE_1"
cd "$DEMO_REPO_1"
"$PYTHON" -m hupy prepare-commit-msg prepend-commit-header || true
cd - >/dev/null
echo

printf "PCH w/ -v" | "$PYTHON" -m hupy.kamilog cb c "="
DEMO_REPO_2="$("$PYTHON" "$REPO_ROOT/tests/ttg/prep_repo.py" --scenario "$SCENARIO")"
cp "$DEMO_REPO_2/.git/MERGE_MSG" "$DEMO_REPO_2/.git/COMMIT_EDITMSG"
cd "$DEMO_REPO_2"
"$PYTHON" -m hupy prepare-commit-msg prepend-commit-header -v || true
cd - >/dev/null
echo

printf "PCH w/ -vvv" | "$PYTHON" -m hupy.kamilog cb c "="
DEMO_REPO_3="$("$PYTHON" "$REPO_ROOT/tests/ttg/prep_repo.py" --scenario "$SCENARIO")"
BEFORE_FILE_3="$DEMO_REPO_3/.git/COMMIT_EDITMSG.before"
cp "$DEMO_REPO_3/.git/MERGE_MSG" "$DEMO_REPO_3/.git/COMMIT_EDITMSG"
cp "$DEMO_REPO_3/.git/COMMIT_EDITMSG" "$BEFORE_FILE_3"
cd "$DEMO_REPO_3"
"$PYTHON" -m hupy prepare-commit-msg prepend-commit-header -vvv || true
cd - >/dev/null
echo

printf "COMMIT_EDITMSG content" | "$PYTHON" -m hupy.kamilog cb c "#"
echo

printf "before PCH" | "$PYTHON" -m hupy.kamilog cb c "="
cat "$BEFORE_FILE_3"
echo

printf "after PCH" | "$PYTHON" -m hupy.kamilog cb c "="
cat "$DEMO_REPO_3/.git/COMMIT_EDITMSG"
