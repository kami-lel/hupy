#!/usr/bin/env bash
#
# pre-commit-demo.sh
#
# demo: Feature Landing merge (add-user-authentication into develop)
# staging two files with no Loud triage tags — a.py (Steady) and
# b.py (Quiet) — driven through the actual `hupy hook pre-commit` CLI
# expected result: PASS, triage tag gating does not block the commit
#
# any -v/-q flags passed to this script are forwarded as-is to
# `hupy hook pre-commit`

set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_REPO_ROOT="$(dirname "$(dirname "$_SCRIPT_DIR")")"
_PREP_REPO_PY="$_REPO_ROOT/tests/fixtures/prep_repo.py"

_VERBOSITY_ARGS=("$@")


# helpers  #####################################################################


_prepare_demo_repo() {
    local dest
    dest="$(mktemp -d -t ttg_demo_XXXXXX)"
    python3 "$_PREP_REPO_PY" --scenario feature_landing_pass --dest "$dest" \
        > /dev/null
    echo "$dest"
}

_run_ttg() {
    local repo_dir="$1"
    shift
    (cd "$repo_dir" && python3 -m hupy hook pre-commit "${_VERBOSITY_ARGS[@]}" "$@")
}


# demo  ########################################################################


printf '%s\n' "$(basename "$0")" | python3 -m hupy.kamilog cb0
printf "scenario:\tFeature Landing, multiple files (steady + quiet, no loud)\n"
printf "expected:\tPASS\n"
echo

printf '%s\n' "pre-commit" | python3 -m hupy.kamilog cb center "#"
demo_repo="$(_prepare_demo_repo)"
_run_ttg "$demo_repo"
