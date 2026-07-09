#!/usr/bin/env python3
"""
fail-feature-finish-demo.py

demo: Feature Finish merge (add-user-authentication into develop) staging three
files — a.py with 1 LOUD tag, b.py with 2 LOUD tags (multiple TT
in a single file), and c.py with a QUIET tag
expected result: fail (Feature Finish gates the Loud tier; both
a.py and b.py's Loud tags are reported, c.py's Quiet tag is not)
"""

# Todo add a pre-commit-demo

import pathlib
import sys
import tempfile

_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
_BUCKET = "feature_finish"
_FILES = {
    "a.py": "tt_loud_only.py",
    "b.py": "tt_2loud.py",
    "c.py": "tt_quiet_only.py",
}

sys.path.insert(0, str(_REPO_ROOT / "tests" / "fixtures"))

from hupy.kamilog import (  # noqa: E402
    gen_comment_banner_centered,
    gen_comment_banner_zero,
    set_logging_level_by_verbosity,
)
from hupy.ttg import TTG_LOGGER_NAME  # noqa: E402
from hupy.ttg.tt_gating import perform_triage_tags_gating  # noqa: E402
from prep_repo import prepare_repo_with_files  # noqa: E402

# helpers  #####################################################################


def _prepare_demo_repo():
    dest_dir = tempfile.mkdtemp(prefix="ttg_demo_")
    return prepare_repo_with_files(dest_dir, _BUCKET, _FILES)


def _run_ttg(repo_dir, verbosity=1):
    set_logging_level_by_verbosity(verbosity, logger_name=TTG_LOGGER_NAME)
    try:
        perform_triage_tags_gating(repo_dir)
    except SystemExit:
        pass


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print("scenario:\tFeature Finish, multiple files with multiple Loud TT")
    print("expected:\tFAIL")
    print(
        "reason:\tLoud tags in both a.py and b.py (multiple files, multiple TT)"
    )
    print()

    print(gen_comment_banner_centered("print out", "#"))
    demo_repo_1 = _prepare_demo_repo()
    demo_repo_2 = _prepare_demo_repo()

    print(gen_comment_banner_centered("TTG", "="))
    _run_ttg(demo_repo_1)
    print()

    print(gen_comment_banner_centered("TTG w/ -vvv", "="))
    _run_ttg(demo_repo_2, verbosity=4)


if __name__ == "__main__":
    main()
