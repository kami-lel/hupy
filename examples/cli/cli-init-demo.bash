#!/usr/bin/env bash
#
# cli-init-demo.bash
#
# demo: `hupy init` against a freshly created, empty git repository,
# run through three sections in sequence on the same repo:
# 1. a first-time init, installing hook stubs and the config file
# 2. a re-init with --create-config-file alone, hitting the
#    now-existing config file and letting the conflict raise
# 3. a re-init with --install-hook-stubs -f, replacing the
#    just-installed stubs
# expected result: section 1 PASS, section 2 FAIL (config conflict),
# section 3 PASS
#
# any -v/-q flags passed to this script are forwarded as-is to every
# `hupy init` call

set -uo pipefail

_VERBOSITY_ARGS=("$@")


# helpers  #####################################################################


_prepare_empty_repo() {
    local dest
    dest="$(mktemp -d -t init_demo_XXXXXX)"
    git init --quiet "$dest"
    echo "$dest"
}

_run_hupy_init() {
    local repo_dir="$1"
    shift
    python3 -m hupy init "$repo_dir" "${_VERBOSITY_ARGS[@]}" "$@"
}


# demo  ########################################################################


printf '%s\n' "$(basename "$0")" | python3 -m hupy.kamilog cb0
printf "scenario:\tfirst-time init on a freshly created, empty repository\n"
printf "expected:\tsection 1 PASS, section 2 FAIL (config conflict), section 3 PASS\n"
echo

demo_repo="$(_prepare_empty_repo)"

printf '%s\n' "first-time init on the empty repo"
printf '%s\n' "hupy init" | python3 -m hupy.kamilog cb center "#"
_run_hupy_init "$demo_repo"
echo

printf '%s\n' "config file already exists from section 1, so this raises"
printf '%s\n' "hupy init --create-config-file" \
    | python3 -m hupy.kamilog cb center "#"
_run_hupy_init "$demo_repo" --create-config-file
echo

printf '%s\n' "-f replaces the hook stubs installed in section 1"
printf '%s\n' "hupy init --install-hook-stubs -f" \
    | python3 -m hupy.kamilog cb center "#"
_run_hupy_init "$demo_repo" --install-hook-stubs -f
