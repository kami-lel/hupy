"""
vg_helpers.py

repo-building helpers for `grep_source_branch_version` and
`grep_target_branch_version` tests; commits
a caller-chosen version file onto a Feature Landing merge's source
branch (and optionally its target branch) before the merge starts, so
the merge stays in progress (`MERGE_HEAD` intact) with real, readable
branch tips
"""

import os
from pathlib import Path

import git

from prep_repo import DEV_BRANCH, MAIN_BRANCH

_BUNDLE_PATH = Path(__file__).parent.parent / "fixtures" / "default_repo.bundle"

SOURCE_BRANCH = "add-user-authentication"


# helpers  ######################################################################


def _clone_and_enter(dest_dir):
    git.Repo.clone_from(str(_BUNDLE_PATH), str(dest_dir), branch=MAIN_BRANCH)
    os.chdir(str(dest_dir))
    return git.Repo(str(dest_dir))


def _commit_file(dest_dir, repo, filename, content):
    path = Path(dest_dir) / filename
    path.write_text(content)
    repo.index.add([filename])
    repo.index.commit("add {}".format(filename))


# Public API  ##################################################################


def prepare_merge_repo_with_version(
    dest_dir, version_file, source_content, target_content=None
):
    """
    build an in-progress Feature Landing merge (`SOURCE_BRANCH` into
    `DEV_BRANCH`), committing `version_file` with `source_content` on
    the source branch tip, and with `target_content` on the target
    branch beforehand when given.
    """
    repo = _clone_and_enter(dest_dir)
    repo.git.checkout("-q", "-b", DEV_BRANCH)
    if target_content is not None:
        _commit_file(dest_dir, repo, version_file, target_content)
    repo.git.checkout("-q", "-b", SOURCE_BRANCH)
    _commit_file(dest_dir, repo, version_file, source_content)
    repo.git.checkout("-q", DEV_BRANCH)
    repo.git.merge("--no-commit", "--no-ff", SOURCE_BRANCH)
    return repo


def prepare_merge_repo_without_version_file(dest_dir):
    """
    build an in-progress Feature Landing merge whose source branch
    never adds a version file, for exercising the not-found error
    path.
    """
    repo = _clone_and_enter(dest_dir)
    repo.git.checkout("-q", "-b", DEV_BRANCH)
    repo.git.checkout("-q", "-b", SOURCE_BRANCH)
    _commit_file(dest_dir, repo, "feature.py", "# feature work\n")
    repo.git.checkout("-q", DEV_BRANCH)
    repo.git.merge("--no-commit", "--no-ff", SOURCE_BRANCH)
    return repo
