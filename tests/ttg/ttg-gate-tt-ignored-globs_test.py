"""
ttg-gate-tt-ignored-globs_test.py

tests for `perform_triage_tags_gating` respecting the
`ttg.ignored_path_globs` config: staged files matching a configured
glob must be skipped from TT scanning entirely
"""

from unittest import mock

import git
import pytest

from config_fixture import load_config_fixture
from prep_repo import prepare_repo_with_files

from hupy.ttg.gate_tt import perform_triage_tags_gating
from hupy.state.state_file import HupyStateFile

_BUCKET = "feature_landing"
_STATE_FILE = HupyStateFile()


# helpers  ######################################################################


def _run(repo_dir, files, ignored_path_globs):
    prepare_repo_with_files(repo_dir, _BUCKET, files)
    config = load_config_fixture(
        overrides={"ttg": {"ignored_path_globs": list(ignored_path_globs)}}
    )
    with mock.patch(
        "hupy.ttg.gate_tt.load_hupy_config", return_value=config
    ), mock.patch(
        "hupy.should_run_module.load_hupy_config", return_value=config
    ):
        perform_triage_tags_gating(git.Repo(str(repo_dir)), _STATE_FILE)


def _assert_gated(repo_dir, files, ignored_path_globs=()):
    with pytest.raises(SystemExit) as exc_info:
        _run(repo_dir, files, ignored_path_globs)
    assert exc_info.value.code == 1


def _assert_passes(repo_dir, files, ignored_path_globs=()):
    _run(repo_dir, files, ignored_path_globs)


# tests  ########################################################################


class TestIgnoredPathGlobsSingleFile:
    def test_no_globs_configured_gates_as_before(self, repo_dir):
        _assert_gated(repo_dir, {"feature.py": "tt_loud_only.py"})

    def test_exact_match_glob_skips_file(self, repo_dir):
        _assert_passes(
            repo_dir,
            {"feature.py": "tt_loud_only.py"},
            ignored_path_globs=["feature.py"],
        )

    def test_wildcard_glob_skips_file(self, repo_dir):
        _assert_passes(
            repo_dir,
            {"feature.py": "tt_loud_only.py"},
            ignored_path_globs=["*.py"],
        )

    def test_non_matching_glob_still_gates(self, repo_dir):
        _assert_gated(
            repo_dir,
            {"feature.py": "tt_loud_only.py"},
            ignored_path_globs=["*.md"],
        )

    def test_one_of_multiple_globs_matches_skips_file(self, repo_dir):
        _assert_passes(
            repo_dir,
            {"feature.py": "tt_loud_only.py"},
            ignored_path_globs=["*.md", "feature.py", "*.txt"],
        )


class TestIgnoredPathGlobsMultipleFiles:
    def test_ignored_file_skipped_while_other_still_gates(self, repo_dir):
        _assert_gated(
            repo_dir,
            {"a.py": "tt_loud_only.py", "b.py": "tt_loud_only.py"},
            ignored_path_globs=["a.py"],
        )

    def test_all_matching_glob_passes(self, repo_dir):
        _assert_passes(
            repo_dir,
            {"a.py": "tt_loud_only.py", "b.py": "tt_loud_only.py"},
            ignored_path_globs=["*.py"],
        )

    def test_ignored_file_with_safe_tier_still_passes(self, repo_dir):
        _assert_passes(
            repo_dir,
            {"a.py": "tt_loud_only.py", "b.py": "tt_steady_only.py"},
            ignored_path_globs=["a.py"],
        )
