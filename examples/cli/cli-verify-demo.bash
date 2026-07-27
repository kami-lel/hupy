#!/usr/bin/env bash
#
# cli-verify-demo.bash
#
# demo: `hupy verify` across three scenarios, each on its own freshly
# prepared repo (prep_repo.py scenario, then `hupy init --only stubs`):
# 1. clean repo: every check passes
# 2. hook stubs drifted from demand (pre-commit removed, an unused
#    pre-push stub added) — verify only warns, writes/removes nothing
# 3. the config file with its `vg` field dropped (a missing required
#    field) — the config-load check exits nonzero
# expected result: 1 PASS, 2 WARNS but exits 0 (drift reported, hooks
# dir left untouched), 3 FAILS (config)
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
    python3 -m hupy init "$dest" --only stubs > /dev/null
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
echo

printf '%s\n' "clean repo" | python3 -m hupy.kamilog cb center "#"
printf '%s\n' "clean repo: every check passes" \
    | python3 -m hupy.kamilog cg
demo_repo_1="$(_prepare_demo_repo)"

printf '%s\n' "OUTPUT" | python3 -m hupy.kamilog cb center "-"
_run_verify "$demo_repo_1"
echo

printf '%s\n' "drifted hooks" | python3 -m hupy.kamilog cb center "#"
printf '%s\n' "pre-commit stub removed, unused pre-push stub added" \
    | python3 -m hupy.kamilog cg
printf '%s\n' "— verify never writes or removes a file" \
    | python3 -m hupy.kamilog cg
demo_repo_2="$(_prepare_demo_repo)"
hooks_dir_2="$demo_repo_2/.git/hooks"
_drift_hooks_dir "$hooks_dir_2"

printf '%s\n' "OUTPUT" | python3 -m hupy.kamilog cb center "-"
_run_verify "$demo_repo_2"
echo

printf '%s\n' "malformed config" | python3 -m hupy.kamilog cb center "#"
printf '%s\n' "config file's vg field dropped, a missing required field" \
    | python3 -m hupy.kamilog cg
demo_repo_3="$(_prepare_demo_repo)"
_drop_config_field "$demo_repo_3/.hupy.config.jsonc" vg

printf '%s\n' "OUTPUT" | python3 -m hupy.kamilog cb center "-"
_run_verify "$demo_repo_3"
