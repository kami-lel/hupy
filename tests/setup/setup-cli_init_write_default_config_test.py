"""
setup-cli_init_write_default_config_test.py

tests for `_write_default_config`: fresh write, conflict abort
without --force, and override with --force
"""

import pytest

from hupy.setup.cli_init import (
    _CONFIG_FILENAME,
    _DEFAULT_CONFIG_TEMPLATE,
    _write_default_config,
)


# tests  ########################################################################


class TestWriteDefaultConfigFreshRoot:
    def test_writes_config_matching_template(self, tmp_path):
        _write_default_config(tmp_path, force=False)

        config_path = tmp_path / _CONFIG_FILENAME
        assert config_path.read_bytes() == _DEFAULT_CONFIG_TEMPLATE.read_bytes()


class TestWriteDefaultConfigConflict:
    def test_without_force_raises_and_leaves_config_untouched(self, tmp_path):
        config_path = tmp_path / _CONFIG_FILENAME
        config_path.write_text("stale content")

        with pytest.raises(SystemExit) as exc_info:
            _write_default_config(tmp_path, force=False)

        assert exc_info.value.code == 1
        assert config_path.read_text() == "stale content"

    def test_with_force_overrides_stale_content(self, tmp_path):
        config_path = tmp_path / _CONFIG_FILENAME
        config_path.write_text("stale content")

        _write_default_config(tmp_path, force=True)

        assert config_path.read_bytes() == _DEFAULT_CONFIG_TEMPLATE.read_bytes()
