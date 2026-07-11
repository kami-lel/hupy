#!/usr/bin/env python3
"""
pre-commit-lead-demo.py

demo: pre-commit hook, lead bracket configured with two commands
(a lint check and a format check)
expected result: both lead commands run, in configured order
"""

import pathlib

from hupy.kamilog import (
    gen_comment_banner_zero,
)
from __init__ import prepare_demo_repo, run_hb

_HB_OVERRIDES = {
    "pre_commit": {
        "lead": [
            {
                "cmd": "echo '>> lint check'",
                "remark": "Lint the Staged Sources Before Committing",
            },
            {"cmd": "echo '>> format check'"},
        ],
    },
}


# helpers  #####################################################################


def _prepare_demo_repo():
    return prepare_demo_repo(_HB_OVERRIDES)


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print("scenario:\tpre-commit, lead bracket w/ 2 configured commands")
    print("expected:\tboth lead commands run, in configured order")
    print()

    demo_repo_1 = _prepare_demo_repo()
    demo_repo_2 = _prepare_demo_repo()

    print(gen_comment_banner_zero(["HB"]))
    run_hb(demo_repo_1, "pre-commit", True)
    print()

    print(gen_comment_banner_zero(["HB w/ -vvv"]))
    run_hb(demo_repo_2, "pre-commit", True, verbosity=4)


if __name__ == "__main__":
    main()
