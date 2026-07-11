#!/usr/bin/env python3
"""
pcm-trail-fail-abort-demo.py

demo: prepare-commit-msg hook, trail bracket configured with two
commands: log the final commit message, then a lint that exits
non-zero
expected result: the log command runs, the lint command fails, prints
its error to the terminal, and aborts the trail bracket with its
non-zero exit code
"""

import pathlib

from hupy.kamilog import (
    gen_comment_banner_zero,
)
from __init__ import prepare_demo_repo, run_hb

_HB_OVERRIDES = {
    "prepare_commit_msg": {
        "trail": [
            {"cmd": "echo '>> log commit message'"},
            {
                "cmd": "echo '>> commit message lint failed' >&2; exit 1",
                "remark": "Lint the Prepared Commit Message",
            },
        ],
    },
}


# helpers  #####################################################################


def _prepare_demo_repo():
    return prepare_demo_repo(_HB_OVERRIDES)


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print(
        "scenario:\tprepare-commit-msg, trail bracket w/ 2 configured "
        "commands, the second exits non-zero"
    )
    print(
        "expected:\tthe log command runs, the lint command fails and "
        "aborts the bracket"
    )
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
