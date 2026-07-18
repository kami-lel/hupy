"""
ttg-detect-tt_test.py

tests for triage tag detection in `detect_tt.py`
"""

import shutil
from pathlib import Path
from unittest import mock

import git
import pytest

from hupy.ttg.detect_tt import detect_triage_tags_in_staged_file
from hupy.ttg.triage_tag_type import TriageTagType

_FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
_FIXTURES_ROOT = Path(__file__).parent / "fixtures"


# fixtures  #####################################################################


@pytest.fixture
def repo_dir(tmp_path):
    """clone the default_repo bundle to tmp_path."""
    dest = tmp_path / "repo"
    git.Repo.clone_from(
        str(_FIXTURES_DIR / "default_repo.bundle"),
        str(dest),
        branch="main",
    )
    return dest


# auxiliaries  #################################################################


def _stage_fixture(repo_dir, filename, fixture_name):
    """copy fixture file, stage it, and return the repo."""
    src = str(_FIXTURES_ROOT / fixture_name)
    dst = str(Path(repo_dir) / filename)
    shutil.copyfile(src, dst)
    repo = git.Repo(str(repo_dir))
    repo.index.add([filename])
    return repo


# tests  ########################################################################


class TestDetectTriageTagsInStagedFile:
    def test_detects_loud_tag(self, repo_dir):
        repo = _stage_fixture(repo_dir, "test.py", "tt_loud_only.py")

        results = detect_triage_tags_in_staged_file("test.py", repo)

        assert len(results) == 1
        tag, line, line_no = results[0]
        assert tag == TriageTagType.LOUD_TODO
        assert "TODO" in line

    def test_detects_multiple_tags_in_file(self, repo_dir):
        repo = _stage_fixture(repo_dir, "test.py", "tt_2loud.py")

        results = detect_triage_tags_in_staged_file("test.py", repo)

        assert len(results) == 2
        tags = [tag for tag, _, _ in results]
        assert all(tag in TriageTagType.LOUDS for tag in tags)
        assert TriageTagType.LOUD_TODO in tags
        assert TriageTagType.LOUD_BUG in tags

    def test_git_error_raises_system_exit(self, repo_dir):
        repo = git.Repo(str(repo_dir))
        with mock.patch.object(
            git.Git,
            "diff",
            create=True,
            side_effect=git.GitCommandError("git diff", 1),
        ):
            with pytest.raises(SystemExit) as exc_info:
                detect_triage_tags_in_staged_file("test.py", repo)

            assert exc_info.value.code == 1

    def test_git_error_on_missing_file(self, repo_dir):
        repo = git.Repo(str(repo_dir))
        with mock.patch.object(
            git.Git,
            "diff",
            create=True,
            side_effect=git.GitCommandError(
                "git diff", 128, "fatal: path does not exist"
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                detect_triage_tags_in_staged_file("missing.py", repo)

            assert exc_info.value.code == 1

    def test_only_flags_lines_added_by_this_diff(self, repo_dir):
        repo = git.Repo(str(repo_dir))
        _stage_fixture(repo_dir, "test.py", "tt_loud_only.py")
        repo.index.commit("initial")

        _stage_fixture(repo_dir, "test.py", "tt_loud_and_steady.py")

        results = detect_triage_tags_in_staged_file("test.py", repo)

        assert len(results) == 1
        assert results[0][0] == TriageTagType.STEADY_TODO

    def test_returns_empty_list_for_file_without_tags(self, repo_dir):
        repo = _stage_fixture(repo_dir, "test.py", "tt_none.py")

        results = detect_triage_tags_in_staged_file("test.py", repo)

        assert results == []

    def test_detects_tag_after_c_style_comment_leader(self, repo_dir):
        repo = _stage_fixture(repo_dir, "test.c", "tt_loud_only.c")

        results = detect_triage_tags_in_staged_file("test.c", repo)

        assert len(results) == 1
        assert results[0][0] == TriageTagType.LOUD_TODO

    def test_detects_tag_after_html_comment_leader(self, repo_dir):
        repo = _stage_fixture(repo_dir, "test.html", "tt_loud_only.html")

        results = detect_triage_tags_in_staged_file("test.html", repo)

        assert len(results) == 1
        assert results[0][0] == TriageTagType.LOUD_TODO

    def test_ignores_tag_not_after_expected_comment_leader(self, repo_dir):
        repo = _stage_fixture(repo_dir, "test.py", "tt_bare_in_string.py")

        results = detect_triage_tags_in_staged_file("test.py", repo)

        assert results == []

    def test_falls_back_to_bare_match_for_unmapped_extension(self, repo_dir):
        repo = _stage_fixture(repo_dir, "test.md2", "tt_bare_in_string.py")

        results = detect_triage_tags_in_staged_file("test.md2", repo)

        assert len(results) == 1
        assert results[0][0] == TriageTagType.LOUD_TODO

    def test_falls_back_to_bare_match_for_no_extension(self, repo_dir):
        repo = _stage_fixture(repo_dir, "ttg_demo_note", "ttg_demo_note")

        results = detect_triage_tags_in_staged_file("ttg_demo_note", repo)

        assert len(results) == 1
        assert results[0][0] == TriageTagType.LOUD_FIXME

    def test_disable_tt_detect_by_type_matches_bare_tag(self, repo_dir):
        repo = _stage_fixture(repo_dir, "test.py", "tt_bare_in_string.py")

        results = detect_triage_tags_in_staged_file(
            "test.py", repo, disable_tt_detect_by_type=True
        )

        assert len(results) == 1
        assert results[0][0] == TriageTagType.LOUD_TODO
