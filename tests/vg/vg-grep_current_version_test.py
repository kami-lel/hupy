"""
vg-grep_current_version_test.py

tests for `grep_current_version` in `gcv.py`
"""

from unittest import mock

import pytest

from hupy.config.hupy_config_file import HupyConfigFile
from hupy.ver_grep import grep_current_version


# helpers  ######################################################################


def _grep(version_file, pattern):
    """
    run ``grep_current_version`` against a stubbed config carrying the
    given ``version_file`` and ``pattern``, bypassing disk/git config
    loading.
    """
    config = HupyConfigFile(
        ver_grep={
            "version_file": str(version_file),
            "version_line_pattern": pattern,
        }
    )
    with mock.patch(
        "hupy.ver_grep.gcv.load_hupy_config", return_value=config
    ):
        return grep_current_version()


def _write(tmp_path, name, text):
    """write ``text`` into ``tmp_path/name`` and return the path."""
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


# tests  ########################################################################


class TestGrepCurrentVersionMatch:
    def test_returns_captured_group(self, tmp_path):
        path = _write(tmp_path, "pyproject.toml", 'version = "1.2.3"\n')
        assert _grep(path, r'version = "(.*)"') == "1.2.3"

    def test_returns_first_group_when_pattern_has_many(self, tmp_path):
        path = _write(tmp_path, "v.txt", "release 4.5.6 stable\n")
        assert _grep(path, r"release (\d+\.\d+\.\d+) (\w+)") == "4.5.6"

    def test_returns_first_matching_line(self, tmp_path):
        path = _write(
            tmp_path, "v.txt", 'version = "1.0.0"\nversion = "2.0.0"\n'
        )
        assert _grep(path, r'version = "(.*)"') == "1.0.0"

    def test_skips_leading_non_matching_lines(self, tmp_path):
        path = _write(
            tmp_path, "v.txt", "# header\nname = hupy\nversion = 9.9\n"
        )
        assert _grep(path, r"version = (.*)") == "9.9"

    def test_matches_mid_line_with_search(self, tmp_path):
        path = _write(tmp_path, "v.txt", "  __version__ = '0.4.1'  # noqa\n")
        assert _grep(path, r"__version__ = '(.*?)'") == "0.4.1"


class TestGrepCurrentVersionNotConfigured:
    def test_empty_version_file_returns_empty(self):
        assert _grep("", r'version = "(.*)"') == ""

    def test_dot_version_file_returns_empty(self):
        assert _grep(".", r'version = "(.*)"') == ""

    def test_empty_pattern_returns_empty(self, tmp_path):
        path = _write(tmp_path, "v.txt", 'version = "1.2.3"\n')
        assert _grep(path, "") == ""

    def test_whitespace_pattern_returns_empty(self, tmp_path):
        path = _write(tmp_path, "v.txt", 'version = "1.2.3"\n')
        assert _grep(path, "   ") == ""


class TestGrepCurrentVersionErrors:
    def test_missing_version_file_raises_system_exit(self, tmp_path):
        missing = tmp_path / "does_not_exist.toml"
        with pytest.raises(SystemExit) as ei:
            _grep(missing, r'version = "(.*)"')
        assert ei.value.code == 1

    def test_no_matching_line_raises_system_exit(self, tmp_path):
        path = _write(tmp_path, "v.txt", "name = hupy\nauthor = kami\n")
        with pytest.raises(SystemExit) as ei:
            _grep(path, r'version = "(.*)"')
        assert ei.value.code == 1
