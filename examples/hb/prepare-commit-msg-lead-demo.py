#!/usr/bin/env python3
"""
prepare-commit-msg-lead-demo.py

demo: prepare-commit-msg hook, lead bracket configured with one
command (validate the current branch name before the message is
prepared)
expected result: the lead command runs
"""

import pathlib

from hupy.kamilog import (
    gen_comment_banner_centered,
    gen_comment_banner_zero,
)
from __init__ import prepare_demo_repo, run_hb

_HB_OVERRIDES = {
    "prepare_commit_msg": {
        "lead": [{"cmd": "echo '>> validate branch name'"}],
    },
}


# helpers  #####################################################################


def _prepare_demo_repo():
    return prepare_demo_repo(_HB_OVERRIDES)


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print(
        "scenario:\tprepare-commit-msg, lead bracket w/ 1 configured command"
    )
    print("expected:\tthe lead command runs")
    print()

    print(gen_comment_banner_centered("print out", "#"))
    demo_repo_1 = _prepare_demo_repo()
    demo_repo_2 = _prepare_demo_repo()

    print(gen_comment_banner_centered("HB", "="))
    run_hb(demo_repo_1, "prepare-commit-msg", True)
    print()

    print(gen_comment_banner_centered("HB w/ -vvv", "="))
    run_hb(demo_repo_2, "prepare-commit-msg", True, verbosity=4)


if __name__ == "__main__":
    main()
