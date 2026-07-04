"""
conftest.py

shared pytest fixtures for `setup` (hupy init) tests
"""

import git
import pytest


# fixtures  #####################################################################


@pytest.fixture
def repo_dir(tmp_path):
    """path for a scenario repo; not yet a git repository."""
    return tmp_path / "repo"


@pytest.fixture
def git_repo_dir(repo_dir):
    """path for a freshly-initialized, empty git repository."""
    repo_dir.mkdir()
    git.Repo.init(str(repo_dir))
    return repo_dir
