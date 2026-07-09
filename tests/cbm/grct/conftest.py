"""
conftest.py

shared pytest fixtures for `get_current_commit_type.py` (grct) tests
"""

import pytest

from . import prepare_merge_repo


# fixtures  #####################################################################


@pytest.fixture
def repo_dir(tmp_path):
    """path for a repo prepared with an in-progress Feature Finish merge."""
    return tmp_path / "repo"


@pytest.fixture
def repo(repo_dir):
    """
    git.Repo for repo_dir, mid an in-progress Feature Finish merge
    (source branch ``add-user-authentication`` into target ``dev``).
    """
    return prepare_merge_repo(repo_dir, "feature_finish")
