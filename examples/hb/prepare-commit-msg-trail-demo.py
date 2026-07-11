#!/usr/bin/env python3
"""
prepare-commit-msg-trail-demo.py

demo: prepare-commit-msg hook, trail bracket configured with one
command (log the final commit message)
expected result: the trail command runs
"""

import pathlib

from hupy.kamilog import (
    gen_comment_banner_zero,
)
from __init__ import prepare_demo_repo, run_hb

_HB_OVERRIDES = {
    "prepare_commit_msg": {
        "trail": [{"cmd": "echo '>> log commit message'"}],
    },
}


# helpers  #####################################################################


def _prepare_demo_repo():
    return prepare_demo_repo(_HB_OVERRIDES)


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print(
        "scenario:\tprepare-commit-msg, trail bracket w/ 1 configured command"
    )
    print("expected:\tthe trail command runs")
    print()

    demo_repo_1 = _prepare_demo_repo()
    demo_repo_2 = _prepare_demo_repo()

    print(gen_comment_banner_zero(["HB"]))
    run_hb(demo_repo_1, "prepare-commit-msg", False)
    print()

    print(gen_comment_banner_zero(["HB w/ -vvv"]))
    run_hb(demo_repo_2, "prepare-commit-msg", False, verbosity=4)


if __name__ == "__main__":
    main()
