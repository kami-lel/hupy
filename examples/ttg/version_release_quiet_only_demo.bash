#!/usr/bin/env bash
#
# version_release_quiet_only_demo.bash
#
# demo: Version Release merge (develop into main) staging only a
# QUIET "# todo skip me" comment (no Loud or Steady tags)
# expected TTG result: PASSED (Quiet tier tags are never gated),
# exit code 0

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCENARIO="version_release_quiet_only"

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
