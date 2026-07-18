#!/usr/bin/env python3
"""
fail-feature-landing-demo.py

demo: Feature Landing merge (add-user-authentication into develop) staging three
files — a.py with 1 LOUD tag, b.py with 2 LOUD tags (multiple TT
in a single file), and c.py with a QUIET tag
expected result: fail (Feature Landing gates the Loud tier; both
a.py and b.py's Loud tags are reported, c.py's Quiet tag is not)
"""

import pathlib

from hupy.kamilog import (
    gen_comment_banner_centered,
    gen_comment_banner_zero,
)
from __init__ import prepare_demo_repo, run_ttg

_BUCKET = "feature_landing"
_FILES = {
    "a.py": "tt_loud_only.py",
    "b.py": "tt_2loud.py",
    "c.py": "tt_quiet_only.py",
}


# auxiliaries  #################################################################


def _prepare_demo_repo():
    return prepare_demo_repo(_BUCKET, _FILES)


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print("scenario:\tFeature Landing, multiple files with multiple Loud TT")
    print("expected:\tFAIL")
    print(
        "reason:\tLoud tags in both a.py and b.py (multiple files, multiple TT)"
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
