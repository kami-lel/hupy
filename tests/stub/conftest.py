"""
conftest.py

shared pytest fixtures for `stub` tests
"""

import sys
from pathlib import Path

import git
import pytest

# make the shared config fixture loader importable from here
sys.path.insert(0, str(Path(__file__).parent.parent / "fixtures"))

from config_fixture import load_config_fixture  # noqa: E402

from hupy.stub.names_by_demand import get_hook_names_by_demand  # noqa: E402

# fixtures  #####################################################################


@pytest.fixture
def repo(repo_dir):
    """git.Repo for a freshly-initialized, empty git repository."""
    repo_dir.mkdir()
    return git.Repo.init(str(repo_dir))


@pytest.fixture(autouse=True)
def _stub_hupy_config(monkeypatch):
    """
    stand in for the on-disk HUPy config with the shared fixture, so
    hook-demand checks don't need a real ``.hupy.config.jsonc``
    """
    monkeypatch.setattr(
        "hupy.stub.names_by_demand.load_hupy_config",
        lambda repo: load_config_fixture(),
    )


@pytest.fixture
def stub_names(repo):
    """sorted hook names currently demanded for ``repo``."""
    return sorted(get_hook_names_by_demand(repo))
