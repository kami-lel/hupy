"""
conftest.py

shared pytest fixtures for `config_file` tests
"""

import json5
import pytest

from hupy.config_file.config_file_path import DEFAULT_CONFIG_ASSET

# fixtures  #####################################################################


@pytest.fixture
def shipped_config():
    """the shipped config asset, parsed but not yet schema-validated."""
    return json5.loads(DEFAULT_CONFIG_ASSET.read_text())
