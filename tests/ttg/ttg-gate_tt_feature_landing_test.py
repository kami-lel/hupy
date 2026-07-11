"""
ttg-gate_tt_feature_landing_test.py

tests for `perform_triage_tags_gating` on Feature Landing merges
(gates on LOUD triage tags only)
"""

import git
import pytest

from hupy.state.state_file import HupyStateFile
from hupy.ttg.gate_tt import perform_triage_tags_gating
from prep_repo import prepare_repo_with_files

_STATE_FILE = HupyStateFile()

_BUCKET = "feature_landing"


# helpers  ######################################################################


def _assert_gated(repo_dir, files):
    prepare_repo_with_files(repo_dir, _BUCKET, files)
    with pytest.raises(SystemExit) as exc_info:
        perform_triage_tags_gating(git.Repo(str(repo_dir)), _STATE_FILE)
    assert exc_info.value.code == 1


def _assert_passes(repo_dir, files):
    prepare_repo_with_files(repo_dir, _BUCKET, files)
    perform_triage_tags_gating(git.Repo(str(repo_dir)), _STATE_FILE)


# tests  ########################################################################


class TestFeatureFinishSingleFile:
    def test_loud_only_is_gated(self, repo_dir):
        _assert_gated(repo_dir, {"feature.py": "tt_loud_only.py"})

    def test_steady_only_passes(self, repo_dir):
        _assert_passes(repo_dir, {"feature.py": "tt_steady_only.py"})

    def test_quiet_only_passes(self, repo_dir):
        _assert_passes(repo_dir, {"feature.py": "tt_quiet_only.py"})

    def test_loud_and_steady_is_gated(self, repo_dir):
        _assert_gated(repo_dir, {"feature.py": "tt_loud_and_steady.py"})

    def test_loud_and_quiet_is_gated(self, repo_dir):
        _assert_gated(repo_dir, {"feature.py": "tt_loud_and_quiet.py"})

    def test_steady_and_quiet_passes(self, repo_dir):
        _assert_passes(repo_dir, {"feature.py": "tt_steady_and_quiet.py"})

    def test_loud_steady_quiet_is_gated(self, repo_dir):
        _assert_gated(repo_dir, {"feature.py": "tt_loud_steady_quiet.py"})

    def test_multiple_loud_tags_is_gated(self, repo_dir):
        _assert_gated(repo_dir, {"feature.py": "tt_2loud.py"})

    def test_multiple_quiet_tags_only_passes(self, repo_dir):
        _assert_passes(repo_dir, {"feature.py": "tt_3quiet.py"})

    def test_multiple_quiet_and_one_steady_passes(self, repo_dir):
        _assert_passes(repo_dir, {"feature.py": "tt_2quiet_1steady.py"})

    def test_one_loud_and_multiple_steady_is_gated(self, repo_dir):
        _assert_gated(repo_dir, {"feature.py": "tt_1loud_2steady.py"})


class TestFeatureFinishMultipleFiles:
    def test_none_have_tt_passes(self, repo_dir):
        _assert_passes(
            repo_dir,
            {"a.py": "tt_none.py", "b.py": "tt_none.py"},
        )

    def test_only_safe_tiers_pass(self, repo_dir):
        _assert_passes(
            repo_dir,
            {"a.py": "tt_steady_only.py", "b.py": "tt_quiet_only.py"},
        )

    def test_one_file_has_loud_is_gated(self, repo_dir):
        _assert_gated(
            repo_dir,
            {
                "a.py": "tt_loud_only.py",
                "b.py": "tt_none.py",
                "c.py": "tt_steady_only.py",
            },
        )

    def test_all_files_have_loud_is_gated(self, repo_dir):
        _assert_gated(
            repo_dir,
            {"a.py": "tt_loud_only.py", "b.py": "tt_loud_only.py"},
        )
