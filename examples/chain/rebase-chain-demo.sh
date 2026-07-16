#!/usr/bin/env bash
#
# rebase-chain-demo.sh
#
# run the Rebase Chain in sequence, on the same repo: a plain
# non-merge commit through `hupy hook pre-rebase`, then through
# `hupy hook post-rewrite` (mirroring git's own hook order for
# `git rebase`)
# expected result: both PASS (neither has a dedicated feature wired
# in yet, per chain_doc.md)
#
# any -v/-q flags passed to this script are forwarded to
# `hupy set verbosity` to configure the repo once up front

set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_REPO_ROOT="$(dirname "$(dirname "$_SCRIPT_DIR")")"
_PREP_REPO_PY="$_REPO_ROOT/tests/fixtures/prep_repo.py"

_VERBOSITY_ARGS=("$@")


# auxiliaries  #################################################################

_prepare_demo_repo() {
    local dest
    dest="$(mktemp -d -t rebase_demo_XXXXXX)"
    python3 "$_PREP_REPO_PY" --scenario non_merge_commit --dest "$dest" \
        > /dev/null
    echo "$dest"
}

_set_verbosity() {
    local repo_dir="$1"
    (cd "$repo_dir" && python3 -m hupy set verbosity "${_VERBOSITY_ARGS[@]}")
}

_run_pre_rebase() {
    local repo_dir="$1"
    (cd "$repo_dir" && python3 -m hupy hook pre-rebase)
}

_run_post_rewrite() {
    local repo_dir="$1"
    (cd "$repo_dir" && python3 -m hupy hook post-rewrite)
}


# demo  ########################################################################


printf '%s\n' "$(basename "$0")" | python3 -m hupy.kamilog cb0
printf "scenario:\tplain non-merge commit, rebased\n"
printf "expected:\tPASS\n"
echo

demo_repo="$(_prepare_demo_repo)"
_set_verbosity "$demo_repo"

printf '%s\n' "pre-rebase" | python3 -m hupy.kamilog cb center "-"
_run_pre_rebase "$demo_repo"

printf '%s\n' "post-rewrite" | python3 -m hupy.kamilog cb center "-"
_run_post_rewrite "$demo_repo"
