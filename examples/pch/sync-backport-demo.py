#!/usr/bin/env python3
"""
sync-backport-demo.py

demo: Sync Backport merge (main into dev), a CBM merge type that CBM
already classifies (see hupy/cbm/commit_type.py) but that PCH does
not yet prepend a header for
expected result: skip (merge type not yet handled by PCH)
"""

import pathlib
import shutil
import subprocess
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
)
from hupy.config.write_config import write_default_config  # noqa: E402


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
    repo.git.checkout("-q", "main")
    _commit_file(repo, dest_dir, "hotdoc.py", "# patched directly on main\n")
    repo.git.checkout("-q", "dev")
    repo.git.merge("--no-commit", "--no-ff", "main")

    write_default_config(pathlib.Path(dest_dir), force=True)
    return dest_dir


def _run_pch(repo_dir, *extra_args):
    subprocess.run(
        [sys.executable, "-m", "hupy", "prepare-commit-msg", *extra_args],
        cwd=repo_dir,
    )


# demo  ########################################################################


def main():
    print(gen_comment_banner_zero([pathlib.Path(__file__).name]))
    print("scenario:\tSync Backport merge (main into dev)")
    print("expected:\tSKIP (merge type not yet handled by PCH)")
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
