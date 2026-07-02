#!/usr/bin/env bash
#
# irrelevant_merge_demo.bash
#
# demo: merging two unrelated, non-protected branches (hotfix into
# release), staging a Loud fix comment along the way
# expected TTG result: SKIPPED (source/target branches don't match
# the Feature Finish or Version Release pattern), exit code 0

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCENARIO="irrelevant_merge"

if [ -x "$REPO_ROOT/venv/bin/python3" ]; then
    PYTHON="$REPO_ROOT/venv/bin/python3"
else
    PYTHON="python3"
    export PYTHONPATH="$REPO_ROOT:${PYTHONPATH:-}"
fi

"$PYTHON" -m hupy.kamilog lp c \
  "preparing demo repo (scenario: $SCENARIO)" "#"
DEMO_REPO="$("$PYTHON" "$REPO_ROOT/tests/ttg/prep_repo.py" --scenario "$SCENARIO")"
"$PYTHON" -m hupy.kamilog lp l "demo repo: $DEMO_REPO" "-"
echo

"$PYTHON" -m hupy.kamilog lp c \
  "running: python -m hupy triage_tag_gating -vvv" "-"
cd "$DEMO_REPO"
if "$PYTHON" -m hupy triage_tag_gating -vvv; then
    EXIT_CODE=0
else
    EXIT_CODE=$?
fi

echo
"$PYTHON" -m hupy.kamilog lp c \
  "TTG exit code: $EXIT_CODE (expected: 0, commit allowed)" "-"
