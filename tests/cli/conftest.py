"""
conftest.py

shared pytest fixtures for `cli` (hupy init) tests
"""

import git
import pytest


# fixtures  #####################################################################


@pytest.fixture
def git_repo_dir(repo_dir):
    """path for a freshly-initialized, empty git repository."""
    repo_dir.mkdir()
    git.Repo.init(str(repo_dir))
    return repo_dir
