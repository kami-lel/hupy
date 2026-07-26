#!/usr/bin/env bash
#
# cli-init-demo.bash
#
# demo: `hupy init` against a freshly created, empty git repository,
# run through four sections in sequence on the same repo:
# 1. a first-time init, installing hook stubs and the config file
# 2. a repeat init with --only config alone: the file is already
#    correct, so it's left untouched (still logs that it did so)
# 3. a stub is hand-edited (drifted) and another repo hook is added
#    (no longer demanded); a plain re-init reports both but touches
#    neither
# 4. the same drift, resolved with -f (rewrites the drifted stub)
#    and --prune (removes the unused one)
# expected result: every section PASS; init never aborts
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
echo

demo_repo="$(_prepare_empty_repo)"
hooks_dir="$demo_repo/.git/hooks"

printf '%s\n' "hupy init" | python3 -m hupy.kamilog cb center "#"
printf '%s\n' "first-time init on the empty repo"

printf '%s\n' "OUTPUT" | python3 -m hupy.kamilog cb center "-"
_run_hupy_init "$demo_repo"
echo

printf '%s\n' "hupy init --only config" | python3 -m hupy.kamilog cb center "#"
printf '%s\n' "repeat init, config-only: already correct, left untouched"

printf '%s\n' "OUTPUT" | python3 -m hupy.kamilog cb center "-"
_run_hupy_init "$demo_repo" --only config
echo

printf '%s\n' "hupy init" | python3 -m hupy.kamilog cb center "#"
printf '%s\n' "pre-commit hand-edited (drifted), unused pre-push added"
printf '\n# hand-edited\n' >> "$hooks_dir/pre-commit"
printf '#!/usr/bin/env bash\nexec "python3" -m hupy hook pre-push "$@"\n' \
    > "$hooks_dir/pre-push"

printf '%s\n' "OUTPUT" | python3 -m hupy.kamilog cb center "-"
_run_hupy_init "$demo_repo"
echo

printf '%s\n' "hupy init -f --prune" | python3 -m hupy.kamilog cb center "#"
printf '%s\n' "same drift, resolved with -f --prune"

printf '%s\n' "OUTPUT" | python3 -m hupy.kamilog cb center "-"
_run_hupy_init "$demo_repo" -f --prune
echo

printf '%s\n' "pre-commit rewritten, pre-push removed"
printf '%s\n' "stubs after" | python3 -m hupy.kamilog cb center "-"
for entry in "$hooks_dir"/*; do
    case "$entry" in
        *.sample) continue ;;
    esac
    printf '%s\n' "$(basename "$entry")"
done
