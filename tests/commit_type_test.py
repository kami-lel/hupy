"""
commit_type_test.py

tests for the `get_current_commit_type` function in `commit_type.py`
"""

from pathlib import Path

import git
import pytest

from hupy.cbm import CommitType, get_current_commit_type
from hupy.config import CONFIG_FILENAME
from hupy.config.hupy_config_file import HupyConfigFile

_FIXTURES_DIR = Path(__file__).parent / "fixtures"


# FIXME rewrite ut


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
    (dest / CONFIG_FILENAME).write_text(HupyConfigFile().model_dump_json())
    return dest


@pytest.fixture
def repo(repo_dir):
    """return a git.Repo for the repo_dir."""
    return git.Repo(str(repo_dir))


@pytest.fixture
def dev_branch():
    """name of the dev branch used by the tests."""
    return "dev"


@pytest.fixture
def main_branch():
    """name of the main branch used by the tests."""
    return "main"


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

    def test_pull_merge_is_other_merge(self, repo, repo_dir, dev_branch):
        repo.git.checkout("-q", "-b", dev_branch)
        _commit(repo_dir, dev_branch)
        sha_dev = _sha(repo_dir, dev_branch)
        repo.git.remote("remove", "origin")
        repo.git.remote("add", "origin", "https://example.invalid/repo.git")
        repo.git.update_ref("refs/remotes/origin/{}".format(dev_branch), sha_dev)
        repo.git.checkout("-q", dev_branch)
        _write_merge_head(repo_dir, sha_dev)
        assert get_current_commit_type(str(repo_dir)) == CommitType.OTHER_MERGE

    def test_feature_landing_merge(self, repo, repo_dir, dev_branch):
        repo.git.checkout("-q", "-b", dev_branch)
        _commit(repo_dir, dev_branch)
        repo.git.checkout("-q", "-b", "add-user-authentication")
        _commit(repo_dir, "feature")
        sha_feature = _sha(repo_dir, "add-user-authentication")
        repo.git.checkout("-q", dev_branch)
        _write_merge_head(repo_dir, sha_feature)
        assert (
            get_current_commit_type(str(repo_dir)) == CommitType.FEATURE_LANDING
        )

    def test_version_release_merge(self, repo, repo_dir, dev_branch, main_branch):
        repo.git.checkout("-q", "-b", dev_branch)
        _commit(repo_dir, dev_branch)
        sha_dev = _sha(repo_dir, dev_branch)
        repo.git.checkout("-q", main_branch)
        _write_merge_head(repo_dir, sha_dev)
        assert (
            get_current_commit_type(str(repo_dir)) == CommitType.VERSION_RELEASE
        )

    def test_main_to_dev_boundary_is_sync_backport(
        self, repo, repo_dir, dev_branch, main_branch
    ):
        sha_main = _sha(repo_dir, main_branch)
        repo.git.checkout("-q", "-b", dev_branch)
        _commit(repo_dir, dev_branch)
        _write_merge_head(repo_dir, sha_main)
        assert get_current_commit_type(str(repo_dir)) == CommitType.SYNC_BACKPORT

    def test_unrelated_branches_merge_is_other_merge(self, repo, repo_dir):
        repo.git.checkout("-q", "-b", "hotfix")
        _commit(repo_dir, "hotfix")
        sha_hotfix = _sha(repo_dir, "hotfix")
        repo.git.checkout("-q", "-b", "release")
        _commit(repo_dir, "release")
        _write_merge_head(repo_dir, sha_hotfix)
        assert get_current_commit_type(str(repo_dir)) == CommitType.OTHER_MERGE

    def test_detached_head_merge_is_other_merge(self, repo, repo_dir):
        repo.git.checkout("-q", "-b", "add-user-authentication")
        _commit(repo_dir, "feature")
        sha_feature = _sha(repo_dir, "add-user-authentication")
        repo.git.checkout("-q", sha_feature)
        _write_merge_head(repo_dir, sha_feature)
        assert get_current_commit_type(str(repo_dir)) == CommitType.OTHER_MERGE

    def test_missing_repo_path_raises(self, tmp_path):
        with pytest.raises(git.NoSuchPathError):
            get_current_commit_type(str(tmp_path / "does_not_exist"))
