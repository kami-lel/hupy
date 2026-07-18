#!/usr/bin/env bash
#
# patch-apply-chain-demo.sh
#
# run the Patch Apply Chain in sequence, on the same repo: a plain
# non-merge commit through `hupy hook applypatch-msg`, then through
# `hupy hook pre-applypatch`, then through
# `hupy hook post-applypatch` (mirroring git's own hook order for
# `git am`)
# expected result: all three PASS (none has a dedicated feature wired
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
    dest="$(mktemp -d -t patch_apply_demo_XXXXXX)"
    python3 "$_PREP_REPO_PY" --scenario non_merge_commit --dest "$dest" \
        > /dev/null
    echo "$dest"
}

_set_verbosity() {
    local repo_dir="$1"
    (cd "$repo_dir" && python3 -m hupy set verbosity "${_VERBOSITY_ARGS[@]}")
}

_run_applypatch_msg() {
    local repo_dir="$1"
    (cd "$repo_dir" && python3 -m hupy hook applypatch-msg)
}

_run_pre_applypatch() {
    local repo_dir="$1"
    (cd "$repo_dir" && python3 -m hupy hook pre-applypatch)
}

_run_post_applypatch() {
    local repo_dir="$1"
    (cd "$repo_dir" && python3 -m hupy hook post-applypatch)
}


# demo  ########################################################################


printf '%s\n' "$(basename "$0")" | python3 -m hupy.kamilog cb0
printf "scenario:\tplain non-merge commit, applied as a patch\n"
printf "expected:\tPASS\n"
echo

demo_repo="$(_prepare_demo_repo)"
_set_verbosity "$demo_repo"

printf '%s\n' "applypatch-msg" | python3 -m hupy.kamilog cb center "-"
_run_applypatch_msg "$demo_repo"

printf '%s\n' "pre-applypatch" | python3 -m hupy.kamilog cb center "-"
_run_pre_applypatch "$demo_repo"

printf '%s\n' "post-applypatch" | python3 -m hupy.kamilog cb center "-"
_run_post_applypatch "$demo_repo"
