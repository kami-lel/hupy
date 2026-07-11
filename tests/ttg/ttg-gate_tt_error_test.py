"""
ttg-gate_tt_error_test.py

tests for error handling in `perform_triage_tags_gating` in `gate_tt.py`
"""

from unittest import mock

import git
import pytest

from hupy.state.state_file import HupyStateFile
from hupy.ttg.gate_tt import perform_triage_tags_gating
from prep_repo import prepare_repo_with_files

_STATE_FILE = HupyStateFile()


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
        test that a git error running `git diff --cached --name-only`
        causes SystemExit(1); uses a feature_landing merge scenario so
        TTG actually runs.
        """
        prepare_repo_with_files(
            repo_dir, "feature_landing", {"test.py": "tt_none.py"}
        )
        repo = git.Repo(str(repo_dir))
        with mock.patch.object(
            git.Git,
            "diff",
            create=True,
            side_effect=git.GitCommandError("git diff", 1),
        ):
            with pytest.raises(SystemExit) as exc_info:
                perform_triage_tags_gating(repo, _STATE_FILE)

            assert exc_info.value.code == 1

    def test_git_diff_cached_name_only_permission_error(self, repo_dir):
        """
        test that a permission error from git diff raises SystemExit(1);
        uses a version_release merge scenario so TTG actually runs.
        """
        prepare_repo_with_files(
            repo_dir, "version_release", {"test.py": "tt_none.py"}
        )
        repo = git.Repo(str(repo_dir))
        with mock.patch.object(
            git.Git,
            "diff",
            create=True,
            side_effect=git.GitCommandError(
                "git diff", 128, "fatal: Permission denied"
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                perform_triage_tags_gating(repo, _STATE_FILE)

            assert exc_info.value.code == 1

    def test_git_diff_cached_name_only_generic_error(self, repo_dir):
        """
        test that a generic git error during name-only diff raises
        SystemExit(1); uses a feature_landing merge scenario so TTG runs.
        """
        prepare_repo_with_files(
            repo_dir, "feature_landing", {"test.py": "tt_none.py"}
        )
        repo = git.Repo(str(repo_dir))
        with mock.patch.object(
            git.Git,
            "diff",
            create=True,
            side_effect=git.GitCommandError(
                "git diff", 1, "fatal: unknown error"
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                perform_triage_tags_gating(repo, _STATE_FILE)

            assert exc_info.value.code == 1
