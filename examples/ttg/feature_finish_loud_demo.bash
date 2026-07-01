#!/usr/bin/env bash
#
# feature_finish_loud_demo.bash
#
# demo: Feature Finish merge (feature/x into develop) staging a
# LOUD "# TODO gate me" comment
# expected TTG result: BLOCKED (Feature Finish gates the Loud tier),
# exit code 1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCENARIO="feature_finish_loud"

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
echo "== TTG exit code: $EXIT_CODE (expected: 1, commit blocked) =="
