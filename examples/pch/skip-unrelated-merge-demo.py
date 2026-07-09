#!/usr/bin/env python3
"""
skip-unrelated-merge-demo.py

demo: merging two unrelated, non-protected branches (hotfix into
release); the hotfix side stages two files — a.py with a LOUD
"# TODO loud marker" comment and b.py with no tags at all
expected result: skip (merge type is not Feature Finish or Version Release)
"""

import pathlib
import subprocess
import sys
import tempfile

_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
_SCENARIO = "irrelevant_merge"

sys.path.insert(0, str(_REPO_ROOT / "tests" / "ttg"))

from hupy.kamilog import (  # noqa: E402
    gen_comment_banner_centered,
    gen_comment_banner_zero,
)
from hupy.config.write_config import write_default_config  # noqa: E402
from prep_repo import prepare_repo  # noqa: E402


# helpers  #####################################################################


def _prepare_demo_repo():
    dest_dir = tempfile.mkdtemp(prefix="pch_demo_")
    repo_dir = prepare_repo(dest_dir, _SCENARIO)
    write_default_config(pathlib.Path(repo_dir), force=True)
    return repo_dir


def _run_pch(repo_dir, *extra_args):
    subprocess.run(
        [sys.executable, "-m", "hupy", "prepare-commit-msg", *extra_args],
        cwd=repo_dir,
    )


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print(
        "scenario:\tIrrelevant merge (hotfix to release), "
        "multiple files (loud + clean)"
    )
    print("expected:\tSKIP")
    print()

    print(gen_comment_banner_centered("setup", "#"))
    demo_repo_1 = _prepare_demo_repo()
    demo_repo_2 = _prepare_demo_repo()
    print()

    print(gen_comment_banner_centered("PCH", "#"))
    _run_pch(demo_repo_1)
    print()

    print(gen_comment_banner_centered("PCH w/ -vvv", "#"))
    _run_pch(demo_repo_2, "-vvv")


if __name__ == "__main__":
    main()
