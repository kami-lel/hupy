#!/usr/bin/env python3
"""
pch-pass-feature_finish_demo.py

demo: Feature Finish merge (add-user-authentication into develop) with the
in-progress merge message copied into COMMIT_EDITMSG (mirroring
what git itself does before invoking the commit-msg hook)
expected result: header prepended to COMMIT_EDITMSG
"""

import pathlib
import shutil
import subprocess
import sys
import tempfile

_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
_SCENARIO = "feature_finish_pass"

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
        "scenario:\tFeature Finish merge "
        "(add-user-authentication into develop)"
    )
    print("expected:\tPASS, header prepended to COMMIT_EDITMSG")
    print()

    print(gen_comment_banner_centered("print out", "#"))
    print()

    print(gen_comment_banner_centered("PCH", "="))
    demo_repo_1 = _prepare_demo_repo()
    editmsg_1 = pathlib.Path(demo_repo_1, ".git", "COMMIT_EDITMSG")
    before_file_1 = pathlib.Path(demo_repo_1, ".git", "COMMIT_EDITMSG.before")
    shutil.copy(pathlib.Path(demo_repo_1, ".git", "MERGE_MSG"), editmsg_1)
    shutil.copy(editmsg_1, before_file_1)
    _run_pch(demo_repo_1)
    print()

    print(gen_comment_banner_centered("PCH w/ -v", "="))
    demo_repo_2 = _prepare_demo_repo()
    shutil.copy(
        pathlib.Path(demo_repo_2, ".git", "MERGE_MSG"),
        pathlib.Path(demo_repo_2, ".git", "COMMIT_EDITMSG"),
    )
    _run_pch(demo_repo_2, "-v")
    print()

    print(gen_comment_banner_centered("PCH w/ -vvv", "="))
    demo_repo_3 = _prepare_demo_repo()
    editmsg_3 = pathlib.Path(demo_repo_3, ".git", "COMMIT_EDITMSG")
    before_file_3 = pathlib.Path(demo_repo_3, ".git", "COMMIT_EDITMSG.before")
    shutil.copy(pathlib.Path(demo_repo_3, ".git", "MERGE_MSG"), editmsg_3)
    shutil.copy(editmsg_3, before_file_3)
    _run_pch(demo_repo_3, "-vvv")
    print()

    print(gen_comment_banner_centered("COMMIT_EDITMSG content", "#"))
    print()

    print(gen_comment_banner_centered("before PCH", "="))
    print(before_file_3.read_text(), end="")
    print()

    print(gen_comment_banner_centered("after PCH", "="))
    print(editmsg_3.read_text(), end="")


if __name__ == "__main__":
    main()
