#!/usr/bin/env python3
"""
fail-version-release-demo.py

demo: Version Release merge (develop into main) staging three
files — a.py with 1 LOUD tag, b.py with 1 LOUD and 2 STEADY tags
(multiple TT in a single file), and c.py with a QUIET tag
expected result: fail (Version Release gates Loud and Steady tiers;
both a.py and b.py's gating tags are reported, c.py's Quiet tag is not)
"""

import pathlib

from hupy.kamilog import (
    gen_comment_banner_centered,
    gen_comment_banner_zero,
)
from __init__ import prepare_demo_repo, run_ttg

_BUCKET = "version_release"
_FILES = {
    "a.py": "tt_loud_only.py",
    "b.py": "tt_1loud_2steady.py",
    "c.py": "tt_quiet_only.py",
}


# auxiliaries  #################################################################


def _prepare_demo_repo():
    return prepare_demo_repo(_BUCKET, _FILES)


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print("scenario:\tVersion Release, multiple files with multiple gating TT")
    print("expected:\tFAIL")
    print(
        "reason:\tLoud/Steady tags in both a.py and b.py "
        "(multiple files, multiple TT)"
    )
    print()

    print(gen_comment_banner_centered("print out", "#"))
    demo_repo_1 = _prepare_demo_repo()
    demo_repo_2 = _prepare_demo_repo()

    print(gen_comment_banner_centered("TTG", "="))
    run_ttg(demo_repo_1)
    print()

    print(gen_comment_banner_centered("TTG w/ -vvv", "="))
    run_ttg(demo_repo_2, verbosity=4)


if __name__ == "__main__":
    main()
