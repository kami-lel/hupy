#!/usr/bin/env python3
"""
pass-feature-finish-demo.py

demo: Feature Finish merge (add-user-authentication into develop) staging two
files — a.py with a STEADY "# Todo steady marker" comment and
b.py with a QUIET "# todo quiet marker" comment (no Loud tags
anywhere)
expected result: pass
"""

import pathlib

from hupy.kamilog import (
    gen_comment_banner_centered,
    gen_comment_banner_zero,
)
from __init__ import prepare_demo_repo, run_ttg

_BUCKET = "feature_finish"
_FILES = {"a.py": "tt_steady_only.py", "b.py": "tt_quiet_only.py"}


# helpers  #####################################################################


def _prepare_demo_repo():
    return prepare_demo_repo(_BUCKET, _FILES)


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print("scenario:\tFeature Finish, multiple files (steady + quiet, no loud)")
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
