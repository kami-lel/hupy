#!/usr/bin/env python3
"""
pass-version-release-demo.py

demo: Version Release merge (develop into main) staging two files
— a.py and b.py, each with only a QUIET "# todo quiet marker"
comment (no Loud or Steady tags anywhere)
expected result: pass
"""

import pathlib

from hupy.kamilog import (
    gen_comment_banner_centered,
    gen_comment_banner_zero,
)
from __init__ import prepare_demo_repo, run_ttg

_BUCKET = "version_release"
_FILES = {"a.py": "tt_quiet_only.py", "b.py": "tt_quiet_only.py"}


# auxiliaries  #################################################################


def _prepare_demo_repo():
    return prepare_demo_repo(_BUCKET, _FILES)


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print("scenario:\tVersion Release, multiple files (quiet only, no loud/steady)")
    print("expected:\tPASS")
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
