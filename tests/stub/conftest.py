"""
conftest.py

shared pytest fixtures for `stub` tests
"""

import git
import pytest

from hupy.stub.names_by_demand import get_hook_names_by_demand

# fixtures  #####################################################################


@pytest.fixture
def repo(repo_dir):
    """git.Repo for a freshly-initialized, empty git repository."""
    repo_dir.mkdir()
    return git.Repo.init(str(repo_dir))


@pytest.fixture
def stub_names(repo):
    """sorted hook names currently demanded for ``repo``."""
    return sorted(get_hook_names_by_demand(repo))
