#!/usr/bin/env python3
"""
prepare-commit-msg-lead-demo.py

demo: prepare-commit-msg hook, lead bracket configured with two
commands: one unrestricted (validate the current branch name before
the message is prepared), one restricted to ``RELEASE_CUT`` commits
expected result: the unrestricted command runs, the restricted one is
skipped since the demo commit is a regular, non-merge commit
"""

import pathlib

from hupy.kamilog import (
    gen_comment_banner_centered,
    gen_comment_banner_zero,
)
from __init__ import prepare_demo_repo, run_hb

_HB_OVERRIDES = {
    "prepare_commit_msg": {
        "lead": [
            {"cmd": "echo '>> validate branch name'"},
            {
                "cmd": "echo '>> tag release notes'",
                "commit_types": ["RELEASE_CUT"],
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
        "scenario:\tprepare-commit-msg, lead bracket w/ 2 configured "
        "commands, one restricted to RELEASE_CUT"
    )
    print("expected:\tthe unrestricted command runs, the restricted one "
          "is skipped")
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
