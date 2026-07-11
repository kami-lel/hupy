#!/usr/bin/env python3
"""
pre-commit-trail-demo.py

demo: pre-commit hook, trail bracket configured with one command
(notify CI of a completed pre-commit run)
expected result: the trail command runs
"""

import pathlib

from hupy.kamilog import (
    gen_comment_banner_centered,
    gen_comment_banner_zero,
)
from __init__ import prepare_demo_repo, run_hb

_HB_OVERRIDES = {
    "pre_commit": {
        "trail": [{"cmd": "echo '>> notify CI'"}],
    },
}


# helpers  #####################################################################


def _prepare_demo_repo():
    return prepare_demo_repo(_HB_OVERRIDES)


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print("scenario:\tpre-commit, trail bracket w/ 1 configured command")
    print("expected:\tthe trail command runs")
    print()

    print(gen_comment_banner_centered("print out", "#"))
    demo_repo_1 = _prepare_demo_repo()
    demo_repo_2 = _prepare_demo_repo()

    print(gen_comment_banner_centered("HB", "="))
    run_hb(demo_repo_1, "pre-commit", False)
    print()

    print(gen_comment_banner_centered("HB w/ -vvv", "="))
    run_hb(demo_repo_2, "pre-commit", False, verbosity=4)


if __name__ == "__main__":
    main()
