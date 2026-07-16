"""
config-shipped-config-file_test.py

quality tests for the shipped default HUPy config asset
(``hupy/assets/.hupy.config.jsonc``)
"""

from importlib.metadata import version

from hupy.config_file.config_file import HupyConfigFile

# tests  ########################################################################


# Fixme upd to use this only during release


class TestShippedConfigFile:
    def test_validates_without_exception(self, shipped_config):
        HupyConfigFile.model_validate(shipped_config)

    def test_hupy_version_matches_installed_version(self, shipped_config):
        config = HupyConfigFile.model_validate(shipped_config)
        assert config.hupy_version == version("HUPy")
