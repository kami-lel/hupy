#!/usr/bin/env bash
#
# all-hooks-demo.sh
#
# run every demo in examples/hooks/ in sequence, on the same repo:
# Feature Landing merge (add-user-authentication into develop) through
# `hupy hook pre-commit`, then through `hupy hook prepare-commit-msg`
# (mirroring
# git's own hook order), at default and `-vvv` verbosity
# expected result: both PASS

set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_REPO_ROOT="$(dirname "$(dirname "$_SCRIPT_DIR")")"
_PREP_REPO_PY="$_REPO_ROOT/tests/fixtures/prep_repo.py"


# helpers  #####################################################################


_prepare_demo_repo() {
    local dest
    dest="$(mktemp -d -t hooks_demo_XXXXXX)"
    python3 "$_PREP_REPO_PY" --scenario feature_landing_pass --dest "$dest" \
        > /dev/null
    cp "$dest/.git/MERGE_MSG" "$dest/.git/COMMIT_EDITMSG"
    echo "$dest"
}

_run_pre_commit() {
    local repo_dir="$1"
    shift
    (cd "$repo_dir" && python3 -m hupy hook pre-commit "$@")
}

_run_prepare_commit_msg() {
    local repo_dir="$1"
    shift
    (cd "$repo_dir" && python3 -m hupy hook prepare-commit-msg "$@")
}


# demo  ########################################################################


printf '%s\n' "$(basename "$0")" | python3 -m hupy.kamilog cb0
printf "scenario:\tFeature Landing merge (add-user-authentication into develop)\n"
printf "expected:\tPASS\n"
echo

printf '%s\n' "default" | python3 -m hupy.kamilog cb center "="
demo_repo_1="$(_prepare_demo_repo)"

printf '%s\n' "pre-commit" | python3 -m hupy.kamilog cb center "-"
_run_pre_commit "$demo_repo_1"

printf '%s\n' "prepare-commit-msg" | python3 -m hupy.kamilog cb center "-"
_run_prepare_commit_msg "$demo_repo_1"
echo

printf '%s\n' "w/ -vvv" | python3 -m hupy.kamilog cb center "="
demo_repo_2="$(_prepare_demo_repo)"

printf '%s\n' "pre-commit" | python3 -m hupy.kamilog cb center "-"
_run_pre_commit "$demo_repo_2" -vvv

printf '%s\n' "prepare-commit-msg" | python3 -m hupy.kamilog cb center "-"
_run_prepare_commit_msg "$demo_repo_2" -vvv
