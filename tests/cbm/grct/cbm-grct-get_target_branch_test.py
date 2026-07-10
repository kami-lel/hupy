"""
cbm-grct-get_target_branch_test.py

tests for `get_target_branch` in `get_current_commit_type.py`
"""

from . import clone_repo, prepare_merge_repo, sha_of

from hupy.cbm.get_current_commit_type import get_target_branch

# tests  ########################################################################


class TestGetTargetBranchOnBranch:
    def test_returns_active_branch_name(self, repo):
        # `repo` fixture: Feature Landing merge, add-user-authentication -> dev
        assert get_target_branch(repo) == "dev"


class TestGetTargetBranchDetachedHead:
    def test_returns_none_on_detached_head(self, repo_dir):
        repo = clone_repo(repo_dir)
        sha = sha_of(repo, "main")
        repo.git.checkout("-q", sha)

        assert get_target_branch(repo) is None


class TestGetTargetBranchCaching:
    def test_result_is_cached_across_calls(self, repo):
        first = get_target_branch(repo)
        assert first == "dev"

        # the repo has since moved past the merge, but the cached
        # value must not change for this repo
        repo.git.checkout("-q", "-b", "some-other-branch")

        second = get_target_branch(repo)
        assert second == first == "dev"

    def test_separate_repos_cache_independently(self, tmp_path):
        repo_a = prepare_merge_repo(tmp_path / "repo_a", "feature_landing")
        repo_b = prepare_merge_repo(tmp_path / "repo_b", "regular_merge")

        assert get_target_branch(repo_a) == "dev"
        assert get_target_branch(repo_b) == "release"

    def test_detached_head_result_is_also_cached(self, repo_dir):
        repo = clone_repo(repo_dir)
        sha = sha_of(repo, "main")
        repo.git.checkout("-q", sha)
        first = get_target_branch(repo)
        assert first is None

        repo.git.checkout("-q", "-b", "now-on-a-branch")
        second = get_target_branch(repo)
        assert second is None
