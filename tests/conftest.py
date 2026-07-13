"""
conftest.py

pytest fixtures shared across all test suites
"""

# FIXME clean up tests file naming & cmt


import pytest

# fixtures  #####################################################################


@pytest.fixture
def repo_dir(tmp_path):
    """path for a scenario repo, not yet created."""
    return tmp_path / "repo"
