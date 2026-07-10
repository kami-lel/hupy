"""
vg-grep_target_branch_version_test.py

tests for `grep_target_branch_version` in `branch_version.py`
"""

from unittest import mock

import pytest

from hupy.config.hupy_config_file import HupyConfigFile
from hupy.ver_grep import grep_target_branch_version
from vg_helpers import (
    prepare_merge_repo_with_version,
    prepare_merge_repo_without_version_file,
)

_VERSION_FILE = "VERSION"
_PATTERN = r"(\d+\.\d+\.\d+)"


# helpers  ######################################################################


def _grep(pattern=_PATTERN, version_file=_VERSION_FILE):
    """
    run ``grep_target_branch_version`` against a stubbed config
    carrying ``version_file`` and ``pattern``, bypassing disk/git
    config loading; the current working directory is expected to
    already be inside the prepared merge repo.
    """
    config = HupyConfigFile(
        ver_grep={"version_file": version_file, "version_line_pattern": pattern}
    )
    with mock.patch(
        "hupy.ver_grep.branch_version.load_hupy_config", return_value=config
    ):
        return grep_target_branch_version()


# tests  ########################################################################


class TestGrepTargetBranchVersionMatch:
    def test_returns_captured_group_from_target_branch(self, repo_dir):
        prepare_merge_repo_with_version(
            repo_dir, _VERSION_FILE, source_content="9.9.9\n", target_content="1.2.3\n"
        )
        assert _grep() == "1.2.3"

    def test_reads_target_not_source_branch_content(self, repo_dir):
        # mid-merge, the source branch tip holds "2.0.0"; the target
        # branch tip (read straight via git) must win
        prepare_merge_repo_with_version(
            repo_dir,
            _VERSION_FILE,
            source_content="2.0.0\n",
            target_content="1.2.3\n",
        )
        assert _grep() == "1.2.3"

    def test_returns_first_matching_line(self, repo_dir):
        prepare_merge_repo_with_version(
            repo_dir,
            _VERSION_FILE,
            source_content="9.9.9\n",
            target_content="1.0.0\n2.0.0\n",
        )
        assert _grep() == "1.0.0"

    def test_custom_pattern_with_capturing_group(self, repo_dir):
        prepare_merge_repo_with_version(
            repo_dir,
            "pyproject.toml",
            source_content='version = "9.9.9"\n',
            target_content='version = "4.5.6"\n',
        )
        assert (
            _grep(pattern=r'version = "(.*)"', version_file="pyproject.toml")
            == "4.5.6"
        )


class TestGrepTargetBranchVersionNotConfigured:
    def test_empty_version_file_returns_empty(self, repo_dir):
        prepare_merge_repo_with_version(
            repo_dir, _VERSION_FILE, source_content="9.9.9\n", target_content="1.2.3\n"
        )
        assert _grep(version_file="") == ""

    def test_empty_pattern_returns_empty(self, repo_dir):
        prepare_merge_repo_with_version(
            repo_dir, _VERSION_FILE, source_content="9.9.9\n", target_content="1.2.3\n"
        )
        assert _grep(pattern="") == ""


class TestGrepTargetBranchVersionErrors:
    def test_missing_version_file_on_target_branch_raises_system_exit(
        self, repo_dir
    ):
        # target_content omitted: the target branch never commits
        # _VERSION_FILE, only the source branch does
        prepare_merge_repo_with_version(
            repo_dir, _VERSION_FILE, source_content="1.2.3\n"
        )
        with pytest.raises(SystemExit) as ei:
            _grep()
        assert ei.value.code == 1

    def test_missing_version_file_on_both_branches_raises_system_exit(
        self, repo_dir
    ):
        prepare_merge_repo_without_version_file(repo_dir)
        with pytest.raises(SystemExit) as ei:
            _grep()
        assert ei.value.code == 1

    def test_no_matching_line_raises_system_exit(self, repo_dir):
        prepare_merge_repo_with_version(
            repo_dir,
            _VERSION_FILE,
            source_content="1.2.3\n",
            target_content="unreleased\n",
        )
        with pytest.raises(SystemExit) as ei:
            _grep()
        assert ei.value.code == 1
