#!/usr/bin/env python3
"""
skip-unrelated-merge-demo.py

demo: merging two unrelated, non-protected branches (hotfix into
release); the hotfix side stages two files — a.py with a LOUD
"# TODO loud marker" comment and b.py with no tags at all
expected result: skip (merge type is not Feature Landing or Version Release)
"""

import pathlib

from hupy.kamilog import (
    gen_comment_banner_centered,
    gen_comment_banner_zero,
)
from __init__ import prepare_demo_repo_by_scenario, run_pch

_SCENARIO = "irrelevant_merge"


# auxiliaries  #################################################################


def _prepare_demo_repo():
    return prepare_demo_repo_by_scenario(_SCENARIO)


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print(
        "scenario:\tIrrelevant merge (hotfix to release), "
        "multiple files (loud + clean)"
    )
    print("expected:\tSKIP")
    print()

    demo_repo_1 = _prepare_demo_repo()
    demo_repo_2 = _prepare_demo_repo()
    print()

    print(gen_comment_banner_centered("PCH", "#"))
    run_pch(demo_repo_1)
    print()

    print(gen_comment_banner_centered("PCH w/ -vvv", "#"))
    run_pch(demo_repo_2, verbosity=3)


if __name__ == "__main__":
    main()
