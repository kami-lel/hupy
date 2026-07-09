#!/usr/bin/env python3
"""
catch-up-demo.py

demo: Catch Up merge (dev into add-payment-gateway), a CBM merge type
that CBM already classifies (see hupy/cbm/commit_type.py) but that
PCH does not yet prepend a header for
expected result: skip (merge type not yet handled by PCH)
"""

import os
import pathlib
import shutil
import sys
import tempfile

import git

_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
_BUNDLE_PATH = _REPO_ROOT / "tests" / "testee" / "default_repo.bundle"

sys.path.insert(0, str(_REPO_ROOT / "tests" / "ttg"))

from hupy.kamilog import (  # noqa: E402
    gen_comment_banner_centered,
    gen_comment_banner_zero,
    set_logging_level_by_verbosity,
)
from hupy.pch import prepend_commit_header  # noqa: E402


# helpers  #####################################################################


def _commit_file(repo, repo_dir, filename, content):
    path = pathlib.Path(repo_dir) / filename
    path.write_text(content)
    repo.index.add([filename])
    repo.index.commit("add {}".format(filename))


def _prepare_demo_repo():
    dest_dir = tempfile.mkdtemp(prefix="pch_demo_")
    repo = git.Repo.clone_from(str(_BUNDLE_PATH), dest_dir, branch="main")

    repo.git.checkout("-q", "-b", "dev")
    repo.git.checkout("-q", "-b", "add-payment-gateway")
    repo.git.checkout("-q", "dev")
    _commit_file(repo, dest_dir, "notify.py", "# new work landed on dev\n")
    repo.git.checkout("-q", "add-payment-gateway")
    repo.git.merge("--no-commit", "--no-ff", "dev")

    return dest_dir


def _run_pch(repo_dir, verbosity=1):
    set_logging_level_by_verbosity(verbosity)
    cwd = os.getcwd()
    os.chdir(repo_dir)
    try:
        prepend_commit_header(repo_dir)
    finally:
        os.chdir(cwd)


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print("scenario:\tCatch Up merge (dev into add-payment-gateway)")
    print("expected:\tSKIP (merge type not yet handled by PCH)")
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
    _run_pch(demo_repo_1)
    print()

    print(gen_comment_banner_centered("PCH w/ -vvv", "="))
    _run_pch(demo_repo_2, verbosity=3)
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
