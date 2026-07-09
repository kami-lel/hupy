#!/usr/bin/env bash
#
# prepare-commit-msg-demo.sh
#
# demo: Version Release merge (develop into main) with the
# in-progress merge message copied into COMMIT_EDITMSG (mirroring
# what git itself does before invoking the commit-msg hook), driven
# through the actual `hupy prepare-commit-msg` CLI
# expected result: header prepended to COMMIT_EDITMSG

set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_REPO_ROOT="$(dirname "$_SCRIPT_DIR")"
_BUNDLE="$_REPO_ROOT/tests/testee/default_repo.bundle"


# helpers  #####################################################################


# FIXME prepare demo to py side


_prepare_demo_repo() {
    local dest
    dest="$(mktemp -d -t pch_demo_XXXXXX)"
    git clone -q --branch main "$_BUNDLE" "$dest" > /dev/null 2>&1
    (
        cd "$dest"
        git checkout -q -b dev
        echo "# todo quiet marker" > a.py
        git add a.py
        git commit -q -m "add a.py" > /dev/null
        echo "# todo quiet marker" > b.py
        git add b.py
        git commit -q -m "add b.py" > /dev/null
        git checkout -q main
        git merge -q --no-commit --no-ff dev > /dev/null 2>&1
    )
    echo "$dest"
}

_run_pch() {
    local repo_dir="$1"
    shift
    (cd "$repo_dir" && python3 -m hupy prepare-commit-msg "$@")
}


# demo  ########################################################################


printf '%s\n' "$(basename "$0")" | python3 -m hupy.kamilog cb0
printf "scenario:\tVersion Release merge (develop into main)\n"
printf "expected:\tPASS, header prepended to COMMIT_EDITMSG\n"
echo

printf '%s\n' "print out" | python3 -m hupy.kamilog cb center "#"
demo_repo_1="$(_prepare_demo_repo)"
editmsg_1="$demo_repo_1/.git/COMMIT_EDITMSG"
before_file_1="$demo_repo_1/.git/COMMIT_EDITMSG.before"
cp "$demo_repo_1/.git/MERGE_MSG" "$editmsg_1"
cp "$editmsg_1" "$before_file_1"

demo_repo_2="$(_prepare_demo_repo)"
editmsg_2="$demo_repo_2/.git/COMMIT_EDITMSG"
before_file_2="$demo_repo_2/.git/COMMIT_EDITMSG.before"
cp "$demo_repo_2/.git/MERGE_MSG" "$editmsg_2"
cp "$editmsg_2" "$before_file_2"

printf '%s\n' "PCH" | python3 -m hupy.kamilog cb center "="
_run_pch "$demo_repo_1"
echo

printf '%s\n' "PCH w/ -vvv" | python3 -m hupy.kamilog cb center "="
_run_pch "$demo_repo_2" -vvv
echo

printf '%s\n' "COMMIT_EDITMSG content" | python3 -m hupy.kamilog cb center "#"
echo

printf '%s\n' "before PCH" | python3 -m hupy.kamilog cb center "="
cat "$before_file_2"
echo

printf '%s\n' "after PCH" | python3 -m hupy.kamilog cb center "="
cat "$editmsg_2"
