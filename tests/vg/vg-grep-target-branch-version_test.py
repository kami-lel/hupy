"""
vg-grep-target-branch-version_test.py

tests for `grep_target_branch_version` in `branch_version.py`
"""

from unittest import mock

from config_fixture import load_config_fixture

from hupy.state.state_file import HupyStateFile
from hupy.ver_grep import grep_target_branch_version

_VERSION_FILE = "VERSION"
_PATTERN = r"(\d+\.\d+\.\d+)"

_STATE_FILE = HupyStateFile()


# auxiliaries  #################################################################


def _grep(repo, pattern=_PATTERN, version_file=_VERSION_FILE):
    """
    run ``grep_target_branch_version`` against a stubbed config
    carrying ``version_file`` and ``pattern``, bypassing disk/git
    config loading.
    """
    config = load_config_fixture(
        overrides={
            "vg": {
                "version_file": version_file,
                "version_line_pattern": pattern,
            }
        }
    )
    with mock.patch(
        "hupy.ver_grep.ver_grep.load_hupy_config", return_value=config
    ):
        return grep_target_branch_version(repo, _STATE_FILE)


# tests  ########################################################################


class TestGrepTargetBranchVersionMatch:
    def test_returns_captured_group_from_target_branch(
        self, make_merge_repo_with_version
    ):
        repo = make_merge_repo_with_version(
            _VERSION_FILE,
            source_content="9.9.9\n",
            target_content="1.2.3\n",
        )
        assert _grep(repo) == "1.2.3"

    def test_reads_target_not_source_branch_content(
        self, make_merge_repo_with_version
    ):
        # mid-merge, the source branch tip holds "2.0.0"; the target
        # branch tip (read straight via git) must win
        repo = make_merge_repo_with_version(
            _VERSION_FILE,
            source_content="2.0.0\n",
            target_content="1.2.3\n",
        )
        assert _grep(repo) == "1.2.3"

    def test_returns_first_matching_line(self, make_merge_repo_with_version):
        repo = make_merge_repo_with_version(
            _VERSION_FILE,
            source_content="9.9.9\n",
            target_content="1.0.0\n2.0.0\n",
        )
        assert _grep(repo) == "1.0.0"

    def test_custom_pattern_with_capturing_group(
        self, make_merge_repo_with_version
    ):
        repo = make_merge_repo_with_version(
            "pyproject.toml",
            source_content='version = "9.9.9"\n',
            target_content='version = "4.5.6"\n',
        )
        assert (
            _grep(
                repo,
                pattern=r'version = "(.*)"',
                version_file="pyproject.toml",
            )
            == "4.5.6"
        )


class TestGrepTargetBranchVersionNotConfigured:
    def test_empty_version_file_returns_empty(
        self, make_merge_repo_with_version
    ):
        repo = make_merge_repo_with_version(
            _VERSION_FILE,
            source_content="9.9.9\n",
            target_content="1.2.3\n",
        )
        assert _grep(repo, version_file="") == ""

    def test_empty_pattern_returns_empty(self, make_merge_repo_with_version):
        repo = make_merge_repo_with_version(
            _VERSION_FILE,
            source_content="9.9.9\n",
            target_content="1.2.3\n",
        )
        assert _grep(repo, pattern="") == ""


class TestGrepTargetBranchVersionGracefulEmpty:
    def test_missing_version_file_on_target_branch_returns_empty(
        self, make_merge_repo_with_version
    ):
        # target_content omitted: the target branch never commits
        # _VERSION_FILE, only the source branch does
        repo = make_merge_repo_with_version(
            _VERSION_FILE, source_content="1.2.3\n"
        )
        assert _grep(repo) == ""

    def test_missing_version_file_on_both_branches_returns_empty(
        self, merge_repo_without_version_file
    ):
        assert _grep(merge_repo_without_version_file) == ""

    def test_no_matching_line_returns_empty(
        self, make_merge_repo_with_version
    ):
        repo = make_merge_repo_with_version(
            _VERSION_FILE,
            source_content="1.2.3\n",
            target_content="unreleased\n",
        )
        assert _grep(repo) == ""

    def test_pattern_without_capture_group_returns_empty(
        self, make_merge_repo_with_version
    ):
        repo = make_merge_repo_with_version(
            _VERSION_FILE,
            source_content="1.2.3\n",
            target_content="1.2.3\n",
        )
        assert _grep(repo, pattern=r"\d+\.\d+\.\d+") == ""
