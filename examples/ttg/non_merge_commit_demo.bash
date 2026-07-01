#!/usr/bin/env bash
#
# non_merge_commit_demo.bash
#
# demo: a regular (non-merge) commit stages a Loud TODO
# expected TTG result: SKIPPED (not a Feature Finish/Version Release
# merge, so gating never inspects the staged content), exit code 0

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

echo "== preparing demo repo (scenario: $SCENARIO) =="
DEMO_REPO="$("$PYTHON" "$REPO_ROOT/tests/ttg/prep_repo.py" --scenario "$SCENARIO")"
echo "demo repo: $DEMO_REPO"
echo

echo "== running: python -m hupy triage_tag_gating -vvv =="
cd "$DEMO_REPO"
if "$PYTHON" -m hupy triage_tag_gating -vvv; then
    EXIT_CODE=0
else
    EXIT_CODE=$?
fi

echo
echo "== TTG exit code: $EXIT_CODE (expected: 0, commit allowed) =="
