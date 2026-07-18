#!/usr/bin/env python3
"""
fail-direct-commit-to-main-demo.py

demo: a regular (non-merge) commit made directly on main, staging
one plain file
expected result: fail (main is protected by default and this commit
carries no merge type)
"""

import pathlib

from hupy.kamilog import (
    gen_comment_banner_centered,
    gen_comment_banner_zero,
)
from __init__ import prepare_demo_repo_by_bucket, run_bdc

_BUCKET = "non_merge_commit"
_FILES = {"a.py": "tt_none.py"}


# auxiliaries  #################################################################


def _prepare_demo_repo():
    return prepare_demo_repo_by_bucket(_BUCKET, _FILES)


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print("scenario:\tNon-merge commit staged directly on main")
    print("expected:\tFAIL")
    print("reason:\tmain is protected by default, and this commit is not a merge")
    print()

    print(gen_comment_banner_centered("print out", "#"))
    demo_repo_1 = _prepare_demo_repo()
    demo_repo_2 = _prepare_demo_repo()

    print(gen_comment_banner_centered("BDC", "="))
    run_bdc(demo_repo_1)
    print()

    print(gen_comment_banner_centered("BDC w/ -vvv", "="))
    run_bdc(demo_repo_2, verbosity=4)


if __name__ == "__main__":
    main()
