"""
ttg-tt_detect_test.py

tests for triage tag detection in `tt_detect.py`
"""

import shutil
import subprocess
from pathlib import Path
from unittest import mock

import git
import pytest

from hupy.ttg.tt_detect import (
    TriageTagType,
    detect_triage_tags_in_staged_file,
)

_TESTEE_ROOT = Path(__file__).parent.parent / "testee"
_FIXTURES_ROOT = _TESTEE_ROOT / "ttg"


# fixtures  #####################################################################


@pytest.fixture
def repo_dir(tmp_path):
    """clone the default_repo bundle to tmp_path."""
    dest = tmp_path / "repo"
    git.Repo.clone_from(
        str(_TESTEE_ROOT / "default_repo.bundle"),
        str(dest),
        branch="main",
    )
    return dest


# helpers  ######################################################################


def _stage_fixture(repo_dir, filename, fixture_name):
    """copy fixture file and stage it in the repo."""
    src = str(_FIXTURES_ROOT / fixture_name)
    dst = str(Path(repo_dir) / filename)
    shutil.copyfile(src, dst)
    repo = git.Repo(str(repo_dir))
    repo.index.add([filename])


# tests  ########################################################################


class TestDetectTriageTagsInStagedFile:
    def test_detects_loud_tag(self, repo_dir):
        _stage_fixture(repo_dir, "test.py", "tt_loud_only.py")

        results = detect_triage_tags_in_staged_file("test.py", repo_dir)

        assert len(results) == 1
        tag, line = results[0]
        assert tag == TriageTagType.LOUD_TODO
        assert "TODO" in line

    def test_detects_multiple_tags_in_file(self, repo_dir):
        _stage_fixture(repo_dir, "test.py", "tt_2loud.py")

        results = detect_triage_tags_in_staged_file("test.py", repo_dir)

        assert len(results) == 2
        tags = [tag for tag, _ in results]
        assert all(tag in TriageTagType.LOUDS for tag in tags)
        assert TriageTagType.LOUD_TODO in tags
        assert TriageTagType.LOUD_BUG in tags

    def test_subprocess_error_raises_system_exit(self, repo_dir):
        with mock.patch(
            "hupy.ttg.tt_detect.subprocess.check_output",
            side_effect=subprocess.CalledProcessError(1, "git"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                detect_triage_tags_in_staged_file("test.py", str(repo_dir))

            assert exc_info.value.code == 1

    def test_subprocess_error_on_missing_file(self, repo_dir):
        with mock.patch(
            "hupy.ttg.tt_detect.subprocess.check_output",
            side_effect=subprocess.CalledProcessError(
                128, "git", stderr="fatal: not a git repo"
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                detect_triage_tags_in_staged_file("missing.py", str(repo_dir))

            assert exc_info.value.code == 1

    def test_ignores_deleted_lines(self, repo_dir):
        repo = git.Repo(str(repo_dir))
        _stage_fixture(repo_dir, "test.py", "tt_loud_only.py")
        repo.index.commit("initial")

        _stage_fixture(repo_dir, "test.py", "tt_loud_and_steady.py")

        results = detect_triage_tags_in_staged_file("test.py", repo_dir)

        # Should detect only the newly added steady tag (loud was already there)
        assert len(results) == 1
        assert results[0][0] == TriageTagType.STEADY_TODO

    def test_returns_empty_list_for_file_without_tags(self, repo_dir):
        _stage_fixture(repo_dir, "test.py", "tt_none.py")

        results = detect_triage_tags_in_staged_file("test.py", repo_dir)

        assert results == []
