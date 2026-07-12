#!/usr/bin/env bash
#
# cli-verify-demo.bash
#
# demo: `hupy verify` across four scenarios, each on its own freshly
# prepared repo (prep_repo.py scenario, then `hupy init
# --install-hook-stubs`):
# 1. hook stubs drifted from demand (pre-commit removed, an unused
#    pre-push stub added), but no -u — only warns, leaves them as is
# 2. the config file with its `vg` field dropped (a missing required
#    field) — the config-load check raises
# 3. the same drift as case 1 — `-u` adds the missing one and removes
#    the unused one
# 4. the same drift as case 3, plus a tainted already-installed
#    post-commit stub — `-u -f` also refreshes it
# expected result: 1 WARNS (stub drift, no sync), 2 FAIL (config),
# 3 syncs stubs, 4 syncs and refreshes
#
# any -v/-q flags passed to this script are forwarded as-is to
# `hupy verify`

set -uo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_REPO_ROOT="$(dirname "$(dirname "$_SCRIPT_DIR")")"
_PREP_REPO_PY="$_REPO_ROOT/tests/fixtures/prep_repo.py"

_VERBOSITY_ARGS=("$@")


# helpers  #####################################################################


_prepare_demo_repo() {
    local dest
    dest="$(mktemp -d -t verify_demo_XXXXXX)"
    python3 "$_PREP_REPO_PY" --scenario non_merge_commit --dest "$dest" \
        > /dev/null
    python3 -m hupy init "$dest" --install-hook-stubs > /dev/null
    echo "$dest"
}

_run_verify() {
    local repo_dir="$1"
    shift
    python3 -m hupy verify "$repo_dir" "${_VERBOSITY_ARGS[@]}" "$@"
}

_drift_hooks_dir() {
    local hooks_dir="$1"
    rm -f "$hooks_dir/pre-commit"
    printf '#!/usr/bin/env bash\n"python3" -m hupy hook pre-push "$@"\n' \
        > "$hooks_dir/pre-push"
}

_drop_config_field() {
    local config_path="$1" field="$2"
    python3 - "$config_path" "$field" <<'EOF'
import json
import sys

import json5

path, field = sys.argv[1], sys.argv[2]
config = json5.loads(open(path).read())
del config[field]
open(path, "w").write(json.dumps(config, indent=2))
EOF
}


# demo  ########################################################################


printf '%s\n' "$(basename "$0")" | python3 -m hupy.kamilog cb0
printf "scenario:\tfour hupy verify runs, each on its own freshly prepared repo\n"
printf "expected:\t1 WARNS (stub drift, no sync), 2 FAIL (config), 3 syncs stubs, 4 syncs and refreshes\n"
echo

printf '%s\n' "1. pre-commit stub removed, unused pre-push stub added, no -u"
printf '%s\n' "hupy verify" | python3 -m hupy.kamilog cb center "#"
demo_repo_1="$(_prepare_demo_repo)"
hooks_dir_1="$demo_repo_1/.git/hooks"
_drift_hooks_dir "$hooks_dir_1"

printf '%s\n' "stubs before" | python3 -m hupy.kamilog cb center "="
ls "$hooks_dir_1" | grep -v '\.sample$'
echo

printf '%s\n' "OUTPUT" | python3 -m hupy.kamilog cb center "="
_run_verify "$demo_repo_1"
echo

printf '%s\n' "stubs after" | python3 -m hupy.kamilog cb center "="
ls "$hooks_dir_1" | grep -v '\.sample$'
echo

printf '%s\n' "2. config file's vg field dropped, a missing required field"
printf '%s\n' "hupy verify" | python3 -m hupy.kamilog cb center "#"
demo_repo_2="$(_prepare_demo_repo)"
_drop_config_field "$demo_repo_2/.hupy.config.jsonc" vg

printf '%s\n' "OUTPUT" | python3 -m hupy.kamilog cb center "="
_run_verify "$demo_repo_2"
echo

printf '%s\n' "3. pre-commit stub removed, unused pre-push stub added"
printf '%s\n' "hupy verify -u" | python3 -m hupy.kamilog cb center "#"
demo_repo_3="$(_prepare_demo_repo)"
hooks_dir_3="$demo_repo_3/.git/hooks"
_drift_hooks_dir "$hooks_dir_3"

printf '%s\n' "stubs before" | python3 -m hupy.kamilog cb center "="
ls "$hooks_dir_3" | grep -v '\.sample$'
echo

printf '%s\n' "OUTPUT" | python3 -m hupy.kamilog cb center "="
_run_verify "$demo_repo_3" -u
echo

printf '%s\n' "stubs after" | python3 -m hupy.kamilog cb center "="
ls "$hooks_dir_3" | grep -v '\.sample$'
echo

printf '%s\n' "4. same drift as case 3, plus a tainted post-commit stub"
printf '%s\n' "hupy verify -u -f" | python3 -m hupy.kamilog cb center "#"
demo_repo_4="$(_prepare_demo_repo)"
hooks_dir_4="$demo_repo_4/.git/hooks"
_drift_hooks_dir "$hooks_dir_4"
printf '\n# stale marker\n' >> "$hooks_dir_4/post-commit"

printf '%s\n' "stubs before" | python3 -m hupy.kamilog cb center "="
cat "$hooks_dir_4/post-commit"
echo

printf '%s\n' "OUTPUT" | python3 -m hupy.kamilog cb center "="
_run_verify "$demo_repo_4" -u -f
echo

printf '%s\n' "stubs after" | python3 -m hupy.kamilog cb center "="
cat "$hooks_dir_4/post-commit"
