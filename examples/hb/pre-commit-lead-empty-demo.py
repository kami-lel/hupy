#!/usr/bin/env python3
"""
pre-commit-lead-empty-demo.py

demo: pre-commit hook, lead bracket left at its default empty
command list
expected result: skip (no lead bracket commands configured)
"""

import pathlib

from hupy.kamilog import (
    gen_comment_banner_centered,
    gen_comment_banner_zero,
)
from __init__ import prepare_demo_repo, run_hb

_HB_OVERRIDES = {}


# helpers  #####################################################################


def _prepare_demo_repo():
    return prepare_demo_repo(_HB_OVERRIDES)


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print("scenario:\tpre-commit, lead bracket w/ empty command list")
    print("expected:\tSKIP (no lead bracket commands configured)")
    print()

    print(gen_comment_banner_centered("print out", "#"))
    demo_repo_1 = _prepare_demo_repo()
    demo_repo_2 = _prepare_demo_repo()

    print(gen_comment_banner_centered("HB", "="))
    run_hb(demo_repo_1, "pre-commit", True)
    print()

    print(gen_comment_banner_centered("HB w/ -vvv", "="))
    run_hb(demo_repo_2, "pre-commit", True, verbosity=4)


if __name__ == "__main__":
    main()
