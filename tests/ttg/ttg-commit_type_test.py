"""
ttg-commit_type_test.py

tests for the `get_current_commit_type` function in `commit_type.py`
"""

from pathlib import Path

import git
import pytest

from hupy.commit_type import CommitType, get_current_commit_type

_TESTEE_ROOT = Path(__file__).parent.parent / "testee"


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


@pytest.fixture
def repo(repo_dir):
    """return a git.Repo for the repo_dir."""
    return git.Repo(str(repo_dir))


# helpers  ######################################################################


def _sha(repo_dir, ref):
    """get the sha of a ref in the repo."""
    repo = git.Repo(str(repo_dir))
    return repo.git.rev_parse(ref)


def _write_merge_head(repo_dir, *shas):
    """write MERGE_HEAD file with the given shas."""
    (repo_dir / ".git" / "MERGE_HEAD").write_text("\n".join(shas) + "\n")


def _commit(repo_dir, msg):
    """create a commit with the given message."""
    repo = git.Repo(str(repo_dir))
    (repo_dir / msg).write_text(msg)
    repo.index.add([msg])
    repo.index.commit(msg)


# tests  ########################################################################


class TestGetCurrentCommitType:
    def test_no_merge_head_is_other_commit(self, repo_dir):
        assert get_current_commit_type(str(repo_dir)) == CommitType.OTHER_COMMIT

    def test_octopus_merge_is_other_merge(self, repo_dir):
        _write_merge_head(
            repo_dir,
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        )
        assert get_current_commit_type(str(repo_dir)) == CommitType.OTHER_MERGE

    def test_pull_merge_is_other_merge(self, repo, repo_dir):
        repo.git.checkout("-q", "-b", "develop")
        _commit(repo_dir, "develop")
        sha_develop = _sha(repo_dir, "develop")
        repo.git.remote("remove", "origin")
        repo.git.remote("add", "origin", "https://example.invalid/repo.git")
        repo.git.update_ref("refs/remotes/origin/develop", sha_develop)
        repo.git.checkout("-q", "develop")
        _write_merge_head(repo_dir, sha_develop)
        assert get_current_commit_type(str(repo_dir)) == CommitType.OTHER_MERGE

    def test_feature_finish_merge(self, repo, repo_dir):
        repo.git.checkout("-q", "-b", "develop")
        _commit(repo_dir, "develop")
        repo.git.checkout("-q", "-b", "feature/x")
        _commit(repo_dir, "feature")
        sha_feature = _sha(repo_dir, "feature/x")
        repo.git.checkout("-q", "develop")
        _write_merge_head(repo_dir, sha_feature)
        assert (
            get_current_commit_type(str(repo_dir)) == CommitType.FEATURE_FINISH
        )

    def test_version_release_merge(self, repo, repo_dir):
        repo.git.checkout("-q", "-b", "develop")
        _commit(repo_dir, "develop")
        sha_develop = _sha(repo_dir, "develop")
        repo.git.checkout("-q", "main")
        _write_merge_head(repo_dir, sha_develop)
        assert (
            get_current_commit_type(str(repo_dir)) == CommitType.VERSION_RELEASE
        )

    def test_main_to_develop_boundary_is_other_merge(self, repo, repo_dir):
        sha_main = _sha(repo_dir, "main")
        repo.git.checkout("-q", "-b", "develop")
        _commit(repo_dir, "develop")
        _write_merge_head(repo_dir, sha_main)
        assert get_current_commit_type(str(repo_dir)) == CommitType.OTHER_MERGE

    def test_unrelated_branches_merge_is_other_merge(self, repo, repo_dir):
        repo.git.checkout("-q", "-b", "hotfix")
        _commit(repo_dir, "hotfix")
        sha_hotfix = _sha(repo_dir, "hotfix")
        repo.git.checkout("-q", "-b", "release")
        _commit(repo_dir, "release")
        _write_merge_head(repo_dir, sha_hotfix)
        assert get_current_commit_type(str(repo_dir)) == CommitType.OTHER_MERGE

    def test_detached_head_merge_is_other_merge(self, repo, repo_dir):
        repo.git.checkout("-q", "-b", "feature/x")
        _commit(repo_dir, "feature")
        sha_feature = _sha(repo_dir, "feature/x")
        repo.git.checkout("-q", sha_feature)
        _write_merge_head(repo_dir, sha_feature)
        assert get_current_commit_type(str(repo_dir)) == CommitType.OTHER_MERGE

    def test_missing_repo_path_raises(self, tmp_path):
        with pytest.raises(git.NoSuchPathError):
            get_current_commit_type(str(tmp_path / "does_not_exist"))
