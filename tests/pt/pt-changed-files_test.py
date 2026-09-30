"""
pt-changed-files_test.py

tests for `get_changed_file_paths` in `changed_files.py`: only the
staged files count, and a git failure aborts with exit code 1
"""

from unittest import mock

import git
import pytest

from prep_repo import prepare_repo_with_files

from hupy.pt.changed_files import get_changed_file_paths

# auxiliaries  #################################################################


def _get_paths(repo_dir, bucket, files):
    """
    :return: paths reported for the repo prepared with ``files``
    :rtype: list[str]
    """
    prepare_repo_with_files(repo_dir, bucket, files)
    return get_changed_file_paths(git.Repo(str(repo_dir)))


# tests  ########################################################################


class TestGetChangedFilePaths:
    def test_single_staged_file_is_returned(self, repo_dir):
        result = _get_paths(
            repo_dir, "non_merge_commit", {"feature.py": "tt_none.py"}
        )
        assert result == ["feature.py"]

    def test_multiple_staged_files_are_all_returned(self, repo_dir):
        result = _get_paths(
            repo_dir,
            "non_merge_commit",
            {"a.py": "tt_none.py", "b.py": "tt_none.py"},
        )
        assert sorted(result) == ["a.py", "b.py"]

    def test_merge_scenario_returns_staged_files(self, repo_dir):
        result = _get_paths(
            repo_dir, "feature_landing", {"feature.py": "tt_none.py"}
        )
        assert "feature.py" in result

    def test_nothing_staged_returns_empty_list(self, repo_dir):
        assert _get_paths(repo_dir, "non_merge_commit", {}) == []

    def test_committed_file_is_not_returned(self, repo_dir):
        prepare_repo_with_files(repo_dir, "non_merge_commit", {})
        repo = git.Repo(str(repo_dir))
        (repo_dir / "old.py").write_text("x = 1\n")
        repo.index.add(["old.py"])
        repo.index.commit("add old.py")
        assert get_changed_file_paths(repo) == []


class TestGetChangedFilePathsError:
    def test_git_diff_failure_raises_system_exit(self, repo_dir):
        prepare_repo_with_files(repo_dir, "non_merge_commit", {})
        repo = git.Repo(str(repo_dir))
        with mock.patch.object(
            git.Git,
            "diff",
            create=True,
            side_effect=git.GitCommandError("git diff", 1),
        ):
            with pytest.raises(SystemExit) as exc_info:
                get_changed_file_paths(repo)
        assert exc_info.value.code == 1

    def test_git_diff_permission_error_raises_system_exit(self, repo_dir):
        prepare_repo_with_files(repo_dir, "non_merge_commit", {})
        repo = git.Repo(str(repo_dir))
        with mock.patch.object(
            git.Git,
            "diff",
            create=True,
            side_effect=git.GitCommandError(
                "git diff", 128, stderr="fatal: Permission denied"
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                get_changed_file_paths(repo)
        assert exc_info.value.code == 1
