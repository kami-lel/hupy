"""
config-shipped-config-file_test.py

quality tests for the shipped default HUPy config asset
(``hupy/assets/.hupy.config.jsonc``)
"""

import pytest

from hupy.config_file.config_file import HupyConfigFile

# tests  ########################################################################


@pytest.mark.release
class TestShippedConfigFile:
    def test_validates_without_exception(self, shipped_config):
        HupyConfigFile.model_validate(shipped_config)
