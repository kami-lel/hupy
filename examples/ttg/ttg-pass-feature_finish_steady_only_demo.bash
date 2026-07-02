#!/usr/bin/env bash
#
# feature_finish_steady_only_demo.bash
#
# demo: Feature Finish merge (feature/x into develop) staging only
# a STEADY "# Todo skip me" comment (no Loud tags)
# expected TTG result: PASSED (Feature Finish only gates the Loud
# tier, so Steady tags are allowed through), exit code 0

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCENARIO="feature_finish_steady_only"

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
