"""
conftest.py

shared pytest fixtures for `cli` (hupy init) tests
"""

import git
import pytest

from hupy.stub.names_by_demand import get_hook_names_by_demand


# fixtures  #####################################################################


@pytest.fixture
def git_repo_dir(repo_dir):
    """path for a freshly-initialized, empty git repository."""
    repo_dir.mkdir()
    git.Repo.init(str(repo_dir))
    return repo_dir


@pytest.fixture
def stub_names(git_repo_dir):
    """sorted hook names currently demanded for ``git_repo_dir``."""
    repo = git.Repo(str(git_repo_dir))
    return sorted(get_hook_names_by_demand(repo))
