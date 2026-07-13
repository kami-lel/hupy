"""
conftest.py

pytest fixtures shared across all test suites
"""

import sys
from pathlib import Path

import pytest

# make the shared config fixture loader / repo-prep fixture builder
# importable from every suite
sys.path.insert(0, str(Path(__file__).parent / "fixtures"))

# fixtures  #####################################################################


@pytest.fixture
def repo_dir(tmp_path):
    """path for a scenario repo, not yet created."""
    return tmp_path / "repo"
