#!/usr/bin/env python3
"""
skip-non-protected-branch-demo.py

demo: a regular (non-merge) commit made directly on a fresh feature
branch, staging one plain file
expected result: skip (the branch is neither main, dev, nor listed
in ban_commit_to_branches)
"""

import pathlib

from hupy.kamilog import (
    gen_comment_banner_centered,
    gen_comment_banner_zero,
)
from __init__ import prepare_demo_repo_on_branch, run_bdc

_BRANCH = "feature/add-metrics"
_FILENAME = "a.py"


# auxiliaries  #################################################################


def _prepare_demo_repo():
    return prepare_demo_repo_on_branch(_BRANCH, _FILENAME)


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print("scenario:\tNon-merge commit staged directly on '{}'".format(_BRANCH))
    print("expected:\tSKIP")
    print("reason:\tthe branch is not protected")
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
