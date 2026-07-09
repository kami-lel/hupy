"""
cbm-grct-get_current_commit_type_test.py

tests for `get_current_commit_type` in `get_current_commit_type.py`
"""

from pathlib import Path

import git
import pytest

from . import (
    clone_repo,
    commit_file,
    prepare_merge_repo,
    sha_of,
    write_merge_head,
)

from hupy.cbm.commit_type import CommitType
from hupy.cbm.get_current_commit_type import get_current_commit_type

# tests  ########################################################################


class TestGetCurrentCommitTypeRegularCommit:
    def test_no_merge_head_is_other_commit(self, repo_dir):
        clone_repo(repo_dir)
        assert (
            get_current_commit_type(str(repo_dir)) == CommitType.OTHER_COMMIT
        )


class TestGetCurrentCommitTypeOctopusMerge:
    def test_multiple_merge_heads_is_other_merge(self, repo_dir):
        repo = clone_repo(repo_dir)
        repo.git.checkout("-q", "-b", "hotfix")
        commit_file(repo_dir, "hotfix.py")
        sha_hotfix = sha_of(repo, "hotfix")
        repo.git.checkout("-q", "-b", "release")
        commit_file(repo_dir, "release.py")
        sha_release = sha_of(repo, "release")
        (Path(repo_dir) / ".git" / "MERGE_HEAD").write_text(
            "{}\n{}\n".format(sha_hotfix, sha_release)
        )

        assert get_current_commit_type(str(repo_dir)) == CommitType.OTHER_MERGE


class TestGetCurrentCommitTypePullMerge:
    def test_pull_merge_is_other_merge(self, repo_dir):
        repo = clone_repo(repo_dir)
        repo.git.checkout("-q", "-b", "dev")
        commit_file(repo_dir, "dev.py")
        sha_dev = sha_of(repo, "dev")
        repo.git.remote("remove", "origin")
        repo.git.remote("add", "origin", "https://example.invalid/repo.git")
        repo.git.update_ref("refs/remotes/origin/dev", sha_dev)
        write_merge_head(repo_dir, sha_dev)

        assert get_current_commit_type(str(repo_dir)) == CommitType.OTHER_MERGE


class TestGetCurrentCommitTypeKnownMerges:
    def test_feature_landing_is_feature_landing(self, repo_dir):
        prepare_merge_repo(repo_dir, "feature_landing")
        assert (
            get_current_commit_type(str(repo_dir))
            == CommitType.FEATURE_LANDING
        )

    def test_version_release_is_version_release(self, repo_dir):
        prepare_merge_repo(repo_dir, "version_release")
        assert (
            get_current_commit_type(str(repo_dir))
            == CommitType.VERSION_RELEASE
        )

    def test_unrelated_merge_is_other_merge(self, repo_dir):
        prepare_merge_repo(repo_dir, "regular_merge")
        assert get_current_commit_type(str(repo_dir)) == CommitType.OTHER_MERGE


class TestGetCurrentCommitTypeDetachedHead:
    def test_detached_head_merge_is_other_merge(self, repo_dir):
        repo = clone_repo(repo_dir)
        repo.git.checkout("-q", "-b", "add-user-authentication")
        commit_file(repo_dir, "feature.py")
        sha_feature = sha_of(repo, "add-user-authentication")
        repo.git.checkout("-q", sha_feature)
        write_merge_head(repo_dir, sha_feature)

        assert get_current_commit_type(str(repo_dir)) == CommitType.OTHER_MERGE


class TestGetCurrentCommitTypeErrors:
    def test_missing_repo_path_raises(self, tmp_path):
        with pytest.raises(git.NoSuchPathError):
            get_current_commit_type(str(tmp_path / "does_not_exist"))


class TestGetCurrentCommitTypeCaching:
    def test_result_is_cached_across_calls(self, repo_dir):
        prepare_merge_repo(repo_dir, "feature_landing")
        first = get_current_commit_type(str(repo_dir))
        assert first == CommitType.FEATURE_LANDING

        # MERGE_HEAD is gone now, but the cached value must not
        # change for this repo path
        (Path(repo_dir) / ".git" / "MERGE_HEAD").unlink()

        second = get_current_commit_type(str(repo_dir))
        assert second == first == CommitType.FEATURE_LANDING

    def test_separate_repo_paths_cache_independently(self, tmp_path):
        dir_a = tmp_path / "repo_a"
        dir_b = tmp_path / "repo_b"
        prepare_merge_repo(dir_a, "feature_landing")
        prepare_merge_repo(dir_b, "version_release")

        assert (
            get_current_commit_type(str(dir_a)) == CommitType.FEATURE_LANDING
        )
        assert (
            get_current_commit_type(str(dir_b)) == CommitType.VERSION_RELEASE
        )
