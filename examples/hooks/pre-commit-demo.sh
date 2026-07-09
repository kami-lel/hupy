#!/usr/bin/env bash
#
# pre-commit-demo.sh
#
# demo: Feature Finish merge (add-user-authentication into develop)
# staging two files with no Loud triage tags — a.py (Steady) and
# b.py (Quiet) — driven through the actual `hupy pre-commit` CLI
# expected result: PASS, triage tag gating does not block the commit

set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_REPO_ROOT="$(dirname "$(dirname "$_SCRIPT_DIR")")"
_PREP_REPO_PY="$_REPO_ROOT/tests/fixtures/prep_repo.py"


# helpers  #####################################################################


_prepare_demo_repo() {
    local dest
    dest="$(mktemp -d -t ttg_demo_XXXXXX)"
    python3 "$_PREP_REPO_PY" --scenario feature_finish_pass --dest "$dest" \
        > /dev/null
    echo "$dest"
}

_run_ttg() {
    local repo_dir="$1"
    shift
    (cd "$repo_dir" && python3 -m hupy pre-commit "$@")
}


# demo  ########################################################################


printf '%s\n' "$(basename "$0")" | python3 -m hupy.kamilog cb0
printf "scenario:\tFeature Finish, multiple files (steady + quiet, no loud)\n"
printf "expected:\tPASS\n"
echo

printf '%s\n' "pre-commit" | python3 -m hupy.kamilog cb center "#"
demo_repo_1="$(_prepare_demo_repo)"
_run_ttg "$demo_repo_1"
echo

printf '%s\n' "pre-commit w/ -vvv" | python3 -m hupy.kamilog cb center "#"
demo_repo_2="$(_prepare_demo_repo)"
_run_ttg "$demo_repo_2" -vvv
