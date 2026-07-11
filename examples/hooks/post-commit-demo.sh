#!/usr/bin/env bash
#
# post-commit-demo.sh
#
# demo: a plain non-merge commit, with `bdc` and `ttg` flagged for
# one-time skip via `hupy skip-once` beforehand, driven through the
# actual `hupy hook post-commit` CLI
# expected result: `skip_once` cleared from `hupy-state.json`

set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_REPO_ROOT="$(dirname "$(dirname "$_SCRIPT_DIR")")"
_PREP_REPO_PY="$_REPO_ROOT/tests/fixtures/prep_repo.py"


# helpers  #####################################################################


_prepare_demo_repo() {
    local dest
    dest="$(mktemp -d -t post_commit_demo_XXXXXX)"
    python3 "$_PREP_REPO_PY" --scenario non_merge_commit --dest "$dest" \
        > /dev/null
    echo "$dest"
}

_run_skip_once() {
    local repo_dir="$1"
    shift
    (cd "$repo_dir" && python3 -m hupy skip-once "$@")
}

_run_post_commit() {
    local repo_dir="$1"
    shift
    (cd "$repo_dir" && python3 -m hupy hook post-commit "$@")
}


# demo  ########################################################################


printf '%s\n' "$(basename "$0")" | python3 -m hupy.kamilog cb0
printf "scenario:\tplain non-merge commit, bdc+ttg flagged for one-time skip\n"
printf "expected:\tskip_once cleared from hupy-state.json\n"
echo

demo_repo="$(_prepare_demo_repo)"
state_file="$demo_repo/.git/hupy-state.json"

printf '%s\n' "skip-once" | python3 -m hupy.kamilog cb center "#"
_run_skip_once "$demo_repo" bdc ttg
echo

printf '%s\n' "hupy-state.json before post-commit" | python3 -m hupy.kamilog cb center "="
cat "$state_file"
echo

printf '%s\n' "post-commit" | python3 -m hupy.kamilog cb center "#"
_run_post_commit "$demo_repo"
echo

printf '%s\n' "hupy-state.json after post-commit" | python3 -m hupy.kamilog cb center "="
cat "$state_file"
