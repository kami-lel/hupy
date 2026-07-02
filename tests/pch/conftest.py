"""
conftest.py

shared pytest fixtures for PCH (prepend commit header) tests
"""

import sys
from pathlib import Path

import pytest

# make the TTG commit-type-bucket fixture builder importable from here
sys.path.insert(0, str(Path(__file__).parent.parent / "ttg"))


# fixtures  #####################################################################


@pytest.fixture
def repo_dir(tmp_path):
    """path for the scenario repo; created by ``prepare_repo_with_files``."""
    return tmp_path / "repo"
