"""
vg-grep_source_branch_version_test.py

tests for `grep_source_branch_version` in `branch_version.py`
"""

from unittest import mock

import pytest

from config_fixture import load_config_fixture

from hupy.ver_grep import grep_source_branch_version
from vg_helpers import (
    prepare_merge_repo_with_version,
    prepare_merge_repo_without_version_file,
)

_VERSION_FILE = "VERSION"
_PATTERN = r"(\d+\.\d+\.\d+)"


# helpers  ######################################################################


def _grep(pattern=_PATTERN, version_file=_VERSION_FILE):
    """
    run ``grep_source_branch_version`` against a stubbed config
    carrying ``version_file`` and ``pattern``, bypassing disk/git
    config loading; the current working directory is expected to
    already be inside the prepared merge repo.
    """
    config = load_config_fixture(
        overrides={
            "ver_grep": {
                "version_file": version_file,
                "version_line_pattern": pattern,
            }
        }
    )
    with mock.patch(
        "hupy.ver_grep.branch_version.load_hupy_config", return_value=config
    ):
        return grep_source_branch_version()


# tests  ########################################################################


class TestGrepSourceBranchVersionMatch:
    def test_returns_captured_group_from_source_branch(self, repo_dir):
        prepare_merge_repo_with_version(repo_dir, _VERSION_FILE, "1.2.3\n")
        assert _grep() == "1.2.3"

    def test_reads_source_not_target_branch_content(self, repo_dir):
        # mid-merge, the working tree/target holds "2.0.0"; the source
        # branch tip (read straight via git) must win
        prepare_merge_repo_with_version(
            repo_dir,
            _VERSION_FILE,
            source_content="1.2.3\n",
            target_content="2.0.0\n",
        )
        assert _grep() == "1.2.3"

    def test_returns_first_matching_line(self, repo_dir):
        prepare_merge_repo_with_version(
            repo_dir, _VERSION_FILE, "1.0.0\n2.0.0\n"
        )
        assert _grep() == "1.0.0"

    def test_custom_pattern_with_capturing_group(self, repo_dir):
        prepare_merge_repo_with_version(
            repo_dir, "pyproject.toml", 'version = "4.5.6"\n'
        )
        assert (
            _grep(pattern=r'version = "(.*)"', version_file="pyproject.toml")
            == "4.5.6"
        )


class TestGrepSourceBranchVersionNotConfigured:
    def test_empty_version_file_returns_empty(self, repo_dir):
        prepare_merge_repo_with_version(repo_dir, _VERSION_FILE, "1.2.3\n")
        assert _grep(version_file="") == ""

    def test_empty_pattern_returns_empty(self, repo_dir):
        prepare_merge_repo_with_version(repo_dir, _VERSION_FILE, "1.2.3\n")
        assert _grep(pattern="") == ""


class TestGrepSourceBranchVersionErrors:
    def test_missing_version_file_on_source_branch_raises_system_exit(
        self, repo_dir
    ):
        prepare_merge_repo_without_version_file(repo_dir)
        with pytest.raises(SystemExit) as ei:
            _grep()
        assert ei.value.code == 1

    def test_no_matching_line_raises_system_exit(self, repo_dir):
        prepare_merge_repo_with_version(repo_dir, _VERSION_FILE, "unreleased\n")
        with pytest.raises(SystemExit) as ei:
            _grep()
        assert ei.value.code == 1
