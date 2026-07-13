"""
config-shipped-config-file_test.py

quality tests for the shipped default HUPy config asset
(``hupy/assets/.hupy.config.jsonc``)
"""

from importlib.metadata import version

import json5
import pytest

from hupy.config_file.config_file import HupyConfigFile
from hupy.config_file.config_file_path import DEFAULT_CONFIG_ASSET

# fixtures  #####################################################################


@pytest.fixture
def shipped_config():
    """the shipped config asset, parsed but not yet schema-validated."""
    return json5.loads(DEFAULT_CONFIG_ASSET.read_text())


# tests  ########################################################################


class TestShippedConfigFile:
    def test_validates_without_exception(self, shipped_config):
        HupyConfigFile.model_validate(shipped_config)

    def test_hupy_version_matches_installed_version(self, shipped_config):
        config = HupyConfigFile.model_validate(shipped_config)
        assert config.hupy_version == version("HUPy")
