"""
conftest.py

shared pytest fixtures for TTG (triage tag gating) tests
"""

import pytest

# fixtures  #####################################################################


@pytest.fixture
def repo_dir(tmp_path):
    """path for the scenario repo; created by ``prepare_repo_with_files``."""
    return tmp_path / "repo"
