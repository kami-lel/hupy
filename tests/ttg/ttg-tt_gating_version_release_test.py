"""
ttg-tt_gating_version_release_test.py

tests for `perform_triage_tags_gating` on Version Release merges
(gates on LOUD and STEADY triage tags)
"""

import pytest

from hupy.ttg.tt_gating import perform_triage_tags_gating
from prep_repo import prepare_repo_with_files

_BUCKET = "version_release"


# helpers  ######################################################################


def _assert_gated(repo_dir, files):
    prepare_repo_with_files(repo_dir, _BUCKET, files)
    with pytest.raises(SystemExit) as exc_info:
        perform_triage_tags_gating(str(repo_dir))
    assert exc_info.value.code == 1


def _assert_passes(repo_dir, files):
    prepare_repo_with_files(repo_dir, _BUCKET, files)
    perform_triage_tags_gating(str(repo_dir))


# tests  ########################################################################


class TestVersionReleaseSingleFile:
    def test_loud_only_is_gated(self, repo_dir):
        _assert_gated(repo_dir, {"release.py": "tt_loud_only.py"})

    def test_steady_only_is_gated(self, repo_dir):
        _assert_gated(repo_dir, {"release.py": "tt_steady_only.py"})

    def test_quiet_only_passes(self, repo_dir):
        _assert_passes(repo_dir, {"release.py": "tt_quiet_only.py"})

    def test_loud_and_steady_is_gated(self, repo_dir):
        _assert_gated(repo_dir, {"release.py": "tt_loud_and_steady.py"})

    def test_loud_and_quiet_is_gated(self, repo_dir):
        _assert_gated(repo_dir, {"release.py": "tt_loud_and_quiet.py"})

    def test_steady_and_quiet_is_gated(self, repo_dir):
        _assert_gated(repo_dir, {"release.py": "tt_steady_and_quiet.py"})

    def test_loud_steady_quiet_is_gated(self, repo_dir):
        _assert_gated(repo_dir, {"release.py": "tt_loud_steady_quiet.py"})

    def test_multiple_loud_tags_is_gated(self, repo_dir):
        _assert_gated(repo_dir, {"release.py": "tt_2loud.py"})

    def test_multiple_quiet_tags_only_passes(self, repo_dir):
        _assert_passes(repo_dir, {"release.py": "tt_3quiet.py"})

    def test_multiple_quiet_and_one_steady_is_gated(self, repo_dir):
        _assert_gated(repo_dir, {"release.py": "tt_2quiet_1steady.py"})

    def test_one_loud_and_multiple_steady_is_gated(self, repo_dir):
        _assert_gated(repo_dir, {"release.py": "tt_1loud_2steady.py"})


class TestVersionReleaseMultipleFiles:
    def test_none_have_tt_passes(self, repo_dir):
        _assert_passes(
            repo_dir,
            {"a.py": "tt_none.py", "b.py": "tt_none.py"},
        )

    def test_only_quiet_tier_passes(self, repo_dir):
        _assert_passes(
            repo_dir,
            {"a.py": "tt_quiet_only.py", "b.py": "tt_quiet_only.py"},
        )

    def test_one_file_has_steady_is_gated(self, repo_dir):
        _assert_gated(
            repo_dir,
            {
                "a.py": "tt_steady_only.py",
                "b.py": "tt_none.py",
                "c.py": "tt_quiet_only.py",
            },
        )

    def test_mixed_gating_tiers_across_files_is_gated(self, repo_dir):
        _assert_gated(
            repo_dir,
            {"a.py": "tt_loud_only.py", "b.py": "tt_steady_only.py"},
        )
