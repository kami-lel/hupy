#!/usr/bin/env bash
#
# commit-chain-demo.sh
#
# run every demo in examples/hooks/ in sequence, on the same repo:
# Feature Landing merge (add-user-authentication into develop) through
# `hupy hook pre-commit`, then through `hupy hook prepare-commit-msg`,
# then through `hupy hook commit-msg`, then through
# `hupy hook post-commit` (mirroring git's own hook order)
# expected result: all four PASS
#
# any -v/-q flags passed to this script are forwarded to
# `hupy set verbosity` to configure the repo once up front

set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_REPO_ROOT="$(dirname "$(dirname "$_SCRIPT_DIR")")"
_PREP_REPO_PY="$_REPO_ROOT/tests/fixtures/prep_repo.py"

_VERBOSITY_ARGS=("$@")


# TODO write all chain demos


# auxiliaries  #################################################################

_prepare_demo_repo() {
    local dest
    dest="$(mktemp -d -t hooks_demo_XXXXXX)"
    python3 "$_PREP_REPO_PY" --scenario feature_landing_pass --dest "$dest" \
        > /dev/null
    cp "$dest/.git/MERGE_MSG" "$dest/.git/COMMIT_EDITMSG"
    echo "$dest"
}

_set_verbosity() {
    local repo_dir="$1"
    (cd "$repo_dir" && python3 -m hupy set verbosity "${_VERBOSITY_ARGS[@]}")
}

_run_pre_commit() {
    local repo_dir="$1"
    (cd "$repo_dir" && python3 -m hupy hook pre-commit)
}

_run_prepare_commit_msg() {
    local repo_dir="$1"
    (cd "$repo_dir" && python3 -m hupy hook prepare-commit-msg)
}

_run_commit_msg() {
    local repo_dir="$1"
    (cd "$repo_dir" && python3 -m hupy hook commit-msg)
}

_run_post_commit() {
    local repo_dir="$1"
    (cd "$repo_dir" && python3 -m hupy hook post-commit)
}


# demo  ########################################################################


printf '%s\n' "$(basename "$0")" | python3 -m hupy.kamilog cb0
printf "scenario:\tFeature Landing merge (add-user-authentication into develop)\n"
printf "expected:\tPASS\n"
echo

demo_repo="$(_prepare_demo_repo)"
_set_verbosity "$demo_repo"

printf '%s\n' "pre-commit" | python3 -m hupy.kamilog cb center "-"
_run_pre_commit "$demo_repo"

printf '%s\n' "prepare-commit-msg" | python3 -m hupy.kamilog cb center "-"
_run_prepare_commit_msg "$demo_repo"

printf '%s\n' "commit-msg" | python3 -m hupy.kamilog cb center "-"
_run_commit_msg "$demo_repo"

printf '%s\n' "post-commit" | python3 -m hupy.kamilog cb center "-"
_run_post_commit "$demo_repo"
