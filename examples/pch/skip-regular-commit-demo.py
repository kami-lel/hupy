#!/usr/bin/env python3
"""
skip-regular-commit-demo.py

demo: a regular (non-merge) commit stages two files — a.py with a
LOUD "# TODO loud marker" comment and b.py with no tags at all
expected result: skip (PCH only rewrites in-progress merge commits)
"""

import os
import pathlib
import sys
import tempfile

_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
_SCENARIO = "non_merge_commit"

sys.path.insert(0, str(_REPO_ROOT / "tests" / "fixtures"))

from hupy.kamilog import (  # noqa: E402
    gen_comment_banner_centered,
    gen_comment_banner_zero,
    set_logging_level_by_verbosity,
)
from hupy.pch import prepend_commit_header  # noqa: E402
from prep_repo import prepare_repo  # noqa: E402

# helpers  #####################################################################


def _prepare_demo_repo():
    dest_dir = tempfile.mkdtemp(prefix="pch_demo_")
    return prepare_repo(dest_dir, _SCENARIO)


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
    print("scenario:\tNon-merge commit, multiple files (loud + clean)")
    print("expected:\tSKIP")
    print()

    demo_repo_1 = _prepare_demo_repo()
    demo_repo_2 = _prepare_demo_repo()
    print()

    print(gen_comment_banner_centered("PCH", "#"))
    _run_pch(demo_repo_1)
    print()

    print(gen_comment_banner_centered("PCH w/ -vvv", "#"))
    _run_pch(demo_repo_2, verbosity=3)


if __name__ == "__main__":
    main()
