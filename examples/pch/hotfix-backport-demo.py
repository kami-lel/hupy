#!/usr/bin/env python3
"""
hotfix-backport-demo.py

demo: Hotfix Backport merge (hotfix/fix-login-crash into dev), a CBM
merge type that CBM already classifies (see hupy/cbm/commit_type.py)
but that PCH does not yet prepend a header for
expected result: skip (merge type not yet handled by PCH)
"""

import os
import pathlib
import shutil
import sys
import tempfile

_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
_DEMO_BUCKET = "hotfix_backport"

sys.path.insert(0, str(_REPO_ROOT / "tests" / "fixtures"))

from hupy.kamilog import (  # noqa: E402
    gen_comment_banner_centered,
    gen_comment_banner_zero,
    set_logging_level_by_verbosity,
)
from hupy.pch import prepend_commit_header  # noqa: E402
from prep_repo import prepare_demo_repo  # noqa: E402


# helpers  #####################################################################


def _prepare_demo_repo():
    dest_dir = tempfile.mkdtemp(prefix="pch_demo_")
    return prepare_demo_repo(dest_dir, _DEMO_BUCKET)


def _run_pch(repo_dir, verbosity=1):
    set_logging_level_by_verbosity(verbosity)
    cwd = os.getcwd()
    os.chdir(repo_dir)
    try:
        prepend_commit_header(repo_dir)
    finally:
        os.chdir(cwd)


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print(
        "scenario:\tHotfix Backport merge "
        "(hotfix/fix-login-crash into dev)"
    )
    print("expected:\tSKIP (merge type not yet handled by PCH)")
    print()

    print(gen_comment_banner_centered("print out", "#"))
    demo_repo_1 = _prepare_demo_repo()
    editmsg_1 = pathlib.Path(demo_repo_1, ".git", "COMMIT_EDITMSG")
    before_file_1 = pathlib.Path(demo_repo_1, ".git", "COMMIT_EDITMSG.before")
    shutil.copy(pathlib.Path(demo_repo_1, ".git", "MERGE_MSG"), editmsg_1)
    shutil.copy(editmsg_1, before_file_1)

    demo_repo_2 = _prepare_demo_repo()
    editmsg_2 = pathlib.Path(demo_repo_2, ".git", "COMMIT_EDITMSG")
    before_file_2 = pathlib.Path(demo_repo_2, ".git", "COMMIT_EDITMSG.before")
    shutil.copy(pathlib.Path(demo_repo_2, ".git", "MERGE_MSG"), editmsg_2)
    shutil.copy(editmsg_2, before_file_2)

    print(gen_comment_banner_centered("PCH", "="))
    _run_pch(demo_repo_1)
    print()

    print(gen_comment_banner_centered("PCH w/ -vvv", "="))
    _run_pch(demo_repo_2, verbosity=3)
    print()

    print(gen_comment_banner_centered("COMMIT_EDITMSG content", "#"))
    print()

    print(gen_comment_banner_centered("before PCH", "="))
    print(before_file_2.read_text(), end="")
    print()

    print(gen_comment_banner_centered("after PCH", "="))
    print(editmsg_2.read_text(), end="")


if __name__ == "__main__":
    main()
