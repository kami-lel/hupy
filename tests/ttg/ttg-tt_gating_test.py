"""
ttg-tt_gating_test.py

tests for `perform_triage_tags_gating` in `tt_gating.py`
"""

import pytest

from hupy.ttg.tt_gating import perform_triage_tags_gating
from prep_repo import prepare_repo

# fixtures  #####################################################################


@pytest.fixture
def repo_dir(tmp_path):
    """path for the scenario repo; created by ``prepare_repo``."""
    return tmp_path / "repo"


# tests  ########################################################################

# TODO more comprehensive unit tests


class TestPerformTriageTagsGating:
    def test_non_merge_commit_is_skipped(self, repo_dir):
        prepare_repo(repo_dir, "non_merge_commit")
        perform_triage_tags_gating(str(repo_dir))

    def test_irrelevant_merge_is_skipped(self, repo_dir):
        prepare_repo(repo_dir, "irrelevant_merge")
        perform_triage_tags_gating(str(repo_dir))

    def test_feature_finish_with_loud_tt_is_gated(self, repo_dir):
        prepare_repo(repo_dir, "feature_finish_loud")
        with pytest.raises(SystemExit) as exc_info:
            perform_triage_tags_gating(str(repo_dir))
        assert exc_info.value.code == 1

    def test_feature_finish_with_steady_tt_only_passes(self, repo_dir):
        prepare_repo(repo_dir, "feature_finish_steady_only")
        perform_triage_tags_gating(str(repo_dir))

    def test_version_release_with_steady_tt_is_gated(self, repo_dir):
        prepare_repo(repo_dir, "version_release_steady")
        with pytest.raises(SystemExit) as exc_info:
            perform_triage_tags_gating(str(repo_dir))
        assert exc_info.value.code == 1

    def test_version_release_with_quiet_tt_only_passes(self, repo_dir):
        prepare_repo(repo_dir, "version_release_quiet_only")
        perform_triage_tags_gating(str(repo_dir))
