#!/usr/bin/env python3
"""
version-release-demo.py

demo: Version Release merge (develop into main) with the
in-progress merge message copied into COMMIT_EDITMSG (mirroring
what git itself does before invoking the commit-msg hook)
expected result: header prepended to COMMIT_EDITMSG
"""

import pathlib
import shutil

from hupy.kamilog import (
    gen_comment_banner_centered,
    gen_comment_banner_zero,
)
from __init__ import prepare_demo_repo_by_scenario, run_pch

_SCENARIO = "version_release_pass"


# helpers  #####################################################################


def _prepare_demo_repo():
    return prepare_demo_repo_by_scenario(_SCENARIO)


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print("scenario:\tVersion Release merge (develop into main)")
    print("expected:\tPASS, header prepended to COMMIT_EDITMSG")
    print()

    print(gen_comment_banner_centered("print out", "#"))
    demo_repo_1 = _prepare_demo_repo()
    editmsg_1 = pathlib.Path(demo_repo_1, ".git", "COMMIT_EDITMSG")
    before_file_1 = pathlib.Path(demo_repo_1, ".git", "COMMIT_EDITMSG.before")
    shutil.copy(pathlib.Path(demo_repo_1, ".git", "MERGE_MSG"), editmsg_1)
    shutil.copy(editmsg_1, before_file_1)

    demo_repo_2 = _prepare_demo_repo()
    editmsg_2 = pathlib.Path(demo_repo_2, ".git", "COMMIT_EDITMSG")
    before_file_2 = pathlib.Path(demo_repo_2, ".git", "COMMIT_EDITMSG.before")
    shutil.copy(pathlib.Path(demo_repo_2, ".git", "MERGE_MSG"), editmsg_2)
    shutil.copy(editmsg_2, before_file_2)

    print(gen_comment_banner_centered("PCH", "="))
    run_pch(demo_repo_1)
    print()

    print(gen_comment_banner_centered("PCH w/ -vvv", "="))
    run_pch(demo_repo_2, verbosity=3)
    print()

    print(gen_comment_banner_centered("COMMIT_EDITMSG content", "#"))
    print()

    print(gen_comment_banner_centered("before PCH", "="))
    print(before_file_2.read_text(), end="")
    print()

    print(gen_comment_banner_centered("after PCH", "="))
    print(editmsg_2.read_text(), end="")


if __name__ == "__main__":
    main()
