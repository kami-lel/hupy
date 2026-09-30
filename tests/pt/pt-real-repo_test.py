"""
pt-real-repo_test.py

end-to-end tests for `perform_paper_trail` against real scenario
repos: only config loading is stubbed, git and commit-type detection
run for real
"""

from unittest import mock

import git
import pytest

from config_fixture import load_config_fixture
from prep_repo import prepare_repo_with_files

from hupy.pt.perform_paper_trail import perform_paper_trail
from hupy.state.state_file import HupyStateFile

_STATE_FILE = HupyStateFile()

# auxiliaries  #################################################################


def _changelog_for(commit_type_name):
    return [
        {"glob": "CHANGELOG.md", "allow_commit_types": [commit_type_name]}
    ]


def _run(repo_dir, bucket, files, paper_trails):
    prepare_repo_with_files(repo_dir, bucket, files)
    config = load_config_fixture(
        overrides={"pt": {"trails": list(paper_trails)}}
    )
    with mock.patch(
        "hupy.pt.perform_paper_trail.load_hupy_config", return_value=config
    ), mock.patch(
        "hupy.should_run_module.load_hupy_config", return_value=config
    ):
        perform_paper_trail(
            git.Repo(str(repo_dir)), _STATE_FILE, "pre-commit"
        )


def _assert_gated(*args):
    with pytest.raises(SystemExit) as exc_info:
        _run(*args)
    assert exc_info.value.code == 1


# tests  ########################################################################


class TestPerformPaperTrailRealRepo:
    def test_non_merge_commit_with_matching_staged_file_passes(
        self, repo_dir
    ):
        _run(
            repo_dir,
            "non_merge_commit",
            {"CHANGELOG.md": "tt_none.py"},
            [{"glob": "CHANGELOG.md"}],
        )

    def test_non_merge_commit_without_matching_file_aborts(self, repo_dir):
        _assert_gated(
            repo_dir,
            "non_merge_commit",
            {"feature.py": "tt_none.py"},
            [{"glob": "CHANGELOG.md"}],
        )

    def test_feature_landing_filter_enforced_on_feature_landing_merge(
        self, repo_dir
    ):
        _assert_gated(
            repo_dir,
            "feature_landing",
            {"feature.py": "tt_none.py"},
            _changelog_for("FEATURE_LANDING"),
        )

    def test_feature_landing_filter_skipped_on_regular_commit(
        self, repo_dir
    ):
        _run(
            repo_dir,
            "non_merge_commit",
            {"feature.py": "tt_none.py"},
            _changelog_for("FEATURE_LANDING"),
        )

    def test_version_release_filter_enforced_on_version_release_merge(
        self, repo_dir
    ):
        _assert_gated(
            repo_dir,
            "version_release",
            {"feature.py": "tt_none.py"},
            _changelog_for("VERSION_RELEASE"),
        )
