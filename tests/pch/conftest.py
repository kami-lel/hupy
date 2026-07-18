"""
conftest.py

shared pytest fixtures for PCH (prepend commit header) tests
"""

import git
import pytest

from prep_repo import prepare_repo_with_files


# fixtures  #####################################################################


@pytest.fixture
def feature_landing_repo(repo_dir):
    """git.Repo prepared with an in-progress Feature Landing merge, one file staged."""
    prepare_repo_with_files(
        repo_dir, "feature_landing", {"feature.py": "tt_none.py"}
    )
    return git.Repo(str(repo_dir))


@pytest.fixture
def version_release_repo(repo_dir):
    """git.Repo prepared with an in-progress Version Release merge, one file staged."""
    prepare_repo_with_files(
        repo_dir, "version_release", {"feature.py": "tt_none.py"}
    )
    return git.Repo(str(repo_dir))
