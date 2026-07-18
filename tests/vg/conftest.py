"""
conftest.py

shared pytest fixtures for VG (ver_grep) tests: build an in-progress
Feature Landing merge (`SOURCE_BRANCH` into `DEV_BRANCH`) with a
caller-chosen version file committed on the source branch tip (and
optionally the target branch beforehand), so the merge stays in
progress (`MERGE_HEAD` intact) with real, readable branch tips
"""

import os
from pathlib import Path

import git
import pytest

from prep_repo import DEV_BRANCH, MAIN_BRANCH, _write_config_file

_BUNDLE_PATH = Path(__file__).parent.parent / "fixtures" / "default_repo.bundle"

SOURCE_BRANCH = "add-user-authentication"


# auxiliaries  #################################################################


def _clone_and_enter(dest_dir):
    git.Repo.clone_from(str(_BUNDLE_PATH), str(dest_dir), branch=MAIN_BRANCH)
    os.chdir(str(dest_dir))
    _write_config_file(dest_dir)
    return git.Repo(str(dest_dir))


def _commit_file(dest_dir, repo, filename, content):
    path = Path(dest_dir) / filename
    path.write_text(content)
    repo.index.add([filename])
    repo.index.commit("add {}".format(filename))


# fixtures  #####################################################################


@pytest.fixture
def make_merge_repo_with_version(repo_dir):
    """
    factory: build an in-progress Feature Landing merge, committing
    ``version_file`` with ``source_content`` on the source branch tip,
    and with ``target_content`` on the target branch beforehand when
    given.
    """

    def _make(version_file, source_content, target_content=None):
        repo = _clone_and_enter(repo_dir)
        repo.git.checkout("-q", "-b", DEV_BRANCH)
        if target_content is not None:
            _commit_file(repo_dir, repo, version_file, target_content)
        repo.git.checkout("-q", "-b", SOURCE_BRANCH)
        _commit_file(repo_dir, repo, version_file, source_content)
        repo.git.checkout("-q", DEV_BRANCH)
        repo.git.merge("--no-commit", "--no-ff", SOURCE_BRANCH)
        return repo

    return _make


@pytest.fixture
def merge_repo_without_version_file(repo_dir):
    """
    git.Repo mid an in-progress Feature Landing merge whose source
    branch never adds a version file, for exercising the not-found
    error path.
    """
    repo = _clone_and_enter(repo_dir)
    repo.git.checkout("-q", "-b", DEV_BRANCH)
    repo.git.checkout("-q", "-b", SOURCE_BRANCH)
    _commit_file(repo_dir, repo, "feature.py", "# feature work\n")
    repo.git.checkout("-q", DEV_BRANCH)
    repo.git.merge("--no-commit", "--no-ff", SOURCE_BRANCH)
    return repo
