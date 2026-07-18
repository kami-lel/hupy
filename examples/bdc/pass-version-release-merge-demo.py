#!/usr/bin/env python3
"""
pass-version-release-merge-demo.py

demo: an in-progress Version Release merge (dev into main), staging
one plain file
expected result: pass (main is protected, but a MERGE commit is
exempt from the ban)
"""

import pathlib

from hupy.kamilog import (
    gen_comment_banner_centered,
    gen_comment_banner_zero,
)
from __init__ import prepare_demo_repo_by_bucket, run_bdc

_BUCKET = "version_release"
_FILES = {"a.py": "tt_none.py"}


# auxiliaries  #################################################################


def _prepare_demo_repo():
    return prepare_demo_repo_by_bucket(_BUCKET, _FILES)


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print("scenario:\tVersion Release merge (dev into main), in progress")
    print("expected:\tPASS")
    print("reason:\tmain is protected, but merge commits are exempt")
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
