"""
ttg-tt_gating_error_test.py

tests for error handling in `perform_triage_tags_gating` in `tt_gating.py`
"""

import subprocess
from unittest import mock

import pytest

from hupy.ttg.tt_gating import perform_triage_tags_gating
from prep_repo import prepare_repo_with_files


# fixtures  #####################################################################


@pytest.fixture
def repo_dir(tmp_path):
    """path for the scenario repo; created by ``prepare_repo_with_files``."""
    return tmp_path / "repo"


# tests  ########################################################################


class TestPerformTriageTagsGatingErrors:
    def test_git_diff_cached_name_only_failure_raises_system_exit(
        self, repo_dir
    ):
        """
        test that subprocess.CalledProcessError when running
        `git diff --cached --name-only` causes SystemExit(1).
        uses a feature_finish merge scenario so TTG actually runs.
        """
        prepare_repo_with_files(
            repo_dir, "feature_finish", {"test.py": "tt_none.py"}
        )
        with mock.patch(
            "hupy.ttg.tt_gating.subprocess.check_output",
            side_effect=subprocess.CalledProcessError(1, "git"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                perform_triage_tags_gating(str(repo_dir))

            assert exc_info.value.code == 1

    def test_git_diff_cached_name_only_permission_error(self, repo_dir):
        """
        test that permission error from git diff raises SystemExit(1).
        uses a version_release merge scenario so TTG actually runs.
        """
        prepare_repo_with_files(
            repo_dir, "version_release", {"test.py": "tt_none.py"}
        )
        with mock.patch(
            "hupy.ttg.tt_gating.subprocess.check_output",
            side_effect=subprocess.CalledProcessError(
                128, "git", stderr="fatal: Permission denied"
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                perform_triage_tags_gating(str(repo_dir))

            assert exc_info.value.code == 1

    def test_git_diff_cached_name_only_generic_error(self, repo_dir):
        """
        test that generic git error during name-only diff raises SystemExit(1).
        uses a feature_finish merge scenario so TTG actually runs.
        """
        prepare_repo_with_files(
            repo_dir, "feature_finish", {"test.py": "tt_none.py"}
        )
        with mock.patch(
            "hupy.ttg.tt_gating.subprocess.check_output",
            side_effect=subprocess.CalledProcessError(
                1, "git", stderr="fatal: unknown error"
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                perform_triage_tags_gating(str(repo_dir))

            assert exc_info.value.code == 1
